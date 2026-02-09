import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import time

# --- 1. CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

st.markdown("""
    <style>
    @keyframes flash-glow { 0% { opacity: 0.6; } 50% { opacity: 1; } 100% { opacity: 0.6; } }
    .header-counter { background: #000000; padding: 10px; border-radius: 5px; margin-bottom: 20px; border: 1px solid #00ff00; width: fit-content; }
    .counter-text { font-family: 'Courier New', monospace; font-weight: bold; font-size: 0.85rem; color: #00ff00; }
    .fg-glow-purple { padding: 20px; border-radius: 15px; border: 2px solid #a020f0; box-shadow: 0 0 25px #a020f0; background: #0e1117; text-align: center; color: white; margin-top: 10px; }
    .report-box { padding: 25px; border-radius: 15px; border: 3px solid; margin-top: 20px; animation: flash-glow 2s infinite; }
    .verde { background-color: #1a2e1a; color: #d4edda; border-color: #28a745; box-shadow: 0 0 20px #28a745; }
    .naranja { background-color: #3d2b1a; color: #fff3cd; border-color: #ffa500; box-shadow: 0 0 20px #ffa500; }
    .rojo { background-color: #3e1a1a; color: #f8d7da; border-color: #ff4b4b; box-shadow: 0 0 20px #ff4b4b; }
    .individual-box { padding: 15px; border-radius: 10px; border-left: 5px solid; margin-bottom: 10px; background: #1e1e1e; color: white; }
    .div-llamativa { height: 4px; background: linear-gradient(90deg, #a020f0, #ff4b4b, #a020f0); margin: 30px 0; border-radius: 2px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GESTIÓN DE CUOTA ---
if 'daily_limit' not in st.session_state: st.session_state.daily_limit = 1500
if 'min_limit' not in st.session_state: st.session_state.min_limit = 15

st.markdown(f"""<div class="header-counter"><span class="counter-text">INTENTOS RESTANTES: {st.session_state.daily_limit} DÍA | {st.session_state.min_limit} MIN</span></div>""", unsafe_allow_html=True)

# --- 3. CARGA DE SISTEMA (TU LÓGICA DE CORRECCIÓN) ---
@st.cache_resource
def init_system():
    txt = ""
    try:
        doc = fitz.open("vademecum_renal.pdf")
        txt = "".join([p.get_text() for p in doc])
    except: txt = "Error leyendo vademecum_renal.pdf"
    
    model = None
    if "API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["API_KEY"])
        # Lista de modelos en orden de prioridad
        modelos_a_probar = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-pro"]
        for m_name in modelos_a_probar:
            try:
                temp_model = genai.GenerativeModel(m_name)
                # Test de comunicación real
                _ = temp_model.generate_content("ping")
                model = temp_model
                break 
            except: continue
    return model, txt

ai_model, pdf_context = init_system()

if ai_model is None:
    st.error("fallo de conexión o superado el número de intentos")
    st.stop()

# --- 4. INTERFAZ ---
col_izq, col_der = st.columns([1, 1], gap="large")

with col_izq:
    st.subheader("📋 Calculadora")
    edad = st.number_input("Edad", 18, 110, 70)
    peso = st.number_input("Peso (kg)", 35, 200, 75)
    crea = st.number_input("Creatinina", 0.4, 15.0, 1.2)
    sexo = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
    fg_calc = round((((140 - edad) * peso) / (72 * crea)) * (0.85 if sexo == "Mujer" else 1.0), 1)

with col_der:
    st.subheader("⚡ Filtrado Glomerular")
    fg_manual = st.number_input("FG Directo:", 0.0, 200.0, 0.0)
    fg_final = fg_manual if fg_manual > 0 else fg_calc
    st.markdown(f"""<div class="fg-glow-purple"><h1 style="margin:0;">{fg_final} ml/min</h1><small>Método: {"Manual" if fg_manual > 0 else "Cockcroft-Gault"}</small></div>""", unsafe_allow_html=True)

st.divider()

# --- 5. ENTRADA MULTIMODAL ---
img_up = st.file_uploader("📷 Subir imagen o RECORTE", type=['png', 'jpg', 'jpeg'])
texto_reproducido = ""

if img_up:
    try:
        img = Image.open(img_up)
        # Verificación RGPD
        res_img = ai_model.generate_content(["Analiza: si hay nombres o DNI responde BLOQUEO. Si no, extrae fármacos.", img])
        if "BLOQUEO" in res_img.text.upper():
            st.error("🚫 BLOQUEO DE PRIVACIDAD: Datos de paciente detectados.")
            st.stop()
        else: texto_reproducido = res_img.text
    except: st.error("Error procesando imagen.")

med_input = st.text_area("Escribe o pega tu lista de medicamentos:", value=texto_reproducido, height=150, placeholder="Escribe aquí...")

# --- 6. VALIDACIÓN ---
if st.button("🚀 VALIDAR SEGURIDAD RENAL", use_container_width=True):
    if not med_input:
        st.warning("Introduzca fármacos.")
    else:
        st.session_state.daily_limit -= 1
        st.session_state.min_limit -= 1
        with st.spinner("Consultando..."):
            prompt = f"""Actúa como ASISTENTE RENAL. FG: {fg_final}. Vademécum: {pdf_context[:8000]}. Medicamentos: {med_input}.
            Reglas: 
            1. Empieza con COLOR_GLOBAL: [VERDE/NARANJA/ROJO].
            2. Lista afectados con ⚠️ o ⛔.
            3. DETALLE: [Nombre]|[Color]|[Comentario]|[Explicación]"""
            
            try:
                res = ai_model.generate_content(prompt).text
                color = "rojo" if "ROJO" in res.upper() else "naranja" if "NARANJA" in res.upper() else "verde"
                
                # Cuadro Resumen
                st.markdown(f"""<div class="report-box {color}"><h3>📊 RESULTADO</h3>{res.split('DETALLE:')[0]}</div>""", unsafe_allow_html=True)
                st.markdown('<div class="div-llamativa"></div>', unsafe_allow_html=True)
                
                # Cuadros Individuales
                if "DETALLE:" in res:
                    for line in res.split("DETALLE:")[1].strip().split("\n"):
                        if "|" in line:
                            n, c, m, e = line.split("|")
                            b_col = "#ff4b4b" if "ROJO" in c.upper() else "#ffa500" if "NARANJA" in c.upper() else "#28a745"
                            st.markdown(f"""<div class="individual-box" style="border-color:{b_col}"><b style="color:{b_col}">{n.upper()}</b><br><small>{m}</small><br>{e}</div>""", unsafe_allow_html=True)
                
                st.info("⚠️ Aviso: Los resultados deben ser verificados por un profesional sanitario.")
            except: st.error("fallo de conexión")
