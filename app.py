# v. 10 mar 2026 17:35 (CONTROL DE INTEGRIDAD INTERNO: SISTEMA DE PERSISTENCIA NIVEL PROFESIONAL)
import streamlit as st
import pandas as pd
import io
from datetime import datetime
import google.generativeai as genai
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
#      "Filtrado Glomerular" (cuadro negro con glow morado).
# 4. BLINDAJE DE ELEMENTOS (ZONA ESTÁTICA):
#      - Cuadros negros superiores (ZONA y ACTIVO).
#      - Pestañas (Tabs) de navegación.
#      - Registro de Paciente: Estructura y función de fila única.
#      - Estructura del área de recorte y listado de medicación.
#      - Barra dual de validación (VALIDAR / RESET).
#      - Aviso legal amarillo inferior (Warning).
# 5. PROTOCOLO DE CAMBIOS: Antes de cualquier evolución técnica, explicar
#      "qué", "por qué" y "cómo". Esperar aprobación explícita ("adelante").
# 6. COMPROMISO DE RIGOR: Gemini verificará el cumplimiento de estos 
#      principios antes y después de cada cambio. No se simplifican líneas.
# 7. VERSIONADO LOCAL: Registrar la versión en la esquina inferior derecha.
# 8. CONTADOR DISCRETO: El contador de intentos debe ser discreto y 
#      ubicarse en la esquina superior izquierda (estilo v. 2.5).
# 9. INTEGRIDAD DEL CÓDIGO: Nunca omitir estas líneas; de lo contrario, 
#      se considerará pérdida de principios.
# 10. BLINDAJE DE CONTENIDOS: Quedan blindados todos los cuadros de texto,
#      sus textos flotantes (placeholders) y los textos predefinidos en las
#       secciones S, P e INTERCONSULTA. Prohibido borrarlos o simplificarlos.
# 11. AVISO PARPADEANTE: El aviso parpadeante ante falta de datos es un 
#       principio blindado; es informativo y no debe impedir la validación.
# =================================================================

st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

# --- 1. INICIALIZACIÓN DE VARIABLES DE ESTADO Y CÁLCULO (MEJORA SEGURIDAD) ---
if "active_model" not in st.session_state: st.session_state.active_model = "BUSCANDO..."
if "main_meds" not in st.session_state: st.session_state.main_meds = ""
if "analisis_realizado" not in st.session_state: st.session_state.analisis_realizado = False
if "resp_ia" not in st.session_state: st.session_state.resp_ia = None

# Variables de cálculo inicializadas para evitar NameError
calc_e = st.session_state.get("calc_e", None)
calc_p = st.session_state.get("calc_p", None)
calc_c = st.session_state.get("calc_c", None)
calc_s = st.session_state.get("calc_s", None)
val_mdrd = st.session_state.get("fgl_mdrd", None)
val_ckd = st.session_state.get("fgl_ckd", None)
valor_fg = 0.0 # Valor por defecto

# Diccionarios de UI
for key in ["soip_s", "soip_o", "soip_i", "soip_p", "ic_inter", "ic_clinica", "reg_id", "reg_centro", "reg_res"]:
   if key not in st.session_state: 
       if "soip_s" in key: st.session_state[key] = "Revisión farmacoterapéutica según función renal."
       elif "soip_p" in key: st.session_state[key] = "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
       else: st.session_state[key] = ""

# --- CONFIGURACIÓN IA ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    API_KEY = None
    st.sidebar.error("API Key no encontrada.")

# --- FUNCIONES CORE ---
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
    if not sintesis_texto: return "glow-green"
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
    for key in ["reg_centro", "reg_res", "reg_id", "fgl_ckd", "fgl_mdrd", "main_meds"]: st.session_state[key] = ""
    for key in ["calc_e", "calc_p", "calc_c", "calc_s"]: st.session_state[key] = None
    st.session_state.analisis_realizado = False
    st.session_state.resp_ia = None

def reset_meds():
    st.session_state.main_meds = ""
    st.session_state.soip_s = "Revisión farmacoterapéutica según función renal."
    st.session_state.soip_o = ""; st.session_state.soip_i = ""; st.session_state.soip_p = "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
    st.session_state.ic_inter = ""; st.session_state.ic_clinica = ""
    st.session_state.analisis_realizado = False
    st.session_state.resp_ia = None

# =================================================================
# PERSISTENCIA GOOGLE SHEETS (BLOQUE MEJORADO V. 10 MAR 17:35)
# =================================================================
import gspread
from google.oauth2.service_account import Credentials

COLUMNAS_VALIDACIONES = [
    "FECHA", "CENTRO", "RESIDENCIA", "ID_REGISTRO", "EDAD", "SEXO", "PESO", "CREATININA",
    "Nº_TOTAL_MEDS_PAC", "FG_CG", "Nº_TOT_AFEC_CG", "Nº_PRECAU_CG", "Nº_AJUSTE_DOS_CG",
    "Nº_TOXICID_CG", "Nº_CONTRAIND_CG", "FG_MDRD", "Nº_TOT_AFEC_MDRD", "Nº_PRECAU_MDRD",
    "Nº_AJUSTE_DOS_MDRD", "Nº_TOXICID_MDRD", "Nº_CONTRAIND_MDRD", "FG_CKD",
    "Nº_TOT_AFEC_CKD", "Nº_PRECAU_CKD", "Nº_AJUSTE_DOS_CKD", "Nº_TOXICID_CKD",
    "Nº_CONTRAIND_CKD", "Discrepancia", "ACEPTACION_MEDICO_GLOBAL"
]

COLUMNAS_MEDS_ESPECIFICAS = [
    "FARMACO", "ATC", "VALOR_GC", "CAT_GC", "RIESGO_GC", "NIVEL_GC",
    "VALOR_MDRD", "CAT_MDRD", "RIESGO_MDRD", "NIVEL_MDRD",
    "VALOR_CKD", "CAT_CKD", "RIESGO_CKD", "NIVEL_CKD"
]

def conectar_gsheets():
    """Establece conexión con la API de Google Sheets mediante Service Account."""
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        return client.open_by_key(st.secrets["spreadsheet_id"])
    except Exception as e:
        st.error(f"Fallo de conexión: {e}")
        return None

def registrar_log_error(doc: gspread.Spreadsheet, error_msg: str, contexto: str):
    """Registra cualquier incidencia técnica en la pestaña LOGS_SISTEMA."""
    try:
        log_sheet = doc.worksheet("LOGS_SISTEMA")
        log_sheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), st.session_state.get("reg_id", "SIN_ID"), contexto, error_msg])
    except: pass

def verificar_estructura_col(sheet: gspread.Worksheet, esperado: int, nombre: str, doc: gspread.Spreadsheet) -> bool:
    """Valida que el número de columnas coincida con el esquema esperado."""
    try:
        reales = len(sheet.row_values(1))
        if reales != esperado:
            registrar_log_error(doc, f"Esperadas {esperado}, encontradas {reales}", f"Check {nombre}")
            return False
        return True
    except Exception as e:
        registrar_log_error(doc, str(e), f"Error Crítico Check {nombre}")
        return False

def parsear_tabla_ia(tabla_texto):
    """Convierte la tabla Markdown de la IA en un DataFrame de Pandas filtrado."""
    if not tabla_texto or "|" not in tabla_texto: return pd.DataFrame()
    lineas = tabla_texto.strip().split('\n')
    datos_meds = []
    excluir = ["Total", "Nº", "Resumen", "Contraindicados", "Precaución", "Toxicidad", "Afectados"]
    for linea in lineas:
        if "|" in linea and "---" not in linea and "Medicamento" not in linea:
            cols = [c.strip() for c in linea.split('|') if c.strip()]
            if not cols or any(key in cols[0] for key in excluir): continue
            if len(cols) >= 13:
                datos_meds.append({
                    "FARMACO": cols[0].replace("⚠️", "").replace("⛔", "").strip(), "ATC": cols[1],
                    "VALOR_GC": cols[2], "CAT_GC": cols[3], "RIESGO_GC": cols[4], "NIVEL_GC": cols[5],
                    "VALOR_MDRD": cols[6], "CAT_MDRD": cols[7], "RIESGO_MDRD": cols[8], "NIVEL_MDRD": cols[9],
                    "VALOR_CKD": cols[10], "CAT_CKD": cols[11], "RIESGO_CKD": cols[12], "NIVEL_CKD": cols[13] if len(cols)>13 else ""
                })
    return pd.DataFrame(datos_meds)

def guardar_validacion(sheet_val: gspread.Worksheet, datos_comunes: dict):
    """Inserta una nueva fila en la pestaña VALIDACIONES."""
    fila = [datos_comunes.get(col, "") for col in COLUMNAS_VALIDACIONES]
    sheet_val.append_row(fila)

def guardar_medicamentos(sheet_meds: gspread.Worksheet, df_meds: pd.DataFrame, datos_comunes: dict):
    """Inserta múltiples filas (una por fármaco con riesgo) en MEDICAMENTOS."""
    if df_meds is None or df_meds.empty: return
    filas = []
    for _, row in df_meds.iterrows():
        filas.append([datos_comunes.get(c, "") for c in COLUMNAS_VALIDACIONES] + [row.get(c, "") for c in COLUMNAS_MEDS_ESPECIFICAS])
    if filas: sheet_meds.append_rows(filas)

# --- ESTILOS ---
def inject_styles():
   st.markdown("""
    <style>
    .block-container { max-width: 100% !important; padding-top: 1rem !important; padding-left: 4% !important; padding-right: 4% !important; }
    .black-badge-zona { background-color: #000000; color: #888; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 15px; z-index: 999999; }
    .black-badge-activo { background-color: #000000; color: #00FF00; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 145px; z-index: 999999; text-shadow: 0 0 5px #00FF00; }
    .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin-bottom: 0px; margin-top: 20px; }
    .sub-version { text-align: center; font-size: 0.6rem; color: #bbb; margin-top: -5px; margin-bottom: 20px; font-family: monospace; }
    .fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .unit-label { font-size: 0.65rem; color: #888; margin-top: -10px; margin-bottom: 5px; font-family: sans-serif; text-align: center; }
    .synthesis-box { padding: 15px; border-radius: 12px; margin-bottom: 15px; border-width: 2.2px; border-style: solid; font-size: 0.95rem; line-height: 1.6; }
    .glow-red { background-color: #fff5f5; color: #c53030; border-color: #feb2b2; box-shadow: 0 0 12px #feb2b2; }
    .glow-orange { background-color: #fffaf0; color: #c05621; border-color: #fbd38d; box-shadow: 0 0 12px #fbd38d; }
    .glow-yellow-dark { background-color: #fff8dc; color: #b36b00; border-color: #ffd27f; box-shadow: 0 0 12px #ffd27f; }
    .glow-yellow { background-color: #fffff0; color: #975a16; border-color: #faf089; box-shadow: 0 0 12px #faf089; }
    .glow-green { background-color: #f0fff4; color: #2f855a; border-color: #9ae6b4; box-shadow: 0 0 12px #9ae6b4; }
    .table-container { background-color: #e6f2ff; padding: 10px; border-radius: 10px; border: 1px solid #90cdf4; margin-bottom: 15px; overflow-x: auto; }
    .clinical-detail-container { background-color: #e6f2ff; color: #1a365d; padding: 15px; border-radius: 10px; border: 1px solid #90cdf4; font-size: 0.9rem; line-height: 1.6; }
    .warning-yellow { background-color: #fff9db; color: #856404; padding: 20px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 40px; text-align: center; font-size: 0.85rem; line-height: 1.5; }
    .linea-discreta-soip { border-top: 1px solid #d9d5c7; margin: 15px 0 5px 0; font-size: 0.65rem; font-weight: bold; color: #8e8a7e; text-transform: uppercase; }
    .formula-label { font-size: 0.6rem; color: #666; font-family: monospace; text-align: right; margin-top: 5px; }
    .fg-special-border { border: 1.5px solid #9d00ff !important; border-radius: 5px; }
    @keyframes blinker { 50% { opacity: 0; } }
    .blink-text { animation: blinker 1s linear infinite; color: #c53030; font-weight: bold; padding: 10px; border: 1px solid #c53030; border-radius: 5px; background: #fff5f5; text-align: center; margin-bottom: 15px; }
    div[data-testid="stVerticalBlock"] > div:has(button[key="btn_grabar"]) button {
        animation: blinker 1.5s linear infinite;
        background-color: #fff5f5 !important;
        color: #c53030 !important;
        border: 2.2px solid #c53030 !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

inject_styles()

# --- HEADER ---
st.markdown('<div class="black-badge-zona">ZONA: ACTIVA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="black-badge-activo">ACTIVO: {st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-version">v. 10 mar 2026 17:35</div>', unsafe_allow_html=True)

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
            calc_e = st.number_input("Edad (años)", step=1, key="calc_e", placeholder="Ej: 65", value=None)
            calc_p = st.number_input("Peso (kg)", key="calc_p", placeholder="Ej: 70.5", value=None)
            calc_c = st.number_input("Creatinina (mg/dL)", key="calc_c", placeholder="Ej: 1.2", value=None)
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"], index=None, placeholder="Seleccionar...", key="calc_s")
            
            # Cálculo Cockcroft-Gault Seguro
            if all([calc_e, calc_p, calc_c, calc_s]) and calc_c > 0:
                valor_fg = round(((140 - calc_e) * calc_p) / (72 * calc_c) * (0.85 if calc_s == "Mujer" else 1.0), 1)
            else:
                valor_fg = 0.0

    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual", placeholder="Cockcroft-Gault manual")
        final_fg = fg_m if fg_m else valor_fg
        st.markdown(f'''<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{final_fg}</div><div style="font-size: 0.8rem; color: #9d00ff;">mL/min (C-G)</div></div>''', unsafe_allow_html=True)
        st.markdown('<div class="formula-label">Fórmula Cockcroft-Gault</div>', unsafe_allow_html=True)
        st.write(""); l1, l2 = st.columns(2)
        with l1:
            st.markdown('<div class="fg-special-border">', unsafe_allow_html=True)
            val_mdrd = st.number_input("MDRD-4", value=None, placeholder="MDRD-4", label_visibility="collapsed", key="fgl_mdrd")
            st.markdown('</div><div class="unit-label">mL/min/1,73m²</div>', unsafe_allow_html=True)
        with l2:
            st.markdown('<div class="fg-special-border">', unsafe_allow_html=True)
            val_ckd = st.number_input("CKD-EPI", value=None, placeholder="CKD-EPI", label_visibility="collapsed", key="fgl_ckd")
            st.markdown('</div><div class="unit-label">mL/min/1,73m²</div>', unsafe_allow_html=True)

    st.write(""); st.markdown("---")
    m_col1, m_col2 = st.columns([0.5, 0.5])
    with m_col1: st.markdown("#### 📝 Listado de medicamentos")
    with m_col2: st.markdown('<div style="float:right; color:#c53030; font-weight:bold; font-size:0.8rem;">🛡️ RGPD: No datos personales</div>', unsafe_allow_html=True)
    st.text_area("Listado", height=150, label_visibility="collapsed", key="main_meds", placeholder="Pegue el listado aquí...")
    st.button("Procesar medicamentos", on_click=procesar_y_limpiar_meds)

    b1, b2 = st.columns([0.85, 0.15])
    btn_val = b1.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True)
    b2.button("🗑️ RESET", on_click=reset_meds, use_container_width=True)

    if btn_val:
        if not all([st.session_state.reg_centro, st.session_state.reg_res, calc_e, calc_p, calc_c, calc_s]):
            st.markdown('<div class="blink-text">⚠️ AVISO: FALTAN DATOS. EL ANÁLISIS PUEDE SER INCOMPLETO.</div>', unsafe_allow_html=True)
        if not st.session_state.main_meds: 
            st.error("Por favor, introduce el listado de medicamentos para analizar.")
        else:
            with st.spinner("Analizando situación clínica..."):
                p_final = f"{c.PROMPT_AFR_V10}\n\nFG C-G: {final_fg}\nFG CKD: {val_ckd}\nFG MDRD: {val_mdrd}\n\nMEDS:\n{st.session_state.main_meds}"
                st.session_state.resp_ia = llamar_ia_en_cascada(p_final)
                st.session_state.analisis_realizado = True

    if st.session_state.analisis_realizado and st.session_state.resp_ia:
        resp = st.session_state.resp_ia[st.session_state.resp_ia.find("|||"):] if "|||" in st.session_state.resp_ia else st.session_state.resp_ia
        try:
            partes = [p.strip() for p in resp.split("|||") if p.strip()]
            while len(partes) < 3: partes.append("")
            sintesis, tabla, detalle = partes[:3]
            
            glow = obtener_glow_class(sintesis)
            if sintesis: st.markdown(f'<div class="synthesis-box {glow}">{sintesis.replace("\n","<br>")}</div>', unsafe_allow_html=True)
            if tabla: st.markdown(f'<div class="table-container">{tabla}</div>', unsafe_allow_html=True)
            if detalle: st.markdown(f'''<div class="clinical-detail-container">{detalle.replace("\n","<br>")}</div>''', unsafe_allow_html=True)
            
            # --- MAPEO DE INFORMES ---
            d_obj = []
            if calc_e: d_obj.append(f"Edad: {calc_e}a")
            if calc_p: d_obj.append(f"Peso: {calc_p}kg")
            if calc_c: d_obj.append(f"Crea: {calc_c}mg/dL")
            if final_fg: d_obj.append(f"FG: {final_fg}mL/min")
            st.session_state.soip_o = " | ".join(d_obj)
            st.session_state.soip_i = sintesis.replace("BLOQUE 1: ALERTAS Y AJUSTES", "").strip()
            st.session_state.ic_inter = f"Se solicita revisión de:\n{st.session_state.soip_i}"
            st.session_state.ic_clinica = f"{st.session_state.soip_o}\n\n{detalle.split('⚠️ NOTA IMPORTANTE:')[0].replace('BLOQUE 3: ANALISIS CLINICO', '').strip()}"

            st.write(""); st.markdown('<div class="blink-text">¿DESEAS GRABAR DATOS EN LA NUBE?</div>', unsafe_allow_html=True)
            
            # --- 2. LÓGICA DE BOTÓN GRABAR MEJORADA (PERSISTENCIA TOTAL) ---
            c_s1, c_s2, c_s3 = st.columns([1, 1, 1])
            with c_s2:
                if st.button("💾 GRABAR DATOS", key="btn_grabar", use_container_width=True):
                    # Flag para controlar el flujo sin st.stop()
                    error_proceso = False 
                    with st.spinner("Sincronizando..."):
                        doc = conectar_gsheets()
                        if not doc:
                            st.error("No se pudo conectar con el servidor.")
                            error_proceso = True
                        
                        if not error_proceso:
                            try:
                                s_val = doc.worksheet("VALIDACIONES")
                                s_med = doc.worksheet("MEDICAMENTOS")
                                
                                # Verificación de integridad estructural
                                e1 = verificar_estructura_col(s_val, len(COLUMNAS_VALIDACIONES), "VALIDACIONES", doc)
                                e2 = verificar_estructura_col(s_med, len(COLUMNAS_VALIDACIONES)+len(COLUMNAS_MEDS_ESPECIFICAS), "MEDICAMENTOS", doc)
                                
                                if not e1 or not e2:
                                    st.error("La estructura del Excel no es válida.")
                                    error_proceso = True
                                
                                # Control de Duplicados
                                if not error_proceso and st.session_state.reg_id in s_val.col_values(4):
                                    st.warning(f"Registro '{st.session_state.reg_id}' ya grabado anteriormente.")
                                    error_proceso = True

                                if not error_proceso:
                                    # Extracción de Contadores
                                    st_txt = sintesis.upper()
                                    def _ext(t):
                                        m = re.search(fr"{t.upper()}:\s*(\d+)", st_txt)
                                        return m.group(1).strip() if m else "0"

                                    d_com = {
                                        "FECHA": datetime.now().strftime("%d/%m/%Y"), "CENTRO": st.session_state.reg_centro,
                                        "RESIDENCIA": st.session_state.reg_res, "ID_REGISTRO": st.session_state.reg_id,
                                        "EDAD": calc_e, "SEXO": calc_s, "PESO": calc_p, "CREATININA": calc_c,
                                        "Nº_TOTAL_MEDS_PAC": len(st.session_state.main_meds.strip().split('\n')),
                                        "FG_CG": final_fg, "Nº_TOT_AFEC_CG": _ext("TOTAL AFECTADOS"),
                                        "Nº_PRECAU_CG": _ext("PRECAUCIÓN"), "Nº_AJUSTE_DOS_CG": _ext("AJUSTE DOSIS"),
                                        "Nº_TOXICID_CG": _ext("RIESGO TOXICIDAD"), "Nº_CONTRAIND_CG": _ext("CONTRAINDICADOS"),
                                        "FG_MDRD": val_mdrd if val_mdrd else "", "FG_CKD": val_ckd if val_ckd else ""
                                    }

                                    # Volcado final
                                    guardar_validacion(s_val, d_com)
                                    df_r = parsear_tabla_ia(tabla)
                                    if not df_r.empty: 
                                        guardar_medicamentos(s_med, df_r, d_com)
                                    
                                    st.success(f"✅ Éxito: Registro {st.session_state.reg_id} sincronizado.")
                                    st.toast("Datos guardados.")

                            except Exception as e_proc:
                                registrar_log_error(doc, str(e_proc), "Fallo Proceso Grabado")
                                st.error(f"Error técnico al grabar: {str(e_proc)}")
            # --- FIN LÓGICA GRABAR ---

        except Exception as e: st.error(f"Error Visualización: {e}")

with tabs[1]:
    for l, k, h in [("Subjetivo (S)", "soip_s", 70), ("Objetivo (O)", "soip_o", 70), ("Interpretación (I)", "soip_i", 120), ("Plan (P)", "soip_p", 100)]:
        st.markdown(f'<div class="linea-discreta-soip">{l}</div>', unsafe_allow_html=True)
        st.text_area(k, st.session_state[k], height=h, label_visibility="collapsed")
    st.markdown('<div class="linea-discreta-soip">INTERCONSULTA</div>', unsafe_allow_html=True)
    st.text_area("IC_B1", st.session_state.ic_inter, height=150, label_visibility="collapsed")
    st.markdown('<div class="linea-discreta-soip">INFORMACIÓN CLÍNICA</div>', unsafe_allow_html=True)
    st.text_area("IC_B2", st.session_state.ic_clinica, height=250, label_visibility="collapsed")

st.markdown(f"""<div class="warning-yellow">⚠️ <b>Esta herramienta es de apoyo clínico. Verifique siempre con la ficha técnica oficial (AEMPS/EMA).</b></div> 
<div style="text-align:right; font-size:0.6rem; color:#ccc; font-family:monospace; margin-top:10px;">v. 10 mar 2026 17:35</div>""", unsafe_allow_html=True)
