import streamlit as st
import google.generativeai as genai
from google.api_core import exceptions
from PIL import Image
import fitz  # PyMuPDF
import io
import hashlib
from streamlit_paste_button import paste_image_button

# --- 1. CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

st.markdown("""
    <style>
    /* Cuadro discreto versión del modelo */
    .modelo-version {
        position: fixed !important; top: 0px !important; right: 0px !important;
        background-color: #000000 !important; color: #00FF00 !important;
        padding: 6px 12px !important; font-family: 'Courier New', monospace !important;
        font-size: 12px !important; z-index: 999999 !important;
        border-bottom: 1px solid #333 !important; border-left: 1px solid #333 !important;
    }
    .fg-glow-purple { padding: 20px; border-radius: 15px; border: 2px solid #a020f0; box-shadow: 0 0 20px #a020f0; background: #000; text-align: center; color: white; }
    .resumen-unico { padding: 25px; border-radius: 15px; margin-top: 20px; border: 2px solid; }
    .v-glow { background-color: #e8f5e9; border-color: #28a745; color: #1b5e20; border-width: 2px; }
    .n-glow { background-color: #fff3e0; border-color: #ffa500; color: #e65100; border-width: 2px; }
    .r-glow { background-color: #ffeef0; border-color: #ff4b4b; color: #b71c1c; border-width: 2px; }
    .aviso-seguridad { background-color: #fdfae5; padding: 15px; border-radius: 10px; border: 1px solid #ffeeba; color: #856404; margin-top: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. GESTIÓN DE ESTADO (PERSISTENCIA) ---

@st.cache_resource
def setup_ia_system():
    genai.configure(api_key=st.secrets["API_KEY"])
    # Modelos cargados en memoria una sola vez
    m_pro = genai.GenerativeModel('gemini-1.5-pro')  # Motor principal
    m_flash = genai.GenerativeModel('gemini-2.5-flash')  # Fallback
    pdf_txt = ""
    try:
        with fitz.open("vademecum_renal.pdf") as doc:
            pdf_txt = "".join([p.get_text() for p in doc])
    except:
        pdf_txt = "Error al cargar el vademécum."
    return m_pro, m_flash, pdf_txt

mod_pro, mod_flash, v_txt = setup_ia_system()

def llamar_ia_renal_segura(prompt, imagen=None):
    """ÚNICO PUNTO DE CONTACTO: Fallback automático y gestión de errores"""
    modelos = [mod_pro, mod_flash]
    for i, model in enumerate(modelos):
        try:
            if imagen:
                res = model.generate_content([prompt, imagen])
            else:
                res = model.generate_content(prompt)
            # Devuelve la respuesta y la versión del modelo (solo versión, sin "Gemini")
            version = "1.5 Pro" if i == 0 else "2.5 Flash"
            return res.text, version
        except exceptions.ResourceExhausted:
            if i == 0: continue
            else: raise Exception("Cuota agotada en todos los modelos")
        except Exception as e:
            raise e
    return None, None

# --- 3. INTERFAZ ---
# Mostrar cuadro discreto con versión del modelo
modelo_activo = "1.5 Pro"  # valor por defecto
st.markdown(
    f'<div class="modelo-version">Versión: {modelo_activo}</div>',
    unsafe_allow_html=True
)

st.title("ASISTENTE RENAL")

c1, c2 = st.columns(2)
with c1:
    st.subheader("📋 Parámetros")
    ed = st.number_input("Edad", 18, 110, 70)
    ps = st.number_input("Peso (kg)", 35, 200, 75)
    cr = st.number_input("Creatinina", 0.4, 15.0, 1.2)
    sx = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
    fg_calc = round((((140 - ed) * ps) / (72 * cr)) * (0.85 if sx == "Mujer" else 1.0), 1)

with c2:
    st.subheader("⚡ Filtrado")
    fg_m = st.number_input("FG Manual:", 0.0, 200.0, 0.0)
    fg_final = fg_m if fg_m > 0 else fg_calc
    st.markdown(f'<div class="fg-glow-purple"><h1>{fg_final} ml/min</h1></div>', unsafe_allow_html=True)
    img_up = st.file_uploader("Sube imagen", type=['png', 'jpg', 'jpeg'])
    pst_btn = paste_image_button("📋 Pegar recorte (Ctrl+V)")

# --- 4. LÓGICA DE BOTONES ---
raw_img = pst_btn.image_data if pst_btn.image_data else img_up
if raw_img:
    if st.button("🔍 EXTRAER MEDICAMENTOS"):
        img_pil = Image.open(io.BytesIO(raw_img) if not isinstance(raw_img, Image.Image) else raw_img).convert("RGB")
        with st.spinner("Leyendo imagen..."):
            try:
                # Usamos la función segura
                texto, modelo_usado = llamar_ia_renal_segura("Extrae solo nombres de fármacos y dosis.", img_pil)
                st.session_state.txt_fijo = texto
                # Actualizamos el cuadro con la versión usada
                modelo_activo = modelo_usado
                st.experimental_rerun()
            except:
                st.error("Fallo de conexión o cuota agotada.")

st.write("### Listado de fármacos")
f_input = st.text_area("Edite la lista aquí:", value=st.session_state.txt_fijo, height=150)

if st.button("🚀 VALIDAR SEGURIDAD RENAL", use_container_width=True):
    if f_input:
        with st.spinner("Analizando con Vademécum..."):
            try:
                p = f"Actúa como nefrólogo clínico. FG:{fg_final}. Vademécum:{v_txt[:8000]}. Lista:{f_input}. Analiza dosis y seguridad."
                ans, motor = llamar_ia_renal_segura(p)
                st.session_state.res_clinico = ans
                modelo_activo = motor  # actualizamos cuadro con la versión usada
                if motor == "2.5 Flash": st.toast("Utilizando motor de respaldo (Flash)")
                st.experimental_rerun()
            except:
                st.error("fallo de conexión o superado el número de intentos")

# --- 5. RENDERIZADO ANCLADO ---
if st.session_state.res_clinico:
    ans = st.session_state.res_clinico
    clr = "v-glow"
    if any(x in ans.upper() for x in ["⛔", "CONTRAINDICADO", "ROJO"]): clr = "r-glow"
    elif any(x in ans.upper() for x in ["⚠️", "AJUSTE", "NARANJA", "PRECAUCIÓN"]): clr = "n-glow"
    
    st.markdown(f'<div class="resumen-unico {clr}"><h3>🔲 Análisis de Seguridad Renal</h3>{ans}</div>', unsafe_allow_html=True)

st.markdown('<div class="aviso-seguridad">⚠️ <b>Aviso</b>: Herramienta de apoyo profesional. Verifique siempre con fuentes oficiales.</div>', unsafe_allow_html=True)
