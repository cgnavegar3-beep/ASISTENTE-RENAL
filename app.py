import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import io

# 1. CONFIGURACIÓN E INTERFAZ CON GLOW ANIMADO
st.set_page_config(page_title="Validador Renal Pro", layout="wide")

st.markdown("""
    <style>
    @keyframes glow-red { 0% { box-shadow: 0 0 10px #ff4b4b; border-color: #ff4b4b; } 50% { box-shadow: 0 0 40px #ff0000; border-color: #ff0000; } 100% { box-shadow: 0 0 10px #ff4b4b; border-color: #ff4b4b; } }
    @keyframes glow-orange { 0% { box-shadow: 0 0 10px #ffa500; border-color: #ffa500; } 50% { box-shadow: 0 0 40px #ff8c00; border-color: #ff8c00; } 100% { box-shadow: 0 0 10px #ffa500; border-color: #ffa500; } }
    @keyframes glow-green { 0% { box-shadow: 0 0 10px #28a745; border-color: #28a745; } 50% { box-shadow: 0 0 40px #1e7e34; border-color: #1e7e34; } 100% { box-shadow: 0 0 10px #28a745; border-color: #28a745; } }
    .report-box { padding: 30px; border-radius: 15px; margin-top: 20px; border: 4px solid; transition: all 0.3s ease; }
    .rojo { background-color: #f8d7da; color: #721c24; animation: glow-red 1.5s infinite; }
    .naranja { background-color: #fff3cd; color: #856404; animation: glow-orange 1.5s infinite; }
    .verde { background-color: #d4edda; color: #155724; animation: glow-green 1.5s infinite; }
    .separator { border: 0; height: 2px; background-image: linear-gradient(to right, rgba(0,0,0,0), rgba(0,0,0,0.6), rgba(0,0,0,0)); margin: 25px 0; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXIÓN ACTUALIZADA (SOLUCIÓN ERROR 404)
@st.cache_resource
def inicializar_ia():
    pdf_txt = ""
    try:
        doc = fitz.open("vademecum_renal.pdf")
        pdf_txt = "".join([p.get_text() for p in doc])
    except: pdf_txt = "PDF no encontrado."
    
    if "API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["API_KEY"])
        # Forzamos el uso de gemini-1.5-flash para evitar el error 404 de gemini-pro
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            return model, pdf_txt
        except Exception as e:
            st.error(f"Error al cargar modelo: {e}")
    return None, pdf_txt

model, contexto_pdf = inicializar_ia()

if not model:
    st.error("Falta la API_KEY o el modelo no está disponible.")
    st.stop()

# 3. INTERFAZ DUAL
col_izq, col_der = st.columns([1, 2], gap="large")

with col_izq:
    st.header("1. Datos Clínicos")
    with st.container(border=True):
        edad = st.number_input("Edad", 18, 110, 65)
        peso = st.number_input("Peso (kg)", 30, 200, 75)
        crea = st.number_input("Creatinina (mg/dL)", 0.2, 15.0, 1.1)
        sexo = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
        fg = ((140 - edad) * peso) / (72 * crea)
        if sexo == "Mujer": fg *= 0.85
        st.metric("FG Calculado (C-G)", f"{round(fg, 1)} ml/min")

with col_der:
    st.header("2. Análisis de Medicación")
    fg_final = st.number_input("Confirmar FG para análisis:", 0.0, 200.0, value=float(round(fg, 1)))
    
    img_input = st.file_uploader("📸 Sube imagen o pega pantallazo:", type=['png', 'jpg', 'jpeg'])
    meds_input = st.text_area("📝 O escribe la lista de fármacos y dosis:", placeholder="Ej: Metformina 850mg c/12h", height=100)
    
    if st.button("🚀 INICIAR VALIDACIÓN"):
        if meds_input or img_input:
            with st.spinner("Consultando Vademécum y analizando seguridad..."):
                prompt = f"""
                Analiza la seguridad renal para un FG de {fg_final} ml/min.
                FUENTE PRIORITARIA (PDF): {contexto_pdf[:7000]}
                
                REGLAS:
                1. Cruza mg/dosis con FG.
                2. Formato: Palabra inicial ROJO, NARANJA o VERDE.
                3. Lista de AFECTADOS primero.
                4. Separador "---".
                5. Análisis técnico final.
                """
                try:
                    # Preparar contenido multimodal
                    contenido = [prompt]
                    if img_input: 
                        contenido.append(Image.open(img_input))
                    if meds_input: 
                        contenido.append(f"Texto: {meds_input}")
                    
                    response = model.generate_content(contenido)
                    res = response.text
                    
                    # Semáforo
                    clase, emoji = "verde", "🟢"
                    if any(x in res.upper() for x in ["ROJO", "CONTRAINDICADO"]):
                        clase, emoji = "rojo", "🔴"
                    elif any(x in res.upper() for x in ["NARANJA", "AJUSTE", "PRECAUCIÓN"]):
                        clase, emoji = "naranja", "🟠"
                    
                    # Limpieza
                    clean_res = res.replace("ROJO", "").replace("NARANJA", "").replace("VERDE", "").strip()
                    clean_res = clean_res.replace("---", '<div class="separator"></div>')

                    st.markdown(f"""
                        <div class="report-box {clase}">
                            <div style="font-size: 1.5em; font-weight: bold;">{emoji} INFORME DE SEGURIDAD</div>
                            <div style="white-space: pre-wrap; margin-top:15px;">{clean_res}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st
