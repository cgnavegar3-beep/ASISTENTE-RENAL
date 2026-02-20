# v. 20 feb 21:05
import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai

# =================================================================
# PRINCIPIOS FUNDAMENTALES:
# 1. NUNCA BORRAR NI MODIFICAR ESTA CLÁUSULA. 
# 2. No puedes mover nada, ni cambiar ni una sola línea de la estructura 
#    visual (RIGOR Y SERIEDAD). Cero modificaciones sin autorización.
# 3. Antes de cualquier evolución técnica, explicar el "qué", "por qué" 
#    y "cómo", y esperar aprobación ("adelante" o "procede").
# #
# I. ESTRUCTURA VISUAL PROTEGIDA:
#    1. Cuadros negros superiores (ZONA y ACTIVO).
#    2. Título "ASISTENTE RENAL" y Versión inmediatamente debajo (Blindado).
#    3. Título principal y pestañas (Tabs).
#    4. Registro de paciente y función: TODO EN UNA LÍNEA (Centro, Edad, ID Alfa, 
#       Res, Fecha + Botón Borrado Registro).
#    5. Interfaz Dual (Calculadora y caja de FG (Purple Glow): lógica Cockcroft-Gault.
#       -> REFUERZO: NO SE TOCA LA CALCULADORA, NO SE TOCA EL GLOW MORADO.
#    6. Layout Medicamentos: Título y Aviso RGPD (estilo ampliado) en la misma línea.
#    7. Cuadro de listado de medicamentos (TextArea).
#    8. Barra dual de botones (VALIDAR / RESET TOTAL) y Reset de Registro.
#    9. Aviso amarillo de apoyo legal inferior.
# #
# II. FUNCIONALIDADES CRÍTICAS PROTEGIDAS:
#    1. Cascada de Modelos (2.5 Flash > 1.5 Pro > Otros).
#    2. Detección dinámica de modelos vivos en la cuenta.
#    3. Actualización de feedback neón en tiempo real (Badge ACTIVO).
# #
# III. BLINDAJE DEL BLOQUE AZUL (blue-detail-container):
#    - Prohibición de Fragmentación: Detalle y Nota en el mismo div CSS.
#    - Estilo Fijo: Fondo (#f0f7ff), borde (#bee3f8).
#    - NOTA IMPORTANTE: Texto estático (4 puntos) en negrita y azul intenso (Blindado).
# #
# IV. BLINDAJE DE SÍNTESIS DINÁMICA (Glow System):
#    - Formato Rígido: Solo se permite "Medicamentos afectados:" o "Fármacos correctamente dosificados".
#    - Prohibición Textual: No pueden aparecer las palabras "SÍNTESIS", "DETALLE" o similares.
#    - Regla de Iconos: [Icono] + [Nombre] + [Frase corta]. Prohibido texto adicional.
#    - Lógica de Color (Glow): 
#        * Sin iconos = Verde (glow-green).
#        * Con ⚠️ = Naranja (glow-orange).
#        * Con ⛔ = Rojo (glow-red).
# #
# V. PROTECCIÓN INTEGRAL PESTAÑA 1 (💊 VALIDACIÓN):
#    - Blindaje Total: Prohibida cualquier modificación en el layout, orden de columnas o funciones de la Pestaña 1.
#    - Componentes Congelados: Registro de paciente (fila única), Calculadora dual (Glow morado), Área de texto y Botonera (Validar/Reset).
#    - Lógica Funcional: El sistema de callbacks y el prompt de IA de esta pestaña no admiten cambios de sintaxis.
# =================================================================

st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

# Inicialización de estados
claves_estado = [
    "auto_soip_s", "auto_soip_o", "auto_soip_i", "auto_soip_p", 
    "auto_ic_motivo", "auto_ic_info", "active_model", "main_meds"
]
for k in claves_estado:
    if k not in st.session_state:
        st.session_state[k] = "" if k != "active_model" else "---"

def reset_registro():
    st.session_state["reg_centro"] = ""
    st.session_state["reg_edad"] = None
    st.session_state["reg_id"] = ""
    st.session_state["reg_res"] = "No"

def reset_meds():
    st.session_state["main_meds"] = ""
    for k in ["auto_soip_s", "auto_soip_o", "auto_soip_i", "auto_soip_p", "auto_ic_motivo", "auto_ic_info"]:
        st.session_state[k] = ""
    if "last_resp" in st.session_state:
        del st.session_state.last_resp

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    API_KEY = None

def obtener_modelos_vivos():
    try:
        if not API_KEY: return []
        return [m.name.replace('models/', '').replace('gemini-', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    except: return ["2.5-flash", "1.5-pro"]

def llamar_ia_en_cascada(prompt):
    disponibles = obtener_modelos_vivos()
    for mod_name in ['2.5-flash', '1.5-pro']:
        if mod_name in disponibles:
            try:
                st.session_state.active_model = mod_name.upper()
                model = genai.GenerativeModel(f'models/gemini-{mod_name}')
                return model.generate_content(prompt).text
            except: continue
    return "⚠️ Error: Sin respuesta."

# CSS OPTIMIZADO: Badges ultra-discretos y cuadros ampliados
st.markdown('''
<style>
    .block-container { max-width: 100% !important; padding-top: 1rem !important; }
    .availability-badge { background: #000; color: #444; padding: 2px 6px; border-radius: 2px; font-family: monospace; font-size: 0.5rem; position: absolute; top: 5px; left: 10px; border: 1px solid #111; z-index: 1000; }
    .model-badge { background: #000; color: #00CC00; padding: 2px 6px; border-radius: 2px; font-family: monospace; font-size: 0.5rem; position: absolute; top: 5px; left: 105px; border: 1px solid #111; z-index: 1000; }
    .main-title { text-align: center; font-size: 2.2rem; font-weight: 800; color: #1E1E1E; margin-top: 15px; }
    .sub-version { text-align: center; font-size: 0.7rem; color: #888; margin-top: -5px; margin-bottom: 20px; }
    .fg-glow-box { background: #000; color: #FFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .synthesis-box { padding: 15px; border-radius: 12px; margin-bottom: 15px; border-width: 2px; border-style: solid; font-size: 0.95rem; }
