import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import io
import hashlib

# --- 1. CONFIGURACIÓN INICIAL (DEBE SER LA PRIMERA LÍNEA) ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

# --- 2. GESTIÓN DE MODELOS (CASCADA) ---
MODELS = ["gemini-1.5-pro", "gemini-1.5-flash"]

def get_active_model_name():
    if 'active_model_idx' not in st.session_state:
        st.session_state.active_model_idx = 0
    raw_name = MODELS[st.session_state.active_model_idx]
    return raw_name.replace("gemini-", "").replace("-", " ").title()

def run_ia_task(prompt, image=None):
    for i in range(st.session_state.active_model_idx, len(MODELS)):
        try:
            current_model_id = MODELS[i]
            genai.configure(api_key=st.secrets["API_KEY"])
            model = genai.GenerativeModel(current_model_id)
            content = [prompt, image] if image else [prompt]
            response = model.generate_content(content)
            st.session_state.active_model_idx = i 
            return response.text
        except Exception:
            continue
    return "Fallo de conexión o superado el número de intentos"

# --- 3. RECURSOS Y ESTILOS ---
@st.cache_resource
def load_vademecum():
    try:
        doc = fitz.open("vademecum_renal.pdf")
        return "".join([page.get_text() for page in doc])
    except:
        return "Error crítico: Archivo vademecum_renal.pdf no encontrado."

def inject_ui_styles():
    st.markdown(f"""
    <style>
        .discreet-v {{
            position: fixed; top: 0; left: 0; background-color: #000; color: #0F0;
            padding: 5px 15px; font-family: monospace; font-size: 11px;
            z-index: 999999; border-bottom-right-radius: 10px; border: 1px solid #333;
        }}
        .fg-glow-box {{
            background-color: #000 !important; color: #fff !important;
            padding: 15px; border-radius: 12px; text-align: center;
            border: 2px solid #6a0dad; box-shadow: 0 0 20px #a020f0; margin: 10px 0;
        }}
        .fg-glow-box h1 {{ font-size: 48px !important; margin: 0; color: #fff !important; }}
        @keyframes flash-destello {{
            0% {{ opacity: 0; filter: brightness(5); transform: scale(0.98); }}
            100% {{ opacity: 1; filter: brightness(1); transform: scale(1); }}
        }}
        .result-card {{ animation: flash-destello 0.7s ease-out; padding: 20px; border-radius: 15px; margin-top: 15px; color: #000; }}
        [data-testid="column"] {{ display: flex; flex-direction: column; justify-content: flex-start !important; }}
