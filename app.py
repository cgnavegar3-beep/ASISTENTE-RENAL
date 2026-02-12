import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz
import io

# Intentar importar el botón de pegado
try:
    from streamlit_paste_button import paste_image_button
except ImportError:
    paste_image_button = None

# --- 1. CONFIGURACIÓN Y ESTILOS DE PRECISIÓN ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

# Primero inyectamos el CSS para asegurar que los divs se reconozcan
st.markdown("""
    <style>
    /* INDICADOR DE VERSIÓN: FIJO Y CON Z-INDEX MÁXIMO */
    .discreet-v {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        background-color: #000000 !important;
        color: #00FF00 !important;
        padding: 4px 12px !important;
        font-family: 'Courier New', monospace !important;
        font-size: 12px !important;
        font-weight: bold !important;
        z-index: 999999 !important;
        border-bottom-right-radius: 8px !important;
        border: 1px solid #333 !important;
    }
    
    /* CUADRO FG: REDIMENSIONADO AL ANCHO DE LA COLUMNA (IGUAL AL UPLOADER) */
    .fg-card-wide {
        background-color: #000000 !important;
        color: #ffffff !important;
        padding: 20px !important;
        border-radius: 12px !important;
        text-align: center !important;
        border: 2px solid #6a0dad !important;
        box-shadow: 0 0 15px #a020f0 !important;
        display: block !important;
        width: 100% !important;
        max-width: 100% !important;
        margin-bottom: 15px !important;
    }
    .fg-card-wide h1 { color: #ffffff !important; font-size: 48px !important; margin: 0 !important; }
    .fg-card-wide p { color: #ffffff !important; font-size: 14px !important; margin: 0 !important; opacity: 0.8 !important; }

    /* COMPACTACIÓN DE CALCULADORA */
    .calc-compact div[data-baseweb="input"] {
        margin-bottom: -15px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Renderizado inmediato del indicador de versión antes de las columnas
st.markdown('<div class="discreet-v">V 2.5</div>', unsafe_allow_html=True)

# --- 2. MOTOR DE IA ---
if 'meds_list' not in st.session_state: st.session_state.meds_list = ""
if 'analisis' not in st.session_state: st.session_state.analisis = ""

@st.cache_resource
def load_engine():
    try:
        genai.configure(api_key=st.secrets["API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        with fitz.open("vademecum_renal.pdf") as doc:
            txt = "".join([p.get_text() for p in doc])
        return model, txt
    except Exception as e:
        return None, str(e)

model_ia, vademecum_txt = load_engine()

if model_ia is None:
    st.error(f"Error de sistema: {vademecum_txt}")
    st.stop()

# --- 3. INTERFAZ DUAL (CALCULADORA + FG) ---
st.title("ASISTENTE RENAL")

# Ratios ajustados para proporcionalidad con el uploader
col_izq, col_der = st.columns([0.25, 0.75], gap="medium")

with col_izq:
    st.markdown('<div class="calc-compact">', unsafe_allow_html=True)
    st.subheader("📋 Datos")
    edad = st.number_input("Edad", 18, 110, 75, label_visibility="collapsed")
    peso = st.number_input("Peso (kg)", 35, 180, 70, label_visibility="collapsed")
    crea = st.number_input("Crea (mg/dL)", 0.4, 15.0, 1.1, label_visibility="collapsed")
    sexo = st.radio("Sexo", ["H", "M"], horizontal=True, label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)
    
    fg_val = round((((140 - edad) * peso) / (72 * crea)) * (0.85 if sexo == "M" else 1.0), 1)

with col_der:
    # Cuadro FG que ocupa el 100% del ancho de esta columna
    st.markdown(f"""
        <div class="fg-card-wide">
            <h1>{fg_val}</h1>
            <p>mL/min (Filtrado Glomerular)</p>
        </div>
    """, unsafe_allow_html=True)

# --- 4. ZONA DE CARGA (ANCHO TOTAL) ---
st.write("---")
c_up, c_pst = st.columns([0.7, 0.3])

img_final = None

with c_up:
    file = st.file_uploader("Subir imagen", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
    if file:
        img_final = Image.open(file).convert("RGB")

with c_pst:
    if paste_image_button:
        pasted = paste_image_button("📋 Pegar (Ctrl+V)", key="paster")
        if pasted and pasted.image_data:
            img_final = pasted.image_data
    else:
        st.info("Falta: streamlit-paste-button")

# Procesamiento automático
if img_final:
    with st.spinner("IA extrayendo medicamentos..."):
        try:
            res = model_ia.generate_content(["Identifica medicamentos y dosis:", img_final])
            st.session_state.meds_list = res.text
        except:
            st.error("Error al procesar la imagen.")

# --- 5. RESULTADOS ---
st.write("**LISTADO DETECTADO**")
med_edit = st.text_area("Lista:", value=st.session_state.meds_list, height=150, label_visibility="collapsed")

if st.button("🚀 VALIDAR MEDICACIÓN", use_container_width=True):
    if med_edit:
        with st.spinner("Validando..."):
            p = f"FG: {fg_val}. Vademécum: {vademecum_txt[:7500]}. Lista: {med_edit}. Indica ⚠️ o ⛔."
            st.session_state.analisis = model_ia.generate_content(p).text

if st.session_state.analisis:
    st.divider()
    st.info(st.session_state.analisis)

if st.button("🗑️ Reset"):
    st.session_state.meds_list = ""
    st.session_state.analisis = ""
    st.rerun()
