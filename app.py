import streamlit as st
import pandas as pd
from datetime import datetime

# ESTRUCTURA ASISTENTE RENAL - VERSIÓN 3.1.2 (FORZAR RECARGA)
st.set_page_config(page_title="Asistente Renal", layout="wide")

# CSS INYECTADO PARA CUMPLIR EL PROMPT
st.markdown("""
<style>
    /* LÍNEA ROJA Y NEGRITA EN PESTAÑA ACTIVA */
    div[data-baseweb="tab-list"] button[aria-selected="true"] {
        border-bottom: 3px solid red !important;
        font-weight: bold !important;
        color: black !important;
    }
    /* INDICADOR DE MODELO NEGRO/VERDE */
    .model-indicator {
        background-color: #000000;
        color: #00FF00;
        padding: 4px 10px;
        border-radius: 4px;
        font-family: monospace;
        display: inline-block;
        margin-bottom: 10px;
    }
    /* CUADRO FG NEGRO/MORADO NEÓN */
    .fg-glow-box {
        background-color: #000000;
        color: #FFFFFF;
        border: 2px solid #9d00ff;
        box-shadow: 0 0 15px #9d00ff;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
    }
    .separator-groove {
        border-top: 1px solid #bbb;
        border-bottom: 1px solid #fff;
        margin: 25px 0;
    }
</style>
""", unsafe_allow_html=True)

# 1. INDICADOR DISCRETO
st.markdown('<div class="model-indicator">2.5 Flash</div>', unsafe_allow_html=True)

# 2. BARRA DE PESTAÑAS (SEGÚN PROMPT)
tab1, tab2, tab3, tab4 = st.tabs([
    "💊 VALIDACIÓN", 
    "📄 INFORME", 
    "📊 EXCEL-datos", 
    "📈 GRÁFICOS"
])

with tab1:
    st.markdown("### Registro de Paciente")
    c1, c2, c3 = st.columns([1.5, 2.5, 1])
    with c1: st.text_input("Centro", placeholder="G/M")
    with c2:
        cc1, cc2, cc3 = st.columns(3)
        with cc1: st.number_input("Edad", value=None, placeholder="Edad")
        with cc2: st.text_input("ID", placeholder="Alfanumérico")
        with cc3: st.selectbox("Residencia", ["No", "Sí"])
    with c3: st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)
    
    st.markdown("---")
    
    col_izq, col_der = st.columns(2)
    with col_izq:
        st.subheader("📋 Calculadora")
        with st.container(border=True):
            st.number_input("Creatinina", value=1.0)
            st.number_input("Peso", value=70.0)
    with col_der:
        st.subheader("💊 Ajuste y Captura")
        st.markdown('<div class="fg-glow-box"><h2>45.5 mL/min</h2><small>Fórmula CKD-EPI</small></div>', unsafe_allow_html=True)

    st.markdown('<div class="separator-groove"></div>', unsafe_allow_html=True)
    st.text_area("Listado de medicamentos", placeholder="Escribe o edita la lista...", height=150)
    
    b1, b2 = st.columns([0.85, 0.15])
    with b1: st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True, type="primary")
    with b2: st.button("🗑️ RESET", use_container_width=True)

with tab2: st.write("Sección de Informe")
with tab3: st.write("Sección Excel")
with tab4: st.write("Sección Gráficos")
