import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import io
import hashlib
import numpy as np

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

# --- 2. GESTIÓN DE MODELOS (CASCADA 1.5 PRO -> 2.5 FLASH) ---
MODELS = ["gemini-1.5-pro", "gemini-2.5-flash"]

if 'active_model_idx' not in st.session_state:
    st.session_state.active_model_idx = 0

def get_active_model_name():
    raw_name = MODELS[st.session_state.active_model_idx]
    # Limpieza visual para el contador superior
    return raw_name.replace("gemini-", "").replace("-", " ").title()

def run_ia_task(prompt, image_bytes=None):
    """Lógica de cascada reactiva que actualiza la UI al instante."""
    for i in range(len(MODELS)):
        st.session_state.active_model_idx = i
        try:
            genai.configure(api_key=st.secrets["API_KEY"])
            model = genai.GenerativeModel(MODELS[i])
            
            content = []
            if prompt: content.append(prompt)
            if image_bytes:
                content.append({'mime_type': 'image/png', 'data': image_bytes})
            
            response = model.generate_content(content)
            return response.text
        except Exception:
            continue
    
    st.session_state.active_model_idx = 0
    return "ERROR: Agotados todos los intentos (Pro y 2.5 Flash)."

# --- 3. ESTILOS CSS (ESTILO EXCEL: SOLO COLOR DE TEXTO) ---
@st.cache_resource
def load_vademecum():
    try:
        doc = fitz.open("vademecum_renal.pdf")
        return "".join([page.get_text() for page in doc])
    except:
        return "Vademécum no disponible."

def inject_ui_styles():
    model_name = get_active_model_name()
    style_html = """
    <style>
        /* Contador de versión discreto */
        .discreet-v {
            position: fixed; top: 0; left: 0; background-color: #000; color: #0F0;
            padding: 5px 15px; font-family: monospace; font-size: 11px;
            z-index: 999999; border-bottom-right-radius: 10px; border: 1px solid #333;
        }
        
        /* ESTILO EXCEL PARA PESTAÑAS (SOLO TEXTO) */
        /* Texto de la pestaña activa */
        div[role="tab"]:not([aria-selected="false"]) p {
            color: #ff4b4b !important;  /* Rojo Streamlit para resaltar */
            font-weight: bold !important;
        }

        /* Texto de las pestañas inactivas */
        div[role="tab"][aria-selected="false"] p {
            color: #31333F !important;     /* Gris oscuro estándar */
            font-weight: normal !important;
        }
        
        /* Quitar fondos y bordes extra de los botones de pestañas */
        button[data-baseweb="tab"] {
            background-color: transparent !important;
            border: none !important;
        }

        /* Caja de Filtrado Glomerular */
        .fg-glow-box {
            background-color: #000 !important; color: #fff !important;
            padding: 15px; border-radius: 12px; text-align: center;
            border: 2px solid #6a0dad; box-shadow: 0 0 20px #a020f0; margin: 10px 0;
        }
        .fg-glow-box h1 { font-size: 48px !important; margin: 0; color: #fff !important; }
        .result-card { padding: 20px; border-radius: 15px; margin-top: 15px; color: #000; font-weight: 500; }
        [data-testid="column"] { display: flex; flex-direction: column; justify-content: flex-start !important; }
    </style>
    <div class="discreet-v">V-""" + model_name + """</div>"""
    st.markdown(style_html, unsafe_allow_html=True)

# --- 4. LÓGICA DE VALIDACIÓN ---
def render_tab_validacion(v_text):
    if 'meds_input' not in st.session_state:
        st.session_state.meds_input = ""

    col_izq, col_der = st.columns([0.4, 0.6], gap="large")
    
    with col_izq:
        st.subheader("📋 Parámetros")
        ed = st.number_input("Edad", 18, 110, 75)
        ps = st.number_input("Peso (kg)", 35, 180, 70)
        cr = st.number_input("Creatinina (mg/dL)", 0.4, 15.0, 1.1)
        sx = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
        f_sex = 0.85 if sx == "Mujer" else 1.0
        fg_auto = round((((140 - ed) * ps) / (72 * cr)) * f_sex, 1)

    with col_der:
        st.subheader(" ")
        fg_man = st.text_input("FG Manual", placeholder="Auto: " + str(fg_auto))
        fg_final = round(float(fg_man.replace(",", ".").strip()) if fg_man else fg_auto, 1)
        st.markdown('<div class="fg-glow-box"><h1>' + str(fg_final) + '</h1><p>mL/min (FG Final)</p></div>', unsafe_allow_html=True)
        
        st.write("**Captura de Medicación**")
        c1, c2 = st.columns([0.6, 0.4])
        img_temp = None
        
        with c1:
            f = st.file_uploader("Subir", type=['png','jpg','jpeg'], label_visibility="collapsed")
            if f: img_temp = Image.open(f).convert("RGB")
        with c2:
            try:
                from streamlit_paste_button import paste_image_button
                p = paste_image_button("📋 Pegar Recorte")
                if p and p.image_data is not None:
                    if isinstance(p.image_data, Image.Image):
                        img_temp = p.image_data.convert("RGB")
                    else:
                        img_temp = Image.fromarray(np.uint8(p.image_data)).convert("RGB")
            except: pass

    if img_temp:
        with st.spinner("IA transcribiendo..."):
            buf = io.BytesIO()
            img_temp.save(buf, format="PNG")
            img_bytes = buf.getvalue()
            
            prompt_ocr = "Extrae nombres y dosis de medicamentos de esta imagen. Solo texto plano."
            res_ocr = run_ia_task(prompt_ocr, img_bytes)
            
            if "ERROR" not in res_ocr:
                st.session_state.meds_input = res_ocr
                st.rerun()

    st.write("---")
    meds_text = st.text_area("Medicamentos detectados", value=st.session_state.meds_input, height=200, key="meds_text_area")

    if st.button("🚀 VALIDAR AJUSTES", use_container_width=True):
        if not meds_text:
            st.warning("No hay datos.")
        else:
            with st.spinner("Analizando..."):
                prompt_val = "FG: " + str(fg_final) + ". Vademécum: " + v_text[:8000] + ". Lista: " + meds_text + ". Indica ajustes."
                res = run_ia_task(prompt_val)
                bg = "#ffcdd2" if "⛔" in res else "#ffe0b2" if "⚠️" in res else "#c8e6c9"
                st.markdown('<div class="result-card" style="background-color: ' + bg + ';">' + res + '</div>', unsafe_allow_html=True)

# --- 5. MAIN ---
def main():
    inject_ui_styles()
    v_text = load_vademecum()
    st.title("ASISTENTE RENAL")
    
    t1, t2, t3, t4 = st.tabs(["💊 Validación Renal", "📄 Informe", "📊 Excel (Datos)", "📈 Gráficos"])
    
    with t1: render_tab_validacion(v_text)
    with t2: st.info("Módulo Informe...")
    with t3: st.info("Módulo Excel...")
    with t4: st.info("Módulo Gráficos...")

    if st.button("🗑️ Reset"):
        st.session_state.meds_input = ""
        st.rerun()

if __name__ == "__main__":
    main()
