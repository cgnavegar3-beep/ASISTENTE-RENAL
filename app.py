import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import io

# Intentamos importar el botón de pegado, si falla, avisamos
try:
    from streamlit_paste_button import paste_image_button
except ImportError:
    st.error("Error: No se encuentra la librería 'streamlit-paste-button'. Instálala con: pip install streamlit-paste-button")

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="ASISTENTE RENAL", layout="centered")

# 2. INICIALIZACIÓN DE VARIABLES
if 'medicamentos' not in st.session_state:
    st.session_state.medicamentos = ""
if 'analisis' not in st.session_state:
    st.session_state.analisis = ""

# 3. CARGA DE IA Y PDF (Simplificada al máximo)
@st.cache_resource
def cargar_ia():
    try:
        genai.configure(api_key=st.secrets["API_KEY"])
        return genai.GenerativeModel('gemini-1.5-pro')
    except Exception as e:
        st.error(f"Error de configuración de IA: {e}")
        return None

@st.cache_resource
def cargar_pdf():
    try:
        with fitz.open("vademecum_renal.pdf") as doc:
            return "".join([p.get_text() for p in doc])
    except:
        return "Vademécum no disponible localmente."

ia_model = cargar_ia()
vademecum_txt = cargar_pdf()

# 4. INTERFAZ (ORDEN VERTICAL GARANTIZADO)
st.title("👨‍⚕️ Asistente de Seguridad Renal")

# --- BLOQUE 1: CALCULADORA ---
st.header("1. Función Renal")
edad = st.number_input("Edad", 18, 110, 70)
peso = st.number_input("Peso (kg)", 35, 200, 75)
crea = st.number_input("Creatinina (mg/dL)", 0.4, 15.0, 1.2)
fg = round(((140 - edad) * peso) / (72 * crea), 1)
st.subheader(f"Filtrado Glomerular: {fg} ml/min")

st.divider()

# --- BLOQUE 2: ENTRADA DE IMAGEN (PROBLEMA POTENCIAL AQUÍ) ---
st.header("2. Captura de Medicamentos")
st.info("Sube una foto o usa el botón de pegar")

# Ponemos el botón de pegar solo si la librería cargó
archivo_subido = st.file_uploader("Subir archivo de imagen", type=['png', 'jpg', 'jpeg'])
boton_pegar = paste_image_button("📋 Pegar Recorte (Ctrl+V)")

# --- BLOQUE 3: PROCESAMIENTO ---
if st.button("🔍 PASO A: EXTRAER TEXTO"):
    img_data = None
    if boton_pegar.image_data:
        img_data = boton_pegar.image_data
    elif archivo_subido:
        img_data = archivo_subido

    if img_data:
        try:
            with st.spinner("La IA está leyendo la imagen..."):
                img_pil = Image.open(io.BytesIO(img_data) if not isinstance(img_data, Image.Image) else img_data).convert("RGB")
                resultado = ia_model.generate_content(["Extrae los fármacos y dosis de esta imagen.", img_pil])
                st.session_state.medicamentos = resultado.text
                st.success("¡Texto extraído!")
        except Exception as e:
            st.error(f"Error al procesar: {e}")
    else:
        st.warning("No has seleccionado ninguna imagen.")

# --- BLOQUE 4: LISTADO EDITABLE ---
st.header("3. Listado de Fármacos")
# Este cuadro SIEMPRE se dibuja
texto_usuario = st.text_area(
    "Medicamentos a analizar:", 
    value=st.session_state.medicamentos, 
    height=200,
    placeholder="Aquí aparecerán los medicamentos o puedes escribirlos tú..."
)
st.session_state.medicamentos = texto_usuario

# --- BLOQUE 5: VALIDACIÓN ---
if st.button("🚀 PASO B: VALIDAR SEGURIDAD RENAL"):
    if st.session_state.medicamentos:
        with st.spinner("Analizando con el Vademécum..."):
            prompt = f"Paciente con FG {fg}. Vademécum: {vademecum_txt[:6000]}. Revisa esta lista: {st.session_state.medicamentos}"
            analisis = ia_model.generate_content(prompt)
            st.session_state.analisis = analisis.text
    else:
        st.warning("El cuadro de texto está vacío.")

# --- BLOQUE 6: RESULTADOS ---
if st.session_state.analisis:
    st.markdown("### 📋 Resultados del Análisis")
    st.write(st.session_state.analisis)

st.divider()
st.caption("Aviso: Herramienta de soporte clínico.")
