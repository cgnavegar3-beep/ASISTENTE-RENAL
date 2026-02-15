import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURACIÓN Y ESTILOS (CONTROL DE SIMETRÍA Y AIRE) ---
st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

def inject_ui_styles():
    style = """
    <style>
    .block-container { max-width: 900px !important; padding-top: 2rem !important; }

    /* 1. INDICADOR DISCRETO (SIN BORDE) */
    .model-badge {
        background-color: #000000 !important;
        color: #00FF00 !important;
        padding: 4px 10px;
        border-radius: 3px;
        font-family: monospace !important;
        font-size: 0.75rem;
        position: fixed;
        top: 15px;
        left: 15px;
        z-index: 1000000;
    }
    
    .main-title { text-align: center; font-size: 2.2rem; font-weight: 800; color: #1E1E1E; margin-top: -40px; }

    /* 2. CUADRO FG GLOW MORADO (SIMETRÍA VERTICAL) */
    .fg-glow-box { 
        background-color: #000000; 
        color: #FFFFFF; 
        border: 2px solid #9d00ff; 
        box-shadow: 0 0 12px #9d00ff; 
        padding: 10px; 
        border-radius: 10px; 
        text-align: center; 
        height: 120px; /* Ajuste para simetría */
        display: flex; 
        flex-direction: column; 
        justify-content: center;
        margin-bottom: 25px; /* Aire para separar de los botones */
    }

    /* ESTILO PARA IGUALAR BOTONES DE CAPTURA */
    [data-testid="stFileUploader"] { padding-bottom: 0px; }
    [data-testid="stFileUploader"] section { padding: 0px !important; min-height: 45px !important; }
    
    /* BOTÓN RECORTE A LA MISMA ALTURA QUE EL UPLOADER */
    .stButton > button { height: 45px !important; margin-top: 0px !important; }

    .static-warning { 
        background-color: #fffdf2; 
        color: #856404; 
        text-align: center; 
        padding: 10px; 
        border-radius: 8px; 
        border: 1px solid #fcf8e3; 
        margin-top: 30px; 
        font-size: 0.8rem; 
    }
    </style>
    """
    st.markdown(style, unsafe_allow_html=True)

# --- 2. LÓGICA DE MODELO Y ESTADO ---
raw_model_name = "gemini-2.5-flash" 
clean_model = raw_model_name.replace("gemini-", "").replace("-", " ").title()

if 'reset_counter' not in st.session_state: st.session_state.reset_counter = 0
if 'meds_input' not in st.session_state: st.session_state.meds_input = ""

inject_ui_styles()

st.markdown(f'<div class="model-badge">{clean_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 EXCEL", "📈 GRÁFICOS"])

with tabs[0]:
    # A) REGISTRO DE PACIENTE
    c_reg_header, c_reg_btn = st.columns([0.85, 0.15])
    with c_reg_header: st.markdown("### Registro de Paciente")
    with c_reg_btn: 
        if st.button("🗑️ Limpiar", key="reset_reg"):
            st.session_state.reset_counter += 1
            st.rerun()

    c_reg1, c_reg2, c_reg3 = st.columns([1, 2, 1])
    with c_reg1:
        centro = st.text_input("Centro", placeholder="G/M", key=f"c_{st.session_state.reset_counter}")
    with c_reg2:
        rc1, rc2, rc3 = st.columns(3)
        with rc1: edad_reg = st.number_input("Edad", value=None, placeholder="0", key=f"e_{st.session_state.reset_counter}")
        with rc2: alfanum = st.text_input("ID Alfanumérico", placeholder="ID...", key=f"id_{st.session_state.reset_counter}")
        with rc3: residencia = st.selectbox("¿Residencia?", ["No", "Sí"], key=f"res_{st.session_state.reset_counter}")
    with c_reg3:
        st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)

    st.write("") 

    # B) INTERFAZ DUAL SIMÉTRICA (CALCULADORA VS FG + CAPTURA)
    col_izq, col_der = st.columns(2, gap="large")

    with col_izq:
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            # 4 campos que definen la altura total
            c_edad = st.number_input("Edad (años)", value=edad_reg if edad_reg else 65, key=f"ce_{st.session_state.reset_counter}")
            c_peso = st.number_input("Peso (kg)", value=70.0, step=0.1, key=f"cp_{st.session_state.reset_counter}")
            c_creat = st.number_input("Creatinina (mg/dL)", value=1.0, step=0.1, key=f"cc_{st.session_state.reset_counter}")
            c_sexo = st.selectbox("Sexo", ["Hombre", "Mujer"], key=f"cs_{st.session_state.reset_counter}")
            
            fg_calc = ((140 - c_edad) * c_peso) / (72 * c_creat)
            if c_sexo == "Mujer": fg_calc *= 0.85
            fg_calc = round(fg_calc, 1)

    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        # Ajuste manual arriba para que respire
        fg_manual = st.text_input("Valor Manual", placeholder="Opcional...", key=f"fgm_{st.session_state.reset_counter}")
        
        # Cuadro Glow Morado
        st.markdown(f"""
            <div class="fg-glow-box">
                <div style="font-size: 2.6rem; font-weight: bold; line-height: 1;">{fg_manual if fg_manual else fg_calc}</div>
                <div style="font-size: 0.8rem; color: #9d00ff; font-weight: bold;">mL/min</div>
            </div>
        """, unsafe_allow_html=True)
        
        # FILA DE CAPTURA ALINEADA AL FINAL
        c_up, c_btn = st.columns(2)
        with c_up:
            st.file_uploader("Subir 📁", label_visibility="collapsed", key=f"up_{st.session_state.reset_counter}")
        with c_btn:
            st.button("Recorte 📋", use_container_width=True)

    st.write("")
    st.markdown("---")

    # C) MEDICAMENTOS
    st.markdown("#### 📝 Listado de medicamentos")
    st.session_state.meds_input = st.text_area(
        "Listado", value=st.session_state.meds_input, height=120, 
        label_visibility="collapsed", key=f"area_{st.session_state.reset_counter}"
    )

    # D) BOTONERA PRINCIPAL
    b_val, b_res = st.columns([0.8, 0.2])
    with b_val:
        st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True)
    with b_res:
        if st.button("🗑️ RESET TODO", use_container_width=True):
            st.session_state.reset_counter += 1
            st.session_state.meds_input = ""
            st.rerun()

st.markdown('<div class="static-warning">⚠️ Apoyo a la revisión farmacoterapéutica. Verifique con fuentes oficiales.</div>', unsafe_allow_html=True)
