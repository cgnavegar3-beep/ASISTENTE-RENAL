import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import io

# --- 1. CLÁUSULA DE INVARIABILIDAD: CSS ESTRUCTURAL (FONDO NEGRO Y DIMENSIONES) ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Fondo Negro General */
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }
    
    /* Cuadro discreto superior izquierdo (Modelo) */
    .indicator-header {
        position: fixed !important; top: 0px !important; left: 0px !important;
        background-color: #000000 !important; color: #00FF00 !important;
        padding: 5px 12px !important; font-family: 'Courier New', monospace !important;
        font-size: 12px !important; z-index: 999999 !important;
        border-bottom: 1px solid #333 !important; border-right: 1px solid #333 !important;
    }
    
    /* FG con fondo morado reducido y sombra glow */
    .fg-card-renal {
        background-color: #6a0dad !important;
        color: white !important;
        padding: 20px 10px !important;
        border-radius: 15px !important;
        text-align: center !important;
        box-shadow: 0 0 25px #a020f0 !important;
        border: 1px solid #a020f0 !important;
        width: 60% !important; /* Ancho reducido a la mitad aprox */
        margin: 0 auto 20px auto !important;
    }
    .fg-card-renal h1 { color: white !important; font-size: 45px !important; margin: 0 !important; }
    
    /* Ajustes de inputs para fondo negro */
    .stNumberInput input, .stTextArea textarea, .stSelectbox div {
        background-color: #111 !important;
        color: white !important;
        border: 1px solid #333 !important;
    }

    /* Cuadro de resultados dinámico */
    .resumen-afectados { padding: 20px; border-radius: 12px; border: 2px solid; margin-top: 20px; background-color: #050505; }
    .verde-glow { border-color: #00FF00; box-shadow: 0 0 15px #00FF00; }
    .naranja-glow { border-color: #FFA500; box-shadow: 0 0 15px #FFA500; }
    .rojo-glow { border-color: #FF0000; box-shadow: 0 0 15px #FF0000; }
    
    /* Aviso seguridad sombreado amarillo pálido */
    .aviso-legal-renal { 
        background-color: #1a1a00 !important; padding: 15px !important; 
        border-radius: 10px !important; border: 1px solid #444000 !important; 
        color: #ffffcc !important; margin-top: 30px !important; 
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. GESTIÓN DE ESTADO ---
if 'meds_input' not in st.session_state: st.session_state.meds_input = ""
if 'analisis_clinico' not in st.session_state: st.session_state.analisis_clinico = ""
if 'cache_val' not in st.session_state: st.session_state.cache_val = ""
if 'model_label' not in st.session_state: st.session_state.model_label = "V 2.5"

# --- 3. RECURSOS (IA Y PDF) ---
@st.cache_resource
def setup_asistente():
    try:
        genai.configure(api_key=st.secrets["API_KEY"])
        m_pro = genai.GenerativeModel('gemini-1.5-pro')
        m_flash = genai.GenerativeModel('gemini-2.5-flash')
        with fitz.open("vademecum_renal.pdf") as doc:
            v_txt = "".join([p.get_text() for p in doc])
        return m_pro, m_flash, v_txt
    except:
        return None, None, ""

model_p, model_f, v_memoria = setup_asistente()

def llamar_ia(prompt, image=None):
    for i, m in enumerate([model_p, model_f]):
        try:
            st.session_state.model_label = "V 2.5" if i == 0 else "V 2.5 S"
            if image: return m.generate_content([prompt, image]).text
            return m.generate_content(prompt).text
        except: continue
    return "Fallo de conexión."

# --- 4. INTERFAZ DUAL: CALCULADORA CORTA (IZQ) Y FG PEQUEÑO (DER) ---
st.markdown(f'<div class="indicator-header">{st.session_state.model_label}</div>', unsafe_allow_html=True)
st.title("ASISTENTE RENAL")

# Ajuste de columnas: 40% izquierda, 60% derecha para dar aire al centro
col_calc, col_fg = st.columns([0.4, 0.6], gap="large")

with col_calc:
    st.subheader("📋 Calculadora")
    edad = st.number_input("Edad", 18, 110, 70)
    peso = st.number_input("Peso (kg)", 35, 200, 75)
    crea = st.number_input("Creatinina (mg/dL)", 0.4, 15.0, 1.20)
    sexo = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
    
    fg_calc = round((((140 - edad) * peso) / (72 * crea)) * (0.85 if sexo == "Mujer" else 1.0), 1)

with col_fg:
    st.subheader("⚡ Filtrado Glomerular")
    fg_manual = st.number_input("Introducir FG Manual:", 0.0, 200.0, 0.0)
    fg_final = fg_manual if fg_manual > 0 else fg_calc
    
    # Cuadro morado PEQUEÑO con glow
    st.markdown(f"""
        <div class="fg-card-renal">
            <h1>{fg_final}</h1>
            <p style='font-size:14px; margin:0;'>mL/min</p>
        </div>
    """, unsafe_allow_html=True)
    st.caption("<center>Fórmula: Cockcroft-Gault</center>", unsafe_allow_html=True)
    
    st.write("---")
    img_file = st.file_uploader("Subir imagen", type=['png', 'jpg', 'jpeg'])
    try:
        from streamlit_paste_button import paste_image_button
        paste_btn = paste_image_button("📋 Pegar Recorte (Ctrl+V)")
    except: paste_btn = None

    if st.button("EXTRAER MEDICAMENTOS", use_container_width=True):
        source = paste_btn.image_data if (paste_btn and paste_btn.image_data) else img_file
        if source:
            img_pil = Image.open(io.BytesIO(source) if not isinstance(source, Image.Image) else source).convert("RGB")
            with st.spinner("IA extrayendo fármacos..."):
                st.session_state.meds_input = llamar_ia("Lista solo nombres y dosis de fármacos:", img_pil)
                st.rerun()

# --- 5. CUADRO LISTADO DE MEDICAMENTOS (EDITABLE) ---
st.write("---")
st.subheader("Listado de medicamentos")
med_edit = st.text_area(
    "Escribe o edita la lista que se reproducirá aquí si se ha pegado un RECORTE o se ha subido un pantallazo o imagen.",
    value=st.session_state.meds_input,
    height=150
)
st.session_state.meds_input = med_edit

# --- 6. VALIDACIÓN ---
if st.button("🚀 VALIDAR MEDICACIÓN", use_container_width=True):
    fingerprint = f"{fg_final}{med_edit}"
    if fingerprint == st.session_state.cache_val:
        st.info("Resultado en caché.")
    elif med_edit:
        with st.spinner("Consultando Vademécum..."):
            p_renal = f"FG: {fg_final}. Vademécum: {v_memoria[:7500]}. Lista: {med_edit}. Analiza por rangos de aclaramiento del PDF. Iconos ⚠️/⛔."
            st.session_state.analisis_clinico = llamar_ia(p_renal)
            st.session_state.cache_val = fingerprint
            st.rerun()

# --- 7. RESULTADOS ---
if st.session_state.analisis_clinico:
    res = st.session_state.analisis_clinico
    estilo = "verde-glow"
    if "⛔" in res: estilo = "rojo-glow"
    elif "⚠️" in res: estilo = "naranja-glow"
    
    st.markdown(f'<div class="resumen-afectados {estilo}"><h3>🔲 medicamentos afectados</h3>{res}</div>', unsafe_allow_html=True)

if st.button("🗑️ Reset"):
    st.session_state.meds_input = ""
    st.session_state.analisis_clinico = ""
    st.rerun()

st.markdown("""
    <div class="aviso-legal-renal">
        ⚠️ <b>Aviso</b>: Esta herramienta es un apoyo a la revisión farmacoterapéutica. Requiere verificación profesional.
    </div>
""", unsafe_allow_html=True)
