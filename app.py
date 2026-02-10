import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import time
import io
from streamlit_paste_button import paste_image_button

# --- 1. CONFIGURACIÓN Y ESTILOS (INVARIABLE) ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

st.markdown("""
    <style>
    /* Contador Discreto Estilo 2.5 - Superior Izquierda */
    .discreet-counter {
        position: fixed !important; top: 0px !important; left: 0px !important;
        background-color: #000000 !important; color: #00FF00 !important;
        padding: 8px 15px !important; font-family: 'Courier New', monospace !important;
        font-size: 13px !important; z-index: 999999 !important;
        border-bottom: 1px solid #333 !important; border-right: 1px solid #333 !important;
    }
    .fg-glow-purple { 
        padding: 20px; border-radius: 15px; border: 2px solid #a020f0;
        box-shadow: 0 0 20px #a020f0; background: #000; text-align: center; color: white;
    }
    .resumen-unico { padding: 25px; border-radius: 15px; margin-top: 20px; border: 2px solid; }
    .v-glow { background-color: #e8f5e9; border-color: #28a745; box-shadow: 0 0 15px #28a745; }
    .n-glow { background-color: #fff3e0; border-color: #ffa500; box-shadow: 0 0 15px #ffa500; }
    .r-glow { background-color: #ffeef0; border-color: #ff4b4b; box-shadow: 0 0 15px #ff4b4b; }
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

st.markdown(f'<div class="discreet-counter">INTENTOS: {st.session_state.d_lim} DÍA | {st.session_state.m_lim} MIN | TOKENS: OK</div>', unsafe_allow_html=True)

@st.cache_resource
def load_sys():
    pdf_txt = ""
    try:
        with fitz.open("vademecum_renal.pdf") as doc:
            pdf_txt = "".join([p.get_text() for p in doc])
    except: pdf_txt = "Error en Vademécum."
    genai.configure(api_key=st.secrets["API_KEY"])
    return genai.GenerativeModel('gemini-1.5-flash'), pdf_txt

model, vademecum = load_sys()

# --- 2. INTERFAZ ---
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
    
    st.write("### 📷 Recorte / Imagen")
    img_up = st.file_uploader("Sube imagen", type=['png', 'jpg', 'jpeg'])
    pst_btn = paste_image_button("📋 Pegar recorte (Ctrl+V)")

# --- 3. EL EMBUDO DE LIMPIEZA (REPARACIÓN PNG) ---
img_para_ia = None

# Captura de datos
if pst_btn.image_data:
    # Si viene del portapapeles
    raw = pst_btn.image_data
    img_para_ia = raw if isinstance(raw, Image.Image) else Image.open(io.BytesIO(raw))
elif img_up:
    # Si viene de archivo subido
    img_para_ia = Image.open(img_up)

# Procesamiento de la imagen antes de enviar a Gemini
if img_para_ia:
    with st.spinner("Procesando imagen..."):
        try:
            # BLINDAJE PNG: Eliminar canal Alpha (transparencia) que causa el TypeError
            if img_para_ia.mode in ("RGBA", "P"):
                img_para_ia = img_para_ia.convert("RGB")
            elif img_para_ia.mode != "RGB":
                img_para_ia = img_para_ia.convert("RGB")
            
            # ENVÍO SEGURO (Usamos img_para_ia ya normalizada)
            res = model.generate_content(["Extrae fármacos y dosis. PRIV si hay nombres.", img_para_ia])
            
            if "PRIV" not in res.text.upper():
                st.session_state.texto_fijo = res.text
            else:
                st.error("Datos personales detectados.")
        except Exception as e:
            st.error(f"Error técnico de imagen: {e}")

# --- 4. LISTADO Y VALIDACIÓN ---
st.write("### Listado de medicamentos")
final_txt = st.text_area("Lista extraída:", value=st.session_state.texto_fijo, height=150)

if st.button("🚀 VALIDAR SEGURIDAD RENAL", use_container_width=True):
    if final_txt and st.session_state.d_lim > 0:
        st.session_state.d_lim -= 1
        st.session_state.m_lim -= 1
        with st.spinner("Consultando Vademécum..."):
            p = f"Actúa como nefrólogo. FG:{fg_f}. Vademecum:{vademecum[:12000]}. Lista:{final_txt}."
            ans = model.generate_content(p).text
            style = "r-glow" if any(x in ans.upper() for x in ["ROJO", "⛔"]) else ("n-glow" if any(x in ans.upper() for x in ["NARANJA", "⚠️"]) else "v-glow")
            st.markdown(f'<div class="resumen-unico {style}"><h3>🔲 Medicamentos afectados</h3>{ans}</div>', unsafe_allow_html=True)
            st.rerun()

st.warning("⚠️ Requiere verificación profesional.")
