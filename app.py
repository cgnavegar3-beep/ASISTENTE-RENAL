# v. 20 feb 15:45
import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import google.generativeai as genai
import io

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

# Inicialización de estados para automatización
if "auto_soip_o" not in st.session_state: st.session_state.auto_soip_o = ""
if "auto_soip_i" not in st.session_state: st.session_state.auto_soip_i = ""
if "auto_ic_info" not in st.session_state: st.session_state.auto_ic_info = ""

def reset_registro():
   st.session_state["reg_centro"] = ""
   st.session_state["reg_edad"] = None
   st.session_state["reg_id"] = ""
   st.session_state["reg_res"] = "No"

def reset_meds():
   st.session_state["main_meds"] = ""
   st.session_state.auto_soip_o = ""
   st.session_state.auto_soip_i = ""
   st.session_state.auto_ic_info = ""

if 'active_model' not in st.session_state: st.session_state.active_model = "ESPERANDO..."

try:
    API_KEY = st.secrets["GEMINI_API_KEY_RENAL"] # Ajustado a tu secret
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
    .block-container { max-width: 100% !important; padding-top: 2.5rem !important; padding-left: 4% !important; padding-right: 4% !
