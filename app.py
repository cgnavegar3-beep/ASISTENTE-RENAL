import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import time
from streamlit_paste_button import paste_image_button

# --- ESTRUCTURA BLINDADA ASISTENTE RENAL ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

# CSS para forzar el contador en la esquina superior izquierda
st.markdown("""
    <style>
    .discreet-counter {
        position: fixed !important;
        top: 0px !important;
        left: 0px !important;
        background-color: #000000 !important;
        color: #00FF00 !important;
        padding: 8px 15px !important;
        font-family: 'Courier New', monospace !important;
        font-size: 13px !important;
        z-index: 999999 !important;
        border-bottom: 1px solid #333 !important;
        border-right: 1px solid #333 !important;
    }
    .fg-glow-purple { 
        padding: 20px; border-radius: 15px; border: 2px solid #a020f0;
        box-shadow: 0 0 20px #a020f0; background: #000; text-align: center; color: white;
    }
    .resumen-unico { padding: 25px; border-radius: 15px; margin-top: 20px; border: 2px solid; }
    .v-glow { background-color: #e8f5e9; border-color: #28a745; }
    .n-glow { background-color: #fff3e0; border-color: #ffa500; }
    .r-glow { background-color: #ffeef0; border-color: #ff4b4b; }
    .aviso-amarillo { background-color: #fdfae5; padding: 20px; border-radius: 10px; border: 1px solid #ffeeba; margin-top: 30px; }
    </style>
""", unsafe_allow_html=True)

# Lógica del Contador
if 'd_lim' not in st.session_state: st.session_state.d_lim = 50
if 'm_lim' not in st.session_state: st.session_state.m_lim = 2
if 'last_reset' not in st.session_state: st.session_state.last_reset = time.time()
if 'texto_fijo' not in st.session_state: st.session_state.texto_fijo = ""

if time.time() - st.session_state.last_reset > 60:
    st.session_state.m_lim = 2
    st.session_state.last_reset = time.time()

# Inyección del contador
st.markdown(f'<div class="discreet-counter">INTENTOS: {st.session_state.d_lim} DÍA | {st.session_state.m_lim} MIN | TOKENS: OK</div>', unsafe_allow_html=True)

@st.cache_resource
def load_sys():
    pdf_txt = ""
    try:
        with fitz.open("vademecum_renal.pdf") as doc:
            pdf_txt = "".join([p.get_text() for p in doc])
    except: pass
    genai.configure(api_key=st.secrets["API_KEY"])
    return genai.GenerativeModel('gemini-2.5-flash'), pdf_txt

model, vademecum = load_sys()

# Interfaz
st.title("ASISTENTE RENAL")
col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 Parámetros")
    ed = st.number_input("Edad", 18, 110, 70)
    ps = st.number_input("Peso (kg)", 35, 200, 75)
    cr = st.number_input("Creatinina", 0.4, 15.0, 1.2)
    sx = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
    fg_c = round((((140 - ed) * ps) / (72 * cr)) * (0.85 if sx == "Mujer" else 1.0), 1)

with col2:
    st.subheader("⚡ Filtrado")
    fg_m = st.number_input("FG Manual:", 0.0, 200.0, 0.0)
    fg_f = fg_m if fg_m > 0 else fg_c
    st.markdown(f'<div class="fg-glow-purple"><h1>{fg_f} ml/min</h1></div>', unsafe_allow_html=True)
    
    st.write("### 📷 Recorte")
    img = st.file_uploader("Subir", type=['png', 'jpg', 'jpeg'])
    pst = paste_image_button("📋 Pegar (Ctrl+V)")

# Procesar Imagen
input_img = img if img else (pst.image_data if pst.image_data else None)
if input_img:
    with st.spinner("Leyendo..."):
        res = model.generate_content(["Extrae fármacos. PRIV si hay nombres.", input_img])
        if "PRIV" not in res.text.upper(): st.session_state.texto_fijo = res.text

st.write("### Listado de medicamentos")
final_txt = st.text_area("Listado de medicamentos", value=st.session_state.texto_fijo, 
                         placeholder="Escribe o edita la lista que se reproducirá aquí...", height=150)

if st.button("🚀 VALIDAR SEGURIDAD RENAL", use_container_width=True):
    if final_txt and st.session_state.d_lim > 0:
        st.session_state.d_lim -= 1
        st.session_state.m_lim -= 1
        with st.spinner("Validando..."):
            p = f"Actúa como nefrólogo. FG:{fg_f}. PDF:{vademecum[:10000]}. Lista:{final_txt}."
            ans = model.generate_content(p).text
            style = "r-glow" if "ROJO" in ans.upper() else "n-glow"
            st.markdown(f'<div class="resumen-unico {style}"><h3>🔲 Medicamentos afectados</h3>{ans}</div>', unsafe_allow_html=True)
            st.rerun()

st.markdown('<div class="aviso-amarillo">⚠️ <b>Aviso</b>: Requiere verificación profesional.</div>', unsafe_allow_html=True)
