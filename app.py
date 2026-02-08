import streamlit as st
import google.generativeai as genai

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Asistente Renal", layout="wide")
st.title("🩺 Validador Renal")

# CONEXIÓN INTELIGENTE (SIN NOMBRES FIJOS)
@st.cache_resource
def inicializar_ia(api_key):
    try:
        genai.configure(api_key=api_key)
        # Buscamos qué modelo tiene activo tu cuenta nueva
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                return genai.GenerativeModel(m.name), m.name
    except Exception as e:
        return None, str(e)
    return None, "No se encontraron modelos disponibles"

if "API_KEY" in st.secrets:
    model, nombre_modelo = inicializar_ia(st.secrets["API_KEY"])
    if not model:
        st.error(f"Error de acceso: {nombre_modelo}. Verifica tu API_KEY.")
        st.stop()
    else:
        st.success(f"✅ Sistema conectado vía: {nombre_modelo}")
else:
    st.error("Falta la API_KEY en Secrets.")
    st.stop()

# INTERFAZ DE DOS COLUMNAS
col_izq, col_der = st.columns([1, 2], gap="large")

with col_izq:
    st.header("1. Datos Clínicos")
    with st.container(border=True):
        edad = st.number_input("Edad", 18, 110, 65)
        peso = st.number_input("Peso (kg)", 30, 200, 75)
        crea = st.number_input("Creatinina (mg/dL)", 0.2, 15.0, 1.1)
        sexo = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
        
        fg = ((140 - edad) * peso) / (72 * crea)
        if sexo == "Mujer": fg *= 0.85
        st.metric("FG Calculado", f"{round(fg, 1)} ml/min")

with col_der:
    st.header("2. Validación")
    fg_final = st.number_input("FG para análisis:", 0.0, 200.0, value=float(round(fg, 1)))
    meds = st.text_area("Fármacos y dosis:", placeholder="Ej: Metformina 850mg c/12h")
    
    if st.button("🔍 ANALIZAR SEGURIDAD"):
        if meds:
            prompt = f"Actúa como nefrólogo. FG: {fg_final}. Analiza: {meds}. Responde con ESTADO: VERDE, NARANJA o ROJO y una breve explicación clínica."
            with st.spinner("Analizando..."):
                try:
                    response = model.generate_content(prompt)
                    res = response.text
                    if "ROJO" in res.upper(): st.error(res)
                    elif "NARANJA" in res.upper(): st.warning(res)
                    else: st.success(res)
                except Exception as e:
                    st.error(f"Error en la consulta: {e}")
