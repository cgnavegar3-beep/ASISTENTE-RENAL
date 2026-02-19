# v. 19 feb 18:15
import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import google.generativeai as genai
import io
from streamlit_paste_button import paste_image_button

# =================================================================
# 🛡️ SECCIÓN DE BLINDAJE (PROHIBIDO MODIFICAR SIN PERMISO)
# =================================================================

# --- 0. CONFIGURACIÓN DE IA (SECRETS) ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    API_KEY = None

def obtener_modelos_vivos():
    try:
        if not API_KEY: return []
        return [m.name.replace('models/', '').replace('gemini-', '') 
                for m in genai.list_models() 
                if 'generateContent' in m.supported_generation_methods]
    except:
        return ["2.5-flash", "1.5-pro"]

def llamar_ia_en_cascada(prompt, imagen=None):
    disponibles = obtener_modelos_vivos()
    preferencia = ['2.5-flash', '1.5-pro', '1.5-flash']
    modelos_a_intentar = [m for m in preferencia if m in disponibles]
    for m in disponibles:
        if m not in modelos_a_intentar: modelos_a_intentar.append(m)
    
    for mod_name in modelos_a_intentar:
        try:
            st.session_state.active_model = mod_name.upper()
            model = genai.GenerativeModel(f'models/gemini-{mod_name}')
            contenido = [prompt, imagen] if imagen else [prompt]
            response = model.generate_content(contenido)
            return response.text
        except:
            continue
    return "⚠️ Error: Sin respuesta de modelos."

# --- 1. CONFIGURACIÓN Y ESTILOS (BLINDADO - CORRECCIÓN DE SINTAXIS) ---
st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

def inject_ui_styles():
    # Inyectado como string único para evitar SyntaxError con comillas triples
    style = "<style>"
    style += ".block-container { max-width: 100% !important; padding-top: 2.5rem !important; padding-left: 4% !important; padding-right: 4% !important; }"
    style += ".availability-badge { background-color: #1a1a1a !important; color: #888 !important; padding: 4px 10px; border-radius: 3px; font-family: monospace !important; font-size: 0.65rem; position: fixed; top: 15px; left: 15px; z-index: 1000000; border: 1px solid #333; width: 180px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }"
    style += ".model-badge { background-color: #000000 !important; color: #00FF00 !important; padding: 4px 10px; border-radius: 3px; font-family: monospace !important; font-size: 0.75rem; position: fixed; top: 15px; left: 205px; z-index: 1000000; box-shadow: 0 0 5px #00FF0033; }"
    style += ".main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin-top: 0px; margin-bottom: 0px; }"
    style += ".version-display { text-align: center; font-size: 0.6rem; color: #bbb; font-family: monospace; margin-bottom: 15px; }"
    style += ".id-display { color: #666; font-family: monospace; font-size: 0.85rem; margin-top: -10px; margin-bottom: 20px; }"
    style += ".formula-container { display: flex; justify-content: flex-end; width: 100%; margin-top: 5px; }"
    style += ".formula-tag { font-size: 0.75rem; color: #888; font-style: italic; }"
    style += ".fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; margin-bottom: 20px; }"
    style += ".rgpd-box { background-color: #fff5f5; color: #c53030; padding: 10px; border-radius: 8px; border: 1px solid #feb2b2; font-size: 0.85rem; margin-bottom: 15px; text-align: center; }"
    style += ".warning-yellow { background-color: #fdfde0; color: #856404; padding: 15px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 40px;
