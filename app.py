import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF

# 1. CONFIGURACIÓN E INTERFAZ CON ANIMACIONES GLOW
st.set_page_config(page_title="Validador Renal Pro", layout="wide")

st.markdown("""
    <style>
    /* Animaciones de Parpadeo Glow */
    @keyframes glow-red { 0% { box-shadow: 0 0 10px #ff4b4b; border-color: #ff4b4b; } 50% { box-shadow: 0 0 40px #ff4b4b; border-color: #ff0000; } 100% { box-shadow: 0 0 10px #ff4b4b; border-color: #ff4b4b; } }
    @keyframes glow-orange { 0% { box-shadow: 0 0 10px #ffa500; border-color: #ffa500; } 50% { box-shadow: 0 0 40px #ffa500; border-color: #ff8c00; } 100% { box-shadow: 0 0 10px #ffa500; border-color: #ffa500; } }
    @keyframes glow-green { 0% { box-shadow: 0 0 10px #28a745; border-color: #28a745; } 50% { box-shadow: 0 0 40px #28a745; border-color: #1e7e34; } 100% { box-shadow: 0 0 10px #28a745; border-color: #28a745; } }

    .report-box { padding: 30px; border-radius: 15px; margin-top: 20px; border: 3px solid; transition: all 0.3s ease; }
    .rojo { background-color: #f8d7da; color: #721c24; animation: glow-red 2s infinite; }
    .naranja { background-color: #fff3cd; color: #856404; animation: glow-orange 2s infinite; }
    .verde { background-color: #d4edda; color: #155724; animation: glow-green 2s infinite; }
    
    .linea-separacion { border-top: 2px solid rgba(0,0,0,0.2); margin: 20px 0; }
    .titulo-alerta { font-size: 1.5em; font-weight: bold; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CARGA SILENCIOSA DE PDF Y IA
@st.cache_resource
def cargar_recursos():
    texto_pdf = ""
    try:
        doc = fitz.open("vademecum_renal.pdf")
        texto_pdf = "".join([p.get_text() for p in doc])
    except: pass
    
    modelo = None
    if "API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["API_KEY"])
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                modelo = genai.GenerativeModel(m.name)
                break
    return modelo, texto_pdf

model, contexto_vademecum = cargar_recursos()

# 3. INTERFAZ: COLUMNA IZQUIERDA (CALCULADORA)
st.title("🩺 Validador de Seguridad Farmacológica")
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
        st.metric("FG Calculado", f"{fg} ml/min")

# 4. COLUMNA DERECHA (ENTRADA DUAL Y ANÁLISIS)
with col_der:
    st.header("Análisis de Medicación")
    fg_final = st.number_input("FG para análisis:", 0.0, 200.0, value=float(fg))
    
    tab_txt, tab_img = st.tabs(["📝 Texto / Posología", "📸 Pantallazo / Receta"])
    with tab_txt:
        texto_input = st.text_area("Escriba fármacos y dosis:", placeholder="Ej: Metformina 850mg c/12h", height=100)
    with tab_img:
        img_input = st.file_uploader("Suba o pegue la imagen de la receta", type=['png', 'jpg', 'jpeg'])

    if st.button("🚀 INICIAR VALIDACIÓN"):
        if not (texto_input or img_input):
            st.warning("⚠️ Por favor, introduzca medicación o una imagen.")
        elif model is None:
            st.error("Error de configuración de API.")
        else:
            with st.spinner("Consultando Vademécum Renal..."):
                prompt = f"""
                No saludes. No uses "Como nefrólogo". No uses "Estado:".
                TU PRIORIDAD ES ESTE PDF: {contexto_vademecum[:6000]}
                FG ACTUAL: {fg_final} ml/min.

                INSTRUCCIONES:
                1. Clasifica el riesgo máximo: ROJO, NARANJA o VERDE.
                2. Lista solo los fármacos afectados: "[Nombre]: [PRECAUCIÓN / CONTRAINDICADO / DISMINUIR DOSIS]".
                3. Escribe "---" como separador.
                4. Escribe "Explicación Clínica:" seguido de un análisis breve de la posología y el riesgo renal.
                5. Si no hay riesgos, responde: "OK_VERDE".
                """
                
                try:
                    if img_input:
                        res = model.generate_content([prompt, Image.open(img_input)])
                    else:
                        res = model.generate_content(f"{prompt}\nMedicación: {texto_input}")
                    
                    raw_text = res.text
                    
                    # Lógica de Color y Flash
                    clase_css = "verde"
                    if "ROJO" in raw_text.upper() or "CONTRAINDICADO" in raw_text.upper():
                        clase_css = "rojo"
                    elif any(x in raw_text.upper() for x in ["NARANJA", "PRECAUCIÓN", "DISMINUIR", "AJUSTE"]):
                        clase_css = "naranja"
                    
                    if "OK_VERDE" in raw_text:
                        st.markdown('<div class="report-box verde">🟢 <b>TODOS LOS FÁRMACOS SON SEGUROS</b></div>', unsafe_allow_html=True)
                    else:
                        # Limpiar texto de etiquetas de control y dar formato
                        final_text = raw_text.replace("ROJO", "").replace("NARANJA", "").replace("VERDE", "").strip()
                        final_text = final_text.replace("---", '<div class="linea-separacion"></div>')
                        
                        st.markdown(f"""
                            <div class="report-box {clase_css}">
                                <div class="titulo-alerta">RESULTADO DEL ANÁLISIS</div>
                                {final_text}
                            </div>
                        """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error en análisis: {e}")

st.markdown("---")
st.caption("Uso exclusivo profesional. Basado en Vademécum Renal cargado.")
