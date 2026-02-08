import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Asistente Renal Pro", layout="wide")

# Estilo para el semáforo
st.markdown("""
    <style>
    .stAlert { margin-top: 1rem; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🩺 Validador de Seguridad Renal")

# 2. CONEXIÓN CON IA (LÓGICA DE BLINDAJE)
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])
    
    # Intentamos cargar el modelo más capaz, si falla, el error se captura abajo
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
    except:
        model = genai.GenerativeModel('gemini-pro')
else:
    st.error("⚠️ Configura la API_KEY en los Secrets de Streamlit.")
    st.stop()

# 3. ESTRUCTURA DE COLUMNAS
col_izq, col_der = st.columns([1, 2], gap="large")

# --- COLUMNA IZQUIERDA: DATOS CLÍNICOS ---
with col_izq:
    st.header("1. Función Renal")
    with st.container(border=True):
        edad = st.number_input("Edad", 18, 110, 65)
        peso = st.number_input("Peso (kg)", 30, 200, 75)
        crea = st.number_input("Creatinina (mg/dL)", 0.2, 15.0, 1.1)
        sexo = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)

        # Fórmula Cockcroft-Gault
        fg_calc = ((140 - edad) * peso) / (72 * crea)
        if sexo == "Mujer":
            fg_calc *= 0.85
        
        st.metric("FG Calculado (ml/min)", f"{round(fg_calc, 1)}")

# --- COLUMNA DERECHA: GESTIÓN DE MEDICACIÓN ---
with col_der:
    st.header("2. Validación de Medicación")
    
    # Sincronización: El valor por defecto es el cálculo, pero es editable
    fg_final = st.number_input("FG para análisis (confirmar dato):", 0.0, 200.0, value=float(round(fg_calc, 1)))
    
    st.subheader("Entrada de Medicación")
    tab1, tab2 = st.tabs(["📝 Escribir Texto", "📸 Subir o Pegar Imagen"])
    
    with tab1:
        texto_meds = st.text_area("Nombre del fármaco y posología:", placeholder="Ej: Ciprofloxacino 750mg cada 12h", height=100)
    
    with tab2:
        # Permitimos subir archivo y también capturar si pegan una imagen
        imagen_input = st.file_uploader("Carga el pantallazo o foto de la receta", type=["png", "jpg", "jpeg"])
        if imagen_input:
            st.image(imagen_input, caption="Documento cargado", width=300)

    if st.button("🚀 ANALIZAR SEGURIDAD"):
        prompt = f"""
        Actúa como un experto Nefrólogo. Analiza la seguridad de los medicamentos según el Filtrado Glomerular (FG) de {fg_final} ml/min.
        Considera especialmente la DOSIS y POSOLOGÍA indicada.
        
        INSTRUCCIONES:
        1. Comienza con: 'ESTADO: VERDE', 'ESTADO: NARANJA' o 'ESTADO: ROJO'.
        2. Explica si la dosis es adecuada o si requiere ajuste (ej. reducir al 50% o evitar).
        3. Cita brevemente la recomendación para este fármaco en insuficiencia renal.
        """
        
        with st.spinner("Validando con guías clínicas..."):
            try:
                if imagen_input:
                    img = Image.open(imagen_input)
                    # El modelo Flash permite enviar imagen y texto juntos
                    response = model.generate_content([prompt, img])
                elif texto_meds:
                    response = model.generate_content(f"{prompt}\nMedicamentos: {texto_meds}")
                else:
                    st.warning("⚠️ Introduce texto o una imagen para analizar.")
                    st.stop()

                res_text = response.text
                
                # Lógica del Semáforo
                if "ESTADO: ROJO" in res_text.upper():
                    st.error("🔴 **ALTO RIESGO / CONTRAINDICADO**")
                elif "ESTADO: NARANJA" in res_text.upper():
                    st.warning("🟠 **PRECAUCIÓN / REQUIERE AJUSTE**")
                elif "ESTADO: VERDE" in res_text.upper():
                    st.success("🟢 **SEGURO PARA ESTE FG**")
                
                st.markdown(res_text)

            except Exception as e:
                st.error(f"Error de conexión: {e}")
                st.info("Sugerencia: Si el error persiste, genera una nueva API KEY en Google AI Studio.")

st.markdown("---")
st.caption("Herramienta de apoyo clínico. No sustituye el juicio médico.")
