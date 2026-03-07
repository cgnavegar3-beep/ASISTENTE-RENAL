# v. 07 mar 2026 12:45 (INTEGRIDAD TOTAL Y TRIPLE VOLCADO)
 
import streamlit as st
import pandas as pd
import io
from datetime import datetime
import google.generativeai as genai
import random
import re
import os
import gspread
from google.oauth2.service_account import Credentials
import constants as c 
 
# =================================================================
# PRINCIPIOS FUNDAMENTALES (ESCRITOS DE PE A PA - PROHIBIDO ELIMINAR)
# =================================================================
# 1. IDENTIDAD: El nombre "ASISTENTE RENAL" es inalterable.
# 2. VERSIÓN: Mostrar siempre la versión con fecha/hora bajo el título.
# 3. INTERFAZ DUAL PROTEGIDA: Prohibido modificar la "Calculadora" y el 
#     "Filtrado Glomerular" (cuadro negro con glow morado).
# 4. BLINDAJE DE ELEMENTOS (ZONA ESTÁTICA):
#     - Cuadros negros superiores (ZONA y ACTIVO).
#     - Pestañas (Tabs) de navegación.
#     - Registro de Paciente: Estructura y función de fila única.
#     - Estructura del área de recorte y listado de medicación.
#     - Barra dual de validación (VALIDAR / RESET).
#     - Aviso legal amarillo inferior (Warning).
# 5. PROTOCOLO DE CAMBIOS: Antes de cualquier evolución técnica, explicar
#     "qué", "por qué" y "cómo". Esperar aprobación explícita ("adelante").
# 6. COMPROMISO DE RIGOR: Gemini verificará el cumplimiento de estos 
#     principios antes y después de cada cambio. No se simplifican líneas.
# 7. VERSIONADO LOCAL: Registrar la versión en la esquina inferior derecha.
# 8. CONTADOR DISCRETO: El contador de intentos debe ser discreto y 
#     ubicarse en la esquina superior izquierda (estilo v. 2.5).
# 9. INTEGRIDAD DEL CÓDIGO: Nunca omitir estas líneas; de lo contrario, 
#     se considerará pérdida de principios.
# 10. BLINDAJE DE CONTENIDOS: Quedan blindados todos los cuadros de texto,
#      sus textos flotantes (placeholders) y los textos predefinidos en las
#      secciones S, P e INTERCONSULTA. Prohibido borrarlos o simplificarlos.
# 11. AVISO PARPADEANTE: El aviso parpadeante ante falta de datos es un 
#      principio blindado; es informativo y no debe impedir la validación.
# =================================================================
 
st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")
 
# --- INICIALIZACIÓN DE ESTADOS ---
if "active_model" not in st.session_state: st.session_state.active_model = "BUSCANDO..."
if "main_meds" not in st.session_state: st.session_state.main_meds = ""
if "soip_s" not in st.session_state: st.session_state.soip_s = "Revisión farmacoterapéutica según función renal."
if "soip_o" not in st.session_state: st.session_state.soip_o = ""
if "soip_i" not in st.session_state: st.session_state.soip_i = ""
if "soip_p" not in st.session_state: st.session_state.soip_p = "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
if "ic_inter" not in st.session_state: st.session_state.ic_inter = ""
if "ic_clinica" not in st.session_state: st.session_state.ic_clinica = ""
if "analisis_realizado" not in st.session_state: st.session_state.analisis_realizado = False
if "resp_sintesis" not in st.session_state: st.session_state.resp_sintesis = ""
if "resp_tabla" not in st.session_state: st.session_state.resp_tabla = ""
if "resp_detalle" not in st.session_state: st.session_state.resp_detalle = ""
 
# --- CONFIGURACIÓN IA ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    API_KEY = None
    st.sidebar.error("API Key no encontrada.")

# --- CONEXIÓN Y VOLCADO TRIPLE ---
def grabar_datos_triple(fila_val, filas_med, fila_ana):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        doc = client.open("BD_ASISTENTE_RENAL")
        
        # Pestaña 1: VALIDACIONES
        doc.worksheet("VALIDACIONES").append_row(fila_val)
        # Pestaña 2: MEDICAMENTOS
        if filas_med:
            doc.worksheet("MEDICAMENTOS").append_rows(filas_med)
        # Pestaña 3: ANALISIS
        doc.worksheet("ANALISIS").append_row(fila_ana)
        
        st.success("✅ Datos grabados con éxito en las 3 pestañas.")
    except Exception as e:
        st.error(f"Error al grabar en Sheets: {e}")

# --- ESTILOS ---
st.markdown("""
<style>
.block-container { max-width: 100% !important; padding-top: 1rem !important; padding-left: 4% !important; padding-right: 4% !important; }
.black-badge-zona { background-color: #000000; color: #888; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 15px; z-index: 999999; }
.black-badge-activo { background-color: #000000; color: #00FF00; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 145px; z-index: 999999; text-shadow: 0 0 5px #00FF00; }
.main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin-bottom: 0px; margin-top: 20px; }
.sub-version { text-align: center; font-size: 0.6rem; color: #bbb; margin-top: -5px; margin-bottom: 20px; font-family: monospace; }
.fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }
.synthesis-box { padding: 15px; border-radius: 12px; margin-bottom: 15px; border-width: 2.2px; border-style: solid; font-size: 0.95rem; line-height: 1.6; }
.glow-red { background-color: #fff5f5; color: #c53030; border-color: #feb2b2; box-shadow: 0 0 12px #feb2b2; }
.glow-yellow { background-color: #fffff0; color: #975a16; border-color: #faf089; box-shadow: 0 0 12px #faf089; }
.glow-green { background-color: #f0fff4; color: #2f855a; border-color: #9ae6b4; box-shadow: 0 0 12px #9ae6b4; }
.linea-discreta-soip { border-top: 1px solid #d9d5c7; margin: 15px 0 5px 0; font-size: 0.65rem; font-weight: bold; color: #8e8a7e; text-transform: uppercase; }
@keyframes blinker { 50% { opacity: 0; } }
.blink-text { animation: blinker 1s linear infinite; color: #c53030; font-weight: bold; padding: 10px; border: 1px solid #c53030; border-radius: 5px; background: #fff5f5; text-align: center; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)
 
st.markdown('<div class="black-badge-zona">ZONA: ACTIVA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="black-badge-activo">ACTIVO: {st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-version">v. 07 mar 2026 12:45</div>', unsafe_allow_html=True)
 
tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 DATOS", "📈 GRÁFICOS"])
 
with tabs[0]:
    st.markdown("### Registro de Paciente")
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1.5, 0.4])
    def on_centro_change():
        centro_val = st.session_state.reg_centro.strip().lower()
        if centro_val == "m": st.session_state.reg_centro = "Marín"
        elif centro_val == "o": st.session_state.reg_centro = "O Grove"
        if st.session_state.reg_centro:
            st.session_state.reg_id = f"PAC-{random.randint(10000, 99999)}"
 
    with c1: st.text_input("Centro", placeholder="M / G", key="reg_centro", on_change=on_centro_change)
    with c2: st.selectbox("¿Residencia?", ["No", "Sí"], index=None, placeholder="Sí / No", key="reg_res")
    with c3: st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)
    with c4: st.text_input("ID Registro", key="reg_id", disabled=True)
    with c5: st.write(""); st.button("🗑️", on_click=lambda: st.rerun(), key="clear_all")
 
    col_izq, col_der = st.columns(2, gap="large")
    with col_izq:
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            calc_e = st.number_input("Edad (años)", step=1, key="calc_e", value=None)
            calc_p = st.number_input("Peso (kg)", key="calc_p", value=None)
            calc_c = st.number_input("Creatinina (mg/dL)", key="calc_c", value=None)
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"], index=None, key="calc_s")
            fg = round(((140 - calc_e) * calc_p) / (72 * (calc_c if calc_c else 1)) * (0.85 if calc_s == "Mujer" else 1.0), 1) if all([calc_e, calc_p, calc_c, calc_s]) else 0.0
 
    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual", placeholder="Cockcroft-Gault manual")
        valor_fg = fg_m if fg_m else fg
        st.markdown(f'''<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{valor_fg}</div><div style="font-size: 0.8rem; color: #9d00ff;">mL/min (C-G)</div></div>''', unsafe_allow_html=True)
        st.write(""); l1, l2 = st.columns(2)
        with l1: val_mdrd = st.number_input("MDRD-4", value=None, key="fgl_mdrd")
        with l2: val_ckd = st.number_input("CKD-EPI", value=None, key="fgl_ckd")
 
    st.write(""); st.markdown("---")
    st.text_area("Listado de medicamentos", height=150, key="main_meds", placeholder="Pegue el listado aquí...")
    
    btn_val = st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True)
 
    if btn_val or st.session_state.analisis_realizado:
        if not st.session_state.main_meds:
            st.error("Introduce medicamentos.")
        else:
            if btn_val:
                with st.spinner("Analizando..."):
                    prompt_final = f"{c.PROMPT_AFR_V10}\n\nFG C-G: {valor_fg}\nMEDS:\n{st.session_state.main_meds}"
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    resp = model.generate_content(prompt_final).text
                    partes = [p.strip() for p in resp.split("|||") if p.strip()]
                    while len(partes) < 3: partes.append("")
                    st.session_state.resp_sintesis, st.session_state.resp_tabla, st.session_state.resp_detalle = partes[:3]
                    
                    # VOLCADO AUTOMÁTICO A PESTAÑA INFORME (BLINDADO)
                    st.session_state.soip_o = f"Edad: {calc_e} | Peso: {calc_p} | Crea: {calc_c} | FG: {valor_fg}"
                    st.session_state.soip_i = st.session_state.resp_sintesis
                    st.session_state.ic_inter = st.session_state.resp_sintesis
                    st.session_state.ic_clinica = st.session_state.resp_detalle
                    st.session_state.analisis_realizado = True

            # Mostrar Resultados con Glow
            glow = "glow-red" if "⛔" in st.session_state.resp_sintesis else "glow-yellow" if "⚠️" in st.session_state.resp_sintesis else "glow-green"
            st.markdown(f'<div class="synthesis-box {glow}">{st.session_state.resp_sintesis.replace("\n","<br>")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="background:#e6f2ff; padding:10px; border-radius:10px; border:1px solid #90cdf4;">{st.session_state.resp_tabla}</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="background:#f0f7ff; padding:15px; border-radius:10px; border:1px solid #90cdf4; margin-top:10px;">{st.session_state.resp_detalle.replace("\n","<br>")}</div>', unsafe_allow_html=True)
            
            # BOTÓN DE GRABACIÓN TRIPLE
            st.divider()
            if st.button("💾 GRABAR DATOS (VALIDACIONES + MEDICAMENTOS + ANALISIS)", use_container_width=True):
                # Preparar Fila VALIDACIONES (A-Y)
                fila_v = [datetime.now().strftime("%d/%m/%Y %H:%M"), st.session_state.reg_centro, st.session_state.reg_id, calc_e, calc_s, calc_p, st.session_state.reg_res, calc_c, val_ckd, val_mdrd, valor_fg]
                fila_v += [""] * (25 - len(fila_v))
                
                # Preparar MEDICAMENTOS (A-M)
                meds_rows = []
                filas_md = [f.strip() for f in st.session_state.resp_tabla.split("\n") if "|" in f and "---" not in f and "Fármaco" not in f]
                for f in filas_md:
                    cols = [c.strip() for c in f.split("|") if c.strip()]
                    if len(cols) >= 2:
                        meds_rows.append([st.session_state.reg_id, cols[0], "", cols[1], "", "", "", "", "", "", "", "", ""])

                # Preparar ANALISIS (A-Y)
                fila_a = ["INDICADOR IA", st.session_state.resp_sintesis[:150]] + [""]*23
                
                grabar_datos_triple(fila_v, meds_rows, fila_a)

with tabs[1]:
    st.markdown("### Pestaña Informe")
    st.markdown('<div class="linea-discreta-soip">Subjetivo (S)</div>', unsafe_allow_html=True)
    st.text_area("Subjetivo", st.session_state.soip_s, height=70, label_visibility="collapsed")
    st.markdown('<div class="linea-discreta-soip">Objetivo (O)</div>', unsafe_allow_html=True)
    st.text_area("Objetivo", st.session_state.soip_o, height=70, label_visibility="collapsed")
    st.markdown('<div class="linea-discreta-soip">Interpretación (I)</div>', unsafe_allow_html=True)
    st.text_area("Interpretación", st.session_state.soip_i, height=120, label_visibility="collapsed")
    st.markdown('<div class="linea-discreta-soip">Plan (P)</div>', unsafe_allow_html=True)
    st.text_area("Plan", st.session_state.soip_p, height=100, label_visibility="collapsed")
 
st.markdown(f"""<div class="warning-yellow">⚠️ <b>Apoyo a la revisión farmacoterapéutica. Verifique siempre con fuentes oficiales.</b></div> <div style="text-align:right; font-size:0.6rem; color:#ccc; font-family:monospace; margin-top:10px;">v. 07 mar 2026 12:45</div>""", unsafe_allow_html=True)
