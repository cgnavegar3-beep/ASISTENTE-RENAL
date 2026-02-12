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

# --- 2. GESTIÓN DE MODELOS (CASCADA) ---
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
    return "ERROR: Fallo de conexión o superado el número de intentos"

# --- 3. LECTURA ÚNICA DE PDF ---
@st.cache_resource
def get_vademecum_data():
    try:
        doc = fitz.open("vademecum_renal.pdf")
        text = "".join([page.get_text() for page in doc])
        return text
    except: return ""

# --- 4. ESTILOS CSS (ESTRUCTURA BLINDADA Y ALINEACIÓN) ---
def inject_ui_styles():
    st.markdown(f"""
    <style>
        .model-indicator {{
            position: fixed; top: 10px; left: 10px; background-color: #000; color: #0F0;
            padding: 4px 12px; font-family: monospace; font-size: 11px;
            border-radius: 4px; z-index: 9999; border: 1px solid #333;
        }}
        /* Pestañas Excel */
        div[role="tablist"] {{ gap: 8px; }}
        div[role="tab"]:not([aria-selected="false"]) {{
            color: #6a0dad !important; font-weight: bold !important; border-bottom: 3px solid #6a0dad !important;
        }}
        /* Cuadro FG Glow Morado */
        .fg-glow-box {{
            background-color: #000; color: #fff; border-radius: 12px;
            padding: 15px; text-align: center; border: 2px solid #6a0dad;
            box-shadow: 0 0 20px #a020f0; margin: 5px 0;
        }}
        .fg-glow-box h1 {{ margin: 0; font-size: 42px; color: #fff !important; line-height: 1; }}
        .fg-small {{ font-size: 10px; color: #aaa; margin-top: 5px; }}

        /* Efecto Destello / Flash Glow para Resultados */
        @keyframes flash-glow {{
            0% {{ filter: brightness(1); transform: scale(1); }}
            50% {{ filter: brightness(1.5); transform: scale(1.02); }}
            100% {{ filter: brightness(1); transform: scale(1); }}
        }}
        .result-flash {{
            animation: flash-glow 0.6s ease-in-out;
            padding: 20px; border-radius: 15px; margin-top: 20px;
            border: 1px solid rgba(255,255,255,0.2);
        }}
        
        /* Alineación vertical de columnas */
        [data-testid="column"] {{ display: flex; flex-direction: column; justify-content: space-between; }}
        .stButton button {{ width: 100%; }}
        .aviso-prof {{ background-color: #fffde7; padding: 10px; border-radius: 5px; border-left: 5px solid #ffd600; font-size: 12px; margin-bottom: 15px; }}
    </style>
    <div class="model-indicator">{st.session_state.active_model_name}</div>
    """, unsafe_allow_html=True)

# --- 5. LÓGICA DE VALIDACIÓN ---
def render_tab_validacion():
    st.markdown('<div class="aviso-prof">⚠️ Aviso: Esta herramienta es un apoyo a la revisión farmacoterapéutica. Verifique siempre con fuentes oficiales.</div>', unsafe_allow_html=True)
    
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
        fg_man = st.text_input("Introducir FG Manual", placeholder="Dejar vacío para auto-cálculo")
        
        # Nivel 2: Cuadro Glow
        fg_final = float(fg_man.replace(",", ".")) if fg_man and fg_man.replace(",",".").replace(".","").isdigit() else fg_calc
        metodo = "Fórmula Cockcroft-Gault" if not fg_man else "Valor Manual introducido"
        st.markdown(f"""
            <div class="fg-glow-box">
                <h1>{fg_final}</h1>
                <div class="fg-small">mL/min (FG) - {metodo}</div>
            </div>
        """, unsafe_allow_html=True)

        # Nivel 3: Zona de Imagen (Subida + Pegado)
        c_file, c_paste = st.columns([0.6, 0.4])
        img_temp = None
        with c_file:
            f = st.file_uploader("Imagen", type=['png','jpg','jpeg'], label_visibility="collapsed")
            if f: img_temp = Image.open(f).convert("RGB")
        with c_paste:
            try:
                from streamlit_paste_button import paste_image_button
                p = paste_image_button("📋 Pegar Recorte")
                if p and p.image_data is not None:
                    img_temp = p.image_data.convert("RGB") if isinstance(p.image_data, Image.Image) else Image.fromarray(np.uint8(p.image_data)).convert("RGB")
            except: pass

        if img_temp:
            buf = io.BytesIO()
            img_temp.save(buf, format="PNG")
            with st.spinner("TRANSCRIBIENDO..."):
                res_ocr = run_ia_task("Extrae nombres y dosis. Solo texto plano.", buf.getvalue())
                if "ERROR" not in res_ocr:
                    st.session_state.meds_input = res_ocr

    st.write("---")
    meds_text = st.text_area(
        "Listado de medicamentos",
        value=st.session_state.meds_input,
        placeholder="Escribe o edita la lista que se reproducirá aquí si se ha pegado un RECORTE o se ha subido un pantallazo o imagen.",
        height=180
    )
    st.session_state.meds_input = meds_text

    if st.button("🚀 VALIDAR ADECUACIÓN FARMACOLÓGICA", use_container_width=True):
        query_id = f"{fg_final}-{meds_text}"
        if query_id == st.session_state.last_query and st.session_state.cache_result:
            res = st.session_state.cache_result
        else:
            v_data = get_vademecum_data()
            with st.spinner("ANALIZANDO..."):
                prompt = f"""Cruza esta lista: {meds_text} con FG: {fg_final}. 
                Contexto PDF: {v_data[:4000]}. 
                Reglas: Iconos ⚠️/⛔, colores según riesgo. No menciones el PDF."""
                res = run_ia_task(prompt)
                st.session_state.cache_result = res
                st.session_state.last_query = query_id

        # Semáforo de Fondo y Destello
        bg = "#c8e6c9" if "⛔" not in res and "⚠️" not in res else "#ffcdd2" if "⛔" in res else "#ffe0b2"
        st.markdown(f'<div class="result-flash" style="background-color: {bg}; box-shadow: 0 0 40px {bg};">{res}</div>', unsafe_allow_html=True)

# --- 6. ESTRUCTURA DE PESTAÑAS ---
def main():
    inject_ui_styles()
    st.title("ASISTENTE RENAL")
    
    t1, t2, t3, t4 = st.tabs(["💊 VALIDACION", "📄 INFORME", "📊 EXCEL", "📈 GRAFICOS"])
    
    with t1: render_tab_validacion()
    with t2: st.info("Módulo Informe...")
    with t3: st.info("Módulo Recogida de Datos...")
    with t4: st.info("Módulo Evolución Gráfica...")

    if st.sidebar.button("🗑️ LIMPIAR DATOS"):
        st.session_state.meds_input = ""
        st.session_state.cache_result = None
        st.rerun()

if __name__ == "__main__":
    main()
