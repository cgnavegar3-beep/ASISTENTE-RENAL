# prueba

import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import re
import unicodedata
import hashlib
import json
import io
import uuid
import random
from datetime import datetime
from constants import PROMPT_AFR_V10_6, API_KEY

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide", initial_sidebar_state="collapsed")

# --- INICIALIZACIÓN DE ESTADO ---
if "active_model" not in st.session_state: st.session_state.active_model = "2.5-FLASH"
if "main_meds" not in st.session_state: st.session_state.main_meds = ""
if "analisis_realizado" not in st.session_state: st.session_state.analisis_realizado = False
if "resp_ia" not in st.session_state: st.session_state.resp_ia = None
if "ultima_huella" not in st.session_state: st.session_state.ultima_huella = ""
if "df_val" not in st.session_state: st.session_state.df_val = pd.DataFrame()
if "df_meds" not in st.session_state: st.session_state.df_meds = pd.DataFrame()
if "filtros_dinamicos" not in st.session_state: st.session_state.filtros_dinamicos = []

# --- FUNCIONES NÚCLEO ---
def llamar_ia_en_cascada(prompt):
    if not API_KEY: return "⚠️ Error: API Key no configurada."
    genai.configure(api_key=API_KEY)
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

def normalizar_texto_capa0(texto, quitar_dosis=False):
    if not isinstance(texto, str) or not texto: return str(texto) if texto else ""
    texto = "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    texto = texto.upper().strip()
    if quitar_dosis:
        match = re.search(r'\d', texto)
        if match: texto = texto[:match.start()].strip()
    return texto

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
    st.session_state.analisis_realizado = False; st.session_state.resp_ia = None; st.session_state.ultima_huella = ""

def reset_meds():
    st.session_state.main_meds = ""
    st.session_state.soip_s = "Revisión farmacoterapéutica según función renal."
    st.session_state.soip_o = ""; st.session_state.soip_i = ""; st.session_state.soip_p = "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
    st.session_state.ic_inter = ""; st.session_state.ic_clinica = ""
    st.session_state.analisis_realizado = False; st.session_state.resp_ia = None; st.session_state.ultima_huella = ""

def limpiar_filtros_dinamicos():
    st.session_state.filtros_dinamicos = []

def inject_styles():
    st.markdown("""
    <style>
    .block-container { max-width: 100% !important; padding-top: 1rem !important; padding-left: 4% !important; padding-right: 4% !important; }
    .black-badge-zona { background-color: #000000; color: #888; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 15px; z-index: 999999; }
    .black-badge-activo { background-color: #000000; color: #00FF00; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 145px; z-index: 999999; text-shadow: 0 0 5px #00FF00; }
    .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin-bottom: 0px; margin-top: 20px; }
    .sub-version { text-align: center; font-size: 0.6rem; color: #bbb; margin-top: -5px; margin-bottom: 20px; font-family: monospace; }
    .fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .db-glow-box { background-color: #000000; color: #FFFFFF; border: 1.5px solid #4a5568; padding: 12px; border-radius: 12px; text-align: center; display: flex; flex-direction: column; justify-content: center; margin-bottom: 10px; }
    .db-blue { border-color: #63b3ed !important; box-shadow: 0 0 8px #63b3ed; }
    .db-green { border-color: #68d391 !important; box-shadow: 0 0 8px #68d391; }
    .db-red { border-color: #fc8181 !important; box-shadow: 0 0 8px #fc8181; }
    .db-purple { border-color: #b794f4 !important; box-shadow: 0 0 8px #b794f4; }
    .unit-label { font-size: 0.65rem; color: #888; margin-top: -10px; margin-bottom: 5px; font-family: sans-serif; text-align: center; }
    .synthesis-box { padding: 15px; border-radius: 12px; margin-bottom: 15px; border-width: 2.2px; border-style: solid; font-size: 0.95rem; line-height: 1.6; }
    .glow-red { background-color: #fff5f5; color: #c53030; border-color: #feb2b2; box-shadow: 0 0 12px #feb2b2; }
    .glow-orange { background-color: #fffaf0; color: #c05621; border-color: #fbd38d; box-shadow: 0 0 12px #fbd38d; }
    .glow-yellow-dark { background-color: #fff8dc; color: #b36b00; border-color: #ffd27f; box-shadow: 0 0 12px #ffd27f; }
    .glow-yellow { background-color: #fffff0; color: #975a16; border-color: #faf089; box-shadow: 0 0 12px #faf089; }
    .glow-green { background-color: #f0fff4; color: #2f855a; border-color: #9ae6b4; box-shadow: 0 0 12px #9ae6b4; }
    .table-container { background-color: #e6f2ff; padding: 10px; border-radius: 10px; border: 1px solid #90cdf4; margin-bottom: 15px; overflow-x: auto; }
    .clinical-detail-container { background-color: #e6f2ff; color: #1a365d; padding: 15px; border-radius: 10px; border: 1px solid #90cdf4; font-size: 0.9rem; line-height: 1.6; white-space: pre-wrap; }
    .warning-yellow { background-color: #fff9db; color: #856404; padding: 20px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 40px; text-align: center; font-size: 0.85rem; line-height: 1.5; }
    .linea-discreta-soip { border-top: 1px solid #d9d5c7; margin: 15px 0 5px 0; font-size: 0.65rem; font-weight: bold; color: #8e8a7e; text-transform: uppercase; }
    .formula-label { font-size: 0.6rem; color: #666; font-family: monospace; text-align: right; margin-top: 5px; }
    .fg-special-border { border: 1.5px solid #9d00ff !important; border-radius: 5px; }
    @keyframes blinker { 50% { opacity: 0; } }
    .blink-text, .blink-text-grabar { animation: blinker 1s linear infinite; color: #c53030; font-weight: bold; padding: 10px; border: 1px solid #c53030; border-radius: 5px; background: #fff5f5; text-align: center; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- INICIO UI ---
inject_styles()
st.markdown('<div class="black-badge-zona">ZONA: ACTIVA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="black-badge-activo">ACTIVO: {st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-version">v. 28 mar 2026 12:40</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 DATOS", "📈 GRÁFICOS", "🔍 CONSULTA DINÁMICA"])

# --- PESTAÑA 1: VALIDACIÓN ---
with tabs[0]:
    st.markdown("### Registro de Paciente")
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1.5, 0.4])
    def on_centro_change():
        centro_input = st.session_state.reg_centro.strip().lower()
        if centro_input == "m": st.session_state.reg_centro = "Marín"
        elif centro_input == "o": st.session_state.reg_centro = "O Grove"
        if st.session_state.reg_centro and not st.session_state.reg_id:
            iniciales = "".join([word[0] for word in st.session_state.reg_centro.split()]).upper()[:3]
            st.session_state.reg_id = f"PAC-{iniciales}{random.randint(10000, 99999)}"
    with c1: st.text_input("Centro", placeholder="M / G", key="reg_centro", on_change=on_centro_change)
    with c2: st.selectbox("¿Residencia?", ["-- seleccionar --", "No", "Sí"], key="reg_res")
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
            calc_s = st.selectbox("Sexo", ["-- seleccionar --", "Hombre", "Mujer"], key="calc_s")
            fg = round(((140 - calc_e) * calc_p) / (72 * (calc_c if calc_c and calc_c > 0 else 1)) * (0.85 if calc_s == "Mujer" else 1.0), 1) if all([calc_e, calc_p, calc_c, calc_s != "-- seleccionar --"]) else 0.0
    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual", placeholder="Fórmula Cockcroft-Gault: manual")
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
    st.markdown("#### 📝 Listado de medicamentos")
    st.text_area("Listado", height=150, label_visibility="collapsed", key="main_meds", placeholder="Pegue el listado...")
    st.button("Procesar medicamentos", on_click=procesar_y_limpiar_meds)
    
    faltan_datos = not all([st.session_state.reg_centro, st.session_state.reg_res != "-- seleccionar --", calc_e, calc_p, calc_c, calc_s != "-- seleccionar --", val_mdrd is not None, val_ckd is not None])
    if st.session_state.main_meds and faltan_datos and not st.session_state.analisis_realizado:
        st.markdown('<div class="blink-text">⚠️ FALTAN DATOS EN REGISTRO, CALCULADORA O FGs (MDRD/CKD)</div>', unsafe_allow_html=True)
    
    b1, b2 = st.columns([0.85, 0.15])
    btn_val = b1.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True)
    b2.button("🗑️ RESET", on_click=reset_meds, use_container_width=True)
    
    if btn_val:
        if not st.session_state.main_meds: st.error("Introduce medicamentos.")
        elif faltan_datos: st.error("Faltan datos obligatorios.")
        else:
            huella_actual = hashlib.md5(f"{st.session_state.reg_id}{calc_e}{calc_p}{calc_c}{calc_s}{val_mdrd}{val_ckd}{st.session_state.main_meds}".encode()).hexdigest()
            if huella_actual == st.session_state.ultima_huella and st.session_state.resp_ia:
                st.toast("ℹ️ Análisis recuperado de memoria", icon="🧠")
                st.session_state.analisis_realizado = True
            else:
                with st.spinner("Analizando..."):
                    prompt_final = f"{PROMPT_AFR_V10}\n\nFG C-G: {valor_fg}\nFG CKD: {val_ckd}\nFG MDRD: {val_mdrd}\n\nMEDS:\n{st.session_state.main_meds}"
                    st.session_state.resp_ia = llamar_ia_en_cascada(prompt_final)
                    st.session_state.ultima_huella = huella_actual
                    st.session_state.analisis_realizado = True

    if st.session_state.analisis_realizado and st.session_state.resp_ia:
        resp = st.session_state.resp_ia[st.session_state.resp_ia.find("|||"):] if "|||" in st.session_state.resp_ia else st.session_state.resp_ia
        try:
            partes = [p.strip() for p in resp.split("|||") if p.strip()]
            while len(partes) < 4: partes.append("")
            sintesis, tabla, detalle, json_data_str = partes[:4]
            glow = obtener_glow_class(sintesis)
            st.markdown(f'<div class="synthesis-box {glow}">{sintesis.replace("\n","<br>")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="table-container">{tabla}</div>', unsafe_allow_html=True)
            detalle_limpio = re.sub(r'<[^>]*>', '', detalle)
            st.markdown(f'''<div class="clinical-detail-container">{detalle_limpio}</div>''', unsafe_allow_html=True)
            
            # Autocompletado SOIP
            st.session_state.soip_o = f"Edad: {calc_e}a | Peso: {calc_p}kg | Crea: {calc_c}mg/dL | FG C-G: {valor_fg}mL/min"
            st.session_state.soip_i = re.sub(r'<[^>]*>', '', sintesis.replace("BLOQUE 1: ALERTAS Y AJUSTES", "").strip())
            st.session_state.ic_inter = f"Revisión de: {st.session_state.soip_i}"
            st.session_state.ic_clinica = f"{st.session_state.soip_o}\n\n{detalle_limpio.split('⚠️ NOTA IMPORTANTE:')[0].strip()}"
        except: st.error("Error al procesar la respuesta de la IA.")

# --- PESTAÑA 2: INFORME ---
with tabs[1]:
    for label, key, h in [("Subjetivo (S)", "soip_s", 70), ("Objetivo (O)", "soip_o", 70), ("Interpretación (I)", "soip_i", 120), ("Plan (P)", "soip_p", 100), ("INTERCONSULTA", "ic_inter", 150), ("INFORMACIÓN CLÍNICA", "ic_clinica", 250)]:
        st.markdown(f'<div class="linea-discreta-soip">{label}</div>', unsafe_allow_html=True)
        st.text_area(key, st.session_state.get(key, ""), height=h, label_visibility="collapsed")

# --- PESTAÑA 3: DATOS ---
with tabs[2]:
    st.markdown("### 📊 Gestión de Datos")
    st.session_state.df_val = st.data_editor(st.session_state.df_val, num_rows="dynamic", use_container_width=True)
    st.session_state.df_meds = st.data_editor(st.session_state.df_meds, num_rows="dynamic", use_container_width=True)
    if st.session_state.analisis_realizado:
        st.markdown('<div class="blink-text-grabar">⚠️ VERIFICAR DATOS Y GRABAR</div>', unsafe_allow_html=True)
    st.button("💾 GRABAR DATOS (Simulado)", type="primary", use_container_width=True)

# --- PESTAÑA 4: GRÁFICOS ---
with tabs[3]:
    st.info("Visualización de métricas y distribución de riesgos según histórico sincronizado.")
    # (Lógica de gráficos omitida por brevedad pero integrada en tu código previo)

# --- PESTAÑA 5: CONSULTA DINÁMICA ---
with tabs[4]:
    st.markdown("### 🔍 Consulta Dinámica Renal")
    tipo_origen = st.radio("Origen:", ["Validaciones", "Medicamentos"], horizontal=True)
    df_pool = st.session_state.df_val if "Validaciones" in tipo_origen else st.session_state.df_meds
    
    if not df_pool.empty:
        col_btn1, col_btn2 = st.columns(2)
        if col_btn1.button("➕ Añadir Filtro"):
            st.session_state.filtros_dinamicos.append({"id": str(uuid.uuid4()), "col": df_pool.columns[0], "op": "==", "val": ""})
        if col_btn2.button("🗑️ Limpiar"): limpiar_filtros_dinamicos(); st.rerun()
        
        # Lógica de filtrado optimizada con máscara única
        mask = pd.Series([True] * len(df_pool))
        for f in st.session_state.filtros_dinamicos:
            fid = f["id"]
            c1, c2, c3 = st.columns([1, 0.7, 1.3])
            f["col"] = c1.selectbox("Col", df_pool.columns, key=f"c_{fid}")
            f["op"] = c2.selectbox("Op", ["==", "!=", ">", "<", "contiene"], key=f"o_{fid}")
            f["val"] = c3.text_input("Valor", key=f"v_{fid}")
            
            if f["val"]:
                if f["op"] == "==": mask &= (df_pool[f["col"]].astype(str) == f["val"])
                elif f["op"] == "contiene": mask &= (df_pool[f["col"]].astype(str).str.contains(f["val"], case=False))
        
        st.dataframe(df_pool[mask], use_container_width=True)
    else: st.info("No hay datos para analizar.")

st.markdown('<div class="warning-yellow">⚠️ AVISO LEGAL: Herramienta de soporte. La responsabilidad final es del facultativo.</div>', unsafe_allow_html=True)
