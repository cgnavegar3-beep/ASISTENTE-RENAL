# v. 01 mar 2026 19:15

import streamlit as st
import pandas as pd
import io
from datetime import datetime
import google.generativeai as genai
import random
import re
import os

# =================================================================
# PRINCIPIOS FUNDAMENTALES:
# 1. RIGOR TÉCNICO: La seguridad y precisión de los datos es la máxima prioridad.
# 2. SEPARACIÓN DE BLOQUES: Los datos de la IA deben parsearse estrictamente usando |||.
# 3. SEGURIDAD TÉCNICA: Se deben proteger los elementos clave contra cambios accidentales.
# 4. NOTA IMPORTANTE: Se deben mostrar los 4 puntos de seguridad clínica obligatorios.
# =================================================================

st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

if "active_model" not in st.session_state:
    st.session_state.active_model = "BUSCANDO..."

# INICIALIZACIÓN DE VARIABLES DE SESIÓN
for key in ["soip_s", "soip_o", "soip_i", "soip_p", "ic_motivo", "ic_info", "main_meds", "reg_id", "reg_centro", "calc_e", "calc_p", "calc_c", "calc_s"]:
    if key not in st.session_state: st.session_state[key] = None

# --- FUNCIONES DE SOPORTE ---
def cargar_prompt_clinico():
    try:
        with open(os.path.join("prompts", "categorizador.txt"), "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Error: No se encontró el archivo de prompt."

def llamar_ia_en_cascada(prompt):
    disponibles = [m.name.replace('models/', '').replace('gemini-', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods] if API_KEY else ["2.5-flash"]
    orden = ['2.5-flash', 'flash-latest', '1.5-pro']
    for mod_name in orden:
        if mod_name in disponibles:
            try:
                st.session_state.active_model = mod_name.upper()
                model = genai.GenerativeModel(f'models/gemini-{mod_name}')
                # Usamos temperatura baja para mayor precisión y estructura
                return model.generate_content(prompt, generation_config={"temperature": 0.1}).text
            except: continue
    return "⚠️ Error en la generación."

# ... [MANTENER FUNCIONES DE PROCESAR MEDICAMENTOS, RESET, ETC.] ...

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    API_KEY = None

# --- UI STYLE ---
def inject_styles():
    st.markdown("""
    <style>
    .blink-text { animation: blinker 1s linear infinite; }
    @keyframes blinker { 50% { opacity: 0; } }
    .block-container { max-width: 100% !important; padding-top: 1rem !important; padding-left: 4% !important; padding-right: 4% !important; }
    .black-badge-zona { background-color: #000000; color: #888; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 15px; z-index: 999999; }
    .black-badge-activo { background-color: #000000; color: #00FF00; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 145px; z-index: 999999; text-shadow: 0 0 5px #00FF00; }
    .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin-bottom: 0px; margin-top: 20px; }
    .sub-version { text-align: center; font-size: 0.6rem; color: #bbb; margin-top: -5px; margin-bottom: 20px; font-family: monospace; }
    .fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .unit-label { font-size: 0.65rem; color: #888; margin-top: -10px; margin-bottom: 5px; font-family: sans-serif; text-align: center; }
    
    /* ESTILOS CLÍNICOS */
    .synthesis-box { padding: 15px; border-radius: 12px; margin-bottom: 15px; border-width: 2.2px; border-style: solid; font-size: 0.95rem; }
    .glow-red { background-color: #fff5f5; color: #c53030; border-color: #feb2b2; box-shadow: 0 0 12px #feb2b2; }
    .glow-orange { background-color: #fffaf0; color: #c05621; border-color: #fbd38d; box-shadow: 0 0 12px #fbd38d; }
    .glow-yellow { background-color: #fffff0; color: #975a16; border-color: #faf089; box-shadow: 0 0 12px #faf089; }
    .glow-green { background-color: #f0fff4; color: #2f855a; border-color: #9ae6b4; box-shadow: 0 0 12px #9ae6b4; }
    
    /* Contenedores nuevos */
    .table-container { background-color: white; padding: 10px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 15px; overflow-x: auto; }
    .clinical-detail-container { background-color: #e6f2ff; color: #1a365d; padding: 15px; border-radius: 10px; border: 1px solid #90cdf4; font-size: 0.9rem; }
    
    .warning-yellow { background-color: #fff9db; color: #856404; padding: 20px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 40px; text-align: center; font-size: 0.85rem; line-height: 1.5; }
    .linea-discreta-soip { border-top: 1px solid #d9d5c7; margin: 15px 0 5px 0; font-size: 0.65rem; font-weight: bold; color: #8e8a7e; text-transform: uppercase; }
    .header-capsule { background-color: #e2e8f0; color: #2d3748; padding: 10px 30px; border-radius: 50px; display: inline-block; font-weight: 800; font-size: 0.9rem; margin-bottom: 20px; }
    .formula-label { font-size: 0.6rem; color: #666; font-family: monospace; text-align: right; margin-top: 5px; }
    .fg-special-border { border: 1.5px solid #9d00ff !important; border-radius: 5px; }
    .nota-importante-box { border-top: 2px dashed #0057b8; margin-top: 15px; padding-top: 10px; font-size: 0.8rem; color: #1a365d; }
    </style>
    """, unsafe_allow_html=True)
inject_styles()

st.markdown('<div class="black-badge-zona">ZONA: ACTIVA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="black-badge-activo">ACTIVO: {st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-version">v. 01 mar 2026 19:15</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 DATOS", "📈 GRÁFICOS"])

with tabs[0]:
    # ... [MANTENER UI DE PACIENTE Y CALCULADORA] ...
    
    # ... UI de medicamentos ...
    txt_meds = st.text_area("Listado", height=150, label_visibility="collapsed", key="main_meds")
    st.button("Procesar medicamentos", on_click=procesar_y_limpiar_meds)
    
    b1, b2 = st.columns([0.85, 0.15])
    btn_val = b1.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True)
    b2.button("🗑️ RESET", on_click=reset_meds, use_container_width=True)

    if btn_val:
        # ... [CHECKEO DE DATOS COMPLETOS] ...
        
        if not txt_meds:
            st.error("Por favor, introduce al menos un medicamento.")
        else:
            placeholder_salida = st.empty()
            with st.spinner("Procesando análisis clínico con AFR-V10..."):
                
                # CARGAR EL PROMPT DEFINITIVO (AFR-V10)
                prompt_base = cargar_prompt_clinico()
                
                # CONECTAR DATOS DE LA UI AL PROMPT
                prompt_final = f"""
                {prompt_base}
                
                DATOS DEL PACIENTE:
                - FG Cockcroft-Gault: {valor_fg} mL/min
                - FG CKD-EPI: {val_ckd} mL/min/1,73m²
                - FG MDRD-4: {val_mdrd} mL/min/1,73m²
                
                MEDICAMENTOS A ANALIZAR:
                {txt_meds}
                """
                
                # LLAMAR A LA IA
                resp = llamar_ia_en_cascada(prompt_final)
                
                try:
                    # --- PARSING ROBUSTO DE 3 BLOQUES ---
                    # Eliminamos espacios en blanco extremos y saltos de línea innecesarios
                    resp_limpia = resp.strip()
                    partes = resp_limpia.split("|||")
                    
                    if len(partes) < 3:
                        raise ValueError("Estructura de bloques incorrecta o incompleta.")
                        
                    sintesis = partes[0].strip()
                    tabla_html = partes[1].strip()
                    detalle_completo = partes[2].strip()
                    
                    # --- APLICAR LÓGICA GLOW ---
                    if "⛔" in sintesis: glow = "glow-red"
                    elif "⚠️⚠️⚠️" in sintesis: glow = "glow-orange"
                    elif "⚠️" in sintesis: glow = "glow-yellow"
                    else: glow = "glow-green"
                    
                    # Contenido de la NOTA IMPORTANTE (Principios Fundamentales)
                    nota_importante = """
                    <div class="nota-importante-box">
                        <b>⚠️ NOTA IMPORTANTE:</b><br>
                        • 3.1. Verifique siempre con la ficha técnica oficial (AEMPS/EMA).<br>
                        • 3.2. Los ajustes propuestos son orientativos según filtrado glomerular actual.<br>
                        • 3.3. La decisión final corresponde siempre al prescriptor médico.<br>
                        • 3.4. Considere la situación clínica global del paciente antes de modificar dosis.
                    </div>
                    """
                    
                    # --- RENDERIZADO EN CONTENEDORES ---
                    with placeholder_salida.container():
                        # 1. Contenedor Síntesis con Glow
                        st.markdown(f'<div class="synthesis-box {glow}">{sintesis}</div>', unsafe_allow_html=True)
                        st.markdown("---")
                        
                        # 2. Contenedor Tabla Comparativa (Forzar HTML seguro)
                        st.markdown(f'<div class="table-container">{tabla_html}</div>', unsafe_allow_html=True)
                        
                        # 3. Contenedor Detalle Clínico + Nota Importante
                        st.markdown(f'<div class="clinical-detail-container">{detalle_completo}{nota_importante}</div>', unsafe_allow_html=True)
                        
                except Exception as e:
                    st.error(f"Error técnico en AFR-V10: {e}")
                    # Mostramos la respuesta para depurar si falla
                    st.code(resp)

# ... [MANTENER EL RESTO DE TABS Y ESTILOS IGUAL] ...
