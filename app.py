# v. 19 feb 18:05
import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import google.generativeai as genai
import io
from streamlit_paste_button import paste_image_button

# =================================================================
# 🛡️ SECCIÓN DE BLINDAJE (PROHIBIDO MODIFICAR SIN PERMISO)
# I. ESTRUCTURA VISUAL:
#    1. Cuadros negros (ZONA y ACTIVO).
#    2. Título principal y pestañas (Tabs).
#    3. Registro de paciente: estructura y función.
#    4. Interfaz Dual (Calculadora y FG): lógica Cockcroft-Gault.
#    5. Zona de recortes (Uploader + Botón 0.65/0.35).
#    6. Cuadro de listado de medicamentos (TextArea).
#    7. Barra dual de botones (VALIDAR / RESET).
#    8. Aviso amarillo inferior.
# II. FUNCIONALIDADES CRÍTICAS:
#    1. Cascada de Modelos (2.5 Flash > 1.5 Pro > Otros).
#    2. Detección dinámica de modelos vivos en la cuenta.
#    3. Actualización de feedback neón en tiempo real (Badge ACTIVO).
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

# --- 1. CONFIGURACIÓN Y ESTILOS (BLINDADO) ---
st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

def inject_ui_styles():
    style = """
    <style>
    .block-container { max-width: 100% !important; padding-top: 2.5rem !important; padding-left: 4% !important; padding-right: 4% !important; }
    .availability-badge { 
        background-color: #1a1a1a !important; color: #888 !important; padding: 4px 10px; 
        border-radius: 3px; font-family: monospace !important; font-size: 0.65rem; 
        position: fixed; top: 15px; left: 15px; z-index: 1000000; border: 1px solid #333;
        width: 180px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;
    }
    .model-badge { 
        background-color: #000000 !important; color: #00FF00 !important; padding: 4px 10px; 
        border-radius: 3px; font-family: monospace !important; font-size: 0.75rem; 
        position: fixed; top: 15px; left: 205px; z-index: 1000000; box-shadow: 0 0 5px #00FF0033;
    }
    .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin-top: 0px; margin-bottom: 0px; }
    .version-display { text-align: center; font-size: 0.6rem; color: #bbb; font-family: monospace; margin-bottom: 15px; }
    .id-display { color: #666; font-family: monospace; font-size: 0.85rem; margin-top: -10px; margin-bottom: 20px; }
    .formula-container { display: flex; justify-content: flex-end; width: 100%; margin-top: 5px; }
    .formula-tag { font-size: 0.75rem; color: #888; font-style: italic; }
    .fg-glow-box { background-color: #0000
