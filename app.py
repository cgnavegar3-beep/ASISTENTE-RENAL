import streamlit as st
from datetime import datetime
from PIL import Image
import io

# -------------------------------------------
# INYECCIÓN DE ESTILOS CSS PARA GLOW Y TAB
# -------------------------------------------
def inject_ui_styles():
    st.markdown("""
    <style>
    .model-indicator { background-color: black; color: white; font-size: 12px; padding: 3px; display:inline-block; }
    .fg-glow-box { background-color: black; color: white; padding: 10px; font-weight:bold; border-radius: 8px; box-shadow: 0 0 10px #8A2BE2; text-align:center;}
    .flash-verde { animation: glow-verde 1s ease-in-out; }
    .flash-naranja { animation: glow-naranja 1s ease-in-out; }
    .flash-rojo { animation: glow-rojo 1s ease-in-out; }
    @keyframes glow-verde { 0% {box-shadow: 0 0 0 #00ff00;} 50% {box-shadow: 0 0 20px #00ff00;} 100% {box-shadow: 0 0 0 #00ff00;} }
    @keyframes glow-naranja { 0% {box-shadow: 0 0 0 #ffa500;} 50% {box-shadow: 0 0 20px #ffa500;} 100% {box-shadow: 0 0 0 #ffa500;} }
    @keyframes glow-rojo { 0% {box-shadow: 0 0 0 #ff0000;} 50% {box-shadow: 0 0 20px #ff0000;} 100% {box-shadow: 0 0 0 #ff0000;} }
    hr { border: none; border-top: 1px solid #ccc; margin: 10px 0; }
    .warning-bar { background-color: #fff3cd; color:#856404; padding:10px; font-weight:bold; }
    </style>
    """, unsafe_allow_html=True)

inject_ui_styles()

# -------------------------------------------
# SESIÓN STATE INICIAL
# -------------------------------------------
if "meds_input" not in st.session_state:
    st.session_state.meds_input = ""
if "fg_manual" not in st.session_state:
    st.session_state.fg_manual = None
if "cache_result" not in st.session_state:
    st.session_state.cache_result = {}
if "active_model_name" not in st.session_state:
    st.session_state.active_model_name = "Modelo activo"
if "reset_counter" not in st.session_state:
    st.session_state.reset_counter = 0
if "vademecum_data" not in st.session_state:
    st.session_state.vademecum_data = None

# -------------------------------------------
# FUNCIONES AUXILIARES
# -------------------------------------------
def get_current_date():
    return datetime.now().strftime("%d/%m/%Y")

@st.cache_resource
def get_vademecum_data():
    # Simula lectura del PDF una sola vez
    return {"Dabigatrán": {"Grupo": "Anticoagulantes orales", "100-50": "150 mg/día", "50-10": "75 mg/día", "<10": "No usar"}}

def calcular_fg(edad, peso, creat, sexo, metodo="CKD-EPI"):
    # Dummy cálculo de FG
    fg = (140 - edad) * peso / (72 * creat)
    if sexo == "Mujer":
        fg *= 0.85
    return round(fg, 1), metodo

def process_image(img_pil):
    # Convierte imagen a RGB y simula extracción de texto
    img_rgb = img_pil.convert("RGB")
    # Aquí se llamaría model.generate_content(img_rgb)
    return "Paracetamol\nIbuprofeno"  # Simulación

def validate_meds_list(meds_list, fg_value):
    vademecum = st.session_state.vademecum_data
    results = []
    color = "verde"
    acciones = []
    for med in meds_list.split("\n"):
        med = med.strip()
        if not med:
            continue
        if med in vademecum:
            grupo = vademecum[med]["Grupo"]
            if fg_value >=50:
                dosis = vademecum[med]["100-50"]
            elif 10 <= fg_value < 50:
                dosis = vademecum[med]["50-10"]
            else:
                dosis = vademecum[med]["<10"]
        else:
            # fallback IA
            grupo = "Desconocido"
            dosis = "Consultar fuentes oficiales"
        results.append(f"{med} ({grupo}): {dosis}")
        # determinar color de cuadro y acciones
        if "<10" in dosis or "No usar" in dosis:
            color = "rojo"
            acciones.append(f"🔴 {med}: Riesgo elevado de efectos adversos. Evitar.")
        elif "50-10" in dosis:
            if color != "rojo":
                color = "naranja"
            acciones.append(f"🟠 {med}: Valorar ajuste de dosis y control clínico.")
        else:
            acciones.append(f"🟢 {med}: Dosis estándar.")
    return results, acciones, color

def reset_app():
    st.session_state.meds_input = ""
    st.session_state.fg_manual = None
    st.session_state.reset_counter += 1

# -------------------------------------------
# RENDER TAB VALIDACION
# -------------------------------------------
def render_tab_validacion():
    st.subheader("Asistente Renal")

    # -----------------------------
    # Fila Superior: Centro, Edad, Residencia, Fecha
    # -----------------------------
    col1, col2, col3 = st.columns([2,4,2])
    with col1:
        centro = st.text_input("Centro", value="G/M", key="centro_input")
    with col2:
        edad = st.number_input("Edad", min_value=0, max_value=120, value=65, key="edad_input")
        cuadro_alfa = st.text_input("Código Alfanumérico", value="XXX", key="alfa_input")
        residencia = st.selectbox("Residencia", ["No", "Sí"], key="residencia_input")
    with col3:
        fecha_actual = st.text_input("Fecha", value=get_current_date(), disabled=True)
    st.write(f"ID Registro: {centro}-{edad}-{cuadro_alfa}")

    st.markdown("---")

    # -----------------------------
    # Calculadora FG
    # -----------------------------
    col_calc, col_ajuste = st.columns([1,1])
    with col_calc:
        st.write("📋 Calculadora")
        st.write("Método: CKD-EPI")
        peso = st.number_input("Peso (kg)", min_value=0.0, value=70.0, step=0.5)
        creat = st.number_input("Creatinina (mg/dL)", min_value=0.0, value=1.0, step=0.01)
        sexo = st.selectbox("Sexo", ["Hombre","Mujer"])
        fg_calc, metodo = calcular_fg(edad, peso, creat, sexo)
    with col_ajuste:
        st.write("💊 Ajuste y Captura")
        fg_manual = st.text_input("FG Manual", value="", key="fg_manual_input")
        fg_final = float(fg_manual) if fg_manual else fg_calc
        st.markdown(f'<div class="fg-glow-box">{fg_final} mL/min<br><small>{ "Manual" if fg_manual else metodo }</small></div>', unsafe_allow_html=True)

        # Zona de carga multimodal
        uploaded_file = st.file_uploader("📁 Subir archivo", type=["png","jpg","jpeg"])
        if uploaded_file:
            img = Image.open(uploaded_file)
            st.session_state.meds_input = process_image(img)
        paste_button = st.button("📋 Pegar Recorte / Ctrl+V")
        if paste_button:
            st.warning("Funcionalidad de pegado simulada")  # placeholder

    st.markdown("---")

    # -----------------------------
    # Listado de medicamentos
    # -----------------------------
    st.write("📝 Listado de medicamentos")
    meds_input = st.text_area("Escribe o edita la lista del archivo o captura subidos", value=st.session_state.meds_input, height=200)
    st.session_state.meds_input = meds_input

    # -----------------------------
    # Botones de acción
    # -----------------------------
    col_val, col_reset = st.columns([7,1])
    with col_val:
        if st.button("🚀 VALIDAR ADECUACIÓN"):
            results, acciones, color = validate_meds_list(st.session_state.meds_input, fg_final)
            glow_class = f"flash-{color}"
            st.markdown(f'<div class="fg-glow-box {glow_class}">{"<br>".join(results)}</div>', unsafe_allow_html=True)
            st.markdown(f'<div>{"<br>".join(acciones)}</div>', unsafe_allow_html=True)
            # Aquí se podría añadir lógica de guardar a Excel
    with col_reset:
        if st.button("🗑️ RESET"):
            reset_app()
            st.experimental_rerun()

    # -----------------------------
    # Aviso de seguridad permanente
    # -----------------------------
    st.markdown('<div class="warning-bar">⚠️ Aviso: Esta herramienta es un apoyo a la revisión farmacoterapéutica. Puede contener errores. Verifique con fuentes oficiales.</div>', unsafe_allow_html=True)

# -------------------------------------------
# MAIN
# -------------------------------------------
render_tab_validacion()
