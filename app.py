import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. CONFIGURACIÓN E INTERFAZ
st.set_page_config(page_title="Asistente Renal Pro", layout="wide")

st.title("🩺 Validador de Seguridad Farmacológica Renal")
st.markdown("---")

# 2. CONFIGURACIÓN DE IA
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Falta la API_KEY en los Secrets.")
    st.stop()

# 3. ESTRUCTURA DE COLUMNAS
col_izq, col_der = st.columns([1, 2], gap="large")

# --- COLUMNA IZQUIERDA: CALCULADORA ---
with col_izq:
    st.header("1. Datos Clínicos")
    edad = st.number_input("Edad", 18, 110, 65)
    peso = st.number_input("Peso (kg)", 30, 200, 75)
    crea = st.number_input("Creatinina (mg/dL)", 0.2, 15.0, 1.1)
    sexo = st.radio("Sexo", ["Hombre", "Mujer"])

    # Fórmula Cockcroft-Gault
    fg_calculado = ((140 - edad) * peso) / (72 * crea)
    if sexo == "Mujer":
        fg_calculado *= 0.85
    
    st.metric("FG Calculado (ml/min)", f"{round(fg_calculado, 1)}")

# --- COLUMNA DERECHA: MEDICACIÓN ---
with col_der:
    st.header("2. Validación de Medicación")
    fg_final = st.number_input("Filtrado Glomerular a usar (ml/min):", 0.0, 200.0, value=float(round(fg_calculado, 1)))
    
    tab1, tab2 = st.tabs(["📝 Escribir Lista", "📸 Cargar Pantallazo"])
    
    with tab1:
        texto_meds = st.text_area("Introduce medicamentos y dosis:")
    
    with tab2:
        imagen_meds = st.file_uploader("Sube una foto o pantallazo", type=["jpg", "jpeg", "png"])

    if st.button("🚀 VALIDAR SEGURIDAD"):
        analisis_input = []
        if imagen_meds:
            img = Image.open(imagen_meds)
            analisis_input = [f"Actúa como nefrólogo. FG: {fg_final}. Analiza la imagen. Empieza con 'ESTADO: VERDE', 'ESTADO: NARANJA' o 'ESTADO: ROJO'.", img]
        elif texto_meds:
            analisis_input = [f"Actúa como nefrólogo. FG: {fg_final}. Analiza esta lista: {texto_meds}. Empieza con 'ESTADO: VERDE', 'ESTADO: NARANJA' o 'ESTADO: ROJO'."]
        
        if analisis_input:
            with st.spinner("Analizando..."):
                try:
                    response = model.generate_content(analisis_input)
                    res = response.text
                    if "ROJO" in res.upper(): st.error("🔴 ALTO RIESGO")
                    elif "NARANJA" in res.upper(): st.warning("🟠 PRECAUCIÓN")
                    else: st.success("🟢 SEGURO")
                    st.write(res)
                except Exception as e:
                    st.error(f"Error: {e}")
