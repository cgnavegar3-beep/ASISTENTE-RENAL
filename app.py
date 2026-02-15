import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import io
import numpy as np
from datetime import datetime

# --- 1. CONFIGURACIÓN E INICIALIZACIÓN ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

# Inicialización de estados de sesión (Blindaje de Persistencia)
if 'active_model_name' not in st.session_state:
    st.session_state.active_model_name = "1.5 Pro"
if 'meds_input' not in st.session_state:
    st.session_state.meds_input = ""
if 'cache_result' not in st.session_state:
    st.session_state.cache_result = None
if 'last_query' not in st.session_state:
    st.session_state.last_query = ""
if 'reset_counter' not in st.session_state:
    st.session_state.reset_counter = 0
if 'memoria_farmacos' not in st.session_state:
    st.session_state.memoria_farmacos = {}

# --- 2. GESTIÓN DE MODELOS (CASCADA CON FALLBACK) ---
def run_ia_task(prompt, image_bytes=None):
    models_to_try = [
        ("gemini-1.5-pro", "1.5 Pro"),
        ("gemini-2.0-flash", "2.0 Flash")
    ]
    for model_id, tech_name in models_to_try:
        try:
            st.session_state.active_model_name = tech_name
            genai.configure(api_key=st.secrets["API_KEY"])
            model = genai.GenerativeModel(model_id)
            content = [prompt] if prompt else []
            if image_bytes:
                content.append({'mime_type': 'image/png', 'data': image_bytes})
            response = model.generate_content(content)
            return response.text
        except Exception:
            continue
    return "Fallo de conexión o superado el número de intentos"

# --- 3. LECTURA DE PDF (CACHÉ DE RENDIMIENTO) ---
@st.cache_resource
def get_vademecum_data():
    try:
        doc = fitz.open("vademecum_renal.pdf")
        return "".join([page.get_text() for page in doc])
    except: return ""

# --- 4. ESTILOS CSS (ESTRUCTURA BLINDADA) ---
def inject_ui_styles():
    st.markdown(f"""
    <style>
        .model-indicator {{
            position: fixed; top: 10px; left: 10px; background-color: #000; color: #0F0;
            padding: 5px 15px; font-family: 'Courier New', monospace; font-size: 13px;
            font-weight: bold; border-radius: 5px; z-index: 999999; border: 1px solid #333;
        }}
        /* Pestaña activa con línea roja (Cláusula de Identidad) */
        div[role="tablist"] {{ gap: 10px; }}
        div[role="tab"]:not([aria-selected="false"]) {{
            color: red !important; font-weight: bold !important; border-bottom: 3px solid red !important;
        }}
        .fg-glow-box {{
            background-color: #000; color: #fff; border-radius: 12px;
            padding: 15px; text-align: center; border: 2px solid #6a0dad;
            box-shadow: 0 0 20px #a020f0; margin: 5px 0; display: flex; flex-direction: column; justify-content: center;
        }}
        .fg-glow-box h1 {{ margin: 0; font-size: 45px; color: #fff !important; line-height: 1; }}
        
        /* Animaciones Flash Glow según resultado */
        @keyframes flash-green {{ 0% {{ box-shadow: 0 0 0px #0f0; }} 50% {{ box-shadow: 0 0 40px #
