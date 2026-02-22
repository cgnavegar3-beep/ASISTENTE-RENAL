# v. 22 feb 13:10
import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import google.generativeai as genai
import io

# =================================================================
# # PRINCIPIOS FUNDAMENTALES:
# #
# 1. NUNCA BORRAR NI MODIFICAR ESTA CLÁUSULA. 
# #
# 2. No puedes mover nada, ni cambiar ni una sola línea de la estructura 
# #
#    visual (RIGOR Y SERIEDAD). Cero modificaciones sin autorización.
# #
# 3. Antes de cualquier evolución técnica, explicar el "qué", "por qué" 
# #
#    y "cómo", y esperar aprobación ("adelante" o "procede").
# #
# #
# I. ESTRUCTURA VISUAL PROTEGIDA:
# #
#    1. Cuadros negros superiores (ZONA y ACTIVO).
# #
#    2. Título "ASISTENTE RENAL" y Versión inmediatamente debajo (Blindado).
# #
#    2. Título principal y pestañas (Tabs).
# #
#    3. Registro de paciente y función: TODO EN UNA LÍNEA (Centro, Edad, ID Alfa, 
# #
#       Res, Fecha + Botón Borrado Registro).
# #
#    4. Interfaz Dual (Calculadora y caja de FG (Purple Glow): lógica Cockcroft-Gault.
# #
#       -> REFUERZO: NO SE TOCA LA CALCULADORA, NO SE TOCA EL GLOW MORADO.
# #
#    5. Layout Medicamentos: Título y Aviso RGPD (estilo ampliado) en la misma línea.
# #
#    6. Cuadro de listado de medicamentos (TextArea).
# #
#    7. Barra dual de botones (VALIDAR / RESET TOTAL) y Reset de Registro.
# #
#    8. Aviso amarillo de apoyo legal inferior.
# #
# #
# II. FUNCIONALIDADES CRÍTICAS PROTEGIDAS:
# #
#    1. Cascada de Modelos (2.5 Flash > 1.5 Pro > Otros).
# #
#    2. Detección dinámica de modelos vivos en la cuenta.
# #
#    3. Actualización de feedback neón en tiempo real (Badge ACTIVO).
# #
#   
# #
# III. BLINDAJE DEL BLOQUE AZUL (blue-detail-container):
# #
#    - Prohibición de Fragmentación: Detalle y Nota en el mismo div CSS.
# #
#    - Estilo Fijo: Fondo (#f0f7ff), borde (#bee3f8).
# #
#    - NOTA IMPORTANTE: Texto estático (4 puntos) en negrita y azul intenso (Blindado).
# #
# #
# IV. BLINDAJE DE SÍNTESIS DINÁMICA (Glow System):
# #
#    - Formato Rígido: Solo se permite "Medicamentos afectados:" o "Fármacos correctamente dosificados".
# #
#    - Prohibición Textual: No pueden aparecer las palabras "SÍNTESIS", "DETALLE" o similares.
# #
#    - Regla de Iconos: [Icono] + [Nombre] + [Frase corta]. Prohibido texto adicional.
# #
#    - Lógica de Color (Glow): 
# #
#        * Sin iconos = Verde (glow-green).
# #
#        * Con ⚠️ = Naranja (glow-orange).
# #
#        * Con ⛔ = Rojo (glow-red).
# #
# #
# V. PROTECCIÓN INTEGRAL PESTAÑA 1 (💊 VALIDACIÓN):
# #
#    - Blindaje Total: Prohibida cualquier modificación en el layout, orden de columnas o funciones de la Pestaña 1.
# #
#    - Componentes Congelados: Registro de paciente (fila única), Calculadora dual (Glow morado), Área de texto y Botonera (Validar/Reset).
# #
#    - Lógica Funcional: El sistema de callbacks y el prompt de IA de esta pestaña no admiten cambios de sintaxis.
# #
# =================================================================

st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

def reset_registro():
   st.session_state["reg_centro"] = ""
   st.session_state["reg_edad"] = None
   st.session_state["reg_id"] = ""
   st.session_state["reg_res"] = "No"

def reset_meds():
   st.session_state["main_meds"] = ""

if 'active_model' not in st.session_state: st.session_state.active_model = "ESPERANDO..."

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

def llamar_ia_en_cascada(prompt):
    disponibles = obtener_modelos_vivos()
    preferencia = ['2.5-flash', '1.5-pro', '1.5-flash']
    modelos_a_intentar = [m for m in preferencia if m in disponibles]
    for mod_name in modelos_a_intentar:
        try:
            st.session_state.active_model = mod_name.upper()
            model = genai.GenerativeModel(f'models/gemini-{mod_name}')
            response = model.generate_content(prompt)
            return response.text
        except: continue
    return "⚠️ Error: Sin respuesta."

def inject_ui_styles():
    st.markdown("""
    <style>
    /* ESPACIADO SUPERIOR PARA NO TAPAR CONTENIDO */
    .block-container { max-width: 100% !important; padding-top: 10rem !important; padding-left: 4% !important; padding-right: 4% !important; }
    
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    
    /* CUADROS NEGROS */
    .availability-badge { background-color: #1a1a1a !important; color: #888 !important; padding: 4px 10px; border-radius: 3px; font-family: monospace !important; font-size: 0.65rem; position: fixed; top: 15px; left: 15px; z-index: 1000001; border: 1px solid #333; width: 180px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
    .model-badge { background-color: #000000 !important; color: #00FF00 !important; padding: 4px 10px; border-radius: 3px; font-family: monospace !important; font-size: 0.75rem; position: fixed; top: 15px; left: 205px; z-index: 1000001; box-shadow: 0 0 5px #00FF0033; }
    
    /* CONTENEDOR FIJO DE TÍTULO */
    .fixed-title-container {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background-color: white;
        z-index: 999;
        padding-top: 20px;
        height: 100px;
    }
    .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin: 0; }
    .sub-version { text-align: center; font-size: 0.8rem; color: #666; margin-top: -5px; font-family: sans-serif; }
    
    /* PESTAÑAS FIJAS */
    div[data-testid="stTabs"] {
        position: fixed !important;
        top: 90px !important;
        background-color: white !important;
        z-index: 998 !important;
        width: 100%;
        padding-left: 4%;
        padding-right: 4%;
    }

    .version-display { text-align: right; font-size: 0.6rem; color: #bbb; font-family: monospace; position: fixed; bottom: 10px; right: 10px; }
    .id-display { color: #666; font-family: monospace; font-size: 0.85rem; margin-top: -5px; margin-bottom: 20px; }
    .formula-tag { font-size: 0.75rem; color: #888; font-style: italic; text-align: right; width: 100%; display: block; margin-top: 5px; }
    .fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .rgpd-inline { background-color: #fff5f5; color: #c53030; padding: 8px 16px; border-radius: 8px; border: 1.5px solid #feb2b2; font-size: 0.85rem; display: inline-block; float: right; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .synthesis-box { padding: 15px; border-radius: 12px; margin-bottom: 15px; text-align: left; border-width: 2px; border-style: solid; font-size: 0.95rem; }
    .glow-green { background-color: #f1f8e9; color: #2e7d32; border-color: #a5d6a7; box-shadow: 0 0 12px #a5d6a7; }
    .glow-orange { background-color: #fff3e0; color: #e65100; border-color: #ffcc80; box-shadow: 0 0 12px #ffcc80; }
    .glow-red { background-color: #fff5f5; color: #c53030; border-color: #feb2b2; box-shadow: 0 0 18px #feb2b2; }
