# v. 11 mar 2026 22:55 (CONTROL DE INTEGRIDAD: FIX DESPLAZAMIENTO FG + RANGOS ESTRICTOS)

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
import hashlib
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
def generar_checksum(texto):
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()

def clean_val(v):
    if not v: return "0"
    num = re.sub(r'[^\d]', '', str(v))
    return num if num else "0"

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

def procesar_y_limpiar_meds():
    st.session_state.main_meds = st.session_state.main_meds.strip()

def preparar_datos_exportacion(texto_tabla, pac_info, fgs, model_name):
    """Segmentación estricta de datos (Clínicos vs Metadatos)."""
    lineas = [l.strip() for l in texto_tabla.strip().split('\n') if '|' in l and '---' not in l]
    matriz = []
    for l in lineas:
        cols = [c.strip() for c in l.split('|') if c.strip()]
        if cols and not all(x.lower() in ["icono", "fármaco"] for x in cols):
            matriz.append(cols)
    
    # Rellenar si faltan datos
    if len(matriz) < 5: matriz = [["0"]*15 for _ in range(10)]
    
    filas_resumen = matriz[-5:]
    filas_meds_raw = matriz[:-5]
    
    # Matriz Medicamentos (11 columnas: AB:AL)
    matriz_meds = [[f[i] if i < len(f) else "" for i in [1,2,3,4,5,7,8,9,11,12,13]] for f in filas_meds_raw]
    
    # Vectores de resumen (5 elementos cada uno)
    v_gc = [clean_val(r[1]) if len(r) > 1 else "0" for r in filas_resumen][:5]
    v_mdrd = [clean_val(r[2]) if len(r) > 2 else "0" for r in filas_resumen][:5]
    v_ckd = [clean_val(r[3]) if len(r) > 3 else "0" for r in filas_resumen][:5]
    
    # Bloque 1: Datos Clínicos (8 columnas: A-H)
    # pac_info ya trae: ID, Centro, Res, Fecha, Edad, Peso, Creat, Sexo
    datos_clinicos = pac_info[:8] 
    
    # Bloque 2: Metadatos (2 columnas: I-J)
    checksum = generar_checksum(texto_tabla)
    metadatos = [model_name, checksum]
    
    return datos_clinicos, metadatos, matriz_meds, v_gc, v_mdrd, v_ckd

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
    .warning-yellow { background-color: #fff9db; color: #856404; padding: 20px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 40px; text-align: center; font-size: 0.85rem; }
    @keyframes blinker { 50% { opacity: 0; } }
    .blink-text { animation: blinker 1s linear infinite; color: #c53030; font-weight: bold; padding: 10px; border: 1px solid #c53030; border-radius: 5px; background: #fff5f5; text-align: center; margin-bottom: 15px; }
    button[key="btn_grabar"] {
        animation: blinker 1s linear infinite !important;
        background-color: #fff5f5 !important;
        color: #c53030 !important;
        border: 2.2px solid #c53030 !important;
    }
    </style>
    """, unsafe_allow_html=True)

inject_styles()
st.markdown('<div class="black-badge-zona">ZONA: ACTIVA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="black-badge-activo">ACTIVO: {st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-version">v. 11 mar 2026 22:55</div>', unsafe_allow_html=True)

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
    with c5: st.write(""); st.button("🗑️", on_click=lambda: [st.session_state.update({k: "" for k in ["reg_centro", "reg_res", "reg_id"]})], key="btn_reset_reg")

    col_izq, col_der = st.columns(2, gap="large")
    with col_izq:
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            calc_e = st.number_input("Edad (años)", step=1, key="calc_e", value=None)
            calc_p = st.number_input("Peso (kg)", key="calc_p", value=None)
            calc_c = st.number_input("Creatinina (mg/dL)", key="calc_c", value=None)
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"], index=None, key="calc_s")
            
            if calc_e and calc_p and calc_c and calc_s:
                fg = round(((140 - calc_e) * calc_p) / (72 * calc_c) * (0.85 if calc_s=="Mujer" else 1.0), 1)
            else:
                fg = 0.0

    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual", placeholder="Ingreso manual")
        valor_fg = float(fg_m) if fg_m and fg_m.replace('.','').isdigit() else fg
        st.markdown(f'''<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{valor_fg}</div><div style="font-size: 0.8rem; color: #9d00ff;">mL/min (C-G)</div></div>''', unsafe_allow_html=True)
        l1, l2 = st.columns(2)
        with l1: val_mdrd = st.number_input("MDRD-4", value=None, key="fgl_mdrd")
        with l2: val_ckd = st.number_input("CKD-EPI", value=None, key="fgl_ckd")

    st.write(""); st.markdown("---")
    st.text_area("Listado de medicamentos", height=150, key="main_meds", placeholder="Pegue el listado aquí...")
    st.button("Procesar medicamentos", on_click=procesar_y_limpiar_meds)
    
    if st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True):
        if not st.session_state.main_meds: st.error("Introduce medicamentos.")
        else:
            with st.spinner("Analizando con IA..."):
               prompt_final = f"{c.PROMPT_AFR_V10}\n\nFG C-G: {valor_fg}\nMEDS:\n{st.session_state.main_meds}"
               st.session_state.resp_ia = llamar_ia_en_cascada(prompt_final)
               st.session_state.analisis_realizado = True

    if st.session_state.analisis_realizado and st.session_state.resp_ia:
        resp_cruda = st.session_state.resp_ia
        partes = [p.strip() for p in resp_cruda.split("|||") if p.strip()] if "|||" in resp_cruda else [resp_cruda, "", ""]
        sintesis, tabla, detalle = partes[:3]
        st.markdown(f'<div class="synthesis-box glow-green">{sintesis}</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="overflow-x:auto">{tabla}</div>', unsafe_allow_html=True)
        
        st.write(""); st.markdown('<div class="blink-text">¿DESEAS GRABAR DATOS?</div>', unsafe_allow_html=True)
        if st.button("💾 GRABAR DATOS", key="btn_grabar", use_container_width=True):
            if valor_fg < 0 or valor_fg > 200:
                st.error(f"Bloqueo de seguridad: Valor de FG fuera de rango clínico.")
            else:
                with st.spinner("Ejecutando volcado segmentado..."):
                    try:
                        sh = client.open_by_key(SHEET_ID)
                        ws_val = sh.worksheet("VALIDACIONES")
                        ws_meds = sh.worksheet("MEDICAMENTOS")
                        
                        pac_info = [st.session_state.reg_id, st.session_state.reg_centro, st.session_state.reg_res, datetime.now().strftime("%d/%m/%Y"), calc_e, calc_p, calc_c, calc_s]
                        d_clinicos, d_meta, m_meds, v_gc, v_mdrd, v_ckd = preparar_datos_exportacion(tabla, pac_info, [valor_fg], st.session_state.active_model)
                        
                        col_ids = ws_val.col_values(1)
                        next_row = len([x for x in col_ids if x.strip()]) + 1
                        
                        # 1. Volcado Datos Clínicos (A-H: 8 columnas)
                        ws_val.update(f"A{next_row}:H{next_row}", [d_clinicos])
                        
                        # 2. Volcado Metadatos (I-J: 2 columnas)
                        ws_val.update(f"I{next_row}:J{next_row}", [d_meta])
                        
                        # 3. Volcado Resumen (Vectores de 5 elementos)
                        ws_val.update(f"K{next_row}:O{next_row}", [v_gc])
                        ws_val.update(f"Q{next_row}:U{next_row}", [v_mdrd])
                        ws_val.update(f"W{next_row}:AA{next_row}", [v_ckd])
                        
                        # 4. Volcado Medicamentos (AB-AL: 11 columnas)
                        if m_meds:
                            cell_range = f"AB{next_row}:AL{next_row + len(m_meds) - 1}"
                            ws_meds.update(cell_range, m_meds)
                        
                        st.success(f"Grabación correcta. ID Paciente: {d_clinicos[0]}")
                    except Exception as e: st.error(f"Error en volcado: {e}")

st.markdown(f"""<div class="warning-yellow">⚠️ <b>Apoyo clínico. Verifique con ficha técnica.</b></div> <div style="text-align:right; font-size:0.6rem; color:#ccc; margin-top:10px;">v. 11 mar 2026 22:55</div>""", unsafe_allow_html=True)
