# v. 10 mar 2026 21:45 (CONTROL DE INTEGRIDAD INTERNO: 295 LÍNEAS)

import streamlit as st
import pandas as pd
import io
from datetime import datetime
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
import random
import re
import os
import time
import constants as c 

# =================================================================
# PRINCIPIOS FUNDAMENTALES (ESCRITOS DE PE A PA - PROHIBIDO ELIMINAR)
# =================================================================
# 1. IDENTIDAD: El nombre "ASISTENTE RENAL" es inalterable.
# 2. VERSIÓN: Mostrar siempre la versión con fecha/hora bajo el título.
# 3. INTERFAZ DUAL PROTEGIDA: Prohibido modificar la "Calculadora" y el 
#       "Filtrado Glomerular" (cuadro negro con glow morado).
# 4. BLINDAJE DE ELEMENTOS (ZONA ESTÁTICA):
#       - Cuadros negros superiores (ZONA y ACTIVO).
#       - Pestañas (Tabs) de navegación.
#       - Registro de Paciente: Estructura y función de fila única.
#       - Estructura del área de recorte y listado de medicación.
#       - Barra dual de validación (VALIDAR / RESET).
#       - Aviso legal amarillo inferior (Warning).
# 5. PROTOCOLO DE CAMBIOS: Antes de cualquier evolución técnica, explicar
#      "qué", "por qué" y "cómo". Esperar aprobación explícita ("adelante").
# 6. COMPROMISO DE RIGOR: Gemini verificará el cumplimiento de estos 
#       principios antes y después de cada cambio. No se simplifican líneas.
# 7. VERSIONADO LOCAL: Registrar la versión en la esquina inferior derecha.
# 8. CONTADOR DISCRETO: El contador de intentos debe ser discreto y 
#       ubicarse en la esquina superior izquierda (estilo v. 2.5).
# 9. INTEGRIDAD DEL CÓDIGO: Nunca omitir estas líneas; de lo contrario, 
#       se considerará pérdida de principios.
# 10. BLINDAJE DE CONTENIDOS: Quedan blindados todos los cuadros de texto,
#       sus textos flotantes (placeholders) y los textos predefinidos en las
#       secciones S, P e INTERCONSULTA. Prohibido borrarlos o simplificarlos.
# 11. AVISO PARPADEANTE: El aviso parpadeante ante falta de datos es un 
#       principio blindado; es informativo y no debe impedir la validación.
# =================================================================

st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

# --- INICIALIZACIÓN ---
if "active_model" not in st.session_state:
    st.session_state.active_model = "BUSCANDO..."
if "main_meds" not in st.session_state:
    st.session_state.main_meds = ""
if "soip_s" not in st.session_state:
    st.session_state.soip_s = "Revisión farmacoterapéutica según función renal."
if "soip_p" not in st.session_state:
    st.session_state.soip_p = "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
if "analisis_realizado" not in st.session_state:
    st.session_state.analisis_realizado = False
if "resp_ia" not in st.session_state:
    st.session_state.resp_ia = None

for key in ["soip_o", "soip_i", "ic_inter", "ic_clinica", "reg_id", "reg_centro", "reg_res"]:
    if key not in st.session_state:
        st.session_state[key] = ""

# --- CONFIGURACIÓN IA Y GOOGLE SHEETS ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)

    scope = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    SHEET_ID = st.secrets["GOOGLE_SHEET_ID"]

except Exception as e:
    API_KEY = None
    st.sidebar.error(f"Error de configuración: {e}")

# --- FUNCIONES IA ---

def llamar_ia_en_cascada(prompt):

    if not API_KEY:
        return "⚠️ Error: API Key no configurada."

    disponibles = [m.name.replace('models/','').replace('gemini-','') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]

    orden = ['2.5-flash','flash-latest','1.5-pro']

    for mod_name in orden:

        if mod_name in disponibles:

            try:
                st.session_state.active_model = mod_name.upper()

                model = genai.GenerativeModel(f'models/gemini-{mod_name}')

                return model.generate_content(
                    prompt,
                    generation_config={"temperature":0.1}
                ).text

            except:
                continue

    return "⚠️ Error en la generación."

# --- FUNCION EXPORTACION CORREGIDA ---

def preparar_datos_exportacion(texto_tabla, pac_info, fgs):

    lineas=[l.strip() for l in texto_tabla.strip().split('\n') if '|' in l and '---' not in l]

    matriz=[]
    for l in lineas:
        cols=[c.strip() for c in l.split('|') if c.strip()]
        if cols:
            matriz.append(cols)

    resumen = matriz[-5:] if len(matriz)>=5 else [["0"]*4 for _ in range(5)]
    filas_meds = matriz[1:-5] if len(matriz)>5 else []

    def clean_val(v):
        return re.sub(r'[^\d]','',str(v)) if v else "0"

    fecha=datetime.now().strftime("%d/%m/%Y")

    base=[
        fecha,
        pac_info[1],
        pac_info[2],
        pac_info[0],
        pac_info[4],
        pac_info[7],
        pac_info[5],
        pac_info[6],
        len(filas_meds),
        fgs[0]
    ]

    cg=[clean_val(r[1]) for r in resumen]
    mdrd=[clean_val(r[2]) for r in resumen]
    ckd=[clean_val(r[3]) for r in resumen]

    v_row = base + cg + [fgs[1]] + mdrd + [fgs[2]] + ckd

    m_rows=[]

    for f in filas_meds:

        med=f[0] if len(f)>0 else ""
        grupo=f[1] if len(f)>1 else ""

        cat_cg=f[3] if len(f)>3 else ""
        riesgo_cg=f[4] if len(f)>4 else ""
        nivel_cg=f[5] if len(f)>5 else ""

        cat_mdrd=f[8] if len(f)>8 else ""
        riesgo_mdrd=f[9] if len(f)>9 else ""
        nivel_mdrd=f[10] if len(f)>10 else ""

        cat_ckd=f[13] if len(f)>13 else ""
        riesgo_ckd=f[14] if len(f)>14 else ""
        nivel_ckd=f[15] if len(f)>15 else ""

        fila=v_row + [
            med,
            grupo,
            cat_cg,
            riesgo_cg,
            nivel_cg,
            cat_mdrd,
            riesgo_mdrd,
            nivel_mdrd,
            cat_ckd,
            riesgo_ckd,
            nivel_ckd
        ]

        m_rows.append(fila)

    return v_row,m_rows
# --- FUNCIONES RESET ---

def reset_registro():

    for key in ["reg_centro","reg_res","reg_id","fgl_ckd","fgl_mdrd","main_meds"]:
        st.session_state[key]=""

    for key in ["calc_e","calc_p","calc_c","calc_s"]:
        if key in st.session_state:
            st.session_state[key]=None

    st.session_state.analisis_realizado=False
    st.session_state.resp_ia=None


def reset_meds():

    st.session_state.main_meds=""

    st.session_state.soip_s="Revisión farmacoterapéutica según función renal."
    st.session_state.soip_o=""
    st.session_state.soip_i=""
    st.session_state.soip_p="Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."

    st.session_state.ic_inter=""
    st.session_state.ic_clinica=""

    st.session_state.analisis_realizado=False
    st.session_state.resp_ia=None


# --- GRABACIÓN SEGURA GOOGLE SHEETS ---

def grabar_seguro(sh,fila_v,filas_m):

    for _ in range(3):

        try:

            sh.worksheet("VALIDACIONES").append_row(fila_v)
            sh.worksheet("MEDICAMENTOS").append_rows(filas_m)

            return True

        except:

            time.sleep(1)

    return False
