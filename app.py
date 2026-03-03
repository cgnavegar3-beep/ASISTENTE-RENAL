# v. 03 mar 2026 10:55 (Evolución: Formato de Línea por Fármaco en Bloques 1 y 3)

import streamlit as st
import pandas as pd
import io
from datetime import datetime
import google.generativeai as genai
import random
import re
import os
import constants as c # IMPORTACIÓN ESENCIAL: NO ELIMINAR constants.py

# =================================================================
# PRINCIPIOS FUNDAMENTALES:
# 1. RIGOR TÉCNICO: La seguridad y precisión de los datos es la máxima prioridad.
# 2. SEPARACIÓN DE BLOQUES: Los datos de la IA deben parsearse estrictamente usando |||.
# 3. SEGURIDAD TÉCNICA: Se deben proteger los elementos clave contra cambios accidentales.
# 4. NOTA IMPORTANTE: Se deben mostrar los 4 puntos de seguridad clínica obligatorios.
# =================================================================

st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

# --- INICIALIZACIÓN DE VARIABLES DE SESIÓN ---
if "active_model" not in st.session_state: st.session_state.active_model = "BUSCANDO..."
if "main_meds" not in st.session_state: st.session_state.main_meds = ""
# Inicialización de campos SOIP/IC
for key in ["soip_s", "soip_o", "soip_i", "soip_p", "ic_motivo", "ic_info", "reg_id", "reg_centro", "calc_e", "calc_p", "calc_c", "calc_s", "reg_res"]:
    if key not in st.session_state: st.session_state[key] = None

# --- CONFIGURACIÓN DE IA ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    API_KEY = None
    st.sidebar.error("API Key no encontrada. Revisa los secretos de Streamlit.")

# --- FUNCIONES DE SOPORTE ---
def llamar_ia_en_cascada(prompt):
    if not API_KEY: return "⚠️ Error: API Key no configurada."
    
    disponibles = [m.name.replace('models/', '').replace('gemini-', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    orden = ['2.5-flash', 'flash-latest', '1.5-pro']
    
    for mod_name in orden:
        if mod_name in disponibles:
            try:
                st.session_state.active_model = mod_name.upper()
                model = genai.GenerativeModel(f'models/gemini-{mod_name}')
                return model.generate_content(prompt, generation_config={"temperature": 0.1}).text
            except: continue
    return "⚠️ Error en la generación."

def obtener_glow_class(sintesis_texto):
    """Determina el color del cuadro según la intensidad de la alerta."""
    if "⛔" in sintesis_texto:
        return "glow-red"
    elif "⚠️⚠️⚠️" in sintesis_texto:
        return "glow-orange"
    elif "⚠️⚠️" in sintesis_texto:
        return "glow-yellow-dark"
    elif "⚠️" in sintesis_texto:
        return "glow-yellow"
    else:
        return "glow-green"

def procesar_y_limpiar_meds():
    texto = st.session_state.main_meds
    if texto:
        texto_limpio = re.sub(r"\s*-\s*|;\s*", "\n", texto)
        texto_limpio = re.sub(r"\n+", "\n", texto_limpio).strip()
        prompt = f"""
        Actúa como farmacéutico clínico. Reescribe el siguiente listado de medicamentos siguiendo estas reglas estrictas:
        1. Estructura cada línea como: [Principio Activo] + [Dosis] + (Marca Comercial).
        2. Si no identificas la marca, omite el paréntesis.
        3. Coloca cada medicamento en una línea independiente.
        4. No agregues numeración ni explicaciones.
        Texto a procesar:
        {texto_limpio}
        """
        st.session_state.main_meds = llamar_ia_en_cascada(prompt)

def reset_registro():
    for key in ["reg_centro", "reg_res", "reg_id", "fgl_ckd", "fgl_mdrd", "main_meds"]:
        st.session_state[key] = ""
    for key in ["calc_e", "calc_p", "calc_c", "calc_s", "calc_e_input", "calc_p_input", "calc_c_input", "calc_s_input"]:
        st.session_state[key] = None

def reset_meds():
    st.session_state.main_meds = ""
    st.session_state.soip_s = "Revisión farmacoterapéutica según función renal."
    st.session_state.soip_o = ""
    st.session_state.soip_i = ""
    st.session_state.soip_p = "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
    st.session_state.ic_motivo = "Se solicita valoración médica tras la revisión de la adecuación del tratamiento a la función renal del paciente."
    st.session_state.ic_info = ""

def verificar_datos_completos():
    campos = {"Centro": "reg_centro", "Edad": "calc_e", "Peso": "calc_p", "Creatinina": "calc_c", "Sexo": "calc_s"}
    return [nombre for nombre, key in campos.items() if st.session_state.get(key) in [None, ""]]

# --- UI STYLE ---
def inject_styles():
    st.markdown("""
    <style>
    .blink-text { animation: blinker 1s linear infinite; }
    @keyframes blinker { 50% { opacity: 0; } }
    .block-container { max-width: 100% !important; padding-top: 1rem !important; padding-left: 4% !important; padding-right: 4% !important; }
    .black-badge-zona { background-color: #000000; color: #888; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 15px; z-index: 999999; }
    .black-badge-activo { background-color: #000000; color: #00FF00; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size:
