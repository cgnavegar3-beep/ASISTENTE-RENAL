import streamlit as st
import google.generativeai as genai

# 1. CONFIGURACIÓN BÁSICA
st.set_page_config(page_title="Asistente Renal", layout="wide")
st.title("🩺 Validador Renal (Versión Estable)")

# 2. CONEXIÓN DIRECTA
if "API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["API_KEY"])
        # Usamos 'gemini-pro', que es el modelo más compatible y estable
        model = genai.GenerativeModel('gemini-pro')
    except Exception as e:
        st.error(f"Error de configuración: {e}")
else:
    st.error("Falta la API_KEY en Secrets.")
    st.stop()

# 3. INTERFAZ EN COLUMNAS
col_izq, col_der = st.columns([1, 2])

with col_izq:
    st.header("Calculadora")
    edad = st.number_input("Edad", 18, 110, 65)
    peso = st.number_input("Peso (kg)", 30, 200, 75)
    crea = st.number_input("Creatinina (mg/dL)", 0.2, 15.0, 1.1)
    sexo = st.radio("Sexo", ["Hombre", "Mujer"])
    
    fg = ((140 - edad) * peso) / (72 * crea)
    if sexo == "Mujer": fg *= 0.85
    st.metric("FG Calculado", f"{round(fg, 1)} ml/min")

with col_der:
    st.header("Análisis")
    texto_meds = st.text_area("Medicamento y dosis:", placeholder="Ej: Metformina 850mg")
    
    if st.button("🔍 VALIDAR"):
        if texto_meds:
            prompt = f"Actúa como nefrólogo. FG del paciente: {round(fg,1)}. Analiza: {texto_meds}. Responde con ESTADO: VERDE, NARANJA o ROJO y una breve explicación."
            
            with st.spinner("Conectando con el servidor..."):
                try:
                    # Llamada estándar sin funciones beta
                    response = model.generate_content(prompt)
                    res = response.text
                    
                    if "ROJO" in res.upper(): st.error(res)
                    elif "NARANJA" in res.upper(): st.warning(res)
                    else: st.success(res)
                except Exception as e:
                    st.error(f"Error: {e}. Si persiste, necesitamos generar una API KEY nueva.")
        else:
            st.warning("Escribe un medicamento.")
