import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Validador Renal Pro", layout="wide")

# Estilos visuales (Semáforo y Glow)
st.markdown("""
    <style>
    @keyframes glow-red { 0% { box-shadow: 0 0 10px #ff4b4b; } 50% { box-shadow: 0 0 30px #ff0000; } 100% { box-shadow: 0 0 10px #ff4b4b; } }
    @keyframes glow-orange { 0% { box-shadow: 0 0 10px #ffa500; } 50% { box-shadow: 0 0 30px #ff8c00; } 100% { box-shadow: 0 0 10px #ffa500; } }
    @keyframes glow-green { 0% { box-shadow: 0 0 10px #28a745; } 50% { box-shadow: 0 0 30px #1e7e34; } 100% { box-shadow: 0 0 10px #28a745; } }
    .report-box { padding: 25px; border-radius: 15px; border: 3px solid; margin-top: 20px; }
    .rojo { background-color: #f8d7da; color: #721c24; animation: glow-red 1.5s infinite; }
    .naranja { background-color: #fff3cd; color: #856404; animation: glow-orange 1.5s infinite; }
    .verde { background-color: #d4edda; color: #155724; animation: glow-green 1.5s infinite; }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE CONEXIÓN ---
@st.cache_resource
def inicializar_todo():
    # 1. Leer PDF
    texto_pdf = ""
    try:
        doc = fitz.open("vademecum_renal.pdf")
        for pagina in doc:
            texto_pdf += pagina.get_text()
    except:
        texto_pdf = "PDF no encontrado."
    
    # 2. Configurar IA
    modelo_ia = None
    if "API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["API_KEY"])
        # Usamos gemini-1.5-flash (versión estable)
        modelo_ia = genai.GenerativeModel('gemini-2.5-flash')
    
    return modelo_ia, texto_pdf

modelo, contexto = inicializar_todo()

# --- INTERFAZ DE USUARIO ---
st.title("🩺 Validador de Seguridad Renal")

if not modelo:
    st.error("Falta la API_KEY en los Secrets de Streamlit.")
    st.stop()

col1, col2 = st.columns([1, 2], gap="large")

with col1:
    st.subheader("Datos del Paciente")
    edad = st.number_input("Edad", 18, 100, 70)
    peso = st.number_input("Peso (kg)", 40, 150, 75)
    crea = st.number_input("Creatinina (mg/dL)", 0.5, 10.0, 1.2)
    sexo = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
    
    # Cockcroft-Gault
    fg = ((140 - edad) * peso) / (72 * crea)
    if sexo == "Mujer": fg *= 0.85
    fg = round(fg, 1)
    
    st.metric("Filtrado Glomerular", f"{fg} ml/min")

with col2:
    st.subheader("Análisis de Medicación")
    imagen = st.file_uploader("Sube foto de receta/caja", type=['jpg', 'jpeg', 'png'])
    texto_libre = st.text_area("O escribe los fármacos aquí:")

    if st.button("🚀 VALIDAR SEGURIDAD"):
        if imagen or texto_libre:
            with st.spinner("Analizando..."):
                prompt = f"Actúa como nefrólogo. Paciente con FG de {fg} ml/min. Usa este vademécum: {contexto[:5000]}. REGLAS: 1. Di primero ROJO, NARANJA o VERDE. 2. Explica brevemente si la dosis es segura. 3. Sé conciso."
                
                # Preparar contenido
                contenido = [prompt]
                if imagen: contenido.append(Image.open(imagen))
                if texto_libre: contenido.append(texto_libre)
                
                try:
                    res = modelo.generate_content(contenido).text
                    
                    # Determinar color
                    clase = "verde"
                    emoji = "🟢"
                    if "ROJO" in res.upper(): clase, emoji = "rojo", "🔴"
                    elif "NARANJA" in res.upper(): clase, icon = "naranja", "🟠"
                    
                    st.markdown(f'<div class="report-box {clase}"><h3>{emoji} Informe</h3>{res}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error de conexión: {e}")
