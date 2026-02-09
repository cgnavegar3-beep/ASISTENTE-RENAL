import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

st.markdown("""
    <style>
    .header-counter { background: #000000; padding: 10px; border-radius: 5px; margin-bottom: 20px; border: 1px solid #00ff00; width: fit-content; }
    .counter-text { font-family: monospace; font-weight: bold; font-size: 0.85rem; color: #00ff00; }
    .fg-glow-purple { padding: 20px; border-radius: 15px; border: 2px solid #a020f0; box-shadow: 0 0 25px #a020f0; background: #0e1117; text-align: center; color: white; margin-top: 10px; }
    .report-box { padding: 25px; border-radius: 15px; border: 3px solid; margin-top: 20px; }
    .verde { background-color: #1a2e1a; color: #d4edda; border-color: #28a745; }
    .naranja { background-color: #3d2b1a; color: #fff3cd; border-color: #ffa500; }
    .rojo { background-color: #3e1a1a; color: #f8d7da; border-color: #ff4b4b; }
    .individual-box { padding: 15px; border-radius: 10px; border-left: 5px solid; margin-bottom: 10px; background: #1e1e1e; color: white; }
    </style>
    """, unsafe_allow_html=True)

# CONTADOR
st.markdown('<div class="header-counter"><span class="counter-text">INTENTOS: 1500 DÍA | 15 MIN</span></div>', unsafe_allow_html=True)

# INTERFAZ
col_izq, col_der = st.columns([1, 1], gap="large")
with col_izq:
    st.subheader("📋 Parámetros")
    edad = st.number_input("Edad", 18, 110, 70)
    peso = st.number_input("Peso (kg)", 35, 200, 75)
    crea = st.number_input("Creatinina", 0.4, 15.0, 1.2)
    sexo = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
    fg_calc = round((((140 - edad) * peso) / (72 * crea)) * (0.85 if sexo == "Mujer" else 1.0), 1)

with col_der:
    st.subheader("⚡ Filtrado Glomerular")
    fg_manual = st.number_input("FG Directo:", 0.0, 200.0, 0.0)
    fg_final = fg_manual if fg_manual > 0 else fg_calc
    st.markdown(f'<div class="fg-glow-purple"><h1 style="margin:0;">{fg_final} ml/min</h1><small>Cockcroft-Gault</small></div>', unsafe_allow_html=True)

st.divider()

# ENTRADA
img_up = st.file_uploader("📷 Imagen/Recorte", type=['png', 'jpg', 'jpeg'])
med_input = st.text_area("Lista de medicamentos:", height=150)

# BOTÓN
if st.button("🚀 VALIDAR SEGURIDAD RENAL", use_container_width=True):
    if "API_KEY" not in st.secrets:
        st.error("fallo de conexión o superado el número de intentos")
    else:
        with st.spinner("Analizando..."):
            try:
                genai.configure(api_key=st.secrets["API_KEY"])
                model = genai.GenerativeModel('gemini-2.5-flash')
                doc = fitz.open("vademecum_renal.pdf")
                pdf_text = "".join([p.get_text() for p in doc])
                
                prompt = f"Actúa como ASISTENTE RENAL. FG: {fg_final}. Vademécum: {pdf_text[:8000]}. Medicamentos: {med_input}. Responde con COLOR_GLOBAL: [ROJO/NARANJA/VERDE] y DETALLE: [Nombre]|[Color]|[Comentario]|[Explicación]"
                
                res = model.generate_content([prompt, Image.open(img_up)] if img_up else prompt).text
                color = "rojo" if "ROJO" in res.upper() else "naranja" if "NARANJA" in res.upper() else "verde"
                
                st.markdown(f'<div class="report-box {color}"><h3>📊 INFORME</h3>{res.split("DETALLE:")[0]}</div>', unsafe_allow_html=True)
                if "DETALLE:" in res:
                    for line in res.split("DETALLE:")[1].strip().split("\n"):
                        if "|" in line:
                            n, c, m, e = line.split("|")
                            st.markdown(f'<div class="individual-box"><b>{n.upper()}</b><br>{e}</div>', unsafe_allow_html=True)
            except: st.error("fallo de conexión o superado el número de intentos")

st.info("⚠️ Aviso: esta herramienta es solo de  apoyo profesional. Verificar resultados.")
