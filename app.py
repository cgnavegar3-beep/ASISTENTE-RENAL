# v. 08 mar 2026 17:15 (CONTROL DE INTEGRIDAD INTERNO: TOTALMENTE BLINDADO)

import streamlit as st
import pandas as pd
import io
from datetime import datetime
import google.generativeai as genai
import random
import re
import os
import constants as c 
from streamlit_gsheets import GSheetsConnection

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
#       "qué", "por qué" y "cómo". Esperar aprobación explícita ("adelante").
# 6. COMPROMISO DE RIGOR: Gemini verificará el cumplimiento de estos 
#       principios antes y después de cada cambio. No se simplifican líneas.
# 7. VERSIONADO LOCAL: Registrar la versión en la esquina inferior derecha.
# 8. CONTADOR DISCRETO: El contador de intentos debe ser discreto y 
#       ubicarse en la esquina superior izquierda (estilo v. 2.5).
# 9. INTEGRIDAD DEL CÓDIGO: Nunca omitir estas líneas; de lo contrario, 
#       se considerará pérdida de principios.
# 10. BLINDAJE DE CONTENIDOS: Quedan blindados todos los cuadros de texto,
#        sus textos flotantes (placeholders) y los textos predefinidos en las
#        secciones S, P e INTERCONSULTA. Prohibido borrarlos o simplificarlos.
# 11. AVISO PARPADEANTE: El aviso parpadeante ante falta de datos es un 
#        principio blindado; es informativo y no debe impedir la validación.
# =================================================================

st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

# --- INICIALIZACIÓN ---
if "active_model" not in st.session_state: st.session_state.active_model = "BUSCANDO..."
if "main_meds" not in st.session_state: st.session_state.main_meds = ""
if "resultado_ia" not in st.session_state: st.session_state.resultado_ia = None
if "soip_s" not in st.session_state: st.session_state.soip_s = "Revisión farmacoterapéutica según función renal."
if "soip_p" not in st.session_state: st.session_state.soip_p = "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."

for key in ["soip_o", "soip_i", "ic_inter", "ic_clinica", "reg_id", "reg_centro", "reg_res"]:
    if key not in st.session_state: st.session_state[key] = ""

# --- CONFIGURACIÓN IA ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    API_KEY = None
    st.sidebar.error("API Key no encontrada.")

# --- FUNCIONES RESTAURADAS ---
def obtener_glow_class(sintesis_texto):
    if "⛔" in sintesis_texto: return "glow-red"
    elif "⚠️⚠️⚠️" in sintesis_texto: return "glow-orange"
    elif "⚠️⚠️" in sintesis_texto: return "glow-yellow-dark"
    elif "⚠️" in sintesis_texto: return "glow-yellow"
    else: return "glow-green"

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

def parsear_tabla_ia(html_tabla):
    filas = re.findall(r'<tr>(.*?)</tr>', html_tabla, re.DOTALL)
    lista_farmacos = []
    for fila in filas[1:]:
        celdas = re.findall(r'<td.*?>(.*?)</td>', fila, re.DOTALL)
        if len(celdas) >= 12:
            clean = [re.sub(r'<.*?>', '', c).strip() for c in celdas]
            lista_farmacos.append(clean)
    return lista_farmacos

def procesar_conteos_exactos(lista_farmacos):
    conteo = {
        "CG": {"1":0, "2":0, "3":0, "4":0},
        "MDRD": {"1":0, "2":0, "3":0, "4":0},
        "CKD": {"1":0, "2":0, "3":0, "4":0}
    }
    for f in lista_farmacos:
        for idx, key in zip([5, 8, 11], ["CG", "MDRD", "CKD"]):
            val = f[idx].lower()
            if "4" in val or "crítico" in val: conteo[key]["4"] += 1
            elif "3" in val or "grave" in val: conteo[key]["3"] += 1
            elif "2" in val or "moderado" in val: conteo[key]["2"] += 1
            elif "1" in val or "leve" in val: conteo[key]["1"] += 1
    return conteo

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
    .nota-importante-box { border-top: 2px dashed #0057b8; margin-top: 15px; padding-top: 12px; font-size: 0.85rem; color: #1a365d; }
    .nota-item { margin-bottom: 4px; font-weight: 500; }
    @keyframes blinker { 50% { opacity: 0; } }
    .blink-text { animation: blinker 1s linear infinite; color: #c53030; font-weight: bold; padding: 10px; border: 1px solid #c53030; border-radius: 5px; background: #fff5f5; text-align: center; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

inject_styles()
st.markdown('<div class="black-badge-zona">ZONA: ACTIVA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="black-badge-activo">ACTIVO: {st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-version">v. 08 mar 2026 17:15</div>', unsafe_allow_html=True)

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
    with c3: st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), disabled=True, placeholder="Fecha")
    with c4: st.text_input("ID Registro", key="reg_id", disabled=True)
    with c5: st.write(""); st.button("🗑️", key="btn_reset_reg")

    col_izq, col_der = st.columns(2, gap="large")
    with col_izq:
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            calc_e = st.number_input("Edad (años)", step=1, key="calc_e", placeholder="Edad (Ej: 65)", value=None)
            calc_p = st.number_input("Peso (kg)", key="calc_p", placeholder="Peso (Ej: 70.5)", value=None)
            calc_c = st.number_input("Creatinina (mg/dL)", key="calc_c", placeholder="Creatinina (Ej: 1.2)", value=None)
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"], index=None, placeholder="Seleccionar sexo...", key="calc_s")
            fg = round(((140 - calc_e) * calc_p) / (72 * (calc_c if calc_c and calc_c > 0 else 1)) * (0.85 if calc_s == "Mujer" else 1.0), 1) if all([calc_e, calc_p, calc_c, calc_s]) else 0.0

    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual", placeholder="Fórmula Cockcroft-Gault: entrada manual")
        valor_fg = fg_m if fg_m else fg
        st.markdown(f'''<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{valor_fg}</div><div style="font-size: 0.8rem; color: #9d00ff;">mL/min (C-G)</div></div>''', unsafe_allow_html=True)
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
    st.text_area("Listado", height=150, label_visibility="collapsed", key="main_meds", placeholder="Pegue el listado de fármacos aquí...")
    
    b1, b2, b3 = st.columns([0.70, 0.15, 0.15])
    if b1.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True):
        if not st.session_state.main_meds: st.error("Introduce medicamentos.")
        else:
            with st.spinner("Analizando..."):
                prompt_final = f"{c.PROMPT_AFR_V10}\n\nFG C-G: {valor_fg}\nFG CKD: {val_ckd}\nFG MDRD: {val_mdrd}\n\nMEDS:\n{st.session_state.main_meds}"
                resp_raw = llamar_ia_en_cascada(prompt_final)
                st.session_state.resultado_ia = resp_raw[resp_raw.find("|||"):] if "|||" in resp_raw else resp_raw
                partes = [p.strip() for p in st.session_state.resultado_ia.split("|||") if p.strip()]
                if len(partes) >= 3:
                    sintesis, tabla, detalle = partes[:3]
                    st.session_state.soip_o = f"Edad: {calc_e}a | Peso: {calc_p}kg | Crea: {calc_c}mg/dL | FG: {valor_fg}mL/min"
                    st.session_state.soip_i = sintesis.replace("BLOQUE 1: ALERTAS Y AJUSTES", "").strip()
                    st.session_state.ic_inter = f"Se solicita revisión de los siguientes fármacos:\n{st.session_state.soip_i}"
                    st.session_state.ic_clinica = f"{st.session_state.soip_o}\n\n{detalle.split('⚠️ NOTA IMPORTANTE:')[0].replace('BLOQUE 3: ANALISIS CLINICO', '').strip()}"

    if b2.button("📥 GUARDAR", use_container_width=True):
        if st.session_state.resultado_ia:
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                partes = [p.strip() for p in st.session_state.resultado_ia.split("|||") if p.strip()]
                lista_farmacos = parsear_tabla_ia(partes[1])
                res_conteos = procesar_conteos_exactos(lista_farmacos)

                # 1. PESTAÑA VALIDACIONES
                df_val_nueva = pd.DataFrame([{
                    "FECHA": datetime.now().strftime("%d/%m/%Y"), "CENTRO": st.session_state.reg_centro, 
                    "RESIDENCIA": st.session_state.reg_res, "ID_REGISTRO": st.session_state.reg_id,
                    "EDAD": calc_e, "SEXO": calc_s, "PESO": calc_p, "CREATININA": calc_c,
                    "TOTAL_MEDS_PAC": len([l for l in st.session_state.main_meds.split('\n') if l.strip()]),
                    "FG_CG": valor_fg, "TOT_AFEC_CG": sum(res_conteos["CG"].values()), "PRECAU_CG": res_conteos["CG"]["1"], "AJUSTE_DOS_CG": res_conteos["CG"]["2"], "TOXICID_CG": res_conteos["CG"]["3"], "CONTRAIND_CG": res_conteos["CG"]["4"],
                    "FG_MDRD": val_mdrd, "TOT_AFEC_MDRD": sum(res_conteos["MDRD"].values()), "PRECAU_MDRD": res_conteos["MDRD"]["1"], "AJUSTE_DOS_MDRD": res_conteos["MDRD"]["2"], "TOXICID_MDRD": res_conteos["MDRD"]["3"], "CONTRAIND_MDRD": res_conteos["MDRD"]["4"],
                    "FG_CKD": val_ckd, "TOT_AFEC_CKD": sum(res_conteos["CKD"].values()), "PRECAU_CKD": res_conteos["CKD"]["1"], "AJUSTE_DOS_CKD": res_conteos["CKD"]["2"], "TOXICID_CKD": res_conteos["CKD"]["3"], "CONTRAIND_CKD": res_conteos["CKD"]["4"],
                    "ACEPTACION_MEDICO_GOBAL": ""
                }])
                conn.update(worksheet="VALIDACIONES", data=pd.concat([conn.read(worksheet="VALIDACIONES"), df_val_nueva], ignore_index=True))

                # 2. PESTAÑA MEDICAMENTOS (Columnas A a P)
                if lista_
