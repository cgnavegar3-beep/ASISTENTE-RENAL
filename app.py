import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF

# 1. CONFIGURACIÓN E INTERFAZ PROFESIONAL CON GLOW
st.set_page_config(page_title="Validador Renal Pro", layout="wide")

st.markdown("""
    <style>
    /* Animaciones de Parpadeo Glow */
    @keyframes glow-red { 0% { box-shadow: 0 0 10px #ff4b4b; border-color: #ff4b4b; } 50% { box-shadow: 0 0 40px #ff0000; border-color: #ff0000; } 100% { box-shadow: 0 0 10px #ff4b4b; border-color: #ff4b4b; } }
    @keyframes glow-orange { 0% { box-shadow: 0 0 10px #ffa500; border-color: #ffa500; } 50% { box-shadow: 0 0 40px #ff8c00; border-color: #ff8c00; } 100% { box-shadow: 0 0 10px #ffa500; border-color: #ffa500; } }
    @keyframes glow-green { 0% { box-shadow: 0 0 10px #28a745; border-color: #28a745; } 50% { box-shadow: 0 0 40px #1e7e34; border-color: #1e7e34; } 100% { box-shadow: 0 0 10px #28a745; border-color: #28a745; } }

    .report-box { padding: 30px; border-radius: 15px; margin-top: 20px; border: 3px solid; transition: all 0.3s ease; }
    .rojo { background-color: #f8d7da; color: #721c24; animation: glow-red 1.5s infinite; }
    .naranja { background-color: #fff3cd; color: #856404; animation: glow-orange 1.5s infinite; }
    .verde { background-color: #d4edda; color: #155724; animation: glow-green 1.5s infinite; }
    
    .separator { border: 0; height: 2px; background-image: linear-gradient(to right, rgba(0,0,0,0), rgba(0,0,0,0.6), rgba(0,0,0,0)); margin: 25px 0; }
    .disclaimer { font-size: 0.85em; margin-top: 25px; padding: 12px; border-top: 1px solid rgba(0,0,0,0.1); font-style: italic; color: #444; }
    </style>
    """, unsafe_allow_html=True)

# 2. CARGA DE RECURSOS (ESTRUCTURA BLINDADA)
@st.cache_resource
def load_assets():
    pdf_text = ""
    try:
        doc = fitz.open("vademecum_renal.pdf")
        pdf_text = "".join([p.get_text() for p in doc])
    except: pass
    
    ai_model = None
    if "API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["API_KEY"])
        # Preferimos 1.5-flash para mayor cuota gratuita
        for m_name in ['models/gemini-1.5-flash', 'models/gemini-pro']:
            try:
                ai_model = genai.GenerativeModel(m_name)
                break
            except: continue
    return ai_model, pdf_text

model, contexto_pdf = load_assets()

# 3. INTERFAZ: COLUMNA IZQUIERDA (CALCULADORA)
st.title("🩺 Validador de Seguridad Farmacológica")
st.markdown("---")
col_izq, col_der = st.columns([1, 2], gap="large")

with col_izq:
    st.header("Datos Clínicos")
    with st.container(border=True):
        edad = st.number_input("Edad", 18, 110, 65)
        peso = st.number_input("Peso (kg)", 30, 200, 75)
        crea = st.number_input("Creatinina (mg/dL)", 0.2, 15.0, 1.1)
        sexo = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
        fg = ((140 - edad) * peso) / (72 * crea)
        if sexo == "Mujer": fg *= 0.85
        fg = round(fg, 1)
        st.metric("FG Calculado (C-G)", f"{fg} ml/min")

# 4. COLUMNA DERECHA (ANÁLISIS HÍBRIDO)
with col_der:
    st.header("Gestión de Medicación")
    fg_f = st.number_input("Confirmar FG para análisis:", 0.0, 200.0, value=float(fg))
    
    tab_txt, tab_img = st.tabs(["📝 Texto / Posología", "📸 Imagen / Receta"])
    with tab_txt:
        t_input = st.text_area("Introduzca fármacos:", placeholder="Ej: Metformina 850mg c/12h, Ciprofloxacino 500...", height=100)
    with tab_img:
        i_input = st.file_uploader("Suba o pegue la imagen", type=['png', 'jpg', 'jpeg'])

    if st.button("🚀 INICIAR VALIDACIÓN"):
        if not (t_input or i_input) or model is None:
            st.warning("⚠️ Introduzca fármacos para analizar.")
        else:
            with st.spinner("Analizando Vademécum y Fuentes Oficiales..."):
                prompt = f"""
                REGLAS ESTRICTAS DE RESPUESTA:
                - PROHIBIDO: Saludar, presentarse o decir "como nefrólogo".
                - PASO 1: Busca en el PDF: {contexto_pdf[:7000]}. Si está el fármaco, usa sus tablas de aclaramiento (100-50, 50-10, <10).
                - PASO 2: Si NO está en el PDF, usa tu base de datos médica oficial (FDA, EMA, KDIGO).
                - FG PACIENTE: {fg_f} ml/min.

                FORMATO DE SALIDA:
                1. Una palabra inicial de categoría: ROJO, NARANJA o VERDE.
                2. LISTADO DE AFECTADOS: Escribe cada fármaco que requiera acción en una línea nueva empezando con un punto (•).
                   Ejemplo:
                   • Fármaco X: [CONTRAINDICADO / PRECAUCIÓN / DISMINUIR DOSIS]
                3. Escribe "---" (esto generará la línea visual).
                4. Título "Explicación Clínica:" y debajo el análisis técnico breve.
                """
                
                try:
                    # Análisis multimodal o texto
                    res = model.generate_content([prompt, Image.open(i_input)] if i_input else f"{prompt}\nLista: {t_input}")
                    txt = res.text
                    
                    # Determinación de Color y Alerta
                    clase = "verde"
                    emoji = "🟢"
                    if any(x in txt.upper() for x in ["ROJO", "CONTRAINDICADO"]): 
                        clase = "rojo"
                        emoji = "🔴"
                    elif any(x in txt.upper() for x in ["NARANJA", "PRECAUCIÓN", "DISMINUIR", "AJUSTE"]): 
                        clase = "naranja"
                        emoji = "🟠"
                    
                    if "VERDE" in txt.upper() and "OK" in txt.upper() and len(txt) < 100:
                        st.markdown(f'<div class="report-box verde">🟢 <b>TODOS LOS FÁRMACOS SON SEGUROS PARA FG {fg_f}</b></div>', unsafe_allow_html=True)
                    else:
                        # Formateo de la respuesta limpia
                        txt_final = txt
