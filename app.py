import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import io

# 1. CONFIGURACIÓN E INTERFAZ
st.set_page_config(page_title="Validador Renal Pro", layout="wide")

st.markdown("""
    <style>
    @keyframes glow-red { 0% { box-shadow: 0 0 10px #ff4b4b; } 50% { box-shadow: 0 0 40px #ff0000; } 100% { box-shadow: 0 0 10px #ff4b4b; } }
    @keyframes glow-orange { 0% { box-shadow: 0 0 10px #ffa500; } 50% { box-shadow: 0 0 40px #ff8c00; } 100% { box-shadow: 0 0 10px #ffa500; } }
    @keyframes glow-green { 0% { box-shadow: 0 0 10px #28a745; } 50% { box-shadow: 0 0 40px #1e7e34; } 100% { box-shadow: 0 0 10px #28a745; } }
    .report-box { padding: 30px; border-radius: 15px; margin-top: 20px; border: 3px solid; }
    .rojo { background-color: #f8d7da; color: #721c24; animation: glow-red 1.5s infinite; }
    .naranja { background-color: #fff3cd; color: #856404; animation: glow-orange 1.5s infinite; }
    .verde { background-color: #d4edda; color: #155724; animation: glow-green 1.5s infinite; }
    .separator { border: 0; height: 2px; background-image: linear-gradient(to right, rgba(0,0,0,0), rgba(0,0,0,0.6), rgba(0,0,0,0)); margin: 25px 0; }
    </style>
    """, unsafe_allow_html=True)

# 2. CARGA DE RECURSOS (MODELO ACTUALIZADO)
@st.cache_resource
def load_assets():
    pdf_txt = ""
    try:
        doc = fitz.open("vademecum_renal.pdf")
        pdf_txt = "".join([p.get_text() for p in doc])
    except: pdf_txt = "PDF no disponible."
    
    ai_mod = None
    if "API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["API_KEY"])
        # Intentamos con 'gemini-pro' que es el más estable para v1
        try:
            ai_mod = genai.GenerativeModel('gemini-pro')
        except:
            ai_mod = genai.GenerativeModel('gemini-1.0-pro')
    return ai_mod, pdf_txt

model, contexto_pdf = load_assets()

# 3. CALCULADORA FG
st.title("🩺 Validador de Seguridad Farmacológica")
col_izq, col_der = st.columns([1, 2], gap="large")

with col_izq:
    st.header("Datos Clínicos")
    edad = st.number_input("Edad", 18, 110, 65)
    peso = st.number_input("Peso (kg)", 30, 200, 75)
    crea = st.number_input("Creatinina (mg/dL)", 0.2, 15.0, 1.1)
    sexo = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
    fg = ((140 - edad) * peso) / (72 * crea)
    if sexo == "Mujer": fg *= 0.85
    fg = round(fg, 1)
    st.metric("FG Calculado", f"{fg} ml/min")

# 4. ENTRADA UNIFICADA Y ANÁLISIS
with col_der:
    st.header("Ent

              
