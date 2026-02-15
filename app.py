import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import io
import numpy as np
import datetime

# --- 1. CONFIGURACIÓN E INICIALIZACIÓN ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

if 'active_model_name' not in st.session_state:
    st.session_state.active_model_name = "1.5 Pro"
if 'meds_input' not in st.session_state:
    st.session_state.meds_input = ""
if 'cache_result' not in st.session_state:
    st.session_state.cache_result = None
if 'last_query' not in st.session_state:
    st.session_state.last_query = ""
if 'reset_counter' not in st.session_state:
    st.session_state.reset_counter = 0

# --- 2. GESTIÓN DE MODELOS (CASCADA CON FALLBACK) ---
def run_ia_task(prompt, image_bytes=None):
    models_to_try = [
        ("gemini-1.5-pro", "1.5 Pro"),
        ("gemini-2.5-flash", "2.5 Flash")
    ]
    for model_id, tech_name in models_to_try:
        try:
            st.session_state.active_model_name = tech_name
            genai.configure(api_key=st.secrets["API_KEY"])
            model = genai.GenerativeModel(model_id)
            content = [prompt] if prompt else []
            if image_bytes:
                content.append({'mime_type': 'image/png', 'data': image_bytes})
            response = model.generate_content(content)
            return response.text
        except Exception:
            continue
    return "Fallo de conexión o superado el número de intentos"

# --- 3. LECTURA DE PDF ---
@st.cache_resource
def get_vademecum_data():
    try:
        doc = fitz.open("vademecum_renal.pdf")
        return "".join([page.get_text() for page in doc])
    except: return ""

# --- 4. ESTILOS CSS (ESTRUCTURA BLINDADA) ---
def inject_ui_styles():
    st.markdown(f"""
    <style>
        .model-indicator {{
            position: fixed; top: 10px; left: 10px; background-color: #000; color: #0F0;
            padding: 5px 15px; font-family: 'Courier New', monospace; font-size: 13px;
            font-weight: bold; border-radius: 5px; z-index: 999999;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.5);
        }}
        div[role="tablist"] {{ gap: 10px; }}
        div[role="tab"]:not([aria-selected="false"]) {{
            color: #6a0dad !important; font-weight: bold !important; border-bottom: 3px solid #6a0dad !important;
        }}
        .fg-glow-box {{
            background-color: #000; color: #fff; border-radius: 12px;
            padding: 15px; text-align: center; border: 2px solid #6a0dad;
            box-shadow: 0 0 20px #a020f0; margin: 5px 0; display: flex;
            flex-direction: column; justify-content: center;
        }}
        .fg-glow-box h1 {{ margin: 0; font-size: 45px; color: #fff !important; line-height: 1; }}
        
        /* Estilo para el campo de fecha bloqueado */
        .stTextInput input:disabled {{
            background-color: #f0f2f6 !important;
            color: #555 !important;
            cursor: not-allowed;
        }}

        @keyframes flash-glow {{ 0% {{ filter: brightness(1); }} 50% {{ filter: brightness(1.6); }} 100% {{ filter: brightness(1); }} }}
        .result-flash {{
            animation: flash-glow 0.7s ease-in-out;
            padding: 20px; border-radius: 15px; margin-top: 20px;
            border: 1px solid rgba(0,0,0,0.1);
        }}
        .aviso-prof {{
            background-color: #fff9c4; padding: 12px; border-radius: 8px;
            border: 1px solid #fbc02d; font-size: 13px; margin-top: 25px;
            text-align: center; box-shadow: 2px 2px 8px rgba(0,0,0,0.05);
        }}
    </style>
    <div class="model-indicator">{st.session_state.active_model_name}</div>
    """, unsafe_allow_html=True)

# --- 5. LÓGICA DE VALIDACIÓN ---
def render_tab_validacion():
    # --- BLOQUE DE REGISTRO (AÑADIDO) ---
    st.markdown("### Registro del Paciente")
    col_reg1, col_reg2, col_reg3, col_reg4 = st.columns([2, 2.5, 1, 1.5])
    
    with col_reg1:
        reg_centro = st.text_input("Centro", value="g/M", key="reg_centro")
    
    with col_reg2:
        c_edad, c_alfa, c_resi = st.columns([1, 1, 1.2])
        with c_edad:
            reg_edad = st.number_input("Edad", 0, 115, 75, key="reg_edad")
        with c_alfa:
            reg_alfa = st.text_input("Cuadro Alfanum.", value="000", key="reg_alfa")
        with c_resi:
            reg_resi = st.selectbox("Residencia", ["No", "Sí"], key="reg_resi")
            
    with col_reg4:
        fecha_str = datetime.datetime.now().strftime("%d/%m/%Y")
        st.text_input("Fecha Actual", value=fecha_str, disabled=True)
    
    # ID Registro dinámico
    id_paciente = f"{reg_centro}-{reg_edad}-{reg_alfa}"
    st.markdown(f"<p style='font-size:11px; color:gray; margin-top:-15px;'>ID Registro: {id_paciente}</p>", unsafe_allow_html=True)
    
    st.write("---")

    col_izq, col_der = st.columns(2, gap="large")
    
    with col_izq:
        st.subheader("📋 Calculadora")
        with st.container(border=True):
            # Usamos reg_edad del bloque de registro para sincronizar
            ed = st.number_input("Edad (confirmar)", 18, 110, reg_edad)
            ps = st.number_input("Peso (kg)", 35, 180, 70)
            cr = st.number_input("Creatinina (mg/dL)", 0.4, 15.0, 1.1)
            sx = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
            f_sex = 0.85 if sx == "Mujer" else 1.0
            fg_calc = round((((140 - ed) * ps) / (72 * cr)) * f_sex, 1)

    with col_der:
        st.subheader("💊 Ajuste y Captura")
        fg_man = st.text_input("Introducir FG Manual", placeholder="Vacío para auto-cálculo")
        
        # Lógica de cálculo o manual
        try:
            fg_final = float(fg_man.replace(",", ".")) if fg_man and fg_man.replace(",",".").replace(".","").isdigit() else fg_calc
        except:
            fg_final = fg_calc
            
        metodo = "CKD-EPI / Cockcroft-Gault" if not fg_man else "Manual"
        
        st.markdown(f"""
            <div class="fg-glow-box" style="height: 120px;">
                <h1>{fg_final}</h1>
                <div style="font-size: 10px; color: #aaa; margin-top: 5px;">mL/min (FG) - {metodo}</div>
            </div>
        """, unsafe_allow_html=True)

        # ZONA DE CARGA MULTIMODAL
        st.write("") # Espaciador
        c_file, c_paste = st.columns([0.6, 0.4])
        img_file = None
        
        with c_file:
            uploaded_file = st.file_uploader("Subir", type=['png','jpg','jpeg'], label_visibility="collapsed", key=f"up_{st.session_state.reset_counter}")
            if uploaded_file: 
                img_file = Image.open(uploaded_file).convert("RGB")
        
        with c_paste:
            try:
                from streamlit_paste_button import paste_image_button
                p = paste_image_button("📋 Pegar Recorte", key=f"paste_{st.session_state.reset_counter}")
                if p and p.image_data is not None:
                    img_file = p.image_data.convert("RGB") if isinstance(p.image_data, Image.Image) else Image.fromarray(np.uint8(p.image_data)).convert("RGB")
            except: pass

        if img_file:
            buf = io.BytesIO()
            img_file.save(buf, format="PNG")
            with st.spinner("TRANSCRIBIENDO..."):
                res_ocr = run_ia_task("Extrae nombres de fármacos y dosis. Si detectas nombres de personas, responde PROTECCION_DATOS.", buf.getvalue())
                if "PROTECCION_DATOS" in res_ocr:
                    st.error("No se puede mostrar el resultado al encontrar datos personales")
                elif "Fallo" not in res_ocr:
                    st.session_state.meds_input = res_ocr
                    st.rerun()

    st.write("---")
    meds_text = st.text_area(
        "Listado de medicamentos",
        value=st.session_state.meds_input,
        placeholder="Escribe o edita la lista aquí...",
        height=180,
        key=f"meds_area_{st.session_state.reset_counter}"
    )
    st.session_state.meds_input = meds_text

    c_act1, c_act2 = st.columns([0.85, 0.15])
    with c_act1:
        validar_click = st.button("🚀 VALIDAR ADECUACIÓN FARMACOLÓGICA", use_container_width=True)
    with c_act2:
        if st.button("🗑️ RESET", use_container_width=True):
            st.session_state.meds_input = ""
            st.session_state.cache_result = None
            st.session_state.reset_counter += 1
            st.rerun()

    if validar_click:
        if not meds_text.strip():
            st.warning("Por favor, introduce medicamentos.")
        else:
            query_id = f"{fg_final}-{meds_text}"
            if query_id == st.session_state.last_query and st.session_state.cache_result:
                res = st.session_state.cache_result
            else:
                v_data = get_vademecum_data()
                with st.spinner("PROCESANDO..."):
                    prompt = f"Actúa como farmacéutico clínico. Analiza la adecuación renal para un FG de {fg_final} mL/min. Vademecum: {v_data[:3500]}. Usa iconos ⚠️ para ajuste y ⛔ para contraindicación."
                    res = run_ia_task(prompt)
                    st.session_state.cache_result = res
                    st.session_state.last_query = query_id

            bg = "#c8e6c9" if "⛔" not in res and "⚠️" not in res else "#ffcdd2" if "⛔" in res else "#ffe0b2"
            st.markdown(f'<div class="result-flash" style="background-color: {bg}; box-shadow: 0 0 35px {bg};">{res}</div>', unsafe_allow_html=True)

    st.markdown('<div class="aviso-prof">⚠️ Aviso: Esta herramienta es un apoyo a la revisión farmacoterapéutica. Verifique siempre con fuentes oficiales.</div>', unsafe_allow_html=True)

# --- 6. ESTRUCTURA DE PESTAÑAS ---
def main():
    inject_ui_styles()
    st.title("ASISTENTE RENAL")
    t1, t2, t3, t4 = st.tabs(["💊 VALIDACION", "📄 INFORME", "📊 EXCEL", "📈 GRAFICOS"])
    with t1: render_tab_validacion()
    with t2: st.info("Pestaña Informe...")
    with t3: st.info("Pestaña Excel...")
    with t4: st.info("Pestaña Gráficos...")

if __name__ == "__main__":
    main()
