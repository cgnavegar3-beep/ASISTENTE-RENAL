# v. 03 mar 2026 19:15 (BLINDAJE INTEGRAL Y NOTAS ESTÁTICAS LITERALES)

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
# PRINCIPIOS FUNDAMENTALES (VERSIÓN INTEGRAL BLINDADA 03-MAR-2026)
# =================================================================
# GEMINI SIEMPRE TENDRÁ RIGOR, RESPETARÁ Y VERIFICARÁ QUE SE CUMPLAN 
# ESTOS PRINCIPIOS ANTES Y DESPUES DE REALIZAR CUALQUIER CAMBIO.
#
# 1. NUNCA BORRAR NI MODIFICAR ESTA CLÁUSULA.
# 2. PROHIBICIÓN DE MOVIMIENTO: No puedes mover, simplificar ni cambiar 
#    la estructura visual (RIGOR Y SERIEDAD). Cero cambios sin autorización.
# 3. PROTOCOLO DE EVOLUCIÓN: Antes de cualquier cambio técnico, explicar 
#    "qué", "por qué" y "cómo", y esperar aprobación ("adelante" o "procede").
#
# I. ESTRUCTURA VISUAL PROTEGIDA (INTERFAZ DUAL):
#    1. Cuadros negros superiores: ZONA (Activa) y ACTIVO (Modelo IA).
#    2. Título "ASISTENTE RENAL" y Versión pequeña inmediatamente debajo.
#    3. Registro de Paciente: Fila única (Centro, Residencia, Fecha, ID, Borrado).
#    4. CALCULADORA Y FG: No se toca la lógica Cockcroft-Gault ni el Glow Morado.
#    5. BLOQUE FG COMPLETO: Blindaje de los 3 cuadros (C-G, MDRD-4, CKD-EPI).
#    6. Layout Medicamentos: Título y Aviso RGPD Rojo en la misma línea.
#    7. Botón "Procesar medicamentos": Obligatorio para limpieza de listado.
#    8. Barra Dual Inferior: Botones "VALIDAR" y "RESET" alineados.
#    9. Aviso Legal Amarillo: Texto estático de apoyo a la revisión oficial.
#
# II. FUNCIONALIDADES Y CASCADA:
#    1. Cascada: 2.5-flash > flash-latest > 1.5-pro. Feedback neón en tiempo real.
#    2. Parseo Estricto: Salida de IA obligatoria en 3 BLOQUES con "|||".
#
# III. GLOW SYSTEM (LÓGICA DE COLOR ACTUALIZADA):
#    1. ROJO (glow-red): ⛔ | 2. NARANJA (glow-orange): ⚠️⚠️⚠️ | 3. AMARILLO OSCURO (glow-yellow-dark): ⚠️⚠️
#    4. AMARILLO (glow-yellow): ⚠️ | 5. VERDE (glow-green): ✅
#
# IV. BLINDAJE DE SALIDA Y NOTA CLÍNICA (NUNCA MODIFICAR):
#    - TABLA COMPARATIVA: Columna "Riesgo" siempre en formato: [Categoría], [Nivel].
#    - NOTA IMPORTANTE (4 PUNTOS ESTÁTICOS):
#      1. Verifique siempre con la ficha técnica oficial (AEMPS/EMA).
#      2. Los ajustes propuestos son orientativos según filtrado glomerular actual.
#      3. La decisión final corresponde siempre al prescriptor médico.
#      4. Considere la situación clínica global del paciente antes de modificar dosis.
# =================================================================

st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

# --- INICIALIZACIÓN ---
if "active_model" not in st.session_state: st.session_state.active_model = "BUSCANDO..."
if "main_meds" not in st.session_state: st.session_state.main_meds = ""
for key in ["soip_s", "soip_o", "soip_i", "soip_p", "ic_motivo", "ic_info", "reg_id", "reg_centro", "calc_e", "calc_p", "calc_c", "calc_s", "reg_res"]:
    if key not in st.session_state: st.session_state[key] = None

# --- CONFIGURACIÓN IA ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    API_KEY = None
    st.sidebar.error("API Key no encontrada.")

# --- FUNCIONES ---
def llamar_ia_en_cascada(prompt):
    if not API_KEY: return "⚠️ Error: API Key no configurada."
    disponibles = [m.name.replace('models/', '').replace('
