import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import time

# --- 1. CONFIGURACIÓN DE PÁGINA (DEBE SER LA PRIMERA ORDEN DE ST) ---
st.set_page_config(page_title="Validador Renal Pro", layout="wide")

# --- 2. ESTILOS CSS (Semáforo, Glow Morado y Contadores) ---
st.markdown("""
    <style>
    @keyframes flash-hit { 0% { opacity: 0.4; } 100% { opacity: 1; } }
    .report-box { padding: 25px; border-radius: 15px; border: 4px solid; margin-top: 20px; animation: flash-hit 0.4s ease-out; }
    .rojo { background-color: #3e1a1a; color: #ff4b4b; border-color: #ff4b4b; box-shadow: 0 0 40px #ff4b4b; }
    .naranja { background-color: #3d2b1a; color: #ffa500; border-color: #ffa500; box-shadow: 0 0 40px #ffa500; }
    .verde { background-color: #1a2e1a; color: #28a745; border-color: #28a745; box-shadow: 0 0 40px #28a745; }
    
    .fg-glow-purple {
        padding: 20px; border-radius: 15px; border: 2px solid #a020f0;
        box-shadow: 0 0 25px #a020f0; background: #0e1117; text-align: center; color: white;
    }
    
    .header-counter {
        background: #1e1e2e;
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #00ff00;
        margin-bottom: 20px;
        text-align: center;
    }
    .counter-text { font-family: monospace; font-weight: bold; font-size: 1rem; color: #00ff00; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. GESTIÓN DE CUOTA ---
# Detectamos si estamos en Gemini 1.5 o 2.5 (Configurable)
MODEL_NAME = "gemini-1.5-flash" 

if 'daily_limit' not in st.session_state: st.session_state.daily_limit = 1500
if 'min_limit' not in st.session_state: st.session_state.min_limit = 15
if 'last_reset' not in st.session_state: st.session_state.last_reset = time.time()

# Reset por minuto
if time.time() - st.session_state.last_reset > 60:
    st.session_state.min_limit = 15
    st.session_state.last_reset = time.time()

# --- 4. CONTADOR VISIBLE (ARRIBA) ---
st.markdown(f"""
    <div class="header-counter">
        <span class="counter-text">MODELO: {MODEL_NAME}</span> | 
        <span class="counter-text">RESTANTES HOY: {st.session_state.daily_limit}</span> | 
        <span class="counter-text">INTENTOS/MIN: {st.session_state.min_limit}</span>
    </div>
""", unsafe_allow_html=True)

# --- 5. CARGA DE SISTEMA ---
@st.cache_resource
def load_data():
    pdf_text = ""
    try:
        doc = fitz.open("vademecum_renal.pdf")
        for pag in doc: pdf_text += pag.get_text()
    except: pdf_text = "PDF no encontrado."
    
    model = None
    if "API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["API_KEY"])
        model = genai.GenerativeModel(MODEL_NAME)
    return model, pdf_text

ai_model, renal_context = load_data()

# --- 6. INTERFAZ DUAL ---
col_izq, col_der = st.columns([1, 1.2], gap="large")

with col_izq:
    st.subheader("📋 Parámetros de Cálculo")
    edad = st.number_input("Edad", 18, 110, 70)
    peso = st.number_input("Peso (kg)", 35, 200, 75)
    crea = st.number_input("Creatinina (mg/dL)", 0.4, 15.0, 1.2)
    sexo = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
    fg_calc = round((((140 - edad) * peso) / (72 * crea)) * (0.85 if sexo == "Mujer" else 1.0), 1)

with col_der:
    st.subheader("⚡ Filtrado Glomerular")
    fg_manual = st.number_input("Introducir FG directo (si se tiene):", 0.0, 200.0, 0.0)
    fg_final = fg_manual if fg_manual > 0 else fg_calc
    
    # EFECTO GLOW MORADO
    st.markdown(f"""
        <div class="fg-glow-purple">
            <h1 style="margin:0;">{fg_final} ml/min</h1>
            <small>Método: {"Manual" if fg_manual > 0 else "Cockcroft-Gault"}</small>
        </div>
    """, unsafe_allow_html=True)

st.divider()

# --- 7. MEDICACIÓN Y PRIVACIDAD ---
st.subheader("💊 Listado de Medicamentos")
img_up = st.file_uploader("📷 Subir o pegar pantallazo", type=['png', 'jpg', 'jpeg'])

texto_reproducido = ""
if img_up:
    with st.spinner("Analizando privacidad y extrayendo fármacos..."):
        try:
            img = Image.open(img_up)
            # PROTECCIÓN RGPD
            privacy_check = ai_model.generate_content([
                "Analiza esta imagen. Si hay nombres, apellidos, DNI o datos de pacientes, responde solo: 'BLOQUEO_PRIVACIDAD'. Si es seguro, extrae fármacos y dosis.",
                img
            ]).text
            
            if "BLOQUEO_PRIVACIDAD" in privacy_check.upper():
                st.error("🚫 SEGURIDAD: Se han detectado datos de pacientes. Uso bloqueado.")
                st.stop()
            else:
                texto_reproducido = privacy_check
        except:
            st.error("Error al procesar la imagen.")

med_input = st.text_area("Listado de medicamentos (aquí se reproducirá la imagen):", value=texto_reproducido, height=200)

# --- 8. BOTÓN Y SEMÁFORO ---
if st.button("🚀 VALIDAR SEGURIDAD RENAL", use_container_width=True):
    if not med_input:
        st.warning("Escribe medicamentos.")
    elif st.session_state.daily_limit <= 0:
        st.error("Cuota diaria agotada.")
    else:
        st.session_state.daily_limit -= 1
        st.session_state.min_limit -= 1
        
        with st.spinner("Buscando en Vademécum..."):
            prompt = f"Actúa como nefrólogo clínico. FG: {fg_final}. Contexto PDF: {renal_context[:12000]}. Medicamentos: {med_input}. REGLAS: Di ROJO, NARANJA o VERDE. Lista afectados con comentario corto (PRECAUCIÓN, CONTRAINDICADO, DISMINUIR DOSIS). Separa con '---' la explicación técnica."
            
            try:
                res = ai_model.generate_content(prompt).text
                clase = "verde"
                if "ROJO" in res.upper() or "CONTRAINDICADO" in res.upper(): clase = "rojo"
                elif "NARANJA" in res.upper() or "PRECAUCIÓN" in res.upper(): clase = "naranja"
                
                if clase == "verde" and "AFECTADO" not in res.upper():
                    res = "No se ha detectado ningún fármaco afectado."

                st.markdown(f'<div class="report-box {clase}">{res.replace("---", "<hr>")}</div>', unsafe_allow_html=True)
                st.rerun() # Para actualizar contadores visuales inmediatamente
            except:
                st.error("Fallo de conexión.")

st.markdown("<div style='font-size:0.8rem; color:grey; margin-top:40px;'>Esta herramienta es solo de ayuda; el profesional debe verificar los resultados.</div>", unsafe_allow_html=True)
