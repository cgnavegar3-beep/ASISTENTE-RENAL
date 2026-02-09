import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import time

# --- 1. CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

# Estilos CSS Estrictos (Glows, Contadores, Animaciones)
st.markdown("""
    <style>
    @keyframes flash-glow { 0% { opacity: 0.6; } 50% { opacity: 1; } 100% { opacity: 0.6; } }
    .header-counter { background: #000000; padding: 10px; border-radius: 5px; margin-bottom: 20px; text-align: left; width: fit-content; }
    .counter-text { font-family: 'Courier New', monospace; font-weight: bold; font-size: 0.85rem; color: #00ff00; }
    
    .fg-glow-purple {
        padding: 20px; border-radius: 15px; border: 2px solid #a020f0;
        box-shadow: 0 0 25px #a020f0; background: #0e1117; text-align: center; color: white; margin-top: 10px;
    }
    
    .report-box { padding: 25px; border-radius: 15px; border: 3px solid; margin-top: 20px; animation: flash-glow 2s infinite; }
    .verde { background-color: #1a2e1a; color: #d4edda; border-color: #28a745; box-shadow: 0 0 20px #28a745; }
    .naranja { background-color: #3d2b1a; color: #fff3cd; border-color: #ffa500; box-shadow: 0 0 20px #ffa500; }
    .rojo { background-color: #3e1a1a; color: #f8d7da; border-color: #ff4b4b; box-shadow: 0 0 20px #ff4b4b; }
    
    .individual-box { padding: 15px; border-radius: 10px; border-left: 5px solid; margin-bottom: 10px; background: #1e1e1e; color: white; }
    .div-llamativa { height: 4px; background: linear-gradient(90deg, #a020f0, #ff4b4b, #a020f0); margin: 30px 0; border-radius: 2px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GESTIÓN DE CUOTA Y MODELO ---
# Lógica de detección automática de modelo para evitar Error 404
if 'daily_limit' not in st.session_state: st.session_state.daily_limit = 1500
if 'min_limit' not in st.session_state: st.session_state.min_limit = 15
if 'tokens_est' not in st.session_state: st.session_state.tokens_est = 0

# Contador Discreto Superior Izquierda
st.markdown(f"""
    <div class="header-counter">
        <span class="counter-text">DÍA: {st.session_state.daily_limit} | MIN: {st.session_state.min_limit} | TOKENS: {st.session_state.tokens_est}</span>
    </div>
""", unsafe_allow_html=True)

@st.cache_resource
def init_system():
    # Carga de PDF una sola vez
    txt = ""
    try:
        doc = fitz.open("vademecum_renal.pdf")
        txt = "".join([p.get_text() for p in doc])
    except: txt = "Error leyendo vademecum_renal.pdf"
    
    # Intento de conexión en cascada
    model = None
    if "API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["API_KEY"])
        for m_name in ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-flash-latest"]:
            try:
                model = genai.GenerativeModel(m_name)
                # Test rápido
                model.generate_content("test")
                break
            except: continue
    return model, txt

ai_model, pdf_context = init_system()

# --- 3. INTERFAZ DUAL ---
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
    fg_manual = st.number_input("Introducir FG directo:", 0.0, 200.0, 0.0)
    fg_final = fg_manual if fg_manual > 0 else fg_calc
    
    st.markdown(f"""
        <div class="fg-glow-purple">
            <h1 style="margin:0;">{fg_final} ml/min</h1>
            <p style="margin:0; font-size:0.8rem;">Método: {"Manual" if fg_manual > 0 else "Cockcroft-Gault"}</p>
        </div>
    """, unsafe_allow_html=True)

st.divider()

# --- 4. ENTRADA MULTIMODAL ---
st.subheader("💊 Listado de Medicamentos")
img_up = st.file_uploader("📷 Subir imagen o RECORTE", type=['png', 'jpg', 'jpeg'])

texto_reproducido = ""
if img_up:
    with st.spinner("Procesando imagen..."):
        try:
            img = Image.open(img_up)
            # Verificación RGPD y extracción
            check = ai_model.generate_content([
                "Analiza la imagen. Si hay nombres, DNI o datos personales, responde BLOQUEO. Si es seguro, extrae solo la lista de fármacos y dosis.",
                img
            ])
            if "BLOQUEO" in check.text.upper():
                st.error("🚫 SEGURIDAD: Se han detectado datos de pacientes. Uso bloqueado.")
                st.stop()
            else:
                texto_reproducido = check.text
        except: st.error("Fallo de conexión o límite excedido.")

med_input = st.text_area("Escribe o pega tu lista de medicamentos (se reproducirá si usas imagen):", 
                         value=texto_reproducido, height=150)

# --- 5. LÓGICA DE VALIDACIÓN ---
if st.button("🚀 VALIDAR SEGURIDAD RENAL", use_container_width=True):
    if not med_input:
        st.warning("Escribe medicamentos.")
    else:
        with st.spinner("Consultando Vademécum y IA..."):
            st.session_state.daily_limit -= 1
            st.session_state.min_limit -= 1
            
            prompt = f"""
            Actúa como ASISTENTE RENAL. FG: {fg_final}. 
            Vademécum (Prioritario): {pdf_context[:8000]}
            Medicamentos: {med_input}
            
            TAREA:
            1. Analiza cada fármaco y dosis (mg).
            2. Clasifica: VERDE (seguro), NARANJA (ajuste/precaución), ROJO (contraindicado).
            3. Si no hay afectados, responde: "Ninguno afectado".
            4. Si hay afectados, responde con este formato:
               COLOR_GLOBAL: [VERDE/NARANJA/ROJO]
               RESUMEN: [Lista de afectados con icono ⚠️ o ⛔]
               DETALLE:
               [Nombre Fármaco]|[Color]|[Comentario corto]|[Explicación clínica breve]
            """
            
            try:
                response = ai_model.generate_content(prompt).text
                
                # Procesamiento de respuesta para la interfaz
                color_global = "verde"
                if "ROJO" in response.upper(): color_global = "rojo"
                elif "NARANJA" in response.upper(): color_global = "naranja"
                
                # Cuadro Resumen Único
                st.markdown(f"""
                    <div class="report-box {color_global}">
                        <h3>📊 RESULTADO DE SEGURIDAD</h3>
                        <p>{response.split('DETALLE:')[0].replace('COLOR_GLOBAL:', '').strip()}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # Línea divisoria
                st.markdown('<div class="div-llamativa"></div>', unsafe_allow_html=True)
                
                # Cuadros Individuales (si hay detalle)
                if "DETALLE:" in response:
                    detalles = response.split("DETALLE:")[1].strip().split("\n")
                    for det in detalles:
                        if "|" in det:
                            name, col, comm, expl = det.split("|")
                            border_col = "#28a745" if "VERDE" in col.upper() else "#ffa500" if "NARANJA" in col.upper() else "#ff4b4b"
                            st.markdown(f"""
                                <div class="individual-box" style="border-color: {border_col};">
                                    <b style="color:{border_col};">{name.upper()}</b><br>
                                    <small>{comm}</small><br>
                                    {expl}
                                </div>
                            """, unsafe_allow_html=True)
                
                st.info("⚠️ Aviso: Apoyo a la revisión farmacoterapéutica. Verificar resultados por un profesional sanitario.")
                
            except Exception as e:
                st.error("fallo de conexión o superado el número de intentos")

st.markdown("<br><br>", unsafe_allow_html=True)
