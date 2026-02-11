import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
from streamlit_paste_button import paste_image_button

# --- 1. CONFIGURACIÓN Y ESTILO (CUADRO IZQUIERDA) ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

st.markdown("""
    <style>
    /* Cuadro Negro Izquierda Superior - Estilo Neón */
    .engine-tag {
        position: fixed !important;
        top: 0px !important;
        left: 0px !important;
        background-color: #000000 !important;
        color: #00FF00 !important;
        padding: 8px 18px !important;
        font-family: 'Courier New', monospace !important;
        font-size: 14px !important;
        font-weight: bold !important;
        z-index: 999999 !important;
        border-bottom: 1px solid #00FF00 !important;
        border-right: 1px solid #00FF00 !important;
        border-radius: 0 0 5px 0;
    }
    /* Espaciado para que el título no choque */
    .main .block-container { padding-top: 4rem !important; }
    
    /* Estética de la App */
    .fg-display { padding: 15px; border-radius: 12px; border: 2px solid #a020f0; box-shadow: 0 0 15px #a020f0; background: #000; text-align: center; color: white; }
    .resumen-clinico { padding: 20px; border-radius: 15px; margin-top: 10px; border: 2px solid #28a745; background-color: #e8f5e9; color: #1b5e20; }
    </style>
""", unsafe_allow_html=True)

# --- 2. INICIALIZACIÓN DE ESTADO SEGURO ---
if 'med_lista' not in st.session_state:
    st.session_state['med_lista'] = ""
if 'analisis_final' not in st.session_state:
    st.session_state['analisis_final'] = ""
if 'v_motor' not in st.session_state:
    st.session_state['v_motor'] = "1.5 PRO"

# --- 3. MOSTRAR INDICADOR ---
st.markdown(f'<div class="engine-tag">{st.session_state.v_motor}</div>', unsafe_allow_html=True)

# --- 4. LÓGICA DE IA ---
@st.cache_resource
def setup_ia():
    try:
        genai.configure(api_key=st.secrets["API_KEY"])
        return {
            "pro": genai.GenerativeModel('gemini-1.5-pro'),
            "flash": genai.GenerativeModel('gemini-2.0-flash-exp')
        }
    except:
        return None

motores = setup_ia()

def llamar_ia(prompt, img=None):
    if not motores: return "Error de configuración de API."
    try:
        st.session_state.v_motor = "1.5 PRO"
        res = motores["pro"].generate_content([prompt, img] if img else prompt)
        return res.text
    except:
        st.session_state.v_motor = "2.5 FLASH"
        res = motores["flash"].generate_content([prompt, img] if img else prompt)
        return res.text

# --- 5. INTERFAZ PRINCIPAL ---
st.title("ASISTENTE RENAL")

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📋 Parámetros")
    edad = st.number_input("Edad", 18, 110, 70)
    peso = st.number_input("Peso (kg)", 35, 200, 75)
    crea = st.number_input("Creatinina", 0.4, 15.0, 1.2)
    sexo = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
    fg_calc = round((((140 - edad) * peso) / (72 * crea)) * (0.85 if sexo == "Mujer" else 1.0), 1)

with col2:
    st.subheader("⚡ FG Estimado")
    fg_man = st.number_input("FG Manual (opcional):", 0.0, 200.0, 0.0)
    fg_final = fg_man if fg_man > 0 else fg_calc
    st.markdown(f'<div class="fg-display"><h1>{fg_final} ml/min)
