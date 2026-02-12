import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import io
import numpy as np

# --- 1. CONFIGURACIÓN E INICIALIZACIÓN ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

if 'active_model_idx' not in st.session_state:
    st.session_state.active_model_idx = 0
if 'meds_input' not in st.session_state:
    st.session_state.meds_input = ""

# Cascada actualizada a 2.5 Flash
MODELS = ["gemini-1.5-pro", "gemini-2.5-flash"]

def get_active_model_name():
    raw_name = MODELS[st.session_state.active_model_idx]
    return raw_name.replace("gemini-", "").replace("-", " ").title()

def run_ia_task(prompt, image_bytes=None):
    """Cascada de modelos con actualización de UI previa al intento."""
    for i in range(len(MODELS)):
        st.session_state.active_model_idx = i
        try:
            genai.configure(api_key=st.secrets["API_KEY"])
            model = genai.GenerativeModel(MODELS[i])
            content = [prompt] if prompt else []
            if image_bytes:
                content.append({'mime_type': 'image/png', 'data': image_bytes})
            response = model.generate_content(content)
            return response.text
        except Exception:
            continue
    return "ERROR"

# --- 2. ESTILOS CSS (ESTILO EXCEL / BARRA INFERIOR) ---
def inject_ui_styles():
    model_name = get_active_model_name()
    st.markdown(f"""
    <style>
        .discreet-v {{
            position: fixed; top: 0; left: 0; background-color: #000; color: #0F0;
            padding: 5px 15px; font-family: monospace; font-size: 11px;
            z-index: 999999; border-bottom-right-radius: 10px; border: 1px solid #333;
        }}
        /* Pestañas: Texto activo con barra inferior roja */
        div[role="tab"]:not([aria-selected="false"]) {{
            color: #FF4B4B !important; font-weight: bold !important; position: relative;
        }}
        div[role="tab"]:not([aria-selected="false"]) p {{ color: #FF4B4B !important; }}
        div[role="tab"]:not([aria-selected="false"])::after {{
            content: ""; position: absolute; left: 20%; bottom: 0; width: 60%; height: 3px;
            background-color: #FF4B4B; border-radius: 2px;
        }}
        div[role="tab"][aria-selected="false"] {{ color: #555 !important; }}
        button[data-baseweb="tab"] {{ background-color: transparent !important; border: none !important; }}
        
        .fg-glow-box {{
            background-color: #000 !important; color: #fff !important;
            padding: 15px; border-radius: 12px; text-align: center;
            border: 2px solid #6a0dad; box-shadow: 0 0 20px #a020f0; margin: 10px 0;
        }}
        .fg-glow-box h1 {{ font-size: 48px !important; margin: 0; }}
        .result-card {{ padding: 20px; border-radius: 15px; margin-top: 15px; color: #000; border: 1px solid #ddd; }}
    </style>
    <div class="discreet-v">V-{model_name}</div>
    """, unsafe_allow_html=True)

# --- 3. MÓDULO DE VALIDACIÓN (BLOQUE DE CAPTURA COMPLETADO) ---
def render_tab_validacion():
    col_izq, col_der = st.columns([0.4, 0.6], gap="large")
    
    with col_izq:
        st.subheader("📋 Parámetros")
        ed = st.number_input("Edad", 18, 110, 75)
        ps = st.number_input("Peso (kg)", 35, 180, 70)
        cr = st.number_input("Creatinina (mg/dL)", 0.4, 15.0, 1.1)
        sx = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
        f_sex = 0.85 if sx == "Mujer" else 1.0
        fg_calc = round((((140 - ed) * ps) / (72 * cr)) * f_sex, 1)
        st.markdown(f'<div class="fg-glow-box"><h1>{fg_calc}</h1><p>mL/min (FG)</p></div>', unsafe_allow_html=True)

    with col_der:
        st.subheader("💊 Captura de Medicación")
        c1, c2 = st.columns([0.6, 0.4])
        img_temp = None

        # --- Subida de archivo ---
        with c1:
            f = st.file_uploader("Subir imagen", type=['png','jpg','jpeg'], label_visibility="collapsed")
            if f:
                img_temp = Image.open(f).convert("RGB")

        # --- Pegar recorte ---
        with c2:
            try:
                from streamlit_paste_button import paste_image_button
                p = paste_image_button("📋 Pegar Recorte")
                if p and p.image_data is not None:
                    img_temp = p.image_data.convert("RGB") if isinstance(p.image_data, Image.Image) else Image.fromarray(np.uint8(p.image_data)).convert("RGB")
            except:
                pass

        # --- Procesar OCR (Bloque Crítico) ---
        if img_temp:
            buf = io.BytesIO()
            img_temp.save(buf, format="PNG")
            with st.spinner("TRANSCRIBIENDO..."):
                res_ocr = run_ia_task("Extrae nombres y dosis. Solo texto plano.", buf.getvalue())
            
            if res_ocr != "ERROR":
                st.session_state.meds_input = res_ocr

        st.write("---")
        # Text area sincronizado con session_state sin rerun
        meds_text = st.text_area(
            "Listado para validar:",
            value=st.session_state.meds_input,
            height=200,
            key="meds_area_ocr"
        )
        # Actualizamos el estado para la validación posterior
        st.session_state.meds_input = meds_text

    if st.button("🚀 VALIDAR AJUSTES", use_container_width=True):
        if st.session_state.meds_input:
            with st.spinner("Analizando..."):
                res = run_ia_task(f"Analiza ajustes para FG {fg_calc} en esta lista: {st.session_state.meds_input}")
                bg = "#ffcdd2" if "⛔" in res else "#ffe0b2" if "⚠️" in res else "#c8e6c9"
                st.markdown(f'<div class="result-card" style="background-color: {bg};">{res}</div>', unsafe_allow_html=True)

# --- 4. ESTRUCTURA DE PESTAÑAS ---
def main():
    inject_ui_styles()
    st.title("ASISTENTE RENAL")
    
    t1, t2, t3, t4 = st.tabs(["💊 Validación Renal", "📄 Informe", "📊 Excel (Datos)", "📈 Gráficos"])
    
    with t1: render_tab_validacion()
    with t2: st.info("Módulo Informe: Generación de PDF clínico.")
    with t3: st.info("Módulo Excel: Registro histórico de mediciones.")
    with t4: st.info("Módulo Gráficos: Evolución del filtrado glomerular.")

    if st.button("🗑️ Reset Paciente"):
        st.session_state.meds_input = ""
        st.rerun()

if __name__ == "__main__":
    main()
