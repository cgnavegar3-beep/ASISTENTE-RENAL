import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF

# 1. ESTILO Y CONFIGURACIÓN
st.set_page_config(page_title="Validador Renal Pro", layout="wide")

st.markdown("""
    <style>
    @keyframes glow-red { 0% { box-shadow: 0 0 10px #ff4b4b; } 50% { box-shadow: 0 0 40px #ff0000; } 100% { box-shadow: 0 0 10px #ff4b4b; } }
    @keyframes glow-orange { 0% { box-shadow: 0 0 10px #ffa500; } 50% { box-shadow: 0 0 40px #ff8c00; } 100% { box-shadow: 0 0 10px #ffa500; } }
    @keyframes glow-green { 0% { box-shadow: 0 0 10px #28a745; } 50% { box-shadow: 0 0 40px #1e7e34; } 100% { box-shadow: 0 0 10px #28a745; } }
    .report-box { padding: 30px; border-radius: 15px; margin-top: 20px; border: 4px solid; }
    .rojo { background-color: #f8d7da; color: #721c24; animation: glow-red 1.5s infinite; }
    .naranja { background-color: #fff3cd; color: #856404; animation: glow-orange 1.5s infinite; }
    .verde { background-color: #d4edda; color: #155724; animation: glow-green 1.5s infinite; }
    .separator { border: 0; height: 2px; background-image: linear-gradient(to right, rgba(0,0,0,0), rgba(0,0,0,0.6), rgba(0,0,0,0)); margin: 20px 0; }
    </style>
    """, unsafe_allow_html=True)

# 2. CARGA DE SISTEMA
@st.cache_resource
def load_renal_ai():
    pdf_txt = ""
    try:
        doc = fitz.open("vademecum_renal.pdf")
        pdf_txt = "".join([p.get_text() for p in doc])
    except: pdf_txt = "Contexto PDF no disponible."
    
    ai_model = None
    if "API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["API_KEY"])
        ai_model = genai.GenerativeModel('gemini-1.5-flash')
    return ai_model, pdf_txt

model, contexto_pdf = load_renal_ai()

# 3. INTERFAZ DUAL
st.title("🩺 Validador de Seguridad Farmacológica")
c1, c2 = st.columns([1, 2], gap="large")

with c1:
    st.header("Datos Clínicos")
    with st.container(border=True):
        edad = st.number_input("Edad", 18, 110, 65)
        peso = st.number_input("Peso (kg)", 30, 200, 75)
        crea = st.number_input("Creatinina", 0.2, 15.0, 1.1)
        sexo = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
        fg_calc = round(((140 - edad) * peso) / (72 * crea) * (0.85 if sexo == "Mujer" else 1.0), 1)
        st.metric("FG Calculado (C-G)", f"{fg_calc} ml/min")

with c2:
    st.header("Gestión de Medicación")
    fg_final = st.number_input("Filtrado para el análisis:", 0.0, 200.0, value=float(fg_calc))
    u_img = st.file_uploader("📸 Sube imagen o pega pantallazo:", type=['png', 'jpg', 'jpeg'])
    u_txt = st.text_area("📝 O escribe lista y dosis:", height=100)

    if st.button("🚀 INICIAR VALIDACIÓN"):
        if not (u_img or u_txt) or model is None:
            st.warning("⚠️ Introduce datos para analizar.")
        else:
            with st.spinner("Analizando seguridad renal..."):
                # PROMPT BLINDADO
                prompt_med = f"""
                Analiza para un Filtrado Glomerular de {fg_final} ml/min.
                Usa este Vademécum como prioridad: {contexto_pdf[:7000]}
                
                REGLAS:
                - Empieza SIEMPRE con una palabra: ROJO, NARANJA o VERDE.
                - Enumera con puntos • los fármacos afectados y su acción (PRECAUCIÓN, CONTRAINDICADO, AJUSTE).
                - Usa "---" como separador visual.
                - Cruza la dosis (mg) con el FG del paciente.
                - No menciones a la IA ni saludes.
                """
                
                try:
                    # Construcción de la entrada
                    query = [prompt_med]
                    if u_img: query.append(Image.open(u_img))
                    if u_txt: query.append(u_txt)
                    
                    # Respuesta de la IA
                    raw_response = model.generate_content(query)
                    # Forzamos que sea solo el texto de la respuesta
                    resultado_texto = str(raw_response.text)
                    
                    # Semáforo dinámico
                    categoria = "verde"
                    icon = "🟢"
                    if "ROJO" in resultado_texto.upper(): 
                        categoria, icon = "rojo", "🔴"
                    elif any(x in resultado_texto.upper() for x in ["NARANJA", "AJUSTE", "PRECAUCIÓN"]):
                        categoria, icon = "naranja", "🟠"
                    
                    # Formateo final
                    final_html = resultado_texto.replace("ROJO", "").replace("NARANJA", "").replace("VERDE", "").strip()
                    final_html = final_html.replace("---", '<div class="separator"></div>')

                    st.markdown(f"""
                        <div class="report-box {categoria}">
                            <div style="font-size: 1.5em; font-weight: bold;">{icon} INFORME MÉDICO</div>
                            <div style="white-space: pre-wrap; margin-top:15px;">{final_html}</div>
                        </div>
                    """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Error técnico: {str(e)}")

st.caption("Validación basada en Vademécum Renal Local + Guías Internacionales.")
