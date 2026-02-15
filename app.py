import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import io
import os
import google.generativeai as genai
import fitz  # PyMuPDF

# --- 1. CONFIGURACIÓN Y ESTILOS (LIMPIEZA VISUAL TOTAL) ---
st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

def inject_ui_styles():
    style = "<style>"
    # Indicador de Modelo (Superior Izquierda)
    style += ".model-indicator { background-color: #000000; color: #00FF00; padding: 4px 10px; border-radius: 4px; font-family: monospace; font-size: 0.85rem; position: fixed; top: 12px; left: 12px; z-index: 1001; border: 1px solid #00FF00; }"
    # Título Principal Centrado
    style += ".main-title { text-align: center; font-size: 2.6rem; font-weight: 800; color: #1E1E1E; margin-top: -45px; padding-bottom: 20px; width: 100%; }"
    # Pestaña Activa con línea roja gruesa
    style += "div[data-baseweb='tab-list'] button[aria-selected='true'] { border-bottom: 4px solid red !important; font-weight: bold !important; color: black !important; }"
    # Display FG Glow Morado (Caja Negra)
    style += ".fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2px solid #9d00ff; box-shadow: 0 0 20px #9d00ff; padding: 25px; border-radius: 15px; text-align: center; margin-top: 10px; min-height: 140px; display: flex; flex-direction: column; justify-content: center; }"
    # Separador sutil entre bloques
    style += ".separator-groove { border-top: 1px dotted #bbb; border-bottom: 1px solid #fff; margin: 25px 0; height: 2px; }"
    # Aviso de Seguridad Estático (Amarillo muy pálido, al final)
    style += ".static-warning { background-color: #fffdf2; color: #856404; text-align: center; padding: 20px; border-radius: 10px; border: 1px solid #fcf8e3; margin-top: 50px; font-size: 0.95rem; width: 100%; }"
    style += "</style>"
    st.markdown(style, unsafe_allow_html=True)

# --- 2. GESTIÓN DE ESTADO (MEMORIA RAM) ---
if 'reset_counter' not in st.session_state: st.session_state.reset_counter = 0
if 'meds_input' not in st.session_state: st.session_state.meds_input = ""
if 'active_model' not in st.session_state: st.session_state.active_model = "2.5 Flash"

inject_ui_styles()

# --- 3. ELEMENTOS PERMANENTES ---
st.markdown(f'<div class="model-indicator">{st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 EXCEL", "📈 GRÁFICOS"])

with tabs[0]:
    # A) BLOQUE DE REGISTRO (CAMPOS SILENCIOSOS)
    st.markdown("### Registro de Paciente")
    c_reg1, c_reg2, c_reg3 = st.columns([1.5, 2.5, 1.2])
    
    with c_reg1:
        centro = st.text_input("Centro", placeholder="G/M", key=f"centro_{st.session_state.reset_counter}")
    with c_reg2:
        rc1, rc2, rc3 = st.columns(3)
        with rc1: edad_reg = st.number_input("Edad", value=None, placeholder="0", key=f"edad_r_{st.session_state.reset_counter}")
        with rc2: alfanum = st.text_input("ID Alfanumérico", placeholder="Escriba aquí...", key=f"id_r_{st.session_state.reset_counter}")
        with rc3: residencia = st.selectbox("¿Residencia?", ["No", "Sí"], key=f"res_r_{st.session_state.reset_counter}")
    with c_reg3:
        st.text_input("Fecha Actual", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)

    id_paciente = f"{centro if centro else 'G/M'}-{edad_reg if edad_reg else '00'}-{alfanum if alfanum else 'GEN'}"
    st.markdown(f"<small style='color:gray'>ID Registro: {id_paciente}</small>", unsafe_allow_html=True)
    st.write("") 

    # B) INTERFAZ DUAL (CALCULADORA VS AJUSTE)
    col_izq, col_der = st.columns(2)

    with col_izq:
        st.markdown("#### 📋 Calculadora")
        st.caption("Método: Cockcroft-Gault")
        with st.container(border=True):
            # LINEALIDAD TOTAL: 4 COLUMNAS EN UNA FILA
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                c_edad = st.number_input("Edad", value=edad_reg if edad_reg else 65, key=f"calc_e_{st.session_state.reset_counter}")
            with col2:
                c_peso = st.number_input("Peso (kg)", value=70.0, step=0.1, key=f"calc_p_{st.session_state.reset_counter}")
            with col3:
                c_creat = st.number_input("Creat (mg/dL)", value=1.0, step=0.1, key=f"calc_c_{st.session_state.reset_counter}")
            with col4:
                c_sexo = st.selectbox("Sexo", ["Hombre", "Mujer"], key=f"calc_s_{st.session_state.reset_counter}")
            
            # Lógica de cálculo
            fg_calc = ((140 - c_edad) * c_peso) / (72 * c_creat)
            if c_sexo == "Mujer": fg_calc *= 0.85
            fg_calc = round(fg_calc, 1)
            
            # Espaciado para igualar altura visualmente con la derecha
            st.markdown("<br><br>", unsafe_allow_html=True)

    with col_der:
        st.markdown("#### 💊 Ajuste y Captura")
        fg_manual = st.text_input("Input Manual del FG", placeholder="FG si lo conoce...", key=f"fg_m_{st.session_state.reset_counter}")
        
        valor_fg = fg_manual if fg_manual else fg_calc
        metodo_usado = "Manual" if fg_manual else "Cockcroft-Gault"

        # DISPLAY FG GLOW MORADO
        st.markdown(f"""
            <div class="fg-glow-box">
                <div style="font-size: 2.5rem; font-weight: bold;">{valor_fg} mL/min</div>
                <div style="font-size: 0.85rem; color: #9d00ff; margin-top: 5px; font-weight: bold;">{metodo_usado}</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("") 
        c_up, c_btn = st.columns([4, 1])
        with c_up:
            st.file_uploader("Subida (📁)", label_visibility="collapsed", key=f"up_f_{st.session_state.reset_counter}")
        with c_btn:
            st.button("📋", key=f"clip_{st.session_state.reset_counter}")

    st.markdown('<div class="separator-groove"></div>', unsafe_allow_html=True)

    # C) MEDICAMENTOS
    st.markdown("#### 📝 Listado de medicamentos")
    st.session_state.meds_input = st.text_area(
        "Listado", 
        value=st.session_state.meds_input, 
        placeholder="Escriba o edita la lista aquí...", 
        height=180, 
        label_visibility="collapsed", 
        key=f"area_m_{st.session_state.reset_counter}"
    )

    # D) BOTONERA (DISCRECIÓN MÁXIMA)
    st.write("")
    b_val, b_res = st.columns([0.85, 0.15])
    with b_val:
        # Botón gris discreto (sin type="primary")
        if st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True):
            st.info("Iniciando validación farmacoterapéutica...")
    with b_res:
        if st.button("🗑️ RESET", use_container_width=True):
            st.session_state.reset_counter += 1
            st.session_state.meds_input = ""
            st.rerun()

# E) AVISO DE SEGURIDAD ESTÁTICO FINAL
st.markdown("""
    <div class="static-warning">
        ⚠️ Aviso: Esta herramienta es un apoyo a la revisión farmacoterapéutica. Puede contener errores. Verifique con fuentes oficiales.
    </div>
""", unsafe_allow_html=True)
