import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import io

# --- 1. ARQUITECTURA VISUAL: FONDO CLARO Y CUADRO FG NEGRO ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

st.markdown("""
    <style>
    /* Asegurar fondo claro para la aplicación */
    .stApp {
        background-color: #ffffff !important;
        color: #31333F !important;
    }
    
    /* Cuadro discreto superior izquierdo (Modelo) */
    .indicator-header {
        position: fixed !important; top: 0px !important; left: 0px !important;
        background-color: #000000 !important; color: #00FF00 !important;
        padding: 4px 12px !important; font-family: 'Courier New', monospace !important;
        font-size: 12px !important; z-index: 999999 !important;
        border-bottom: 1px solid #333 !important; border-right: 1px solid #333 !important;
    }
    
    /* CUADRO FG: FONDO NEGRO, BORDE MORADO Y GLOW */
    .fg-card-black {
        background-color: #000000 !important;
        color: #ffffff !important;
        padding: 20px !important;
        border-radius: 15px !important;
        text-align: center !important;
        border: 2px solid #6a0dad !important;
        box-shadow: 0 0 20px #a020f0 !important;
        width: 180px !important; /* Más pequeño y compacto */
        margin: 0 auto 10px auto !important;
    }
    .fg-card-black h1 { 
        color: #ffffff !important; 
        font-size: 42px !important; 
        margin: 0 !important; 
        font-family: sans-serif;
    }
    
    /* Resultados dinámicos */
    .resumen-afectados { padding: 20px; border-radius: 12px; border: 2px solid; margin-top: 15px; }
    .v-glow { background-color: #f0fff0; border-color: #28a745; }
    .n-glow { background-color: #fff9f0; border-color: #ffa500; }
    .r-glow { background-color: #fff0f0; border-color: #dc3545; }

    /* Etiquetas de texto para legibilidad sobre fondo blanco */
    h1, h2, h3, p, span, label { color: #31333F !important; }
    .fg-card-black p, .fg-card-black h1 { color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. GESTIÓN DE ESTADO ---
if 'meds_input' not in st.session_state: st.session_state.meds_input = ""
if 'clinico_res' not in st.session_state: st.session_state.clinico_res = ""
if 'cache_id' not in st.session_state: st.session_state.cache_id = ""
if 'modelo_viz' not in st.session_state: st.session_state.modelo_viz = "V 2.5"

@st.cache_resource
def load_renal_engine():
    try:
        genai.configure(api_key=st.secrets["API_KEY"])
        m_pro = genai.GenerativeModel('gemini-1.5-pro')
        m_flash = genai.GenerativeModel('gemini-2.0-flash-exp')
        with fitz.open("vademecum_renal.pdf") as doc:
            v_txt = "".join([p.get_text() for p in doc])
        return m_pro, m_flash, v_txt
    except: return None, None, ""

model_p, model_f, v_mem = load_renal_engine()

def call_ai(prompt, image=None):
    for i, m in enumerate([model_p, model_f]):
        try:
            st.session_state.modelo_viz = "V 2.5" if i == 0 else "V 2.5 S"
            return m.generate_content([prompt, image] if image else prompt).text
        except: continue
    return "Error"

# --- 3. INTERFAZ DUAL: IZQUIERDA CORTA ---
st.markdown(f'<div class="indicator-header">{st.session_state.modelo_viz}</div>', unsafe_allow_html=True)
st.title("ASISTENTE RENAL")

col_calc, col_fg = st.columns([0.25, 0.75], gap="large")

with col_calc:
    st.subheader("📋 Calculadora")
    edad = st.number_input("Edad", 18, 110, 70)
    peso = st.number_input("Peso (kg)", 35, 200, 75)
    crea = st.number_input("Creatinina (mg/dL)", 0.4, 15.0, 1.20)
    sexo = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
    
    fg_calc = round((((140 - edad) * peso) / (72 * crea)) * (0.85 if sexo == "Mujer" else 1.0), 1)

with col_fg:
    st.subheader("⚡ Filtrado Glomerular")
    fg_manual = st.number_input("Manual:", 0.0, 200.0, 0.0)
    fg_final = fg_manual if fg_manual > 0 else fg_calc
    
    # Cuadro FG Negro con resplandor Morado
    st.markdown(f"""
        <div class="fg-card-black">
            <h1>{fg_final}</h1>
            <p style='font-size:14px; margin:0;'>mL/min</p>
        </div>
    """, unsafe_allow_html=True)
    st.caption("<center>Cockcroft-Gault</center>", unsafe_allow_html=True)
    
    st.write("---")
    file_up = st.file_uploader("Subir imagen de listado", type=['png', 'jpg', 'jpeg'])
    try:
        from streamlit_paste_button import paste_image_button
        paste_btn = paste_image_button("📋 Pegar (Ctrl+V)")
    except: paste_btn = None

    if st.button("EXTRAER MEDICAMENTOS", use_container_width=True):
        src = paste_btn.image_data if (paste_btn and paste_btn.image_data) else file_up
        if src:
            img_pil = Image.open(io.BytesIO(src) if not isinstance(src, Image.Image) else src).convert("RGB")
            with st.spinner("Leyendo..."):
                st.session_state.meds_input = call_ai("Extrae fármacos y dosis:", img_pil)
                st.rerun()

# --- 4. LISTADO DE MEDICAMENTOS ---
st.write("---")
st.subheader("Listado de medicamentos")
med_edit = st.text_area(
    "Edita o pega la lista aquí:",
    value=st.session_state.meds_input,
    height=150
)
st.session_state.meds_input = med_edit

# --- 5. VALIDACIÓN ---
if st.button("🚀 VALIDAR MEDICACIÓN", use_container_width=True):
    ck = f"{fg_final}{med_edit}"
    if ck == st.session_state.cache_id:
        st.info("Caché activa.")
    elif med_edit:
        with st.spinner("Analizando..."):
            p = f"FG: {fg_final}. Vademécum: {v_mem[:7500]}. Lista: {med_edit}. Analiza por rangos de aclaramiento del PDF. Iconos ⚠️/⛔."
            st.session_state.clinico_res = call_ai(p)
            st.session_state.cache_id = ck
            st.rerun()

# --- 6. RESULTADOS ---
if st.session_state.clinico_res:
    r = st.session_state.clinico_res
    clase = "v-glow"
    if "⛔" in r: clase = "r-glow"
    elif "⚠️" in r: clase = "n-glow"
    
    st.markdown(f'<div class="resumen-afectados {clase}"><h3>🔲 medicamentos afectados</h3>{r}</div>', unsafe_allow_html=True)

if st.button("🗑️ Reset"):
    st.session_state.meds_input = ""
    st.session_state.clinico_res = ""
    st.rerun()

st.markdown('<div style="background-color: #fdfae5; padding: 10px; border-radius: 5px; color: #856404; margin-top: 20px;">⚠️ Aviso: Requiere verificación profesional.</div>', unsafe_allow_html=True)
