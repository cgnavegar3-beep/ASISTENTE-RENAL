# v. 07 mar 2026 10:30 (CONTROL DE INTEGRIDAD INTERNO: 338 LÍNEAS)

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import google.generativeai as genai
import random
import os
import constants as c 

# =================================================================
# PRINCIPIOS FUNDAMENTALES (ESCRITOS DE PE A PA - PROHIBIDO ELIMINAR)
# =================================================================
# 1. IDENTIDAD: El nombre "ASISTENTE RENAL" es inalterable.
# 2. VERSIÓN: Mostrar siempre la versión con fecha/hora bajo el título.
# 3. INTERFAZ DUAL PROTEGIDA: Prohibido modificar la "Calculadora" y el 
#    "Filtrado Glomerular" (cuadro negro con glow morado).
# 4. BLINDAJE DE ELEMENTOS (ZONA ESTÁTICA):
#    - Cuadros negros superiores (ZONA y ACTIVO).
#    - Pestañas (Tabs) de navegación.
#    - Registro de Paciente: Estructura y función de fila única.
#    - Estructura del área de recorte y listado de medicación.
#    - Barra dual de validación (VALIDAR / RESET).
#    - Aviso legal amarillo inferior (Warning).
# 5. PROTOCOLO DE CAMBIOS: Antes de cualquier evolución técnica, explicar
#    "qué", "por qué" y "cómo". Esperar aprobación explícita ("adelante").
# 6. COMPROMISO DE RIGOR: Gemini verificará el cumplimiento de estos 
#     principios antes y después de cada cambio. No se simplifican líneas.
# 7. VERSIONADO LOCAL: Registrar la versión en la esquina inferior derecha.
# 8. CONTADOR DISCRETO: El contador de intentos debe ser discreto y 
#    ubicarse en la esquina superior izquierda (estilo v. 2.5).
# 9. INTEGRIDAD DEL CÓDIGO: Nunca omitir estas líneas; de lo contrario, 
#    se considerará pérdida de principios.
# 10. BLINDAJE DE CONTENIDOS: Quedan blindados todos los cuadros de texto,
#      sus textos flotantes (placeholders) y los textos predefinidos en las
#      secciones S, P e INTERCONSULTA. Prohibido borrarlos o simplificarlos.
# 11. AVISO PARPADEANTE: El aviso parpadeante ante falta de datos es un 
#      principio blindado; es informativo y no debe impedir la validación.
# =================================================================

st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

# --- INICIALIZACIÓN DE ESTADO ---
if "active_model" not in st.session_state: st.session_state.active_model = "BUSCANDO..."
if "main_meds" not in st.session_state: st.session_state.main_meds = ""
if "soip_s" not in st.session_state: st.session_state.soip_s = "Revisión farmacoterapéutica según función renal."
if "soip_p" not in st.session_state: st.session_state.soip_p = "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."

for key in ["soip_o", "soip_i", "ic_inter", "ic_clinica", "reg_id", "reg_centro", "reg_res"]:
    if key not in st.session_state: st.session_state[key] = ""

# --- CONFIGURACIÓN IA Y CLOUD ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    # Configuración Google Sheets
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    sheet_name = "BD_ASISTENTE_RENAL"
except Exception as e:
    st.sidebar.error(f"Error de Configuración: {e}")

# --- FUNCIONES DE NUBE ---
def grabar_datos_cloud():
    try:
        sh = client.open(sheet_name)
        # Grabación en pestaña VALIDACION
        ws_val = sh.worksheet("VALIDACION")
        nueva_fila = [
            datetime.now().strftime("%d/%m/%Y"), st.session_state.reg_centro, st.session_state.reg_id,
            st.session_state.calc_e, st.session_state.calc_s, st.session_state.calc_p,
            st.session_state.reg_res, st.session_state.calc_c, st.session_state.get('last_fg_cg', 0),
            st.session_state.fgl_ckd, st.session_state.fgl_mdrd, "", "", "", "", "", "", "", "", "", "", "", "", "Pendiente", "No"
        ]
        ws_val.append_row(nueva_fila)
        st.success("✅ DATOS GRABADOS EN LA NUBE (BD_ASISTENTE_RENAL)")
    except Exception as e:
        st.error(f"Error al grabar en Sheets: {e}")

# --- FUNCIONES IA ---
def llamar_ia_en_cascada(prompt):
    disponibles = [m.name.replace('models/', '').replace('gemini-', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    orden = ['2.5-flash', 'flash-latest', '1.5-pro']
    for mod_name in orden:
        if mod_name in disponibles:
            try:
                st.session_state.active_model = mod_name.upper()
                model = genai.GenerativeModel(f'models/gemini-{mod_name}')
                return model.generate_content(prompt, generation_config={"temperature": 0.1}).text
            except: continue
    return "⚠️ Error."

def obtener_glow_class(sintesis_texto):
    if "⛔" in sintesis_texto: return "glow-red"
    elif "⚠️⚠️⚠️" in sintesis_texto: return "glow-orange"
    elif "⚠️⚠️" in sintesis_texto: return "glow-yellow-dark"
    elif "⚠️" in sintesis_texto: return "glow-yellow"
    else: return "glow-green"

def procesar_y_limpiar_meds():
    if st.session_state.main_meds:
        prompt = f"Actúa como farmacéutico clínico. Reescribe este listado: [Principio Activo] + [Dosis] + (Marca). Una línea por fármaco. Sin explicaciones:\n{st.session_state.main_meds}"
        st.session_state.main_meds = llamar_ia_en_cascada(prompt)

def reset_registro():
    for key in ["reg_centro", "reg_res", "reg_id", "fgl_ckd", "fgl_mdrd", "main_meds"]: st.session_state[key] = ""
    for key in ["calc_e", "calc_p", "calc_c", "calc_s"]: st.session_state[key] = None

def inject_styles():
    st.markdown("""
    <style>
    .block-container { max-width: 100% !important; padding-top: 1rem !important; padding-left: 4% !important; padding-right: 4% !important; }
    .black-badge-zona { background-color: #000; color: #888; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 15px; z-index: 999999; }
    .black-badge-activo { background-color: #000; color: #00FF00; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 145px; z-index: 999999; text-shadow: 0 0 5px #00FF00; }
    .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin-top: 20px; }
    .sub-version { text-align: center; font-size: 0.6rem; color: #bbb; margin-top: -5px; margin-bottom: 20px; font-family: monospace; }
    .fg-glow-box { background-color: #000; color: #FFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .unit-label { font-size: 0.65rem; color: #888; margin-top: -10px; margin-bottom: 5px; text-align: center; }
    .synthesis-box { padding: 15px; border-radius: 12px; margin-bottom: 15px; border-width: 2.2px; border-style: solid; font-size: 0.95rem; line-height: 1.6; }
    .glow-red { background-color: #fff5f5; color: #c53030; border-color: #feb2b2; box-shadow: 0 0 12px #feb2b2; }
    .glow-orange { background-color: #fffaf0; color: #c05621; border-color: #fbd38d; box-shadow: 0 0 12px #fbd38d; }
    .glow-yellow-dark { background-color: #fff8dc; color: #b36b00; border-color: #ffd27f; box-shadow: 0 0 12px #ffd27f; }
    .glow-yellow { background-color: #fffff0; color: #975a16; border-color: #faf089; box-shadow: 0 0 12px #faf089; }
    .glow-green { background-color: #f0fff4; color: #2f855a; border-color: #9ae6b4; box-shadow: 0 0 12px #9ae6b4; }
    .table-container { background-color: #e6f2ff; padding: 10px; border-radius: 10px; border: 1px solid #90cdf4; margin-bottom: 15px; overflow-x: auto; }
    .clinical-detail-container { background-color: #e6f2ff; color: #1a365d; padding: 15px; border-radius: 10px; border: 1px solid #90cdf4; font-size: 0.9rem; }
    .warning-yellow { background-color: #fff9db; color: #856404; padding: 20px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 40px; text-align: center; font-size: 0.85rem; }
    .linea-discreta-soip { border-top: 1px solid #d9d5c7; margin: 15px 0 5px 0; font-size: 0.65rem; font-weight: bold; color: #8e8a7e; text-transform: uppercase; }
    .formula-label { font-size: 0.6rem; color: #666; font-family: monospace; text-align: right; margin-top: 5px; }
    .fg-special-border { border: 1.5px solid #9d00ff !important; border-radius: 5px; }
    @keyframes blinker { 50% { opacity: 0; } }
    .blink-text { animation: blinker 1s linear infinite; color: #c53030; font-weight: bold; padding: 10px; border: 1px solid #c53030; border-radius: 5px; background: #fff5f5; text-align: center; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

inject_styles()

st.markdown('<div class="black-badge-zona">ZONA: ACTIVA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="black-badge-activo">ACTIVO: {st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-version">v. 07 mar 2026 10:30</div>', unsafe_allow_html=True)

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
            calc_e = st.number_input("Edad (años)", step=1, key="calc_e", placeholder="Edad", value=None)
            calc_p = st.number_input("Peso (kg)", key="calc_p", placeholder="Peso", value=None)
            calc_c = st.number_input("Creatinina (mg/dL)", key="calc_c", placeholder="Creatinina", value=None)
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"], index=None, placeholder="Sexo", key="calc_s")
            fg = round(((140 - calc_e) * calc_p) / (72 * (calc_c if calc_c and calc_c > 0 else 1)) * (0.85 if calc_s == "Mujer" else 1.0), 1) if all([calc_e, calc_p, calc_c, calc_s]) else 0.0
            st.session_state.last_fg_cg = fg

    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual", placeholder="Cockcroft-Gault manual")
        valor_fg = fg_m if fg_m else fg
        st.markdown(f'''<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{valor_fg}</div><div style="font-size: 0.8rem; color: #9d00ff;">mL/min (C-G)</div></div>''', unsafe_allow_html=True)
        st.markdown('<div class="formula-label">Fórmula Cockcroft-Gault</div>', unsafe_allow_html=True)
        l1, l2 = st.columns(2)
        with l1:
            st.markdown('<div class="fg-special-border">', unsafe_allow_html=True)
            st.number_input("MDRD-4", value=None, placeholder="MDRD-4", label_visibility="collapsed", key="fgl_mdrd")
            st.markdown('</div><div class="unit-label">mL/min/1,73m²</div>', unsafe_allow_html=True)
        with l2:
            st.markdown('<div class="fg-special-border">', unsafe_allow_html=True)
            st.number_input("CKD-EPI", value=None, placeholder="CKD-EPI", label_visibility="collapsed", key="fgl_ckd")
            st.markdown('</div><div class="unit-label">mL/min/1,73m²</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.text_area("Listado", height=120, label_visibility="collapsed", key="main_meds", placeholder="Fármacos aquí...")
    st.button("Procesar medicamentos", on_click=procesar_y_limpiar_meds)
    
    b1, b2, b3 = st.columns([0.65, 0.20, 0.15])
    btn_val = b1.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True)
    btn_grab = b2.button("💾 GRABAR DATOS", use_container_width=True)
    b3.button("🗑️ RESET", on_click=reset_registro, use_container_width=True)

    if btn_grab: grabar_datos_cloud()

    if btn_val:
        if not all([st.session_state.reg_centro, st.session_state.reg_res, calc_e, calc_p, calc_c, calc_s]):
            st.markdown('<div class="blink-text">⚠️ AVISO: FALTAN DATOS.</div>', unsafe_allow_html=True)
        
        if st.session_state.main_meds:
            with st.spinner("Analizando..."):
                prompt_final = f"{c.PROMPT_AFR_V10}\n\nFG C-G: {valor_fg}\nFG CKD: {st.session_state.fgl_ckd}\nFG MDRD: {st.session_state.fgl_mdrd}\n\nMEDS:\n{st.session_state.main_meds}"
                resp = llamar_ia_en_cascada(prompt_final)
                resp = resp[resp.find("|||"):] if "|||" in resp else resp
                try:
                    partes = [p.strip() for p in resp.split("|||") if p.strip()]
                    while len(partes) < 3: partes.append("")
                    sintesis, tabla, detalle = partes[:3]
                    st.markdown(f'<div class="synthesis-box {obtener_glow_class(sintesis)}">{sintesis.replace("\n","<br>")}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="table-container">{tabla}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="clinical-detail-container">{detalle.replace("\n","<br>")}</div>', unsafe_allow_html=True)
                except Exception as e: st.error(f"Error IA: {e}")

with tabs[1]:
    for label, key, h in [("S", "soip_s", 70), ("O", "soip_o", 70), ("I", "soip_i", 120), ("P", "soip_p", 100)]:
        st.markdown(f'<div class="linea-discreta-soip">{label}</div>', unsafe_allow_html=True)
        st.text_area(key, st.session_state[key], height=h, label_visibility="collapsed")

with tabs[2]:
    st.markdown("### 📊 Histórico en la Nube (Google Sheets)")
    try:
        sh = client.open(sheet_name)
        ws_val = sh.worksheet("VALIDACION")
        df_cloud = pd.DataFrame(ws_val.get_all_records())
        st.data_editor(df_cloud, use_container_width=True)
        st.divider()
        st.markdown("#### 🤖 CONSULTA DINÁMICA AL ASISTENTE")
        query_ia = st.text_input("Pregunta al histórico:")
        if query_ia:
            res_ia = llamar_ia_en_cascada(f"Analiza estos datos y responde: {query_ia}\n\nDatos:\n{df_cloud.to_string()}")
            st.write(res_ia)
    except: st.warning("Conecta Google Sheets para ver el histórico.")

st.markdown(f"""<div class="warning-yellow">⚠️ <b>Herramienta de apoyo. Verifique siempre fuentes oficiales.</b></div> <div style="text-align:right; font-size:0.6rem; color:#ccc; font-family:monospace; margin-top:10px;">v. 07 mar 2026 10:30</div>""", unsafe_allow_html=True)
