import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import io

# --- 1. CONFIGURACIÓN E INYECCIÓN DE INTERFAZ (BLINDAJE VISUAL) ---
st.set_page_config(page_title="Asistente Renal", layout="wide")

def inject_ui_styles():
    st.markdown("""
    <style>
    /* 1. INDICADOR INTELIGENTE DE MODELO (Negro/Verde Neón) */
    .model-indicator {
        background-color: #000000;
        color: #00FF00;
        padding: 4px 10px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 0.85rem;
        position: fixed;
        top: 10px;
        left: 10px;
        z-index: 1001;
        border: 1px solid #00FF00;
    }
    
    /* 2. TÍTULO CENTRADO PROFESIONAL */
    .main-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 800;
        color: #1E1E1E;
        margin-top: -30px;
        padding-bottom: 20px;
        letter-spacing: -1px;
    }

    /* 3. BLINDAJE PESTAÑA ACTIVA: Línea roja y negrita */
    div[data-baseweb="tab-list"] button[aria-selected="true"] {
        border-bottom: 4px solid red !important;
        font-weight: bold !important;
        color: black !important;
    }
    
    /* 4. DISPLAY FG GLOW MORADO */
    .fg-glow-box {
        background-color: #000000;
        color: #FFFFFF;
        border: 2px solid #9d00ff;
        box-shadow: 0 0 20px #9d00ff;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        margin: 15px 0;
    }

    /* 5. SEPARADOR HENDIDURA (Pequeño surco) */
    .separator-groove {
        border-top: 1px solid #bbb;
        border-bottom: 1px solid #fff;
        margin: 30px 0;
    }

    /* 6. AVISO DE SEGURIDAD FLOTANTE (Fixed Bottom) */
    .floating-warning {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #fff3cd;
        color: #856404;
        text-align: center;
        padding: 12px;
        font-size: 0.95rem;
        border-top: 1px solid #ffeeba;
        z-index: 9999;
        box-shadow: 0 -4px 12px rgba(0,0,0,0.1);
        font-weight: 500;
    }

    /* 7. EFECTOS FLASH DINÁMICOS */
    @keyframes flash-green { 0% { box-shadow: 0 0 0px #00ff00; } 50% { box-shadow: 0 0 25px #00ff00; } 100% { box-shadow: 0 0 0px #00ff00; } }
    .flash-verde { background-color: #d4edda; border: 1px solid #c3e6cb; animation: flash-green 1.5s ease-in-out; padding: 20px; border-radius: 10px; }
    
    @keyframes flash-orange { 0% { box-shadow: 0 0 0px #ffA500; } 50% { box-shadow: 0
