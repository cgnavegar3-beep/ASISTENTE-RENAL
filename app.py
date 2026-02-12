import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz
import io

# --- 1. ESTILO AISLADO Y COMPACTACIÓN LOCAL ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

st.markdown("""
    <style>
    /* Indicador discreto esquina superior izquierda */
    .discreet-v {
        position: fixed; top: 0; left: 0;
        background-color: #000; color: #0F0;
        padding: 2px 10px; font-family: monospace; font-size: 11px;
        z-index: 9999; border-bottom-right-radius: 5px;
    }
    
    /* CUADRO FG: NEGRO CON GLOW MORADO */
    .fg-card-black {
        background-color: #000000;
        color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        border: 2px solid #6a0dad;
        box-shadow: 0 0 15px #a020f0;
        width: 150px;
        margin: 5px auto;
    }
    .fg-card-black h1 { color: #ffffff; font-size: 38px; margin: 0; }
    .fg-card-black p { color: #ffffff; font-size: 12px; margin: 0; opacity: 0.8; }

    /* COMPACTACIÓN SOLO PARA LA CALCULADORA */
    .calc-compact div[data-baseweb="input"] {
        margin-bottom: -12px;
    }
    .calc-compact [data-testid="stWidgetLabel"] {
        margin-bottom: -5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. MOTOR DE IA Y PROTECCIÓN ---
if 'meds_list' not in st.session_state: st.session_state.meds_list = ""
if 'analisis' not in st.session_state: st.session_state.analisis = ""

@st.cache_resource
def load_renal_tool():
    try:
        genai.configure(api_key=st.secrets["API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        with fitz.open("vademecum_renal.pdf") as doc:
            txt = "".join([page.get_text() for page in doc])
        return model, txt
    except Exception as e:
        return None, str(e)

model_ia, vademecum_txt = load_renal_tool()

if model_ia is None:
    st.error(f"⚠️ Error de Sistema: {vademecum_txt}")
    st.stop()

# --- 3. ESTRUCTURA DE LA APP ---
st.markdown('<div class="discreet-v">V 2.5</div>', unsafe_allow_html=True)
st.title("ASISTENTE RENAL")

col_calc, col_main = st.columns([0.2, 0.8], gap="medium")

with col_calc:
    st.markdown('<div class="calc-compact">', unsafe_allow_html=True)
    st.write("**DATOS**")
    edad = st.number_input("Edad", 18, 110, 75, label_visibility="collapsed")
    peso = st.number_input("Peso", 35, 180, 70, label_visibility="collapsed")
    crea = st.number_input("Crea", 0.4, 15.0, 1.1, label_visibility="collapsed")
    sexo = st.radio("Sexo", ["H", "M"], horizontal=True, key="sexo_radio", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)
    
    fg_val = round((((140 - edad) * peso) / (72 * crea)) * (0.85 if sexo == "M" else 1.0), 1)

with col_main:
    st.markdown(f'<div class="fg-card-black"><h1>{fg_val}</h1><p>mL/min (FG)</p></div>', unsafe_allow_html=True)
    st.write("---")
    file = st.file_uploader("Subir imagen de medicación", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
    
    if file:
        img = Image.open(file).convert("RGB")
        with st.spinner("IA extrayendo fármacos..."):
            try:
                # Extracción y asignación correcta al estado
                res = model_ia.generate_content(["Identifica medicamentos y sus dosis de esta imagen:", img])
                st.session_state.meds_list = res.text
            except Exception as e:
                st.error(f"Error al procesar la imagen: {e}")

# --- 4. LISTADO Y VALIDACIÓN ---
st.write("**LISTADO DETECTADO**")
med_edit = st.text_area("Edición:", value=st.session_state.meds_list, height=120, label_visibility="collapsed")

if st.button("🚀 VALIDAR MEDICACIÓN", use_container_width=True):
    if med_edit:
        with st.spinner("Analizando con Vademécum..."):
            prompt = f"FG: {fg_val}. Vademécum: {vademecum_txt[:7500]}. Lista: {med_edit}. Identifica ajustes (⚠️) o contraindicaciones (⛔)."
            st.session_state.analisis = model_ia.generate_content(prompt).text

if st.session_state.analisis:
    st.divider()
    st.write("**ANÁLISIS CLÍNICO:**")
    st.info(st.session_state.analisis)

if st.button("🗑️ Reset"):
    st.session_state.meds_list = ""
    st.session_state.analisis = ""
    st.rerun()
