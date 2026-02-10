import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import time
import io

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

st.markdown("""
    <style>
    /* Contador Discreto Superior Izquierda (Estilo 2.5) */
    .discreet-counter {
        position: fixed; top: 5px; left: 10px; background-color: #000;
        color: #00FF00; padding: 3px 8px; border-radius: 3px;
        font-family: monospace; font-size: 10px; z-index: 1000;
        border: 1px solid #333; opacity: 0.7;
    }
    
    /* Glow Morado para FG */
    .fg-glow-purple { 
        padding: 20px; border-radius: 15px; border: 2px solid #a020f0;
        box-shadow: 0 0 20px #a020f0; background: #000; text-align: center; color: white;
    }
    
    /* Resultados con Flash Glow */
    @keyframes flash-glow { 0% { opacity: 0.9; } 50% { opacity: 1; } 100% { opacity: 0.9; } }
    .resumen-unico { padding: 25px; border-radius: 15px; margin-top: 20px; border: 2px solid; animation: flash-glow 2s infinite; }
    .verde-soft { background-color: #1a2e1a; border-color: #28a745; color: #d4edda; box-shadow: 0 0 15px #28a745; }
    .naranja-soft { background-color: #3d2b1a; border-color: #ffa500; color: #ffe5b4; box-shadow: 0 0 15px #ffa500; }
    .rojo-soft { background-color: #3e1a1a; border-color: #ff4b4b; color: #f8d7da; box-shadow: 0 0 15px #ff4b4b; }
    
    .div-llamativa { height: 4px; background: linear-gradient(90deg, transparent, #a020f0, #ff4b4b, #a020f0, transparent); margin: 25px 0; border-radius: 10px; }
    .card-individual { padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 8px solid; background: #1e1e1e; color: #efefef; }
    
    .aviso-amarillo { background-color: #fff9c4; color: #333; padding: 15px; border-radius: 10px; border: 1px solid #fbc02d; font-size: 0.85rem; margin-top: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. GESTIÓN DE ESTADO E INTENTOS (Estilo 2.5) ---
if 'd_lim' not in st.session_state: st.session_state.d_lim = 50
if 'm_lim' not in st.session_state: st.session_state.m_lim = 2
if 'last_t' not in st.session_state: st.session_state.last_t = time.time()
if 'med_list' not in st.session_state: st.session_state.med_list = ""

# Reset minuto
if time.time() - st.session_state.last_t > 60:
    st.session_state.m_lim = 2
    st.session_state.last_t = time.time()

st.markdown(f'<div class="discreet-counter">D: {st.session_state.d_lim} | M: {st.session_state.m_lim}</div>', unsafe_allow_html=True)

# --- 3. CONFIGURACIÓN IA Y PDF ---
@st.cache_resource
def init_system():
    pdf_txt = ""
    try:
        with fitz.open("vademecum_renal.pdf") as doc:
            pdf_txt = "".join([p.get_text() for p in doc])
    except: pdf_txt = "PDF no cargado."
    
    genai.configure(api_key=st.secrets["API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
    return model, pdf_txt

ia_model, pdf_memory = init_system()

# --- 4. INTERFAZ DUAL ---
col_izq, col_der = st.columns([1, 1], gap="large")

with col_izq:
    st.subheader("📋 Datos Paciente")
    ed = st.number_input("Edad", 18, 110, 70)
    ps = st.number_input("Peso (kg)", 35, 200, 75)
    cr = st.number_input("Creatinina", 0.4, 15.0, 1.2)
    sx = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
    fg_calc = round((((140 - ed) * ps) / (72 * cr)) * (0.85 if sx == "Mujer" else 1.0), 1)

with col_der:
    st.subheader("⚡ Función Renal")
    fg_man = st.number_input("FG Manual:", 0.0, 200.0, 0.0)
    fg_final = fg_man if fg_man > 0 else fg_calc
    
    st.markdown(f'<div class="fg-glow-purple"><h1>{fg_final} ml/min</h1><small>{"Manual" if fg_man > 0 else "Cockcroft-Gault"}</small></div>', unsafe_allow_html=True)
    
    # Captura de Recorte/Imagen
    img_up = st.file_uploader("Sube o pega tu recorte aquí", type=['png', 'jpg', 'jpeg'])
    
    if img_up:
        with st.spinner("Extrayendo fármacos..."):
            try:
                img = Image.open(img_up)
                ocr_prompt = "Extrae los nombres y dosis de medicamentos de esta imagen. Si hay datos personales como DNI o nombres de pacientes, responde 'PRIV'. No digas nada más."
                res_ocr = ia_model.generate_content([ocr_prompt, img]).text
                
                if "PRIV" in res_ocr.upper():
                    st.error("RGPD: Datos personales detectados. Bloqueado.")
                    st.stop()
                else:
                    st.session_state.med_list = res_ocr
            except:
                st.error("Error al procesar la imagen.")

# --- 5. CUADRO DE MEDICAMENTOS ---
st.write("### Listado de medicamentos")
med_input = st.text_area(
    "Edita o confirma la lista extraída:", 
    value=st.session_state.med_list, 
    height=150,
    placeholder="Aquí aparecerá el texto de tu recorte automáticamente..."
)

# --- 6. VALIDACIÓN ---
if st.button("🚀 VALIDAR SEGURIDAD RENAL", use_container_width=True):
    if not med_input:
        st.warning("Introduce medicación.")
    elif st.session_state.d_lim <= 0:
        st.error("Límite diario alcanzado.")
    else:
        st.session_state.d_lim -= 1
        st.session_state.m_lim -= 1
        with st.spinner("Cotejando con Vademécum..."):
            try:
                prompt = f"""
                Actúa como ASISTENTE RENAL. FG: {fg_final}. 
                PDF: {pdf_memory[:12000]}
                Lista: {med_input}
                
                1. Busca en PDF según rango de FG.
                2. Si no está, usa guías oficiales.
                3. Devuelve:
                   RIESGO: [VERDE/NARANJA/ROJO]
                   GLOBAL: [Comentario corto]
                   AFECTADOS:
                   - [⚠️/⛔] [Fármaco]: [Dosis]
                   DETALLE:
                   [Nombre]|[COLOR]|[Explicación clínica corta]
                """
                res = ia_model.generate_content(prompt).text
                
                # Sombreado dinámico
                color_bg = "verde-soft"
                if "ROJO" in res.upper(): color_bg = "rojo-soft"
                elif "NARANJA" in res.upper(): color_bg = "naranja-soft"

                # Renderizado
                resumen = res.split("DETALLE:")[0].replace("RIESGO:","").replace("GLOBAL:","").replace("AFECTADOS:","").strip()
                st.markdown(f'<div class="resumen-unico {color_bg}"><h3 style="margin:0;">🔲 Medicamentos afectados</h3>{resumen}</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="div-llamativa"></div>', unsafe_allow_html=True)
                
                if "DETALLE:" in res:
                    for det in res.split("DETALLE:")[1].strip().split("\n"):
                        if "|" in det:
                            n, c, e = det.split("|")
                            if "VERDE" not in c.upper():
                                b_color = "#ffa500" if "NARANJA" in c.upper() else "#ff4b4b"
                                st.markdown(f'<div class="card-individual" style="border-color:{b_color};"><strong>{n.upper()}</strong><br>{e}</div>', unsafe_allow_html=True)
                st.rerun()
            except:
                st.error("fallo de conexión o superado el número de intentos")

st.markdown(f"""
    <div class="aviso-amarillo">
        ⚠️ <b>Aviso</b><br>
        Esta herramienta es un apoyo a la revisión farmacoterapéutica. Los resultados deben ser verificados por un profesional sanitario antes de su aplicación clínica.
    </div>
""", unsafe_allow_html=True)
