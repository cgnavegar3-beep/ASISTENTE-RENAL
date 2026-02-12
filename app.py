import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz
import io
import hashlib

# Soporte para pegado de recortes (Ctrl+V)
try:
    from streamlit_paste_button import paste_image_button
except ImportError:
    paste_image_button = None

# --- 1. CLÁUSULA DE INVARIABILIDAD: ESTILOS DE ALINEACIÓN ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

st.markdown("""
<style>
/* Indicador versión V 2.5 (Sin nombre de modelo) */
.discreet-v {
    position: fixed; top: 0; left: 0;
    background-color: #000; color: #0F0;
    padding: 5px 15px; font-family: monospace; font-size: 11px;
    z-index: 999999; border-bottom-right-radius: 10px;
}

/* Panel derecho forzado a ocupar la misma altura que la calculadora */
.right-panel-stack {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 380px; /* Altura aproximada de la calculadora de la izquierda */
}

/* Cuadro FG Negro con Glow Morado */
.fg-glow-box {
    background-color: #000000 !important;
    color: #ffffff !important;
    padding: 20px !important;
    border-radius: 10px !important;
    text-align: center !important;
    border: 2px solid #6a0dad !important;
    box-shadow: 0 0 15px #a020f0 !important;
    width: 100% !important;
}
.fg-glow-box h1 { font-size: 50px !important; margin: 0 !important; line-height: 1 !important; color: #fff !important; }
.fg-glow-box p { font-size: 13px !important; margin: 0 !important; opacity: 0.8; color: #fff !important; }

/* Compactar inputs de la calculadora */
.stNumberInput, .stRadio { margin-bottom: -10px !important; }

/* Ajuste específico para que el input manual sea visible y estético */
div[data-testid="stTextInput"] label { font-weight: bold; color: #333; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="discreet-v">V 2.5</div>', unsafe_allow_html=True)

# --- 2. MOTOR IA Y MEMORIA (CÓDIGO BLINDADO) ---
if 'meds_list' not in st.session_state: st.session_state.meds_list = ""
if 'analisis' not in st.session_state: st.session_state.analisis = ""
if 'last_hash' not in st.session_state: st.session_state.last_hash = ""

@st.cache_resource
def load_engine():
    try:
        genai.configure(api_key=st.secrets["API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        with fitz.open("vademecum_renal.pdf") as doc:
            txt = "".join([p.get_text() for p in doc])
        return model, txt
    except Exception as e:
        return None, str(e)

model_ia, v_text = load_engine()

if not model_ia:
    st.error("Fallo de conexión. Por favor, revise su API KEY.")
    st.stop()

# --- 3. INTERFAZ DUAL (CALCULADORA vs PANEL DERECHO) ---
st.title("ASISTENTE RENAL")

col_izq, col_der = st.columns([0.4, 0.6], gap="large")

with col_izq:
    st.subheader("📋 Calculadora de Función Renal")
    # Contenedor para la calculadora
    with st.container():
        ed = st.number_input("Edad", 18, 110, 75)
        ps = st.number_input("Peso (kg)", 35, 180, 70)
        cr = st.number_input("Creatinina (mg/dL)", 0.4, 15.0, 1.1)
        sx = st.radio("Sexo", ["H", "M"], horizontal=True)
        
        # Fórmula Cockcroft-Gault
        fg_calc = round((((140 - ed) * ps) / (72 * cr)) * (0.85 if sx == "M" else 1.0), 1)

with col_der:
    # Inicio del Panel Derecho Apilado
    st.markdown('<div class="right-panel-stack">', unsafe_allow_html=True)
    
    # ELEMENTO 1: Input Manual (Ahora forzado a ser visible)
    fg_man = st.text_input("1. Introducir FG Manualmente", 
                          placeholder=f"Si se deja vacío, se usará {fg_calc} mL/min")
    
    # Lógica de valor final
    fg_val = float(fg_man) if fg_man.replace('.','',1).isdigit() else fg_calc
    
    # ELEMENTO 2: Cuadro Negro con Glow
    st.markdown(f"""
    <div class="fg-glow-box">
        <h1>{fg_val}</h1>
        <p>mL/min (Filtrado Glomerular Final)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ELEMENTO 3: Zona de Carga (Subir + Pegar)
    st.write("2. Carga de Medicación")
    c_up, c_pst = st.columns([0.65, 0.35])
    img_pil = None
    with c_up:
        f = st.file_uploader("Imagen", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
        if f: img_pil = Image.open(f).convert("RGB")
    with c_pst:
        if paste_image_button:
            p = paste_image_button("📋 Pegar (Ctrl+V)")
            if p and p.image_data: img_pil = p.image_data.convert("RGB")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- 4. PROCESAMIENTO Y RESULTADOS ---
if img_pil:
    with st.spinner("IA extrayendo medicamentos..."):
        try:
            res_img = model_ia.generate_content(["Lista de fármacos y dosis:", img_pil])
            st.session_state.meds_list = res_img.text
        except: st.error("Error en la lectura de la imagen.")

st.write("---")
st.write("**LISTADO DE MEDICAMENTOS**")
med_edit = st.text_area("Lista:", 
                       value=st.session_state.meds_list if st.session_state.meds_list else "Escribe o edita la lista que se reproducirá aquí si se ha pegado un RECORTE...", 
                       height=120, label_visibility="collapsed")

# Caché de validación para no repetir peticiones idénticas
h_check = hashlib.md5(f"{fg_val}-{med_edit}".encode()).hexdigest()

if st.button("🚀 VALIDAR MEDICACIÓN", use_container_width=True):
    if h_check == st.session_state.last_hash:
        st.toast("Resultado cargado de caché.")
    else:
        with st.spinner("Validando con Vademécum..."):
            prompt = f"FG: {fg_val}. Vademécum: {v_text[:7500]}. Lista: {med_edit}. Indica ajustes (⚠️) o contraindicados (⛔)."
            try:
                st.session_state.analisis = model_ia.generate_content(prompt).text
                st.session_state.last_hash = h_check
            except: st.error("Fallo de conexión.")

if st.session_state.analisis:
    # Semáforo de riesgo
    bg = "#c8e6c9" # Verde
    if "⛔" in st.session_state.analisis: bg = "#ffcdd2" # Rojo
    elif "⚠️" in st.session_state.analisis: bg = "#ffe0b2" # Naranja
    
    st.markdown(f"""
    <div style="background-color: {bg}; padding: 20px; border-radius: 12px; color: #000; border: 1px solid #999;">
        <h3 style="margin-top:0;">MEDICAMENTOS AFECTADOS</h3>
        {st.session_state.analisis}
    </div>
    """, unsafe_allow_html=True)

st.write("---")
st.warning("⚠️ Aviso: Herramienta de apoyo profesional. Requiere verificación clínica.")

if st.button("🗑️ Reset"):
    st.session_state.meds_list = ""; st.session_state.analisis = ""; st.session_state.last_hash = ""; st.rerun()
