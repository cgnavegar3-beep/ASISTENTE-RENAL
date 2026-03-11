# v. 11 mar 2026 19:30 (CONTROL DE INTEGRIDAD: VOLCADO ATÓMICO + MAPEO SEMÁNTICO)

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
    st.sidebar.error(f"Error de configuración: {e}")

# --- FUNCIONES ---
def llamar_ia_en_cascada(prompt):
    if not API_KEY: return "⚠️ Error: API Key no configurada."
    disponibles = [m.name.replace('models/', '').replace('gemini-', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    orden = ['2.5-flash', 'flash-latest', '1.5-pro']
    for mod_name in orden:
       if mod_name in disponibles:
            try:
               st.session_state.active_model = mod_name.upper()
               model = genai.GenerativeModel(f'models/gemini-{mod_name}')
               return model.generate_content(prompt, generation_config={"temperature": 0.1}).text
            except: continue
    return "⚠️ Error en la generación."

def obtener_glow_class(sintesis_texto):
    if "⛔" in sintesis_texto: return "glow-red"
    elif "⚠️⚠️⚠️" in sintesis_texto: return "glow-orange"
    elif "⚠️⚠️" in sintesis_texto: return "glow-yellow-dark"
    elif "⚠️" in sintesis_texto: return "glow-yellow"
    else: return "glow-green"

def procesar_y_limpiar_meds():
    texto = st.session_state.main_meds
    if texto:
       prompt = f"Actúa como farmacéutico clínico. Reescribe este listado: [Principio Activo] + [Dosis] + (Marca). Una línea por fármaco. Sin explicaciones:\n{texto}"
       st.session_state.main_meds = llamar_ia_en_cascada(prompt)

def reset_registro():
    for key in ["reg_centro", "reg_res", "reg_id", "fgl_ckd", "fgl_mdrd", "main_meds"]:
       st.session_state[key] = ""
    for key in ["calc_e", "calc_p", "calc_c", "calc_s"]: 
       if key in st.session_state: st.session_state[key] = None
    st.session_state.analisis_realizado = False
    st.session_state.resp_ia = None

def reset_meds():
    st.session_state.main_meds = ""
    st.session_state.soip_s = "Revisión farmacoterapéutica según función renal."
    st.session_state.soip_o = ""; st.session_state.soip_i = ""; st.session_state.soip_p = "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
    st.session_state.ic_inter = ""; st.session_state.ic_clinica = ""
    st.session_state.analisis_realizado = False
    st.session_state.resp_ia = None

def preparar_datos_exportacion(texto_tabla, pac_info, fgs):
    """Mapeo semántico y máscara de columnas para volcado atómico."""
    lineas = [l.strip() for l in texto_tabla.strip().split('\n') if '|' in l and '---' not in l]
    matriz = []
    for l in lineas:
        cols = [c.strip() for c in l.split('|') if c.strip()]
        if cols: matriz.append(cols)

    def clean_val(v): return re.sub(r'[^\d]', '', str(v)) if v else "0"

    # 1. MAPEO DE RESUMEN POR PALABRAS CLAVE (K-AA)
    # Estructura: [Afectados, Contra, Toxicidad, Dosis, Precaucion]
    res_gc, res_mdrd, res_ckd = ["0"]*5, ["0"]*5, ["0"]*5
    keywords = {
        "afectados": 0, "contraindicados": 1, "toxicidad": 2, "dosis": 3, "precaución": 4
    }
    
    for fila in matriz:
        texto_fila = fila[0].lower()
        for kw, idx in keywords.items():
            if kw in texto_fila and len(fila) >= 4:
                res_gc[idx] = clean_val(fila[1])
                res_mdrd[idx] = clean_val(fila[2])
                res_ckd[idx] = clean_val(fila[3])

    # 2. CONSTRUCCIÓN DE FILA DE VALIDACIONES (A-AA)
    v_row = [None] * 27
    # A-J: Paciente y Metadatos
    v_row[0:len(pac_info)] = pac_info[:10]
    # K-O: Resumen G-C
    v_row[10:15] = res_gc
    # P: FG G-C
    v_row[15] = fgs[0]
    # Q-U: Resumen MDRD
    v_row[16:21] = res_mdrd
    # V: FG MDRD
    v_row[21] = fgs[1]
    # W-AA: Resumen CKD
    v_row[22:27] = res_ckd

    # 3. CONSTRUCCIÓN DE SUPER-FILAS PARA MEDICAMENTOS (A-AN)
    # Identificar filas de fármacos (aquellas que no son encabezados ni resumen)
    filas_farma = []
    for f in matriz:
        if len(f) >= 15 and not any(kw in f[0].lower() for kw in keywords) and "fármaco" not in f[1].lower():
            filas_farma.append(f)

    m_rows = []
    for f in filas_farma:
        # AB-AL: Fármaco, ATC, Cat GC, Riesgo GC, Nivel GC, Cat MDRD, Riesgo MDRD, Nivel MDRD, Cat CKD, Riesgo CKD, Nivel CKD
        # Saltamos indices de FG: 0(Icono), 3(Val GC), 6(Val MDRD), 9(Val CKD)
        try:
            det_farma = [
                f[1], f[2],             # AB, AC
                f[4], f[5], f[7],       # AD, AE, AF
                f[8], f[10], f[11],     # AG, AH, AI
                f[12], f[14], f[15]     # AJ, AK, AL
            ]
        except IndexError:
            det_farma = ["Error Formato"] + [""]*10
            
        # Unir A-AA (v_row) + AB-AL (det_farma)
        m_rows.append(v_row + det_farma)

    return v_row, m_rows

def inject_styles():
    st.markdown("""
    <style>
    .block-container { max-width: 100% !important; padding-top: 1rem !important; padding-left: 4% !important; padding-right: 4% !important; }
    .black-badge-zona { background-color: #000000; color: #888; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 15px; z-index: 999999; }
    .black-badge-activo { background-color: #000000; color: #00FF00; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 145px; z-index: 999999; text-shadow: 0 0 5px #00FF00; }
    .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin-bottom: 0px; margin-top: 20px; }
    .sub-version { text-align: center; font-size: 0.6rem; color: #bbb; margin-top: -5px; margin-bottom: 20px; font-family: monospace; }
    .fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .synthesis-box { padding: 15px; border-radius: 12px; margin-bottom: 15px; border-width: 2.2px; border-style: solid; font-size: 0.95rem; line-height: 1.6; }
    .glow-green { background-color: #f0fff4; color: #2f855a; border-color: #9ae6b4; box-shadow: 0 0 12px #9ae6b4; }
    @keyframes blinker { 50% { opacity: 0; } }
    .blink-text { animation: blinker 1s linear infinite; color: #c53030; font-weight: bold; padding: 10px; border: 1px solid #c53030; border-radius: 5px; background: #fff5f5; text-align: center; margin-bottom: 15px; }
    div[data-testid="stVerticalBlock"] > div:has(button[key="btn_grabar"]) button {
        animation: blinker 1s linear infinite;
        background-color: #fff5f5 !important;
        color: #c53030 !important;
        border: 2.2px solid #c53030 !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

inject_styles()
st.markdown('<div class="black-badge-zona">ZONA: ACTIVA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="black-badge-activo">ACTIVO: {st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-version">v. 11 mar 2026 19:30</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 DATOS", "📈 GRÁFICOS"])

with tabs[0]:
    st.markdown("### Registro de Paciente")
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1.5, 0.4])
    def on_centro_change():
        centro_val = st.session_state.reg_centro.strip().lower()
        if centro_val == "m": st.session_state.reg_centro = "Marín"
        elif centro_val == "o": st.session_state.reg_centro = "O Grove"
        if st.session_state.reg_centro:
           iniciales = "".join([word[0] for word in st.session_state.reg_centro.split()]).upper()[:3]
           st.session_state.reg_id = f"PAC-{iniciales}{random.randint(10000, 99999)}"

    with c1: st.text_input("Centro", placeholder="M / G", key="reg_centro", on_change=on_centro_change)
    with c2: st.selectbox("¿Residencia?", ["No", "Sí"], index=None, placeholder="Sí / No", key="reg_res")
    with c3: st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)
    with c4: st.text_input("ID Registro", key="reg_id", disabled=True)
    with c5: st.write(""); st.button("🗑️", on_click=reset_registro, key="btn_reset_reg")

    col_izq, col_der = st.columns(2, gap="large")
    with col_izq:
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            calc_e = st.number_input("Edad (años)", step=1, key="calc_e", value=None)
            calc_p = st.number_input("Peso (kg)", key="calc_p", value=None)
            calc_c = st.number_input("Creatinina (mg/dL)", key="calc_c", value=None)
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"], index=None, key="calc_s")
            fg = round(((140 - calc_e) * calc_p) / (72 * (calc_c if calc_c and calc_c > 0 else 1)) * (0.85 if calc_s == "Mujer" else 1.0), 1) if all([calc_e, calc_p, calc_c, calc_s]) else 0.0

    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual", placeholder="Fórmula Cockcroft-Gault: entrada manual")
        valor_fg = fg_m if fg_m else fg
        st.markdown(f'''<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{valor_fg}</div><div style="font-size: 0.8rem; color: #9d00ff;">mL/min (C-G)</div></div>''', unsafe_allow_html=True)
        l1, l2 = st.columns(2)
        with l1: val_mdrd = st.number_input("MDRD-4", value=None, key="fgl_mdrd")
        with l2: val_ckd = st.number_input("CKD-EPI", value=None, key="fgl_ckd")

    st.write(""); st.markdown("---")
    st.text_area("Listado", height=150, key="main_meds", placeholder="Pegue el listado de fármacos aquí...")
    st.button("Procesar medicamentos", on_click=procesar_y_limpiar_meds)
    
    btn_val = st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True)

    if btn_val:
        if not st.session_state.main_meds: st.error("Introduce medicamentos.")
        else:
            with st.spinner("Analizando..."):
               prompt_final = f"{c.PROMPT_AFR_V10}\n\nFG C-G: {valor_fg}\nFG CKD: {val_ckd}\nFG MDRD: {val_mdrd}\n\nMEDS:\n{st.session_state.main_meds}"
               st.session_state.resp_ia = llamar_ia_en_cascada(prompt_final)
               st.session_state.analisis_realizado = True

    if st.session_state.analisis_realizado and st.session_state.resp_ia:
        partes = [p.strip() for p in st.session_state.resp_ia.split("|||") if p.strip()]
        if len(partes) >= 3:
            sintesis, tabla, detalle = partes[:3]
            st.markdown(f'<div class="synthesis-box {obtener_glow_class(sintesis)}">{sintesis}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="table-container">{tabla}</div>', unsafe_allow_html=True)
            
            st.write(""); st.markdown('<div class="blink-text">¿DESEAS GRABAR DATOS?</div>', unsafe_allow_html=True)
            if st.button("💾 GRABAR DATOS", key="btn_grabar", use_container_width=True):
                with st.spinner("Grabando..."):
                    try:
                        pac_data = [st.session_state.reg_id, st.session_state.reg_centro, st.session_state.reg_res, datetime.now().strftime("%d/%m/%Y"), calc_e, calc_p, calc_c, calc_s, st.session_state.active_model, "N/A"]
                        fila_v, filas_m = preparar_datos_exportacion(tabla, pac_data, [valor_fg, val_mdrd, val_ckd])
                        sh = client.open_by_key(SHEET_ID)
                        sh.worksheet("VALIDACIONES").append_row(fila_v)
                        sh.worksheet("MEDICAMENTOS").append_rows(filas_m)
                        st.toast("Grabado con éxito."); st.success("¡Registro completado!")
                    except Exception as e: st.error(f"Error: {e}")

with tabs[1]:
    for label, key in [("Subjetivo (S)", "soip_s"), ("Objetivo (O)", "soip_o"), ("Interpretación (I)", "soip_i"), ("Plan (P)", "soip_p")]:
        st.markdown(f'<div class="linea-discreta-soip">{label}</div>', unsafe_allow_html=True)
        st.text_area(key, st.session_state[key], height=100, label_visibility="collapsed")

st.markdown(f"""<div class="warning-yellow">⚠️ <b>Apoyo clínico. Verifique fuentes oficiales.</b></div> <div style="text-align:right; font-size:0.6rem; color:#ccc; margin-top:10px;">v. 11 mar 2026 19:30</div>""", unsafe_allow_html=True)
