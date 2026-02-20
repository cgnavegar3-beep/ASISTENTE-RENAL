# v. 20 feb 19:30
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
#    1. Cuadros negros superiores (ZONA y ACTIVO) -> Ahora ultra-discretos.
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
if "auto_soip_s" not in st.session_state: st.session_state.auto_soip_s = ""
if "auto_soip_o" not in st.session_state: st.session_state.auto_soip_o = ""
if "auto_soip_i" not in st.session_state: st.session_state.auto_soip_i = ""
if "auto_soip_p" not in st.session_state: st.session_state.auto_soip_p = ""
if "auto_ic_motivo" not in st.session_state: st.session_state.auto_ic_motivo = ""
if "auto_ic_info" not in st.session_state: st.session_state.auto_ic_info = ""

def reset_registro():
    st.session_state["reg_centro"] = ""
    st.session_state["reg_edad"] = None
    st.session_state["reg_id"] = ""
    st.session_state["reg_res"] = "No"

def reset_meds():
    st.session_state["main_meds"] = ""
    for k in ["auto_soip_s", "auto_soip_o", "auto_soip_i", "auto_soip_p", "auto_ic_motivo", "auto_ic_info"]:
        st.session_state[k] = ""
    if "last_resp" in st.session_state: del st.session_state.last_resp

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

# CSS OPTIMIZADO: Badges discretos y mayor espacio de texto
st.markdown('<style>'
    '.block-container { max-width: 100% !important; padding-top: 1rem !important; }'
    '.availability-badge { background: #000; color: #555; padding: 2px 8px; border-radius: 3px; font-family: monospace; font-size: 0.55rem; position: absolute; top: 5px; left: 10px; border: 1px solid #222; }'
    '.model-badge { background: #000; color: #00FF00; padding: 2px 8px; border-radius: 3px; font-family: monospace; font-size: 0.55rem; position: absolute; top: 5px; left: 120px; border: 1px solid #222; }'
    '.main-title { text-align: center; font-size: 2.2rem; font-weight: 800; color: #1E1E1E; margin-top: 15px; }'
    '.sub-version { text-align: center; font-size: 0.75rem; color: #888; margin-top: -5px; margin-bottom: 20px; }'
    '.fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }'
    '.synthesis-box { padding: 15px; border-radius: 12px; margin-bottom: 15px; border-width: 2px; border-style: solid; }'
    '.glow-green { background-color: #f1f8e9; color: #2e7d32; border-color: #a5d6a7; }'
    '.glow-orange { background-color: #fff3e0; color: #e65100; border-color: #ffcc80; }'
    '.glow-red { background-color: #fff5f5; color: #c53030; border-color: #feb2b2; }'
    '.blue-detail-container { background-color: #f0f7ff; color: #2c5282; padding: 20px; border-radius: 10px; border: 1px solid #bee3f8; }'
    '.seccion-label-grande { text-align: center; font-weight: 900; color: #4a4a3a; margin: 25px 0 10px 0; font-size: 1.2rem; text-transform: uppercase; }'
    '.surco-uniforme { background: #f4f1ea; border-radius: 12px; margin-bottom: 8px; padding: 2px 15px; box-shadow: inset 2px 2px 5px #d9d5c7; }'
    '.contenedor-informe-unificado { background: #f4f1ea; border-radius: 12px; padding: 15px; box-shadow: inset 2px 2px 5px #d9d5c7; }'
    '.linea-discreta { font-size: 0.7rem; color: #8a8a7a; font-weight: bold; text-transform: uppercase; margin-bottom: 2px; }'
    '.stTextArea textarea, .stTextInput input { background-color: transparent !important; border: none !important; color: #2d2d24 !important; font-size: 0.9rem !important; }'
    '.warning-yellow { background-color: #fdfde0; color: #856404; padding: 15px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 30px; text-align: center; }'
'</style>', unsafe_allow_html=True)

st.markdown(f'<div class="availability
