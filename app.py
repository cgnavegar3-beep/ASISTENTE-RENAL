import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import io
import os
import google.generativeai as genai
import fitz  # PyMuPDF

# --- 1. CONFIGURACIÓN Y ESTILOS (CONCATENACIÓN SEGURA) ---
st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

def inject_ui_styles():
    style = "<style>"
    style += ".model-indicator { background-color: #000000; color: #00FF00; padding: 4px 10px; border-radius: 4px; font-family: monospace; font-size: 0.85rem; position: fixed; top: 12px; left: 12px; z-index: 1001; border: 1px solid #00FF00; }"
    style += ".main-title { text-align: center; font-size: 2.6rem; font-weight: 800; color: #1E1E1E; margin-top: -45px; padding-bottom: 20px; width: 100%; }"
    style += "div[data-baseweb='tab-list'] button[aria-selected='true'] { border-bottom: 4px solid red !important; font-weight: bold !important; color: black !important; }"
    style += ".fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2px solid #9d00ff; box-shadow: 0 0 20px #9d00ff; padding: 30px; border-radius: 15px; text-align: center; margin: 5px 0; }"
    style += ".floating-warning { position: fixed; bottom: 0; left: 0; width: 100%; background-color: #fff3cd; color: #856404; text-align: center; padding: 14px; z-index: 9999; border-top: 1px solid #ffeeba; font-weight: 500; }"
    style += ".separator-groove { border-top: 1px dotted #bbb; border-bottom: 1px solid #fff; margin: 25px 0; height: 2px; }"
    style += "@keyframes flash-green { 0% { box-shadow: 0 0 0px #28a745; } 50% { box-shadow: 0 0 30px #28a745; } 100% { box-shadow: 0 0 0px #28a745; } }"
    style += ".flash-verde { background-color: #d4edda; animation: flash-green 2s infinite; padding: 20px; border-radius: 10px; }"
    style += "</style>"
    st.markdown(style, unsafe_allow_html=True)

# --- 2. LÓGICA DE PERSISTENCIA ---
if 'reset_counter' not in st.session_state: st.session_state.reset_counter = 0
if 'meds_input' not in st.session_state: st.session_state.meds_input = ""
if 'active_model' not in st.session_state: st.session_state.active_model = "2.5 Flash"

@st.cache_resource
def get_vademecum_data():
    try:
        doc = fitz.open("vademecum_renal.pdf")
        return "".join([page.get_text() for page in doc])
    except: return "PDF no encontrado."

inject_ui_styles()
vademecum_text = get_vademecum_data()

# Elementos Permanentes
st.markdown(f'<div class="model-indicator">{st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 EXCEL", "📈 GRÁFICOS"])

with tabs[0]:
    # A) BLOQUE DE REGISTRO (CAMPOS SILENCIOSOS CON PLACEHOLDER)
    st.markdown("### Registro de Paciente")
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

    # ID Registro Dinámico
    id_paciente = f"{centro if centro else 'G/M'}-{edad_reg if edad_reg else '00'}-{alfanum if alfanum else 'GEN'}"
    st.markdown(f"<small style='color:gray'>ID Registro: {id_paciente}</small>", unsafe_allow_html=True)

    st.write("") 

    
            with c1:
                c_edad = st.number_input("Edad (años)", value=edad_reg if edad_reg else 65, key=f"ce_{st.session_state.reset_counter}")
                c_peso = st.number_input("Peso (kg)", value=70.0, step=0.1, key=f"cp_{st.session_state.reset_counter}")
            with c2:
                c_creat = st.number_input("Creatinina (mg/dL)", value=1.0, step=0.1, key=f"cc_{st.session_state.reset_counter}")
                c_sexo = st.selectbox("Sexo", ["Hombre", "Mujer"], key=f"cs_{st.session_state.reset_counter}")
            
            # Cálculo Cockcroft-Gault
            fg_calc = ((140 - c_edad) * c_peso) / (72 * c_creat)
            if c_sexo == "Mujer": fg_calc *= 0.85
            fg_calc = round(fg_calc, 1)

    with col_der:
        st.markdown("#### 💊 Ajuste y Captura")
        fg_manual = st.text_input("Input Manual del FG (Prioritario)", placeholder="Introduzca FG...", key=f"fgm_{st.session_state.reset_counter}")
        
        st.write("") # Espaciador de limpieza
        
        valor_fg = fg_manual if fg_manual else fg_calc
        metodo_usado = "Manual" if fg_manual else "Cockcroft-Gault"

        # DISPLAY FG GLOW MORADO
        st.markdown(f"""
            <div class="fg-glow-box">
                <div style="font-size: 0.9rem; color: #bbbbbb; margin-bottom: 5px;">FILTRADO GLOMERULAR FINAL</div>
                <div style="font-size: 2.8rem; font-weight: bold;">{valor_fg} mL/min</div>
                <div style="font-size: 0.85rem; color: #9d00ff; margin-top: 6px; font-weight: bold;">Método: {metodo_usado}</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("") # Espaciador simetría
        
        c_up, c_btn = st.columns([4, 1])
        with c_up:
            up_file = st.file_uploader("Subida (📁)", label_visibility="collapsed", key=f"up_{st.session_state.reset_counter}")
        with c_btn:
            st.button("📋", help="Pegar (Ctrl+V)")

    st.markdown('<div class="separator-groove"></div>', unsafe_allow_html=True)

    # C) LISTADO DE MEDICAMENTOS
    st.markdown("#### 📝 Listado de medicamentos")
    st.session_state.meds_input = st.text_area(
        "Listado",
        value=st.session_state.meds_input,
        placeholder="Escribe o edita la lista del archivo o captura subidos",
        height=180,
        label_visibility="collapsed",
        key=f"area_{st.session_state.reset_counter}"
    )

    # D) BOTONERA DUAL 85/15
    st.write("")
    b_val, b_res = st.columns([0.85, 0.15])
    with b_val:
        if st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True, type="primary"):
            st.markdown('<div class="flash-verde">Analizando datos...</div>', unsafe_allow_html=True)
    with b_res:
        if st.button("🗑️ RESET", use_container_width=True):
            st.session_state.reset_counter += 1
            st.session_state.meds_input = ""
            st.rerun()

# AVISO DE SEGURIDAD FLOTANTE
st.markdown('<div class="floating-warning">⚠️ Aviso: Esta herramienta es un apoyo a la revisión farmacoterapéutica. Puede contener errores. Verifique con fuentes oficiales.</div>', unsafe_allow_html=True)
