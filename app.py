# v. 10 mar 2026 21:55 (CONTROL DE INTEGRIDAD: MAPEO MATRICIAL A-AL Y HERENCIA TOTAL)
import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai
import random
import re
import gspread
from google.oauth2.service_account import Credentials
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

# --- ESTILOS CSS (BLINDADOS) ---
def inject_styles():
    st.markdown("""
    <style>
    .block-container { max-width: 100% !important; padding-top: 1rem !important; padding-left: 4% !important; padding-right: 4% !important; }
    .black-badge-zona { background-color: #000000; color: #888; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 15px; z-index: 999999; }
    .black-badge-activo { background-color: #000000; color: #00FF00; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 145px; z-index: 999999; text-shadow: 0 0 5px #00FF00; }
    .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin-bottom: 0px; margin-top: 20px; }
    .sub-version { text-align: center; font-size: 0.6rem; color: #bbb; margin-top: -5px; margin-bottom: 20px; font-family: monospace; }
    .fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .unit-label { font-size: 0.65rem; color: #888; margin-top: -10px; margin-bottom: 5px; text-align: center; }
    .synthesis-box { padding: 15px; border-radius: 12px; margin-bottom: 15px; border-width: 2.2px; border-style: solid; font-size: 0.95rem; line-height: 1.6; }
    .glow-red { background-color: #fff5f5; color: #c53030; border-color: #feb2b2; box-shadow: 0 0 12px #feb2b2; }
    .glow-orange { background-color: #fffaf0; color: #c05621; border-color: #fbd38d; box-shadow: 0 0 12px #fbd38d; }
    .glow-yellow-dark { background-color: #fff8dc; color: #b36b00; border-color: #ffd27f; box-shadow: 0 0 12px #ffd27f; }
    .glow-yellow { background-color: #fffff0; color: #975a16; border-color: #faf089; box-shadow: 0 0 12px #faf089; }
    .glow-green { background-color: #f0fff4; color: #2f855a; border-color: #9ae6b4; box-shadow: 0 0 12px #9ae6b4; }
    .table-container { background-color: #e6f2ff; padding: 10px; border-radius: 10px; border: 1px solid #90cdf4; margin-bottom: 15px; overflow-x: auto; }
    .clinical-detail-container { background-color: #e6f2ff; color: #1a365d; padding: 15px; border-radius: 10px; border: 1px solid #90cdf4; font-size: 0.9rem; line-height: 1.6; }
    .warning-yellow { background-color: #fff9db; color: #856404; padding: 20px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 40px; text-align: center; font-size: 0.85rem; }
    .linea-discreta-soip { border-top: 1px solid #d9d5c7; margin: 15px 0 5px 0; font-size: 0.65rem; font-weight: bold; color: #8e8a7e; text-transform: uppercase; }
    .fg-special-border { border: 1.5px solid #9d00ff !important; border-radius: 5px; }
    @keyframes blinker { 50% { opacity: 0; } }
    .blink-text { animation: blinker 1s linear infinite; color: #c53030; font-weight: bold; padding: 10px; border: 1px solid #c53030; border-radius: 5px; background: #fff5f5; text-align: center; margin-bottom: 15px; }
    div[data-testid="stVerticalBlock"] > div:has(button[key="btn_grabar"]) button {
        animation: blinker 1s linear infinite; background-color: #fff5f5 !important; color: #c53030 !important; border: 2.2px solid #c53030 !important; font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

inject_styles()

# --- INICIALIZACIÓN DE ESTADO ---
if "active_model" not in st.session_state: st.session_state.active_model = "BUSCANDO..."
if "main_meds" not in st.session_state: st.session_state.main_meds = ""
if "soip_s" not in st.session_state: st.session_state.soip_s = "Revisión farmacoterapéutica según función renal."
if "soip_p" not in st.session_state: st.session_state.soip_p = "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
if "analisis_realizado" not in st.session_state: st.session_state.analisis_realizado = False
if "resp_ia" not in st.session_state: st.session_state.resp_ia = None
for key in ["soip_o", "soip_i", "reg_id", "reg_centro", "reg_res", "tabla_actual"]:
    if key not in st.session_state: st.session_state[key] = ""

# --- CONEXIÓN GOOGLE SHEETS ---
def conectar_sheets():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        return gspread.authorize(creds).open_by_key(st.secrets["spreadsheet_id"])
    except: return None

# --- LÓGICA DE EXTRACCIÓN MATRICIAL (INGENIERÍA DE DATOS) ---
def procesar_tablas_para_sheets(texto_tabla, pac_data, fgs):
    """
    pac_data: [FECHA, CENTRO, RESIDENCIA, ID_REGISTRO, EDAD, SEXO, PESO, CREATININA, Nº_TOTAL_MEDS, FG_CG] (A-J)
    fgs: [FG_MDRD, FG_CKD]
    """
    lineas = [l.strip() for l in texto_tabla.strip().split('\n') if '|' in l and '---' not in l]
    matriz = []
    for l in lineas:
        cols = [c.strip() for c in l.split('|') if c.strip()]
        if cols: matriz.append(cols)
    
    # Separar Medicamentos (filas 1 a N-5) y Resumen (últimas 5 filas)
    resumen = matriz[-5:] if len(matriz) >= 5 else [["0"]*4 for _ in range(5)]
    filas_meds = matriz[1:-5] if len(matriz) > 5 else []

    def clean(v): return re.sub(r'\D', '', str(v)) if v else "0"

    # 1. PESTAÑA VALIDACIONES (Fila A-AA)
    v_row = [None] * 27
    v_row[0:10] = pac_data # A-J
    
    # G-C (K-O)
    v_row[10] = clean(resumen[0][1]) # K: Total afectados
    v_row[11] = clean(resumen[1][1]) # L: Contraindicados
    v_row[12] = clean(resumen[2][1]) # M: Tox
    v_row[13] = clean(resumen[3][1]) # N: Ajuste dosis
    v_row[14] = clean(resumen[4][1]) # O: Precaución
    
    v_row[15] = fgs[0]                # P: FG_MDRD
    
    # MDRD (Q-U)
    v_row[16] = clean(resumen[0][2]) # Q: Total afectados
    v_row[17] = clean(resumen[1][2]) # R: Contraindicados
    v_row[18] = clean(resumen[2][2]) # S: Tox
    v_row[19] = clean(resumen[3][2]) # T: Ajuste dosis
    v_row[20] = clean(resumen[4][2]) # U: Precaución
    
    v_row[21] = fgs[1]                # V: FG_CKD
    
    # CKD (W-AA)
    v_row[22] = clean(resumen[0][3]) # W: Total afectados
    v_row[23] = clean(resumen[1][3]) # X: Contraindicados
    v_row[24] = clean(resumen[2][3]) # Y: Tox
    v_row[25] = clean(resumen[3][3]) # Z: Ajuste dosis
    v_row[26] = clean(resumen[4][3]) # AA: Precaución

    # 2. PESTAÑA MEDICAMENTOS (Matriz A-AL)
    m_rows = []
    for f in filas_meds:
        # AB: Fármaco, AC: ATC, AD: Cat G-C, AE: Riesgo G-C, AF: Nivel G-C, 
        # AG: Cat MDRD, AH: Riesgo MDRD, AI: Nivel MDRD, 
        # AJ: Cat CKD, AK: Riesgo CKD, AL: Nivel CKD
        det_farma = [
            f[0],                          # AB
            f[1] if len(f)>1 else "",      # AC
            f[3] if len(f)>3 else "",      # AD
            f[4] if len(f)>4 else "",      # AE
            f[5] if len(f)>5 else "",      # AF
            f[6] if len(f)>6 else "",      # AG
            f[7] if len(f)>7 else "",      # AH
            f[8] if len(f)>8 else "",      # AI
            f[9] if len(f)>9 else "",      # AJ
            f[10] if len(f)>10 else "",    # AK
            f[11] if len(f)>11 else ""     # AL
        ]
        m_rows.append(v_row + det_farma)
        
    return v_row, m_rows

# --- LÓGICA IA ---
def llamar_ia(prompt):
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        st.session_state.active_model = "1.5-FLASH"
        return model.generate_content(prompt, generation_config={"temperature": 0.1}).text
    except: return "⚠️ Error API"

# --- UI: HEADER ---
st.markdown('<div class="black-badge-zona">ZONA: ACTIVA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="black-badge-activo">ACTIVO: {st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-version">v. 10 mar 2026 21:55</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 DATOS", "📈 GRÁFICOS"])

with tabs[0]:
    st.markdown("### Registro de Paciente")
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1.5, 0.4])
    def on_centro_change():
        cv = st.session_state.reg_centro.strip().lower()
        if cv == "m": st.session_state.reg_centro = "Marín"
        elif cv == "o": st.session_state.reg_centro = "O Grove"
        if st.session_state.reg_centro:
            ini = "".join([w[0] for w in st.session_state.reg_centro.split()]).upper()[:3]
            st.session_state.reg_id = f"PAC-{ini}{random.randint(10000, 99999)}"

    with c1: st.text_input("Centro", key="reg_centro", on_change=on_centro_change, placeholder="M / O")
    with c2: st.selectbox("¿Residencia?", ["No", "Sí"], index=None, key="reg_res", placeholder="Sí / No")
    with c3: st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)
    with c4: st.text_input("ID Registro", key="reg_id", disabled=True)
    with c5: st.write(""); st.button("🗑️", on_click=lambda: st.session_state.update({"reg_centro":"", "reg_res":None, "reg_id":"", "main_meds":"", "analisis_realizado":False}))

    col_izq, col_der = st.columns(2, gap="large")
    with col_izq:
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            calc_e = st.number_input("Edad (años)", step=1, key="calc_e", value=None)
            calc_p = st.number_input("Peso (kg)", key="calc_p", value=None)
            calc_c = st.number_input("Creatinina (mg/dL)", key="calc_c", value=None)
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"], index=None, key="calc_s")
            fg_calc = round(((140 - (calc_e or 0)) * (calc_p or 0)) / (72 * (calc_c or 1)) * (0.85 if calc_s == "Mujer" else 1.0), 1) if all([calc_e, calc_p, calc_c, calc_s]) else 0.0

    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual", placeholder="Cockcroft-Gault manual")
        valor_fg = fg_m if fg_m else fg_calc
        st.markdown(f'''<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{valor_fg}</div><div style="font-size: 0.8rem; color: #9d00ff;">mL/min (C-G)</div></div>''', unsafe_allow_html=True)
        st.write(""); l1, l2 = st.columns(2)
        with l1: val_mdrd = st.number_input("MDRD-4", value=None, key="fgl_mdrd")
        with l2: val_ckd = st.number_input("CKD-EPI", value=None, key="fgl_ckd")

    st.write(""); st.markdown("---")
    st.text_area("Listado de medicamentos", height=150, key="main_meds", placeholder="Pegue el listado aquí...")
    
    b_val, b_res = st.columns([0.85, 0.15])
    if b_val.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True):
        if not st.session_state.main_meds: st.error("Introduzca medicación.")
        else:
            with st.spinner("Analizando con rigor clínico..."):
                p = f"{c.PROMPT_AFR_V10}\n\nFG C-G: {valor_fg}\nFG CKD: {val_ckd}\nFG MDRD: {val_mdrd}\n\nMEDS:\n{st.session_state.main_meds}"
                st.session_state.resp_ia = llamar_ia(p)
                st.session_state.analisis_realizado = True

    if st.session_state.analisis_realizado and st.session_state.resp_ia:
        partes = [p.strip() for p in st.session_state.resp_ia.split("|||") if p.strip()]
        if len(partes) >= 2:
            sint, tabla, deta = partes[0], partes[1], partes[2] if len(partes)>2 else ""
            st.session_state.tabla_actual = tabla
            st.markdown(f'<div class="synthesis-box glow-green">{sint.replace("\n","<br>")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="table-container">{tabla}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="clinical-detail-container">{deta.replace("\n","<br>")}</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="blink-text">¿DESEAS GRABAR DATOS?</div>', unsafe_allow_html=True)
            if st.button("💾 GRABAR DATOS", key="btn_grabar", use_container_width=True):
                sh = conectar_sheets()
                if sh:
                    try:
                        n_meds = len([l for l in st.session_state.main_meds.split('\n') if l.strip()])
                        p_data = [
                            datetime.now().strftime("%d/%m/%Y %H:%M"), st.session_state.reg_centro, 
                            st.session_state.reg_res, st.session_state.reg_id, calc_e, calc_s, 
                            calc_p, calc_c, n_meds, valor_fg
                        ]
                        f_val, f_meds = procesar_tablas_para_sheets(st.session_state.tabla_actual, p_data, [val_mdrd, val_ckd])
                        
                        sh.worksheet("VALIDACIONES").append_row(f_val)
                        sh.worksheet("MEDICAMENTOS").append_rows(f_meds)
                        st.success("✅ Sincronización Matricial Completada (A-AL).")
                    except Exception as e: st.error(f"Error técnico: {e}")

with tabs[1]:
    for l, k, h in [("Subjetivo", "soip_s", 70), ("Objetivo", "soip_o", 70), ("Interpretación", "soip_i", 120), ("Plan", "soip_p", 100)]:
        st.markdown(f'<div class="linea-discreta-soip">{l}</div>', unsafe_allow_html=True)
        st.session_state[k] = st.text_area(k, st.session_state.get(k, ""), height=h, label_visibility="collapsed")

with tabs[2]:
    st.markdown("### 📊 Datos Sincronizados")
    sh = conectar_sheets()
    if sh:
        try:
            df = pd.DataFrame(sh.worksheet("VALIDACIONES").get_all_records())
            st.dataframe(df, use_container_width=True)
        except: st.info("Pestaña vacía o inaccesible.")

st.markdown(f"""<div class="warning-yellow">⚠️ <b>Apoyo a la revisión. Verifique con fuentes oficiales.</b></div> <div style="text-align:right; font-size:0.6rem; color:#ccc; font-family:monospace; margin-top:10px;">v. 10 mar 2026 21:55</div>""", unsafe_allow_html=True)
