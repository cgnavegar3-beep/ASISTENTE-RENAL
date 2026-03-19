# v. 19 mar 2026 09:30 (CAPA DE VERIFICACIÓN DE VOLCADO GS)
 
import streamlit as st
import pandas as pd
import io
from datetime import datetime
import google.generativeai as genai
import random
import re
import os
import json
import constants as c 
 
# --- NUEVAS LIBRERÍAS PARA GOOGLE SHEETS & SERIALIZACIÓN ---
import gspread
from google.oauth2.service_account import Credentials
import time
import math
 
# MÓDULO DE EVOLUCIÓN - NO AFECTA NÚCLEO (IMPORTACIONES VISUALIZACIÓN)
import plotly.express as px
import plotly.graph_objects as go
 
# =================================================================
# PRINCIPIOS FUNDAMENTALES (ESCRITOS DE PE A PA - PROHIBIDO ELIMINAR)
# =================================================================
# 1. IDENTIDAD: El nombre "ASISTENTE RENAL" es inalterable.
# 2. VERSIÓN: Mostrar siempre la versión con fecha/hora bajo el título.
# 3. INTERFAZ DUAL PROTEGIDA: Prohibido modificar la "Calculadora" y el 
#                       "Filtrado Glomerular" (cuadro negro con glow morado).
# 4. BLINDAJE DE ELEMENTOS (ZONA ESTÁTICA):
#                       - Cuadros negros superiores (ZONA y ACTIVO).
#                       - Pestañas (Tabs) de navegación.
#                       - Registro de Paciente: Estructura y función de fila única.
#                       - Estructura del área de recorte y listado de medicación.
#                       - Barra dual de validación (VALIDAR / RESET).
#                       - Aviso legal amarillo inferior (Warning).
# 5. PROTOCOLO DE CAMBIOS: Antes de cualquier evolución técnica, explicar
#                    "qué", "por qué" y "cómo". Esperar aprobación explícita ("adelante").
# 6. COMPROMISO DE RIGOR: Gemini verificará el cumplimiento de estos 
#                    principios antes y después de cada cambio. No se simplifican líneas.
# 7. VERSIONADO LOCAL: Registrar la versión en la esquina inferior derecha.
# 8. CONTADOR DISCRETO: El contador de intentos debe ser discreto y 
#                    ubicarse en la esquina superior izquierda (estilo v. 2.5).
# 9. INTEGRIDAD DEL CÓDIGO: Nunca omitir estas líneas; de lo contrario, 
#                       se considerará pérdida de principios.
# 10. BLINDAJE DE CONTENIDOS: Quedan blindados todos los cuadros de texto,
#                       sus textos flotantes (placeholders) and los textos predefinidos en las
#                       secciones S, P e INTERCONSULTA. Prohibido borrarlos o simplificarlos.
# 11. AVISO PARPADEANTE: El aviso parpadeante ante falta de datos es un 
#                       principio blindado; es informativo y no debe impedir la validación.
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
 
if "df_val" not in st.session_state:
   st.session_state.df_val = pd.DataFrame()
if "df_meds" not in st.session_state:
    st.session_state.df_meds = pd.DataFrame()
 
# --- NUEVOS ESTADOS PARA ESPEJO NUBE ---
if "df_sync_val" not in st.session_state:
   st.session_state["df_sync_val"] = pd.DataFrame()
if "df_sync_meds" not in st.session_state:
   st.session_state["df_sync_meds"] = pd.DataFrame()
if "df_sync_analisis" not in st.session_state:
   st.session_state["df_sync_analisis"] = pd.DataFrame()
 
for key in ["soip_o", "soip_i", "ic_inter", "ic_clinica", "reg_id", "reg_centro", "reg_res"]:
    if key not in st.session_state: st.session_state[key] = ""
 
# --- CONFIGURACIÓN IA ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    API_KEY = None
    st.sidebar.error("API Key no encontrada.")
 
# --- FUNCIONES DE PERSISTENCIA SEGURA (GOOGLE SHEETS) ---
def conectar_google_sheets():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["GOOGLE_SHEET_ID"])
 
def sincronizar_desde_nube():
    try:
        doc = conectar_google_sheets()
        ws_val = doc.worksheet("VALIDACIONES")
        ws_meds = doc.worksheet("MEDICAMENTOS")
        ws_anal = doc.worksheet("ANALISIS")
        raw_val = ws_val.get_all_records()
        raw_meds = ws_meds.get_all_records()
        raw_anal = ws_anal.get_all_records()
 
        def limpiar_decimales(lista_dicts):
            for d in lista_dicts:
                for k, v in d.items():
                    if isinstance(v, str) and "," in v:
                        clean_v = v.replace(",", ".")
                        try: d[k] = float(clean_v)
                        except ValueError: pass 
            return lista_dicts
 
        st.session_state["df_sync_val"] = pd.DataFrame(limpiar_decimales(raw_val))
        st.session_state["df_sync_meds"] = pd.DataFrame(limpiar_decimales(raw_meds))
        st.session_state["df_sync_analisis"] = pd.DataFrame(limpiar_decimales(raw_anal))
        st.toast("✅ Nube sincronizada", icon="🔄")
    except Exception as e:
        st.error(f"❌ Error al sincronizar: {e}")
 
if st.session_state["df_sync_val"].empty:
    sincronizar_desde_nube()
 
def acquire_lock(sheet_obj):
    try:
        ws_lock = sheet_obj.worksheet("LOCK")
    except gspread.exceptions.WorksheetNotFound:
        ws_lock = sheet_obj.add_worksheet(title="LOCK", rows=2, cols=2)
    lock_val = ws_lock.acell("A1").value
    if lock_val: return False
    ws_lock.update_acell("A1", f"LOCKED_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    return True
 
def release_lock(sheet_obj):
    try:
        ws_lock = sheet_obj.worksheet("LOCK")
        ws_lock.update_acell("A1", "")
    except: pass
 
def guardar_en_google_sheets(df_val_actual, df_meds_actual):
    try:
        doc = conectar_google_sheets()
        intentos = 0
        while not acquire_lock(doc) and intentos < 5:
            time.sleep(2); intentos += 1
        if intentos >= 5: return
 
        id_actual = st.session_state.reg_id
        ws_val = doc.worksheet("VALIDACIONES")
        ids_existentes = ws_val.col_values(4) 
        
        # --- BLOQUE DE VERIFICACIÓN (CAPA DIAGNÓSTICA) ---
        st.write("ID actual:", id_actual)
        st.write("IDs existentes:", ids_existentes[:10])
        st.write("df_val_actual shape:", df_val_actual.shape)

        df_filtrado = df_val_actual[df_val_actual["ID_REGISTRO"] == id_actual]

        st.write("Filtrado filas:", df_filtrado.shape)

        if not df_filtrado.empty:
            fila_val = df_filtrado.iloc[-1].to_dict()
            st.write("Fila a insertar:", fila_val)
        else:
            st.warning("❌ No se encontró fila para este ID_REGISTRO")
        # --- FIN BLOQUE DE VERIFICACIÓN ---

        if id_actual not in ids_existentes:
            if not df_filtrado.empty:
                fila_val = df_filtrado.iloc[-1].fillna("").to_dict()
                fila_val_convertida = [v.item() if hasattr(v, "item") else "" if isinstance(v, float) and math.isnan(v) else v for v in fila_val.values()]
                ws_val.append_row(fila_val_convertida)
 
        ws_meds = doc.worksheet("MEDICAMENTOS")
        data_meds_nube = ws_meds.get_all_records()
        df_nube_meds = pd.DataFrame(data_meds_nube)
        meds_a_procesar = df_meds_actual[df_meds_actual["ID_REGISTRO"] == id_actual].fillna("")
        
        filas_nuevas = []
        for _, fila in meds_a_procesar.iterrows():
            ya_existe = False
            if not df_nube_meds.empty:
                existe = df_nube_meds[(df_nube_meds["ID_REGISTRO"] == id_actual) & (df_nube_meds["MEDICAMENTO"] == fila["MEDICAMENTO"])]
                if not existe.empty: ya_existe = True
            if not ya_existe:
                fila_conv = [v.item() if hasattr(v, "item") else v for v in fila.values.tolist()]
                filas_nuevas.append(fila_conv)
        if filas_nuevas: ws_meds.append_rows(filas_nuevas)
        release_lock(doc)
    except:
        try: release_lock(doc)
        except: pass
 
# --- FUNCIONES NÚCLEO ---
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
        if key in st.session_state:
            st.session_state[key] = None
    st.session_state.analisis_realizado = False; st.session_state.resp_ia = None
 
def reset_meds():
    st.session_state.main_meds = ""
    st.session_state.soip_s = "Revisión farmacoterapéutica según función renal."
    st.session_state.soip_o = ""; st.session_state.soip_i = ""; st.session_state.soip_p = "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
    st.session_state.ic_inter = ""; st.session_state.ic_clinica = ""
    st.session_state.analisis_realizado = False; st.session_state.resp_ia = None
 
def inject_styles():
    st.markdown("""
    <style>
    .block-container { max-width: 100% !important; padding-top: 1rem !important; padding-left: 4% !important; padding-right: 4% !important; }
    .black-badge-zona { background-color: #000000; color: #888; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 15px; z-index: 999999; }
    .black-badge-activo { background-color: #000000; color: #00FF00; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 145px; z-index: 999999; text-shadow: 0 0 5px #00FF00; }
    .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin-bottom: 0px; margin-top: 20px; }
    .sub-version { text-align: center; font-size: 0.6rem; color: #bbb; margin-top: -5px; margin-bottom: 20px; font-family: monospace; }
    .fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .db-glow-box { background-color: #000000; color: #FFFFFF; border: 1.5px solid #4a5568; box-shadow: 0 0 10px #2d3748; padding: 12px; border-radius: 12px; text-align: center; display: flex; flex-direction: column; justify-content: center; margin-bottom: 10px; }
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
 
inject_styles()
st.markdown('<div class="black-badge-zona">ZONA: ACTIVA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="black-badge-activo">ACTIVO: {st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-version">v. 19 mar 2026 09:30</div>', unsafe_allow_html=True)
 
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
            calc_e = st.number_input("Edad (años)", step=1, key="calc_e", placeholder="Edad (Ej: 65)", value=None)
            calc_p = st.number_input("Peso (kg)", key="calc_p", placeholder="Peso (Ej: 70.5)", value=None)
            calc_c = st.number_input("Creatinina (mg/dL)", key="calc_c", placeholder="Creatinina (Ej: 1.2)", value=None)
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"], index=None, placeholder="Seleccionar sexo...", key="calc_s")
            fg = round(((140 - calc_e) * calc_p) / (72 * (calc_c if calc_c and calc_c > 0 else 1)) * (0.85 if calc_s == "Mujer" else 1.0), 1) if all([calc_e, calc_p, calc_c, calc_s]) else 0.0
 
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
    
    faltan_datos = not all([st.session_state.reg_centro, st.session_state.reg_res, calc_e, calc_p, calc_c, calc_s]) or \
                   (not fg_m and not valor_fg) or \
                   (st.session_state.fgl_mdrd is None) or \
                   (st.session_state.fgl_ckd is None)
 
    if st.session_state.main_meds and faltan_datos and not st.session_state.analisis_realizado:
        st.markdown('<div class="blink-text">⚠️ FALTAN DATOS EN REGISTRO, CALCULADORA O FGs (MDRD/CKD)</div>', unsafe_allow_html=True)
 
    b1, b2 = st.columns([0.85, 0.15])
    btn_val = b1.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True)
    b2.button("🗑️ RESET", on_click=reset_meds, use_container_width=True)
 
    if btn_val:
        if not st.session_state.main_meds: st.error("Introduce medicamentos.")
        else:
            with st.spinner("Analizando..."):
                prompt_final = f"{c.PROMPT_AFR_V10}\n\nFG C-G: {valor_fg}\nFG CKD: {val_ckd}\nFG MDRD: {val_mdrd}\n\nMEDS:\n{st.session_state.main_meds}"
                st.session_state.resp_ia = llamar_ia_en_cascada(prompt_final)
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
            
            datos_obj_lista = []
            if calc_e: datos_obj_lista.append(f"Edad: {calc_e}a")
            if calc_p: datos_obj_lista.append(f"Peso: {calc_p}kg")
            if calc_c: datos_obj_lista.append(f"Crea: {calc_c}mg/dL")
            if valor_fg: datos_obj_lista.append(f"FG: {valor_fg}mL/min")
            st.session_state.soip_o = " | ".join(datos_obj_lista)
            sintesis_limpia = re.sub(r'<[^>]*>', '', sintesis.replace("BLOQUE 1: ALERTAS Y AJUSTES", "").strip())
            st.session_state.soip_i = sintesis_limpia
            st.session_state.ic_inter = f"Se solicita revisión de los siguientes fármacos:\n{sintesis_limpia}"
            analisis_clinico_limpio = detalle_limpio.split('⚠️ NOTA IMPORTANTE:')[0].replace('BLOQUE 3: ANÁLISIS CLÍNICO (EXCLUSIVO COCKCROFT-GAULT)', '').strip()
            st.session_state.ic_clinica = f"{st.session_state.soip_o}\n\n{analisis_clinico_limpio}"
 
            try:
                json_data_str = re.sub(r"```json|```", "", json_data_str).strip()
                data = json.loads(json_data_str)
                id_actual = st.session_state.reg_id
                
                if st.session_state.df_val.empty or id_actual not in st.session_state.df_val["ID_REGISTRO"].values:
                    pac_row = {
                        "FECHA": datetime.now().strftime("%d/%m/%Y"), "CENTRO": st.session_state.reg_centro, "RESIDENCIA": st.session_state.reg_res, "ID_REGISTRO": id_actual,
                        "EDAD": calc_e, "SEXO": calc_s, "PESO": calc_p, "CREATININA": calc_c, "Nº_TOTAL_MEDS_PAC": data["paciente"]["N_TOTAL_MEDS_PAC"],
                        "FG_CG": valor_fg, "Nº_TOT_AFEC_CG": data["paciente"]["CG"]["TOT_AFECTADOS"], "Nº_PRECAU_CG": data["paciente"]["CG"]["PRECAUCION"], "Nº_AJUSTE_DOS_CG": data["paciente"]["CG"]["AJUSTE_DOSIS"], "Nº_TOXICID_CG": data["paciente"]["CG"]["TOXICIDAD"], "Nº_CONTRAIND_CG": data["paciente"]["CG"]["CONTRAINDICADOS"],
                        "FG_MDRD": val_mdrd, "Nº_TOT_AFEC_MDRD": data["paciente"]["MDRD"]["TOT_AFECTADOS"], "Nº_PRECAU_MDRD": data["paciente"]["MDRD"]["PRECAUCION"], "Nº_AJUSTE_DOS_MDRD": data["paciente"]["MDRD"]["AJUSTE_DOSIS"], "Nº_TOXICID_MDRD": data["paciente"]["MDRD"]["TOXICIDAD"], "Nº_CONTRAIND_MDRD": data["paciente"]["MDRD"]["CONTRAINDICADOS"],
                        "FG_CKD": val_ckd, "Nº_TOT_AFEC_CKD": data["paciente"]["CKD"]["TOT_AFECTADOS"], "Nº_PRECAU_CKD": data["paciente"]["CKD"]["PRECAUCION"], "Nº_AJUSTE_DOS_CKD": data["paciente"]["CKD"]["AJUSTE_DOSIS"], "Nº_TOXICID_CKD": data["paciente"]["CKD"]["TOXICIDAD"], "Nº_CONTRAIND_CKD": data["paciente"]["CKD"]["CONTRAINDICADOS"]
                    }
                    st.session_state.df_val = pd.concat([st.session_state.df_val, pd.DataFrame([pac_row])], ignore_index=True)
                    
                    for m in data["medicamentos"]:
                        med_nombre = m.get("MEDICAMENTO", "")
                        ya_existe_med = False
                        if not st.session_state.df_meds.empty:
                            ya_existe_med = not st.session_state.df_meds[(st.session_state.df_meds["ID_REGISTRO"] == id_actual) & (st.session_state.df_meds["MEDICAMENTO"] == med_nombre)].empty
                        if not ya_existe_med:
                            med_row = {**pac_row, **m}
                            st.session_state.df_meds = pd.concat([st.session_state.df_meds, pd.DataFrame([med_row])], ignore_index=True)
            except: pass
        except: pass
 
with tabs[1]:
    for label, key, h in [("Subjetivo (S)", "soip_s", 70), ("Objetivo (O)", "soip_o", 70), ("Interpretación (I)", "soip_i", 120), ("Plan (P)", "soip_p", 100), ("INTERCONSULTA", "ic_inter", 150), ("INFORMACIÓN CLÍNICA", "ic_clinica", 250)]:
        st.markdown(f'<div class="linea-discreta-soip">{label}</div>', unsafe_allow_html=True)
        st.text_area(key, st.session_state[key], height=h, label_visibility="collapsed")
 
with tabs[2]:
    st.markdown("### 📊 Gestión de Datos")
    st.session_state.df_val = st.data_editor(st.session_state.df_val, num_rows="dynamic", use_container_width=True, key="editor_val")
    st.session_state.df_meds = st.data_editor(st.session_state.df_meds, num_rows="dynamic", use_container_width=True, key="editor_meds")
    
    if st.session_state.analisis_realizado:
        st.markdown('<div class="blink-text-grabar">⚠️ VERIFICAR DATOS Y GRABAR</div>', unsafe_allow_html=True)
    
    if st.button("💾 GRABAR DATOS", type="primary", use_container_width=True):
        if not st.session_state.df_val.empty:
            guardar_en_google_sheets(st.session_state.df_val, st.session_state.df_meds)
            sincronizar_desde_nube()
            st.session_state.analisis_realizado = False
 
    st.write("---")
    st.markdown("### 📜 Detalle de Histórico")
    sub_hist = st.tabs(["📊 VALIDACIONES", "💊 MEDICAMENTOS", "📝 ANÁLISIS"])
    with sub_hist[0]: st.dataframe(st.session_state["df_sync_val"], use_container_width=True)
    with sub_hist[1]: st.dataframe(st.session_state["df_sync_meds"], use_container_width=True)
    with sub_hist[2]: st.dataframe(st.session_state["df_sync_analisis"], use_container_width=True)
 
    if st.button("🔄 REFRESCAR DESDE NUBE", use_container_width=True):
        sincronizar_desde_nube(); st.rerun()
 
with tabs[3]:
    st.markdown("### 📈 Dashboard de Gestión Renal")
    df_local = st.session_state.df_meds.copy()
    df_nube = st.session_state["df_sync_meds"].copy()
    df_dashboard = pd.concat([df_local, df_nube], ignore_index=True)
    
    if not df_dashboard.empty:
        df_dashboard = df_dashboard.drop_duplicates(subset=["ID_REGISTRO", "MEDICAMENTO"], keep="first")
        df_dashboard['EDAD'] = pd.to_numeric(df_dashboard['EDAD'], errors='coerce').fillna(0)
        df_dashboard['FG_CG'] = pd.to_numeric(df_dashboard['FG_CG'], errors='coerce').fillna(0)
        df_dashboard['NIVEL_ADE_CG'] = pd.to_numeric(df_dashboard['NIVEL_ADE_CG'], errors='coerce').fillna(0)
 
        with st.expander("🔍 Filtros Dinámicos de Análisis", expanded=True):
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)
            with f_col1:
                centros_disp = sorted([str(x) for x in df_dashboard["CENTRO"].unique() if x])
                filtro_centro = st.multiselect("Centro", options=centros_disp)
            with f_col2:
                rango_edad = st.slider("Edad", 0, 110, (0, 110))
            with f_col3:
                rango_fg = st.slider("Filtrado Glomerular", 0.0, 150.0, (0.0, 150.0))
            with f_col4:
                riesgos_disp = sorted([str(x) for x in df_dashboard["CAT_RIESGO_CG"].unique() if x]) if "CAT_RIESGO_CG" in df_dashboard.columns else []
                filtro_riesgo = st.multiselect("Nivel Alerta", options=riesgos_disp)
 
        mask = (df_dashboard['EDAD'].between(rango_edad[0], rango_edad[1])) & (df_dashboard['FG_CG'].between(rango_fg[0], rango_fg[1]))
        if filtro_centro: mask &= df_dashboard['CENTRO'].isin(filtro_centro)
        if filtro_riesgo and "CAT_RIESGO_CG" in df_dashboard.columns: mask &= df_dashboard['CAT_RIESGO_CG'].isin(filtro_riesgo)
        df_filtered = df_dashboard[mask]
 
        total_pacientes = df_filtered["ID_REGISTRO"].nunique() if "ID_REGISTRO" in df_filtered.columns else 0
        total_meds = len(df_filtered)
        afectados = len(df_filtered[df_filtered["NIVEL_ADE_CG"] > 0]) if "NIVEL_ADE_CG" in df_filtered.columns else 0
        porcentaje_afec = (afectados / total_meds * 100) if total_meds > 0 else 0
        promedio_fg = df_filtered['FG_CG'].mean() if not df_filtered.empty else 0
 
        kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)
        with kpi_c1:
            st.markdown(f'<div class="db-glow-box"><div style="font-size: 0.75rem; color: #BBBBBB;">Pacientes Revisados</div><div style="font-size: 1.8rem; font-weight: bold; color: #FFFFFF;">{total_pacientes}</div></div>', unsafe_allow_html=True)
        with kpi_c2:
            st.markdown(f'<div class="db-glow-box"><div style="font-size: 0.75rem; color: #BBBBBB;">Total Fármacos</div><div style="font-size: 1.8rem; font-weight: bold; color: #FFFFFF;">{total_meds}</div></div>', unsafe_allow_html=True)
        with kpi_c3:
            st.markdown(f'<div class="db-glow-box"><div style="font-size: 0.75rem; color: #BBBBBB;">Alertas Detectadas</div><div style="font-size: 1.8rem; font-weight: bold; color: #FFFFFF;">{afectados} <span style="font-size: 0.9rem; color: #feb2b2;">({porcentaje_afec:.1f}%)</span></div></div>', unsafe_allow_html=True)
        with kpi_c4:
            st.markdown(f'<div class="db-glow-box"><div style="font-size: 0.75rem; color: #BBBBBB;">Promedio FG</div><div style="font-size: 1.8rem; font-weight: bold; color: #FFFFFF;">{promedio_fg:.1f}</div></div>', unsafe_allow_html=True)
 
        g_col1, g_col2 = st.columns([0.6, 0.4])
        with g_col1:
            st.markdown("##### Distribución de Riesgos (Cockcroft-Gault)")
            color_map = {"0": "#2f855a", "1": "#faf089", "2": "#ffd27f", "3": "#c05621", "4": "#c53030"}
            if "NIVEL_ADE_CG" in df_filtered.columns:
                df_cat = df_filtered.groupby("NIVEL_ADE_CG").size().reset_index(name='count')
                df_cat["NIVEL_ADE_CG"] = df_cat["NIVEL_ADE_CG"].astype(str)
                fig_bar = px.bar(df_cat, x="NIVEL_ADE_CG", y="count", color="NIVEL_ADE_CG", color_discrete_map=color_map)
                fig_bar.update_layout(showlegend=False, height=350, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_bar, use_container_width=True)
 
        with g_col2:
            st.markdown("##### Top 5 Medicamentos Críticos")
            if "NIVEL_ADE_CG" in df_filtered.columns and "MEDICAMENTO" in df_filtered.columns:
                df_top = df_filtered[df_filtered["NIVEL_ADE_CG"] > 0].groupby("MEDICAMENTO").size().reset_index(name='Frecuencia')
                frecuencias_top = df_top["Frecuencia"].nlargest(5).unique()
                df_top = df_top[df_top["Frecuencia"].isin(frecuencias_top)].sort_values(by="Frecuencia", ascending=False)
                
                if not df_top.empty:
                    fig_pie = px.pie(df_top, values='Frecuencia', names='MEDICAMENTO', hole=.4)
                    fig_pie.update_layout(height=350, margin=dict(t=10, b=10, l=10, r=10))
                    st.plotly_chart(fig_pie, use_container_width=True)
 
        st.write("---")
        st.markdown("##### 💬 Consulta Inteligente sobre Histórico")
        chat_container = st.container(border=True)
        with chat_container:
            if "messages_db" not in st.session_state:
                st.session_state.messages_db = []
            
            for message in st.session_state.messages_db:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
 
            if prompt_db := st.chat_input("Pregunta sobre tendencias o datos específicos..."):
                st.session_state.messages_db.append({"role": "user", "content": prompt_db})
                with st.chat_message("user"):
                    st.markdown(prompt_db)
 
                with st.chat_message("assistant"):
                    contexto_db = df_filtered.to_string()
                    full_prompt = f"Basándote en estos datos del dashboard:\n{contexto_db}\n\nResponde a: {prompt_db}"
                    response = llamar_ia_en_cascada(full_prompt)
                    st.markdown(response)
                st.session_state.messages_db.append({"role": "assistant", "content": response})
    else:
        st.warning("⚠️ No se detectan datos locales ni históricos.")
 
st.markdown(f"""<div class="warning-yellow">⚠️ <b>Apoyo a la revisión farmacoterapéutica. Verifique fuentes oficiales.</b></div> <div style="text-align:right; font-size:0.6rem; color:#ccc; font-family:monospace; margin-top:10px;">v. 19 mar 2026 09:30</div>""", unsafe_allow_html=True)
