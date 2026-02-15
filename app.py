import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import io
import os
import google.generativeai as genai
import fitz  # PyMuPDF

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

def inject_ui_styles():
    style = "<style>"
    style += ".model-indicator { background-color: #000000; color: #00FF00; padding: 4px 10px; border-radius: 4px; font-family: monospace; font-size: 0.85rem; position: fixed; top: 12px; left: 12px; z-index: 1001; border: 1px solid #00FF00; }"
    style += ".main-title { text-align: center; font-size: 2.6rem; font-weight: 800; color: #1E1E1E; margin-top: -45px; padding-bottom: 20px; width: 100%; }"
    style += "div[data-baseweb='tab-list'] button[aria-selected='true'] { border-bottom: 4px solid red !important; font-weight: bold !important; color: black !important; }"
    # Caja de Registro Superior Fondo Negro
    style += ".registro-negro { background-color: #1E1E1E; color: #FFFFFF; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #333; }"
    # Caja FG Glow Morado
    style += ".fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2px solid #9d00ff; box-shadow: 0 0 20px #9d00ff; padding: 20px; border-radius: 15px; text-align: center; height: 320px; display: flex; flex-direction: column; justify-content: center; }"
    style += ".separator-groove { border-top: 1px dotted #bbb; border-bottom: 1px solid #fff; margin: 25px 0; height: 2px; }"
    style += ".static-warning { background-color: #fffdf2; color: #856404; text-align: center; padding: 20px; border-radius: 10px; border: 1px solid #fcf8e3; margin-top: 50px; font-size: 0.95rem; width: 100%; }"
    # Ajuste de inputs para que ocupen todo el ancho
    style += "div[data-testid='stNumberInput'] { width: 100% !important; }"
    style += "</style>"
    st.markdown(style, unsafe_allow_html=True)

if 'reset_counter' not in st.session_state: st.session_state.reset_counter = 0
if 'meds_input' not in st.session_state: st.session_state.meds_input = ""
if 'active_model' not in st.session_state: st.session_state.active_model = "2.5 Flash"

inject_ui_styles()

st.markdown(f'<div class="model-indicator">{st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 EXCEL", "📈 GRÁFICOS"])

with tabs[0]:
    # A) BLOQUE DE REGISTRO CON FONDO NEGRO
    with st.container():
        st.markdown('<div class="registro-negro">', unsafe_allow_html=True)
        c_reg1, c_reg2, c_reg3 = st.columns([1.5, 2.5, 1.2])
        with c_reg1:
            centro = st.text_input("Centro", placeholder="G/M", key=f"c_{st.session_state.reset_counter}")
        with c_reg2:
            rc1, rc2, rc3 = st.columns(3)
            with rc1: edad_reg = st.number_input("Edad", value=None, placeholder="0", key=f"e_{st.session_state.reset_counter}")
            with rc2: alfanum = st.text_input("ID Alfanumérico", placeholder="Escriba aquí...", key=f"id_{st.session_state.reset_counter}")
            with rc3: residencia = st.selectbox("¿Residencia?", ["No", "Sí"], key=f"res_{st.session_state.reset_counter}")
        with c_reg3:
            st.text_input("Fecha Actual", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # B) INTERFAZ DUAL SIMÉTRICA
    col_izq, col_der = st.columns(2)

    with col_izq:
        st.markdown("#### 📋 Calculadora (Cockcroft-Gault)")
        with st.container(border=True):
            # Elementos uno debajo de otro para ocupar altura
            c_edad = st.number_input("Edad (años)", value=edad_reg if edad_reg else 65, key=f"ce_{st.session_state.reset_counter}")
            c_peso = st.number_input("Peso (kg)", value=70.0, step=0.1, key=f"cp_{st.session_state.reset_counter}")
            c_creat = st.number_input("Creatinina (mg/dL)", value=1.0, step=0.1, key=f"cc_{st.session_state.reset_counter}")
            c_sexo = st.selectbox("Sexo", ["Hombre", "Mujer"], key=f"cs_{st.session_state.reset_counter}")
            
            fg_calc = ((140 - c_edad) * c_peso) / (72 * c_creat)
            if c_sexo == "Mujer": fg_calc *= 0.85
            fg_calc = round(fg_calc, 1)

    with col_der:
        st.markdown("#### 💊 Ajuste y Captura")
        fg_manual = st.text_input("Input Manual del FG (Prioritario)", placeholder="Escriba el FG...", key=f"fgm_{st.session_state.reset_counter}")
        
        valor_fg = fg_manual if fg_manual else fg_calc
        metodo_usado = "Manual" if fg_manual else "Calculado"

        st.markdown(f"""
            <div class="fg-glow-box">
                <div style="font-size: 3rem; font-weight: bold;">{valor_fg}</div>
                <div style="font-size: 1.2rem; color: #9d00ff; font-weight: bold;">mL/min</div>
                <div style="font-size: 0.9rem; color: #888; margin-top: 10px;">Método: {metodo_usado}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Botones de captura debajo del cuadro morado
        c_up, c_btn = st.columns([4, 1])
        with c_up:
            st.file_uploader("Subir", label_visibility="collapsed", key=f"up_{st.session_state.reset_counter}")
        with c_btn:
            st.button("📋")

    st.markdown('<div class="separator-groove"></div>', unsafe_allow_html=True)

    # C) MEDICAMENTOS
    st.markdown("#### 📝 Listado de medicamentos")
    st.session_state.meds_input = st.text_area(
        "Listado", value=st.session_state.meds_input, placeholder="Escriba la medicación...", 
        height=150, label_visibility="collapsed", key=f"area_{st.session_state.reset_counter}"
    )

    # D) BOTONERA
    st.write("")
    b_val, b_res = st.columns([0.85, 0.15])
    with b_val:
        if st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True):
            st.info("Validando...")
    with b_res:
        if st.button("🗑️ RESET", use_container_width=True):
            st.session_state.reset_counter += 1
            st.session_state.meds_input = ""
            st.rerun()

# E) AVISO FINAL ESTÁTICO
st.markdown('<div class="static-warning">⚠️ Aviso: Apoyo a la revisión farmacoterapéutica. Verifique con fuentes oficiales.</div>', unsafe_allow_html=True)
