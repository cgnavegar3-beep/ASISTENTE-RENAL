import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import io
import numpy as np

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
        /* Contador Inteligente: Fondo negro, letras verdes, arriba izq */
        .model-indicator {{
            position: fixed; top: 10px; left: 10px; background-color: #000; color: #0F0;
            padding: 5px 15px; font-family: 'Courier New', monospace; font-size: 13px;
            font-weight: bold; border-radius: 5px; z-index: 999999; border: 1px solid #333;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.5);
        }}
        /* Pestañas Excel */
        div[role="tablist"] {{ gap: 10px; }}
        div[role="tab"]:not([aria-selected="false"]) {{
            color: #6a0dad !important; font-weight: bold !important; border-bottom: 3px solid #6a0dad !important;
        }}
        /* Cuadro FG Glow Morado */
        .fg-glow-box {{
            background-color: #000; color: #fff; border-radius: 12px;
            padding: 15px; text-align: center; border: 2px solid #6a0dad;
            box-shadow: 0 0 20px #a020f0; margin: 5px 0; display: flex; flex-direction: column; justify-content: center;
        }}
        .fg-glow-box h1 {{ margin: 0; font-size: 45px; color: #fff !important; line-height: 1; }}
        /* Resultado con Destello Flash */
        @keyframes flash-glow {{
            0% {{ filter: brightness(1); }}
            50% {{ filter: brightness(1.6); }}
            100% {{ filter: brightness(1); }}
        }}
        .result-flash {{
            animation: flash-glow 0.7s ease-in-out;
            padding: 20px; border-radius: 15px; margin-top: 20px;
            border: 1px solid rgba(0,0,0,0.1);
        }}
        /* Aviso Profesional Amarillo Pálido */
        .aviso-prof {{
            background-color: #fff9c4; padding: 12px; border-radius: 8px;
            border: 1px solid #fbc02d; font-size: 13px; margin-top: 25px;
            text-align: center; box-shadow: 2px 2px 8px rgba(0,0,0,0.05);
        }}
        [data-testid="column"] {{ display: flex; flex-direction: column; justify-content: space-between; }}
    </style>
    <div class="model-indicator">{st.session_state.active_model_name}</div>
    """, unsafe_allow_html=True)

# --- 5. LÓGICA DE VALIDACIÓN ---
def render_tab_validacion():
    col_izq, col_der = st.columns(2, gap="large")
    
    with col_izq:
        st.subheader("📋 Calculadora")
        with st.container(border=True):
            ed = st.number_input("Edad", 18, 110, 75)
            ps = st.number_input("Peso (kg)", 35, 180, 70)
            cr = st.number_input("Creatinina (mg/dL)", 0.4, 15.0, 1.1)
            sx = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
            f_sex = 0.85 if sx == "Mujer" else 1.0
            fg_calc = round((((140 - ed) * ps) / (72 * cr)) * f_sex, 1)

    with col_der:
        st.subheader("💊 Ajuste y Captura")
        # Nivel 1: Input Manual
        fg_man = st.text_input("Introducir FG Manual", placeholder="Vacío para auto-cálculo")
        
        # Nivel 2: Cuadro Glow
        fg_final = float(fg_man.replace(",", ".")) if fg_man and fg_man.replace(",",".").replace(".","").isdigit() else fg_calc
        metodo = "CKD-EPI / MDRD" if not fg_man else "Manual"
        st.markdown(f"""
            <div class="fg-glow-box" style="height: 120px;">
                <h1>{fg_final}</h1>
                <div style="font-size: 10px; color: #aaa; margin-top: 5px;">mL/min (FG) - {metodo}</div>
            </div>
        """, unsafe_allow_html=True)

        # Nivel 3: Zona de Imagen (Subida + Pegado) con TRANSCRIPCIÓN BLINDADA
        c_file, c_paste = st.columns([0.6, 0.4])
        img_file = None
        
        with c_file:
            uploaded_file = st.file_uploader("Subir", type=['png','jpg','jpeg'], label_visibility="collapsed", key="file_up")
            if uploaded_file:
                img_file = Image.open(uploaded_file).convert("RGB")
        
        with c_paste:
            try:
                from streamlit_paste_button import paste_image_button
                p = paste_image_button("📋 Pegar Recorte")
                if p and p.image_data is not None:
                    img_file = p.image_data.convert("RGB") if isinstance(p.image_data, Image.Image) else Image.fromarray(np.uint8(p.image_data)).convert("RGB")
            except: pass

        # Ejecutar OCR si hay imagen nueva
        if img_file:
            buf = io.BytesIO()
            img_file.save(buf, format="PNG")
            with st.spinner("TRANSCRIBIENDO..."):
                res_ocr = run_ia_task("Extrae nombres y dosis. Solo texto plano.", buf.getvalue())
                if "Fallo" not in res_ocr:
                    st.session_state.meds_input = res_ocr

    st.write("---")
    meds_text = st.text_area(
        "Listado de medicamentos",
        value=st.session_state.meds_input,
        placeholder="Escribe o edita la lista que se reproducirá aquí si se ha pegado un RECORTE o se ha subido un pantallazo o imagen.",
        height=180,
        key="meds_area_main"
    )
    st.session_state.meds_input = meds_text

    # BOTONES DE ACCIÓN (Validar y Reset juntos)
    c_act1, c_act2 = st.columns([0.85, 0.15])
    with c_act1:
        validar_click = st.button("🚀 VALIDAR ADECUACIÓN FARMACOLÓGICA", use_container_width=True)
    with c_act2:
        if st.button("🗑️ RESET", use_container_width=True):
            st.session_state.meds_input = ""
            st.session_state.cache_result = None
            st.rerun()

    if validar_click:
        query_id = f"{fg_final}-{meds_text}"
        if query_id == st.session_state.last_query and st.session_state.cache_result:
            res = st.session_state.cache_result
        else:
            v_data = get_vademecum_data()
            with st.spinner("PROCESANDO..."):
                prompt = f"Analiza: {meds_text} con FG: {fg_final}. Vademecum: {v_data[:3500]}. Iconos ⚠️/⛔."
                res = run_ia_task(prompt)
                st.session_state.cache_result = res
                st.session_state.last_query = query_id

        bg = "#c8e6c9" if "⛔" not in res and "⚠️" not in res else "#ffcdd2" if "⛔" in res else "#ffe0b2"
        st.markdown(f'<div class="result-flash" style="background-color: {bg}; box-shadow: 0 0 35px {bg};">{res}</div>', unsafe_allow_html=True)

    # Aviso Profesional al final de la pestaña
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
