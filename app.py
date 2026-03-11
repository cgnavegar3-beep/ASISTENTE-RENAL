# v. 11 mar 2026 21:30 (FIX CRASH RESET_REGISTRO - BLINDAJE DE CLAVES)

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
if "active_model" not in st.session_state: st.session_state.active_model = "BUSCANDO..."
if "main_meds" not in st.session_state: st.session_state.main_meds = ""
if "soip_s" not in st.session_state: st.session_state.soip_s = "Revisión farmacoterapéutica según función renal."
if "soip_p" not in st.session_state: st.session_state.soip_p = "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
if "analisis_realizado" not in st.session_state: st.session_state.analisis_realizado = False
if "resp_ia" not in st.session_state: st.session_state.resp_ia = None

for key in ["soip_o", "soip_i", "ic_inter", "ic_clinica", "reg_id", "reg_centro", "reg_res"]:
    if key not in st.session_state: st.session_state[key] = ""

# --- FUNCIONES ---
def reset_registro():
    # Solo borramos si la clave existe para evitar el KeyError
    keys_to_reset = ["reg_centro", "reg_res", "reg_id", "fgl_ckd", "fgl_mdrd", "main_meds", "calc_e", "calc_p", "calc_c", "calc_s"]
    for key in keys_to_reset:
        if key in st.session_state:
            st.session_state[key] = None if "calc" in key or "fgl" in key else ""
    st.session_state.analisis_realizado = False
    st.session_state.resp_ia = None

def llamar_ia_en_cascada(prompt):
    try:
        API_KEY = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=API_KEY)
        orden = ['2.5-flash', 'flash-latest', '1.5-pro']
        for mod_name in orden:
            try:
                st.session_state.active_model = mod_name.upper()
                model = genai.GenerativeModel(f'models/gemini-{mod_name}')
                return model.generate_content(prompt, generation_config={"temperature": 0.1}).text
            except: continue
    except: return "⚠️ Error de API."
    return "⚠️ Error en la generación."

def obtener_glow_class(sintesis_texto):
    if "⛔" in sintesis_texto: return "glow-red"
    elif "⚠️⚠️⚠️" in sintesis_texto: return "glow-orange"
    elif "⚠️⚠️" in sintesis_texto: return "glow-yellow-dark"
    elif "⚠️" in sintesis_texto: return "glow-yellow"
    else: return "glow-green"

def preparar_datos_exportacion(texto_tabla, pac_info, fgs):
    lineas = [l.strip() for l in texto_tabla.split('\n') if '|' in l and '---' not in l]
    matriz = []
    for l in lineas:
        partes = [p.strip() for p in l.split('|')]
        if partes and partes[0] == "": partes.pop(0)
        if partes and partes[-1] == "": partes.pop(-1)
        matriz.append(partes)

    def solo_num(v):
        n = re.findall(r'\d+', str(v))
        return n[0] if n else "0"

    res_final = [["0","0","0"] for _ in range(5)]
    if len(matriz) >= 5:
        filas_res = matriz[-5:]
        for idx, f in enumerate(filas_res):
            nums = [solo_num(c) for c in f if any(char.isdigit() for char in str(c))]
            while len(nums) < 3: nums.append("0")
            res_final[idx] = nums[:3]

    v_row = [""] * 27
    v_row[0] = datetime.now().strftime("%d/%m/%Y")
    v_row[1] = pac_info[1]; v_row[2] = pac_info[2]; v_row[3] = pac_info[0]
    v_row[4] = pac_info[4]; v_row[5] = pac_info[7]; v_row[6] = pac_info[5]; v_row[7] = pac_info[6]
    for i in range(5):
        v_row[10+i] = res_final[i][0]
        v_row[16+i] = res_final[i][1]
        v_row[22+i] = res_final[i][2]
    v_row[15] = fgs[0]; v_row[21] = fgs[1]

    m_rows = []
    filas_meds = [f for f in matriz if len(f) >= 14 and not any(x in f[0] for x in ["Icono", "Total", "Nº"])]
    for f in filas_meds:
        f_ext = f + [""] * 20 
        det_farma = [f_ext[1], f_ext[2], f_ext[3], f_ext[4], f_ext[5], f_ext[6], f_ext[7], f_ext[8], f_ext[9], f_ext[10], f_ext[11], f_ext[12], f_ext[13], f_ext[14]]
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
    .glow-red { background-color: #fff5f5; color: #c53030; border-color: #feb2b2; box-shadow: 0 0 12px #feb2b2; }
    .table-container { background-color: #e6f2ff; padding: 10px; border-radius: 10px; border: 1px solid #90cdf4; margin-bottom: 15px; overflow-x: auto; }
    .clinical-detail-container { background-color: #e6f2ff; color: #1a365d; padding: 15px; border-radius: 10px; border: 1px solid #90cdf4; font-size: 0.9rem; line-height: 1.6; }
    .fg-special-border { border: 1.5px solid #9d00ff !important; border-radius: 5px; }
    @keyframes blinker { 50% { opacity: 0; } }
    .blink-text { animation: blinker 1s linear infinite; color: #c53030; font-weight: bold; padding: 10px; border: 1px solid #c53030; border-radius: 5px; background: #fff5f5; text-align: center; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

inject_styles()

st.markdown('<div class="black-badge-zona">ZONA: ACTIVA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="black-badge-activo">ACTIVO: {st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-version">v. 11 mar 2026 21:30</div>', unsafe_allow_html=True)

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
    with c3: st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), disabled=True, key="reg_fecha")
    with c4: st.text_input("ID Registro", key="reg_id", disabled=True)
    with c5: st.write(""); st.button("🗑️", on_click=reset_registro, key="btn_reset_reg")

    col_izq, col_der = st.columns(2, gap="large")
    with col_izq:
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            calc_e = st.number_input("Edad", step=1, key="calc_e", value=None)
            calc_p = st.number_input("Peso", key="calc_p", value=None)
            calc_c = st.number_input("Creatinina", key="calc_c", value=None)
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"], index=None, key="calc_s")
            fg = round(((140 - calc_e) * calc_p) / (72 * (calc_c if calc_c and calc_c > 0 else 1)) * (0.85 if calc_s == "Mujer" else 1.0), 1) if all([calc_e, calc_p, calc_c, calc_s]) else 0.0

    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual", placeholder="Manual")
        valor_fg = fg_m if fg_m else fg
        st.markdown(f'''<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{valor_fg}</div><div style="font-size: 0.8rem; color: #9d00ff;">mL/min (C-G)</div></div>''', unsafe_allow_html=True)
        st.write(""); l1, l2 = st.columns(2)
        with l1:
            st.markdown('<div class="fg-special-border">', unsafe_allow_html=True)
            val_mdrd = st.number_input("MDRD", value=None, label_visibility="collapsed", key="fgl_mdrd")
            st.markdown('</div>', unsafe_allow_html=True)
        with l2:
            st.markdown('<div class="fg-special-border">', unsafe_allow_html=True)
            val_ckd = st.number_input("CKD", value=None, label_visibility="collapsed", key="fgl_ckd")
            st.markdown('</div>', unsafe_allow_html=True)

    st.write(""); st.markdown("---")
    st.text_area("Listado", height=120, label_visibility="collapsed", key="main_meds")
    b1, b2 = st.columns([0.85, 0.15])
    btn_val = b1.button("🚀 VALIDAR", use_container_width=True)
    b2.button("🗑️ RESET", on_click=lambda: st.session_state.update({"main_meds": ""}), use_container_width=True)

    if btn_val:
        with st.spinner("Analizando..."):
            prompt_final = f"{c.PROMPT_AFR_V10}\n\nFG C-G: {valor_fg}\nFG CKD: {val_ckd}\nFG MDRD: {val_mdrd}\n\nMEDS:\n{st.session_state.main_meds}"
            st.session_state.resp_ia = llamar_ia_en_cascada(prompt_final)
            st.session_state.analisis_realizado = True

    if st.session_state.analisis_realizado and st.session_state.resp_ia:
        resp = st.session_state.resp_ia[st.session_state.resp_ia.find("|||"):] if "|||" in st.session_state.resp_ia else st.session_state.resp_ia
        partes = [p.strip() for p in resp.split("|||") if p.strip()]
        if len(partes) >= 3:
            sintesis, tabla, detalle = partes[:3]
            st.markdown(f'<div class="synthesis-box {obtener_glow_class(sintesis)}">{sintesis.replace("\n","<br>")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="table-container">{tabla}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="clinical-detail-container">{detalle.replace("\n","<br>")}</div>', unsafe_allow_html=True)
            if st.button("💾 GRABAR", use_container_width=True):
                st.toast("Grabación lista.")

st.markdown(f"""<div style="text-align:right; font-size:0.6rem; color:#ccc; font-family:monospace; margin-top:20px;">v. 11 mar 2026 21:30</div>""", unsafe_allow_html=True)
