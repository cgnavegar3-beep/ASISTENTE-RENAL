import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURACIÓN Y ESTILOS (CONTROL ESTRICTO) ---
st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

def inject_ui_styles():
    style = """
    <style>
    /* 1. INDICADOR INTELIGENTE DE MODELO (CUADRO NEGRO ESTRICTO) */
    .model-indicator {
        background-color: #000000 !important;
        color: #00FF00 !important; /* Verde Neón #0F0 */
        padding: 5px 12px;
        border-radius: 3px;
        font-family: 'Courier New', monospace !important;
        font-size: 0.85rem;
        position: fixed;
        top: 15px;
        left: 15px;
        z-index: 1000000;
        border: 1px solid #00FF00;
        line-height: 1.2;
    }
    
    /* TÍTULO Y PESTAÑAS */
    .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin-top: -45px; padding-bottom: 25px; }
    div[data-baseweb='tab-list'] button[aria-selected='true'] { border-bottom: 4px solid red !important; font-weight: bold !important; }

    /* 2. INTERFAZ DUAL: CAJA GLOW MORADO (REDUCIDA) */
    .fg-glow-box { 
        background-color: #000000; 
        color: #FFFFFF; 
        border: 2px solid #9d00ff; 
        box-shadow: 0 0 15px #9d00ff; 
        padding: 10px; 
        border-radius: 12px; 
        text-align: center; 
        height: 160px; /* Reducción de tamaño */
        display: flex; 
        flex-direction: column; 
        justify-content: center;
        margin-bottom: 10px;
    }

    /* ESPACIADO GENERAL PARA "RESPIRAR" */
    .stNumberInput, .stSelectbox, .stTextInput { margin-bottom: 10px !important; }
    
    /* AVISO FINAL AMARILLO PÁLIDO */
    .static-warning { 
        background-color: #fffdf2; 
        color: #856404; 
        text-align: center; 
        padding: 15px; 
        border-radius: 10px; 
        border: 1px solid #fcf8e3; 
        margin-top: 50px; 
        font-size: 0.85rem; 
    }
    </style>
    """
    st.markdown(style, unsafe_allow_html=True)

# --- 2. LÓGICA DE DETECCIÓN DE MODELO ---
# En un entorno real, aquí se detecta el modelo de la API
raw_model_name = "gemini-2.5-flash" 
# Eliminamos "gemini-" y limpiamos formato
clean_model = raw_model_name.replace("gemini-", "").replace("-", " ").title()

# --- 3. GESTIÓN DE ESTADO ---
if 'reset_counter' not in st.session_state: st.session_state.reset_counter = 0
if 'meds_input' not in st.session_state: st.session_state.meds_input = ""

inject_ui_styles()

# Render del Indicador y Título
st.markdown(f'<div class="model-indicator">{clean_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 EXCEL", "📈 GRÁFICOS"])

with tabs[0]:
    # A) REGISTRO
    st.markdown("### Registro de Paciente")
    c_reg1, c_reg2, c_reg3 = st.columns([1.5, 2.5, 1.2])
    with c_reg1:
        centro = st.text_input("Centro", placeholder="G/M", key=f"c_{st.session_state.reset_counter}")
    with c_reg2:
        rc1, rc2, rc3 = st.columns(3)
        with rc1: edad_reg = st.number_input("Edad", value=None, placeholder="0", key=f"e_{st.session_state.reset_counter}")
        with rc2: alfanum = st.text_input("ID Alfanumérico", placeholder="Escriba...", key=f"id_{st.session_state.reset_counter}")
        with rc3: residencia = st.selectbox("¿Residencia?", ["No", "Sí"], key=f"res_{st.session_state.reset_counter}")
    with c_reg3:
        st.text_input("Fecha Actual", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)

    st.write("") 

    # B) INTERFAZ DUAL (SIMETRÍA ABSOLUTA)
    col_izq, col_der = st.columns(2, gap="large")

    with col_izq:
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            # 4 filas para igualar la altura de la derecha de forma natural
            c_edad = st.number_input("Edad (años)", value=edad_reg if edad_reg else 65, key=f"ce_{st.session_state.reset_counter}")
            c_peso = st.number_input("Peso (kg)", value=70.0, step=0.1, key=f"cp_{st.session_state.reset_counter}")
            c_creat = st.number_input("Creatinina (mg/dL)", value=1.0, step=0.1, key=f"cc_{st.session_state.reset_counter}")
            c_sexo = st.selectbox("Sexo", ["Hombre", "Mujer"], key=f"cs_{st.session_state.reset_counter}")
            
            fg_calc = ((140 - c_edad) * c_peso) / (72 * c_creat)
            if c_sexo == "Mujer": fg_calc *= 0.85
            fg_calc = round(fg_calc, 1)

    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_manual = st.text_input("Ajuste Manual", placeholder="Introduzca valor...", key=f"fgm_{st.session_state.reset_counter}")
        
        valor_fg = fg_manual if fg_manual else fg_calc
        
        # Cuadro morado más pequeño
        st.markdown(f"""
            <div class="fg-glow-box">
                <div style="font-size: 3rem; font-weight: bold; line-height: 1;">{valor_fg}</div>
                <div style="font-size: 0.9rem; color: #9d00ff; font-weight: bold; margin-top: 5px;">mL/min</div>
            </div>
        """, unsafe_allow_html=True)
        
        # PROPORCIÓN ESTRICTA 80:20 (Misma anchura total que arriba)
        c_up, c_btn = st.columns([0.8, 0.2])
        with c_up:
            st.file_uploader("Subir", label_visibility="collapsed", key=f"up_{st.session_state.reset_counter}")
        with c_btn:
            st.button("📋", use_container_width=True, help="Recorte Ctrl+V")

    st.markdown("---")

    # C) MEDICAMENTOS
    st.markdown("#### 📝 Listado de medicamentos")
    st.session_state.meds_input = st.text_area(
        "Listado", value=st.session_state.meds_input, height=150, 
        label_visibility="collapsed", key=f"area_{st.session_state.reset_counter}"
    )

    # D) BOTONERA FINAL
    b_val, b_res = st.columns([0.8, 0.2])
    with b_val:
        if st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True):
            st.info("Iniciando validación...")
    with b_res:
        if st.button("🗑️ RESET", use_container_width=True):
            st.session_state.reset_counter += 1
            st.session_state.meds_input = ""
            st.rerun()

# E) AVISO FINAL
st.markdown('<div class="static-warning">⚠️ Apoyo a la revisión farmacoterapéutica. Verifique con fuentes oficiales.</div>', unsafe_allow_html=True)
