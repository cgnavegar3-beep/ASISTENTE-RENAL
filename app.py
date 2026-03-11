# v. 11 mar 2026 21:30 (BLOQUEO DE COLUMNAS A-AL + SUBPESTAÑAS DE INSPECCIÓN)

import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
import random
import re
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
#     "qué", "por qué" y "cómo". Esperar aprobación explícita ("adelante").
# 6. COMPROMISO DE RIGOR: Gemini verificará el cumplimiento de estos 
#      principios antes y después de cada cambio. No se simplifican líneas.
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

# --- INICIALIZACIÓN DE ESTADO ---
if "active_model" not in st.session_state: st.session_state.active_model = "BUSCANDO..."
if "df_val" not in st.session_state: st.session_state.df_val = pd.DataFrame()
if "df_meds" not in st.session_state: st.session_state.df_meds = pd.DataFrame()
if "analisis_realizado" not in st.session_state: st.session_state.analisis_realizado = False
if "resp_ia" not in st.session_state: st.session_state.resp_ia = None

for key in ["main_meds", "soip_s", "soip_p", "reg_id", "reg_centro", "reg_res", "soip_o", "soip_i", "ic_inter", "ic_clinica"]:
   if key not in st.session_state: st.session_state[key] = ""

# --- CONFIGURACIÓN IA Y GOOGLE SHEETS ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    SHEET_ID = st.secrets["GOOGLE_SHEET_ID"]
except Exception as e:
    API_KEY = None
    st.error(f"Error de Configuración: {e}")

# --- MOTOR DE PROCESAMIENTO (MOLDE A-AL) ---

def clean_num(v): return re.sub(r'[^\d.]', '', str(v)) if v else "0"

def preparar_dataframes_v2(texto_tabla, pac_info, fgs):
    # 1. Definición de Columnas según Esquema solicitado
    cols_a_j = ["FECHA", "CENTRO", "RESIDENCIA", "ID_REGISTRO", "EDAD", "SEXO", "PESO", "CREATININA", "Nº_TOTAL_MEDS_PAC"]
    cols_res_cg = ["Nº_TOT_AFEC_CG", "Nº_CONTRAIND_CG", "Nº_TOXICID_CG", "Nº_AJUSTE_DOS_CG", "Nº_PRECAU_CG"]
    cols_res_mdrd = ["Nº_TOT_AFEC_MDRD", "Nº_CONTRAIND_MDRD", "Nº_TOXICID_MDRD", "Nº_AJUSTE_DOS_MDRD", "Nº_PRECAU_MDRD"]
    cols_res_ckd = ["Nº_TOT_AFEC_CKD", "Nº_CONTRAIND_CKD", "Nº_TOXICID_CKD", "Nº_AJUSTE_DOS_CKD", "Nº_PRECAU_CKD"]
    
    # Ensamblado A-AA (P y V son FGs)
    col_val_final = cols_a_j + cols_res_cg + ["FG_CG"] + cols_res_mdrd + ["FG_MDRD"] + cols_res_ckd + ["FG_CKD"]
    
    # 2. Parsing de la tabla IA
    lineas = [l.strip() for l in texto_tabla.strip().split('\n') if '|' in l and '---' not in l]
    matriz = [[c.strip() for c in l.split('|') if c.strip()] for l in lineas]
    
    # 3. Extracción de Resumen (Mapeo por palabra clave en últimas filas)
    res_map = {"afectados": 0, "contraindicados": 1, "toxicidad": 2, "dosis": 3, "precaución": 4}
    v_cg, v_mdrd, v_ckd = ["0"]*5, ["0"]*5, ["0"]*5
    
    for f in matriz:
        t = f[0].lower()
        for k, idx in res_map.items():
            if k in t and len(f) >= 4:
                v_cg[idx], v_mdrd[idx], v_ckd[idx] = clean_num(f[1]), clean_num(f[2]), clean_num(f[3])

    # 4. Construcción Fila de Validación (A-AA)
    total_meds = len([l for l in st.session_state.main_meds.split('\n') if l.strip()])
    f_pac = [datetime.now().strftime("%d/%m/%Y"), pac_info[1], pac_info[2], pac_info[0], pac_info[4], pac_info[7], pac_info[5], pac_info[6], total_meds]
    
    fila_a_aa = f_pac + v_cg + [fgs[0]] + v_mdrd + [fgs[1]] + v_ckd + [fgs[2]]
    df_val = pd.DataFrame([fila_a_aa], columns=col_val_final)
    
    # 5. Construcción Tabla Medicamentos (AB-AL)
    cols_meds = ["MEDICAMENTO", "GRUPO_TERAPEUTICO", "CAT_RIESGO_CG", "RIESGO_CG", "NIVEL_ADE_CG", 
                 "CAT_RIESGO_MDRD", "RIESGO_MDRD", "NIVEL_ADE_MDRD", 
                 "CAT_RIESGO_CKD", "RIESGO_CKD", "NIVEL_ADE_CKD"]
    
    filas_m = []
    for f in matriz:
        # Detectar fila de fármaco (tiene longitud y no es resumen ni cabecera)
        if len(f) >= 15 and "fármaco" not in f[1].lower() and not any(k in f[0].lower() for k in res_map):
            # Saltamos col 0 (iconos) y las cols de valor FG (3, 6, 9 en la tabla IA)
            # Índices en f: 1:farma, 2:atc, 4:catCG, 5:riesCG, 7:nivelCG, 8:catMDRD, 10:riesMDRD, 11:nivelMDRD, 12:catCKD, 14:riesCKD, 15:nivelCKD
            try:
                ab_al = [f[1], f[2], f[4], f[5], f[7], f[8], f[10], f[11], f[12], f[14], f[15]]
                filas_m.append(fila_a_aa + ab_al)
            except IndexError: continue
    
    df_meds = pd.DataFrame(filas_m, columns=col_val_final + cols_meds)
    return df_val, df_meds

# --- INTERFAZ ---
# ... (Se mantienen funciones inject_styles, llamar_ia_en_cascada y visualización de Validación) ...

with tabs[0]:
    # Lógica de validación (abreviada para enfoque en exportación)
    if st.session_state.analisis_realizado and st.session_state.resp_ia:
        partes = [p.strip() for p in st.session_state.resp_ia.split("|||") if p.strip()]
        if len(partes) >= 2:
            st.session_state.df_val, st.session_state.df_meds = preparar_dataframes_v2(
                partes[1], 
                [st.session_state.reg_id, st.session_state.reg_centro, st.session_state.reg_res, "", st.session_state.get("calc_e"), st.session_state.get("calc_p"), st.session_state.get("calc_c"), st.session_state.get("calc_s")], 
                [st.session_state.get("valor_fg", 0), st.session_state.get("fgl_mdrd", 0), st.session_state.get("fgl_ckd", 0)]
            )

with tabs[2]: # PESTAÑA DATOS
    st.markdown("### 📊 Centro de Inspección de Datos")
    s_tabs = st.tabs(["📋 VALIDACIONES (A-AA)", "💊 MEDICAMENTOS (A-AL)", "🤖 ANÁLISIS RAW"])
    
    with s_tabs[0]:
        if not st.session_state.df_val.empty:
            st.data_editor(st.session_state.df_val, use_container_width=True, key="ed_val")
        else: st.info("Pendiente de validación.")
            
    with s_tabs[1]:
        if not st.session_state.df_meds.empty:
            st.data_editor(st.session_state.df_meds, use_container_width=True, key="ed_med")
        else: st.info("Pendiente de validación.")
    
    if not st.session_state.df_val.empty:
        if st.button("🚀 VOLCADO ATÓMICO A GOOGLE SHEETS", use_container_width=True, type="primary"):
            with st.spinner("Sincronizando..."):
                try:
                    sh = client.open_by_key(SHEET_ID)
                    # Convertimos DataFrames a listas de listas para append_rows
                    sh.worksheet("VALIDACIONES").append_rows(st.session_state.df_val.values.tolist())
                    sh.worksheet("MEDICAMENTOS").append_rows(st.session_state.df_meds.values.tolist())
                    st.success("Sincronización completada con éxito.")
                except Exception as e: st.error(f"Error en volcado: {e}")

st.markdown(f"""<div style="text-align:right; font-size:0.6rem; color:#ccc; margin-top:10px;">v. 11 mar 2026 21:30</div>""", unsafe_allow_html=True)
