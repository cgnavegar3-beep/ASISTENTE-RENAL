import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import time
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Validador Renal Pro", layout="wide")

# --- ESTILOS CSS (Semáforo, Glow Morado, Flash y Contadores) ---
st.markdown("""
    <style>
    @keyframes flash-hit { 0% { opacity: 0.4; } 100% { opacity: 1; } }
    .report-box { padding: 25px; border-radius: 15px; border: 4px solid; margin-top: 20px; animation: flash-hit 0.4s ease-in-out; }
    .rojo { background-color: #3e1a1a; color: #ff4b4b; border-color: #ff4b4b; box-shadow: 0 0 40px #ff4b4b; }
    .naranja { background-color: #3d2b1a; color: #ffa500; border-color: #ffa500; box-shadow: 0 0 40px #ffa500; }
    .verde { background-color: #1a2e1a; color: #28a745; border-color: #28a745; box-shadow: 0 0 40px #28a745; }
    
    .fg-glow-purple {
        padding: 20px; border-radius: 15px; border: 2px solid #a020f0;
        box-shadow: 0 0 25px #a020f0; background: #0e1117; text-align: center; color: white;
    }
    .discreet-counter { position: fixed; top: 10px; right: 10px; font-size: 0.7rem; color: #444; z-index: 1000; text-align: right; }
    .footer-warning { font-size: 0.8rem; color: #666; margin-top: 40px; border-top: 1px solid #333; padding-top: 10px; }
    .med-list-area { border: 1px solid #444; border-radius: 10px; padding: 10px; background: #1a1a1a; }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE CONTADORES ---
if 'daily_limit' not in st.session_state: st.session_state.daily_limit = 1500
if 'min_limit' not in st.session_state: st.session_state.min_limit = 15
if 'last_reset' not in st.session_state: st.session_state.last_reset = time.time()

# Reinicio simple de contador por minuto
if time.time() - st.session_state.last_reset > 60:
    st.session_state.min_limit = 15
    st.session_state.last_reset = time.time()

# Mostrar contadores en la esquina
st.markdown(f"""
    <div class="discreet-counter">
        Restantes hoy: {st.session_state.daily_limit}<br>
        Intentos/min: {st.session_state.min_limit}
    </div>
""", unsafe_allow_html=True)

# --- CARGA DE RECURSOS ---
@st.cache_resource
def load_system():
    pdf_text = ""
    try:
        doc = fitz.open("vademecum_renal.pdf")
        for pag in doc: pdf_text += pag.get_text()
    except: pdf_text = "PDF no encontrado."
    
    model = None
    if "API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash') # Versión estable con alta cuota
    return model, pdf_text

ai_engine, renal_pdf = load_system()

# --- INTERFAZ DUAL ---
col_izq, col_der = st.columns([1, 1], gap="large")

with col_izq:
    st.subheader("📋 Calculadora Dinámica")
    edad = st.number_input("Edad", 18, 110, 70)
    peso = st.number_input("Peso (kg)", 35, 200, 75)
    crea = st.number_input("Creatinina (mg/dL)", 0.4, 15.0, 1.2)
    sexo = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
    fg_calc = round((((140 - edad) * peso) / (72 * crea)) * (0.85 if sexo == "Mujer" else 1.0), 1)

with col_der:
    st.subheader("⚡ Filtrado Glomerular")
    fg_input = st.number_input("Introducir FG directo:", 0.0, 200.0, 0.0)
    fg_final = fg_input if fg_input > 0 else fg_calc
    
    st.markdown(f"""
        <div class="fg-glow-purple">
            <h1 style="margin:0;">{fg_final} ml/min</h1>
            <small>Fórmula: {"Manual" if fg_input > 0 else "Cockcroft-Gault"}</small>
        </div>
    """, unsafe_allow_html=True)

    st.write("") # Espaciador
    img_file = st.file_uploader("📷 Pegar/Subir listado (Imagen)", type=['png', 'jpg', 'jpeg'])

# --- ÁREA DE MEDICAMENTOS ---
st.subheader("💊 Listado de Medicamentos")
texto_reproducido = ""

if img_file:
    with st.spinner("Escaneando y verificando privacidad..."):
        img = Image.open(img_file)
        # Verificación de Privacidad + OCR
        check_prompt = "Si en esta imagen hay NOMBRES de personas, apellidos, DNI o direcciones, responde UNICAMENTE 'BLOQUEO_PRIVACIDAD'. Si es seguro, extrae la lista de fármacos y dosis."
        check_res = ai_engine.generate_content([check_prompt, img]).text
        
        if "BLOQUEO_PRIVACIDAD" in check_res.upper():
            st.error("🚫 SEGURIDAD: Se han detectado datos de pacientes. Uso bloqueado para cumplir con RGPD/HIPAA.")
            st.stop()
        else:
            texto_reproducido = check_res

med_list_input = st.text_area(
    "Escribe o pega tu lista de medicamentos y aquí se reproducirá:",
    value=texto_reproducido,
    height=180,
    placeholder="La lista aparecerá aquí automáticamente al subir una imagen..."
)

# --- BOTÓN DE VALIDACIÓN ---
if st.button("🚀 VALIDAR SEGURIDAD RENAL", use_container_width=True):
    if not med_list_input:
        st.warning("Introduce medicación.")
    elif st.session_state.min_limit <= 0 or st.session_state.daily_limit <= 0:
        st.error("Límite de uso alcanzado. Espera un momento.")
    else:
        st.session_state.daily_limit -= 1
        st.session_state.min_limit -= 1
        
        with st.spinner("Cruzando con Vademécum prioritario..."):
            prompt = f"""
            Actúa como nefrólogo experto. FG: {fg_final}. 
            FUENTE PRIORITARIA PDF: {renal_pdf[:12000]}
            MEDICAMENTOS A VALIDAR: {med_list_input}
            
            REGLAS:
            1. Analiza cada fármaco y su dosis (mg).
            2. Di primero: ROJO (si hay contraindicación), NARANJA (precaución/ajuste) o VERDE.
            3. Estructura: 
               - Listado de afectados con: PRECAUCIÓN, CONTRAINDICADO o DISMINUIR DOSIS.
               - ---
               - Explicación clínica técnica.
            """
            
            try:
                res = ai_engine.generate_content(prompt).text
                
                # Semáforo dinámico
                clase = "verde"
                if "ROJO" in res.upper() or "CONTRAINDICADO" in res.upper(): clase = "rojo"
                elif "NARANJA" in res.upper() or "PRECAUCIÓN" in res.upper() or "DISMINUIR" in res.upper(): clase = "naranja"
                
                if clase == "verde" and "AFECTADO" not in res.upper():
                    res = "VERDE. No se ha detectado ningún fármaco o medicamento afectado."

                st.markdown(f"""
                    <div class="report-box {clase}">
                        {res.replace('---', '<hr style="border:1px solid rgba(255,255,255,0.1)">')}
                    </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error("Error en la consulta. Reintenta en unos segundos.")

# --- MENSAJE DE SEGURIDAD ---
st.markdown("""
    <div class="footer-warning">
        ⚠️ Esta herramienta es solo de ayuda pero el profesional debe de verificar los resultados por si hubiera errores o inconsistencias. 
        Uso de IA para soporte clínico asistido.
    </div>
""", unsafe_allow_html=True)
