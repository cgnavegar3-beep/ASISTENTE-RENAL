import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURACIÓN Y ESTILOS (CONCEPT: VISUAL BREATHING) ---
st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

def inject_ui_styles():
    style = """
    <style>
    /* 1. INDICADOR INTELIGENTE DE MODELO (CUADRO NEGRO) */
    .model-badge {
        background-color: #000000;
        color: #00FF00;
        padding: 6px 14px;
        border-radius: 5px;
        font-family: 'Courier New', monospace;
        font-size: 0.8rem;
        position: fixed;
        top: 20px;
        left: 20px;
        z-index: 10000;
        border: 1px solid #00FF00;
    }
    
    /* TÍTULO CON AIRE */
    .main-title { 
        text-align: center; 
        font-size: 2.8rem; 
        font-weight: 800; 
        color: #1E1E1E; 
        margin-top: -30px; 
        padding-bottom: 30px; 
    }

    /* PESTAÑAS CON AIRE */
    div[data-baseweb='tab-list'] { gap: 20px; margin-bottom: 20px; }
    div[data-baseweb='tab-list'] button { font-size: 1.1rem; }
    div[data-baseweb='tab-list'] button[aria-selected='true'] { 
        border-bottom: 4px solid red !important; 
        font-weight: bold !important; 
    }

    /* CAJA FG GLOW (SIMETRÍA Y AIRE) */
    .fg-glow-box { 
        background-color: #000000; 
        color: #FFFFFF; 
        border: 2px solid #9d00ff; 
        box-shadow: 0 0 15px #9d00ff; 
        padding: 30px; 
        border-radius: 15px; 
        text-align: center; 
        height: 230px; 
        display: flex; 
        flex-direction: column; 
        justify-content: center;
        margin-bottom: 25px;
    }

    /* ESPACIADO DE INPUTS */
    .stNumberInput, .stSelectbox, .stTextInput { margin-bottom: 15px !important; }

    /* AVISO FINAL (AMARILLO PÁLIDO Y ESTÁTICO) */
    .static-warning { 
        background-color: #fffdf2; 
        color: #856404; 
        text-align: center; 
        padding: 20px; 
        border-radius: 12px; 
        border: 1px solid #fcf8e3; 
        margin-top: 60px; 
        font-size: 0.9rem; 
        line-height: 1.6;
    }
    </style>
    """
    st.markdown(style, unsafe_allow_html=True)

# --- 2. LÓGICA DE MODELO ---
if 'reset_counter' not in st.session_state: st.session_state.reset_counter = 0
if 'meds_input' not in st.session_state: st.session_state.meds_input = ""

# Detección y limpieza del nombre del modelo
raw_model = "gemini-2.5-flash"
clean_model = raw_model.replace("gemini-", "").replace("-", " ").title()

inject_ui_styles()

# Render del Indicador
st.markdown(f'<div class="model-badge">{clean_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 EXCEL", "📈 GRÁFICOS"])

with tabs[0]:
    # A) REGISTRO DE PACIENTE
    st.markdown("### Registro de Paciente")
    with st.container():
        c_reg1, c_reg2, c_reg3 = st.columns([1.5, 2.5, 1.2])
        with c_reg1:
            centro = st.text_input("Centro", placeholder="G/M", key=f"c_{st.session_state.reset_counter}")
        with c_reg2:
            rc1, rc2, rc3 = st.columns(3)
            with rc1: edad_reg = st.number_input("Edad", value=None, placeholder="0", key=f"e_{st.session_state.reset_counter}")
            with rc2: alfanum = st.text_input("ID Alfanumérico", placeholder="ID-PACIENTE", key=f"id_{st.session_state.reset_counter}")
            with rc3: residencia = st.selectbox("¿Residencia?", ["No", "Sí"], key=f"res_{st.session_state.reset_counter}")
        with c_reg3:
            st.text_input("Fecha Actual", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)

    st.write("") # Salto de línea para que respire

    # B) INTERFAZ DUAL SIMÉTRICA
    col_izq, col_der = st.columns(2, gap="large") # Gap large para evitar que se peguen

    with col_izq:
        st.markdown("#### 📋 Datos de la Calculadora")
        with st.container(border=True):
            c_edad = st.number_input("Edad (años)", value=edad_reg if edad_reg else 65, key=f"ce_{st.session_state.reset_counter}")
            c_peso = st.number_input("Peso (kg)", value=70.0, step=0.1, key=f"cp_{st.session_state.reset_counter}")
            c_creat = st.number_input("Creatinina (mg/dL)", value=1.0, step=0.1, key=f"cc_{st.session_state.reset_counter}")
            c_sexo = st.selectbox("Sexo", ["Hombre", "Mujer"], key=f"cs_{st.session_state.reset_counter}")
            
            fg_calc = ((140 - c_edad) * c_peso) / (72 * c_creat)
            if c_sexo == "Mujer": fg_calc *= 0.85
            fg_calc = round(fg_calc, 1)

    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular (FG)")
        fg_manual = st.text_input("Introducir FG Manual (si existe)", placeholder="Ej: 45.5", key=f"fgm_{st.session_state.reset_counter}")
        valor_fg = fg_manual if fg_manual else fg_calc
        
        st.markdown(f"""
            <div class="fg-glow-box">
                <div style="font-size: 3.5rem; font-weight: bold;">{valor_fg}</div>
                <div style="font-size: 1.2rem; color: #9d00ff; font-weight: bold; letter-spacing: 2px;">mL/min</div>
            </div>
        """, unsafe_allow_html=True)
        
        # CAPTURA 85/15
        c_up, c_btn = st.columns([0.85, 0.15])
        with c_up:
            st.file_uploader("Subir PDF/Imagen", label_visibility="collapsed", key=f"up_{st.session_state.reset_counter}")
        with c_btn:
            st.button("📋", help="Pegar desde Portapapeles")

    st.write("")
    st.markdown("---")
    st.write("")

    # C) MEDICAMENTOS
    st.markdown("#### 📝 Listado de medicamentos")
    st.session_state.meds_input = st.text_area(
        "Listado", value=st.session_state.meds_input, placeholder="Introduzca la medicación del paciente...", 
        height=180, label_visibility="collapsed", key=f"area_{st.session_state.reset_counter}"
    )

    # D) BOTONERA FINAL
    st.write("")
    b_val, b_res = st.columns([0.85, 0.15])
    with b_val:
        if st.button("🚀 INICIAR VALIDACIÓN CLÍNICA", use_container_width=True):
            st.info("Procesando datos...")
    with b_res:
        if st.button("🗑️ RESET", use_container_width=True):
            st.session_state.reset_counter += 1
            st.session_state.meds_input = ""
            st.rerun()

# E) AVISO FINAL (AMARILLO PÁLIDO)
st.markdown('<div class="static-warning">⚠️ <b>Nota de Seguridad:</b> Esta aplicación es una herramienta de apoyo a la toma de decisiones clínicas. Los cálculos y recomendaciones deben ser supervisados por un profesional sanitario colegiado antes de cualquier intervención terapéutica.</div>', unsafe_allow_html=True)
