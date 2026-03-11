# v. 11 mar 2026 22:15 (INTERFAZ COMPLETA + VOLCADO ATÓMICO A-AL + BLINDAJE)

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

# --- DEFINICIÓN DE ESTRUCTURA A-AL (EL MOLDE ESTRUCTURAL) ---
COLS_VAL = [
    "FECHA", "CENTRO", "RESIDENCIA", "ID_REGISTRO", "EDAD", "SEXO", "PESO", "CREATININA", "Nº_TOTAL_MEDS_PAC",
    "Nº_TOT_AFEC_CG", "Nº_CONTRAIND_CG", "Nº_TOXICID_CG", "Nº_AJUSTE_DOS_CG", "Nº_PRECAU_CG", "FG_CG",
    "Nº_TOT_AFEC_MDRD", "Nº_CONTRAIND_MDRD", "Nº_TOXICID_MDRD", "Nº_AJUSTE_DOS_MDRD", "Nº_PRECAU_MDRD", "FG_MDRD",
    "Nº_TOT_AFEC_CKD", "Nº_CONTRAIND_CKD", "Nº_TOXICID_CKD", "Nº_AJUSTE_DOS_CKD", "Nº_TOXICID_CKD", "FG_CKD"
]
COLS_MEDS_EXTRA = [
    "MEDICAMENTO", "GRUPO_TERAPEUTICO", "CAT_RIESGO_CG", "RIESGO_CG", "NIVEL_ADE_CG", 
    "CAT_RIESGO_MDRD", "RIESGO_MDRD", "NIVEL_ADE_MDRD", 
    "CAT_RIESGO_CKD", "RIESGO_CKD", "NIVEL_ADE_CKD"
]

# --- INICIALIZACIÓN DE ESTADO ---
if "active_model" not in st.session_state: st.session_state.active_model = "BUSCANDO..."
if "df_val" not in st.session_state: st.session_state.df_val = pd.DataFrame(columns=COLS_VAL)
if "df_meds" not in st.session_state: st.session_state.df_meds = pd.DataFrame(columns=COLS_VAL + COLS_MEDS_EXTRA)
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

# --- FUNCIONES DE SOPORTE ---
def clean_num(v): return re.sub(r'[^\d.]', '', str(v)) if v else "0"

def parsear_a_dataframes_v3(texto_tabla, pac_info, fgs):
    lineas = [l.strip() for l in texto_tabla.strip().split('\n') if '|' in l and '---' not in l]
    matriz = [[c.strip() for c in l.split('|') if c.strip()] for l in lineas]
    
    res_map = {"afectados": 0, "contraindicados": 1, "toxicidad": 2, "dosis": 3, "precaución": 4}
    v_cg, v_mdrd, v_ckd = ["0"]*5, ["0"]*5, ["0"]*5
    for f in matriz:
        t = f[0].lower()
        for k, idx in res_map.items():
            if k in t and len(f) >= 4:
                v_cg[idx], v_mdrd[idx], v_ckd[idx] = clean_num(f[1]), clean_num(f[2]), clean_num(f[3])

    total_meds = len([l for l in st.session_state.main_meds.split('\n') if l.strip()])
    f_base = [datetime.now().strftime("%d/%m/%Y"), pac_info[1], pac_info[2], pac_info[0], pac_info[4], pac_info[7], pac_info[5], pac_info[6], total_meds]
    fila_val = f_base + v_cg + [fgs[0]] + v_mdrd + [fgs[1]] + v_ckd + [fgs[2]]
    
    filas_m = []
    for f in matriz:
        if len(f) >= 15 and "fármaco" not in f[1].lower() and not any(k in f[0].lower() for k in res_map):
            try:
                ab_al = [f[1], f[2], f[4], f[5], f[7], f[8], f[10], f[11], f[12], f[14], f[15]]
                filas_m.append(fila_val + ab_al)
            except: continue
    return pd.DataFrame([fila_val], columns=COLS_VAL), pd.DataFrame(filas_m, columns=COLS_VAL + COLS_MEDS_EXTRA)

def llamar_ia(prompt):
    model = genai.GenerativeModel('models/gemini-1.5-flash')
    st.session_state.active_model = "1.5-FLASH"
    return model.generate_content(prompt, generation_config={"temperature": 0.1}).text

def inject_styles():
    st.markdown("""
    <style>
    .block-container { max-width: 100% !important; padding-top: 1.5rem !important; }
    .black-badge-zona { background-color: #000; color: #888; padding: 6px 12px; border-radius: 4px; position: fixed; top: 10px; left: 15px; z-index: 9999; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; }
    .black-badge-activo { background-color: #000; color: #0F0; padding: 6px 12px; border-radius: 4px; position: fixed; top: 10px; left: 145px; z-index: 9999; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; text-shadow: 0 0 5px #0F0; }
    .main-title { text-align: center; font-size: 2.2rem; font-weight: 800; margin-top: 15px; color: #1e1e1e; }
    .sub-version { text-align: center; font-size: 0.6rem; color: #bbb; font-family: monospace; margin-top: -8px; margin-bottom: 25px; }
    .fg-glow-box { background-color: #000; color: #FFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 20px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    @keyframes blinker { 50% { opacity: 0; } }
    .blink-text { animation: blinker 1s linear infinite; color: #c53030; font-weight: bold; padding: 10px; border: 1px solid #c53030; border-radius: 5px; background: #fff5f5; text-align: center; margin-bottom: 15px; }
    .warning-yellow { background-color: #fff9db; color: #856404; padding: 15px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 30px; text-align: center; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

# --- CONSTRUCCIÓN INTERFAZ ---
inject_styles()
st.markdown('<div class="black-badge-zona">ZONA: ACTIVA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="black-badge-activo">ACTIVO: {st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-version">v. 11 mar 2026 22:15</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 DATOS", "📈 GRÁFICOS"])

with tabs[0]:
    # 1. Registro de Paciente
    st.markdown("### Registro de Paciente")
    r1, r2, r3, r4, r5 = st.columns([1, 1, 1, 1.5, 0.4])
    with r1: centro = st.text_input("Centro", placeholder="M / G", key="reg_centro")
    with r2: residencia = st.selectbox("¿Residencia?", ["No", "Sí"], index=None, key="reg_res")
    with r3: st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)
    with r4: st.text_input("ID Registro", value=st.session_state.reg_id, disabled=True)
    with r5: st.write(""); st.button("🗑️", on_click=lambda: st.rerun())

    # 2. Calculadora y FG
    c_izq, c_der = st.columns(2, gap="large")
    with c_izq:
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            edad = st.number_input("Edad (años)", step=1, key="calc_e", value=None)
            peso = st.number_input("Peso (kg)", key="calc_p", value=None)
            creat = st.number_input("Creatinina (mg/dL)", key="calc_c", value=None)
            sexo = st.selectbox("Sexo", ["Hombre", "Mujer"], index=None, key="calc_s")
            fg_calc = round(((140 - edad) * peso) / (72 * creat) * (0.85 if sexo == "Mujer" else 1.0), 1) if all([edad, peso, creat, sexo]) else 0.0

    with c_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual (C-G)", placeholder="Entrada manual si aplica")
        fg_final = fg_m if fg_m else fg_calc
        st.markdown(f'<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{fg_final}</div><div style="font-size: 0.8rem; color: #9d00ff;">mL/min (C-G)</div></div>', unsafe_allow_html=True)
        l1, l2 = st.columns(2)
        with l1: mdrd = st.number_input("MDRD-4", value=None, key="fgl_mdrd")
        with l2: ckd = st.number_input("CKD-EPI", value=None, key="fgl_ckd")

    st.write(""); st.markdown("---")
    meds_input = st.text_area("Listado de Medicamentos", height=150, key="main_meds", placeholder="Pegue aquí el listado...")
    
    if st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True, type="primary"):
        if not meds_input: st.warning("Introduzca medicación.")
        else:
            with st.spinner("Analizando..."):
                res = llamar_ia(f"{c.PROMPT_AFR_V10}\n\nFG C-G: {fg_final}\nFG MDRD: {mdrd}\nFG CKD: {ckd}\n\nMEDS:\n{meds_input}")
                st.session_state.resp_ia = res
                st.session_state.analisis_realizado = True
                # Parseo automático al recibir respuesta
                partes = [p.strip() for p in res.split("|||") if p.strip()]
                if len(partes) >= 2:
                    st.session_state.df_val, st.session_state.df_meds = parsear_a_dataframes_v3(
                        partes[1], 
                        [st.session_state.reg_id, centro, residencia, "", edad, peso, creat, sexo],
                        [fg_final, mdrd if mdrd else 0, ckd if ckd else 0]
                    )

    if st.session_state.analisis_realizado:
        st.markdown("### Resultado del Análisis")
        st.write(st.session_state.resp_ia)
        st.markdown('<div class="blink-text">REVISE LA PESTAÑA "DATOS" ANTES DE GRABAR</div>', unsafe_allow_html=True)

with tabs[2]:
    st.markdown("### 📊 Centro de Inspección de Datos (A-AL)")
    s_tabs = st.tabs(["📋 VALIDACIONES (Pestaña A-AA)", "💊 MEDICAMENTOS (Pestaña A-AL)"])
    with s_tabs[0]:
        st.data_editor(st.session_state.df_val, use_container_width=True, key="ed_v_f")
    with s_tabs[1]:
        st.data_editor(st.session_state.df_meds, use_container_width=True, key="ed_m_f")
    
    if not st.session_state.df_val.empty:
        if st.button("💾 CONFIRMAR Y VOLCAR A GOOGLE SHEETS", use_container_width=True, type="primary"):
            with st.spinner("Sincronizando..."):
                try:
                    sh = client.open_by_key(SHEET_ID)
                    sh.worksheet("VALIDACIONES").append_rows(st.session_state.df_val.values.tolist())
                    sh.worksheet("MEDICAMENTOS").append_rows(st.session_state.df_meds.values.tolist())
                    st.success("¡Datos volcados correctamente!")
                except Exception as e: st.error(f"Error: {e}")

st.markdown('<div class="warning-yellow">⚠️ <b>Apoyo clínico. Verifique fuentes oficiales.</b></div>', unsafe_allow_html=True)
st.markdown(f'<div style="text-align:right; font-size:0.6rem; color:#ccc; margin-top:10px;">v. 11 mar 2026 22:15</div>', unsafe_allow_html=True)
