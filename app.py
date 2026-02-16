import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

def inject_ui_styles():
    style = """
    <style>
    .block-container { max-width: 100% !important; padding-top: 2.5rem !important; padding-left: 4% !important; padding-right: 4% !important; }
    .model-badge { background-color: #000000 !important; color: #00FF00 !important; padding: 5px 12px; border-radius: 3px; font-family: monospace !important; font-size: 0.8rem; position: fixed; top: 15px; left: 15px; z-index: 1000000; }
    .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin-top: 0px; padding-bottom: 20px; }
    .id-display { color: #666; font-family: monospace; font-size: 0.85rem; margin-top: -10px; margin-bottom: 20px; }
    .formula-tag { font-size: 1.1rem; color: #444; font-weight: 600; margin-top: 15px; display: block; border-top: 1px solid #eee; padding-top: 10px; }
    .fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; margin-bottom: 20px; }
    .stFileUploader section { min-height: 48px !important; border-radius: 8px !important; }
    .stButton > button { height: 48px !important; border-radius: 8px !important; }
    </style>
    """
    st.markdown(style, unsafe_allow_html=True)

# --- 2. LÓGICA DE ESTADO PARA VOLCADO AUTOMÁTICO ---
if 'meds_content' not in st.session_state:
    st.session_state.meds_content = ""

# Función que se ejecuta al subir un archivo
def process_ocr():
    if st.session_state.uploader_key:
        # Aquí es donde Gemini lee la imagen. Por ahora, simulamos el volcado:
        file_name = st.session_state.uploader_key.name
        texto_simulado = f"--- CONTENIDO DE: {file_name} ---\nMedicamento A 5mg\nMedicamento B 10mg\nRevisar dosis..."
        st.session_state.meds_content = texto_simulado

inject_ui_styles()

# Indicador
raw_model = "gemini-2.5-flash"
st.markdown(f'<div class="model-badge">{raw_model.replace("gemini-", "").replace("-", " ").title()}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 EXCEL", "📈 GRÁFICOS"])

with tabs[0]:
    # A) REGISTRO
    c_reg_header, c_reg_btn = st.columns([0.9, 0.1])
    with c_reg_header: st.markdown("### Registro de Paciente")
    with c_reg_btn: 
        if st.button("🗑️ Limpiar", key="clean_all"):
            st.session_state.meds_content = ""
            st.rerun()

    c_reg1, c_reg2, c_reg3 = st.columns([1, 2, 1])
    with c_reg1: centro = st.text_input("Centro", placeholder="G/M")
    with c_reg2:
        r1, r2, r3 = st.columns(3)
        edad = r1.number_input("Edad", value=None, placeholder="0")
        alfa = r2.text_input("ID Alfanumérico", placeholder="Escriba...")
        res = r3.selectbox("¿Residencia?", ["No", "Sí"])
    with c_reg3: st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)

    st.markdown(f'<div class="id-display">ID Registro: {centro if centro else "---"}-{str(int(edad)) if edad else "00"}-{alfa if alfa else "---"}</div>', unsafe_allow_html=True)

    # B) INTERFAZ DUAL
    col_izq, col_der = st.columns(2, gap="large")

    with col_izq:
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            calc_e = st.number_input("Edad (años)", value=edad if edad else 65)
            calc_p = st.number_input("Peso (kg)", value=70.0)
            calc_c = st.number_input("Creatinina (mg/dL)", value=1.0)
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"])
            fg = round(((140 - calc_e) * calc_p) / (72 * calc_c) * (0.85 if calc_s == "Mujer" else 1.0), 1)
            st.markdown('<span class="formula-tag">Fórmula: Cockcroft-Gault</span>', unsafe_allow_html=True)

    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual", placeholder="Valor...")
        st.markdown(f'<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{fg_m if fg_m else fg}</div><div style="font-size: 1rem; color: #9d00ff;">mL/min</div></div>', unsafe_allow_html=True)
        
        c_up, c_btn = st.columns([0.75, 0.25])
        with c_up:
            # IMPORTANTE: on_change activa el volcado al subir
            st.file_uploader("Subir", label_visibility="collapsed", key="uploader_key", on_change=process_ocr)
        with c_btn:
            if st.button("✂️ RECORTE", use_container_width=True):
                # Simulamos que al pulsar el botón tras un recorte se vuelca el contenido
                st.session_state.meds_content = "Texto extraído del recorte del portapapeles..."
                st.rerun()

    st.write("")
    st.markdown("---")

    # C) MEDICAMENTOS (EDITABLE Y CON VOLCADO)
    st.markdown("#### 📝 Listado de medicamentos (Editable)")
    # El valor está atado a meds_content en session_state
    medicacion_final = st.text_area("Listado", value=st.session_state.meds_content, height=180, label_visibility="collapsed")
    # Actualizamos el estado si el usuario escribe a mano
    st.session_state.meds_content = medicacion_final

    if st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True):
        st.success("Analizando...")

st.markdown('<div class="static-warning">⚠️ Apoyo a la revisión farmacoterapéutica. Verifique con fuentes oficiales.</div>', unsafe_allow_html=True)
