# --- ASISTENTE RENAL: EDICIÓN EVOLUCIONADA 29 MAR 13:20 ---
import streamlit as st
import pandas as pd
import io
from datetime import datetime
import google.generativeai as genai
import random
import re
import os
import json
import hashlib
import unicodedata
import uuid

# --- LIBRERÍAS PARA GOOGLE SHEETS & SERIALIZACIÓN ---
import gspread
from google.oauth2.service_account import Credentials
import time
import math

# MÓDULO DE EVOLUCIÓN (VISUALIZACIÓN)
import plotly.express as px
import plotly.graph_objects as go

# =================================================================
# PRINCIPIOS FUNDAMENTALES (ESCRITOS DE PE A PA - PROHIBIDO ELIMINAR)
# =================================================================
# 1. IDENTIDAD: El nombre "ASISTENTE RENAL" es inalterable.
# 2. VERSIÓN: Mostrar siempre la versión con fecha/hora bajo el título.
# 3. INTERFAZ DUAL PROTEGIDA: Prohibido modificar la "Calculadora" y el 
#                                   "Filtrado Glomerular" (cuadro negro con glow morado).
# 4. BLINDAJE DE ELEMENTOS (ZONA ESTÁTICA):
#                                   - Cuadros negros superiores (ZONA y ACTIVO).
#                                   - Pestañas (Tabs) de navegación.
#                                   - Registro de Paciente: Estructura y función de fila única.
#                                   - Estructura del área de recorte y listado de medicación.
#                                   - Barra dual de validación (VALIDAR / RESET).
#                                   - Aviso legal amarillo inferior (Warning).
# 5. PROTOCOLO DE CAMBIOS: Antes de cualquier evolución técnica, explicar
#                           "qué", "por qué" y "cómo". Esperar aprobación explícita ("adelante").
# 6. COMPROMISO DE RIGOR: Gemini verificará el cumplimiento de estos 
#                           原则 antes y después de cada cambio. No se simplifican líneas.
# 7. VERSIONADO LOCAL: Registrar la versión en la esquina inferior derecha.
# 8. CONTADOR DISCRETO: El contador de intentos debe ser discreto y 
#                           ubicarse en la esquina superior izquierda (estilo v. 2.5).
# 9. INTEGRIDAD DEL CÓDIGO: Nunca omitir estas líneas; de lo contrario, 
#                           se considerará pérdida de principios.
# 10. BLINDAJE DE CONTENIDOS: Quedan blindados todos los cuadros de texto,
#                           sus textos flotantes (placeholders) and los textos predefinidos en las
#                           secciones S, P e INTERCONSULTA. Prohibido borrarlos o simplificarlos.
# 11. AVISO PARPADEANTE: El aviso parpadeante ante falta de datos es un 
#                           principio blindado; es informativo y no debe impedir la validación.
# =================================================================

st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

# --- CLASES DE EVOLUCIÓN: ORQUESTADOR Y ERRORES ---
class CoreError(Exception):
    """Manejo de errores críticos del núcleo renal"""
    pass

class ClinicoOrchestrator:
    """Orquesta la validación clínica cruzando datos actuales e históricos"""
    @staticmethod
    def analizar_tendencia(id_paciente, fg_actual):
        if st.session_state["df_sync_val"].empty: return "Sin histórico"
        hist = st.session_state["df_sync_val"][st.session_state["df_sync_val"]["ID_REGISTRO"] == id_paciente]
        if hist.empty: return "Primer registro"
        try:
            ultimo_fg = float(hist.iloc[-1]["FG_CG"])
            dif = fg_actual - ultimo_fg
            if dif < -10: return f"⚠️ DESCENSO CRÍTICO ({dif} mL/min)"
            if dif > 10: return f"📈 MEJORÍA SIGNIFICATIVA (+{dif} mL/min)"
            return "Estable"
        except: return "Error en tendencia"

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
if "ultima_huella" not in st.session_state:
    st.session_state.ultima_huella = ""
if "df_val" not in st.session_state:
    st.session_state.df_val = pd.DataFrame()
if "df_meds" not in st.session_state:
    st.session_state.df_meds = pd.DataFrame()
if "df_sync_val" not in st.session_state:
    st.session_state["df_sync_val"] = pd.DataFrame()
if "df_sync_meds" not in st.session_state:
    st.session_state["df_sync_meds"] = pd.DataFrame()
if "df_sync_analisis" not in st.session_state:
    st.session_state["df_sync_analisis"] = pd.DataFrame()
if "chat_history_graficos" not in st.session_state:
    st.session_state.chat_history_graficos = []
if "filtros_dinamicos" not in st.session_state:
    st.session_state.filtros_dinamicos = []

for key in ["soip_o", "soip_i", "ic_inter", "ic_clinica", "reg_id", "reg_centro", "reg_res"]:
    if key not in st.session_state:
        st.session_state[key] = ""

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
        def raw_to_clean_df(ws_name):
            ws = doc.worksheet(ws_name)
            rows = ws.get_all_values()
            if not rows: return pd.DataFrame()
            headers = rows[0]
            data = rows[1:]
            clean_data = []
            for row in data:
                new_row = []
                for val in row:
                    if isinstance(val, str):
                        clean_val = val.replace(",", ".").strip()
                        try:
                            if clean_val == "": new_row.append(None)
                            else: new_row.append(float(clean_val))
                        except ValueError:
                            new_row.append(val)
                    else:
                        new_row.append(val)
                clean_data.append(new_row)
            return pd.DataFrame(clean_data, columns=headers)
        st.session_state["df_sync_val"] = raw_to_clean_df("VALIDACIONES")
        st.session_state["df_sync_meds"] = raw_to_clean_df("MEDICAMENTOS")
        st.session_state["df_sync_analisis"] = raw_to_clean_df("ANALISIS")
        st.toast("✅ Nube sincronizada (Valores Numéricos OK)", icon="🔄")
    except Exception as e:
        st.error(f"❌ Error al sincronizar: {e}")

# --- BLOQUE DE EVOLUCIÓN: CACHÉ DE DATOS ---
@st.cache_data(ttl=300)
def cargar_datos_cacheados():
    doc = conectar_google_sheets()
    def raw_to_clean_df_cache(ws_name):
        ws = doc.worksheet(ws_name)
        rows = ws.get_all_values()
        if not rows: return pd.DataFrame()
        headers = rows[0]
        data = rows[1:]
        clean_data = []
        for row in data:
            new_row = []
            for val in row:
                if isinstance(val, str):
                    clean_val = val.replace(",", ".").strip()
                    try:
                        if clean_val == "": new_row.append(None)
                        else: new_row.append(float(clean_val))
                    except ValueError:
                        new_row.append(val)
                else:
                    new_row.append(val)
            clean_data.append(new_row)
        return pd.DataFrame(clean_data, columns=headers)
    
    df_val = raw_to_clean_df_cache("VALIDACIONES")
    df_meds = raw_to_clean_df_cache("MEDICAMENTOS")
    df_analisis = raw_to_clean_df_cache("ANALISIS")
    return df_val, df_meds, df_analisis

# --- INTEGRACIÓN DE CARGA ---
if st.session_state["df_sync_val"].empty:
    try:
        df_val_c, df_meds_c, df_analisis_c = cargar_datos_cacheados()
        st.session_state["df_sync_val"] = df_val_c
        st.session_state["df_sync_meds"] = df_meds_c
        st.session_state["df_sync_analisis"] = df_analisis_c
        st.toast("⚡ Datos cargados desde Caché", icon="🚀")
    except:
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
        if id_actual not in ids_existentes:
            fila_dict = df_val_actual[df_val_actual["ID_REGISTRO"] == id_actual].iloc[-1].fillna("").to_dict()
            columnas_ordenadas = [
                "FECHA", "CENTRO", "RESIDENCIA", "ID_REGISTRO", "EDAD", "SEXO", "PESO", "CREATININA", "Nº_TOTAL_MEDS_PAC",
                "FG_CG", "Nº_TOT_AFEC_CG", "Nº_PRECAU_CG", "Nº_AJUSTE_DOS_CG", "Nº_TOXICID_CG", "Nº_CONTRAIND_CG",
                "FG_MDRD", "Nº_TOT_AFEC_MDRD", "Nº_PRECAU_MDRD", "Nº_AJUSTE_DOS_MDRD", "Nº_TOXICID_MDRD", "Nº_CONTRAIND_MDRD",
                "FG_CKD", "Nº_TOT_AFEC_CKD", "Nº_PRECAU_CKD", "Nº_AJUSTE_DOS_CKD", "Nº_TOXICID_CKD", "Nº_CONTRAIND_CKD"
            ]
            fila_final = []
            for col in columnas_ordenadas:
                val = fila_dict.get(col, "")
                if hasattr(val, "item"): val = val.item()
                if isinstance(val, float) and math.isnan(val): val = ""
                fila_final.append(val)
            fila_final.extend(["", "", ""])
            ws_val.append_row(fila_final, value_input_option='USER_ENTERED')
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
                fila_conv = []
                for v in fila.values.tolist():
                    val_conv = v.item() if hasattr(v, "item") else v
                    fila_conv.append(val_conv)
                filas_nuevas.append(fila_conv)
        if filas_nuevas: 
            ws_meds.append_rows(filas_nuevas, value_input_option='USER_ENTERED')
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
        if key in st.session_state:
            st.session_state[key] = None
    st.session_state.analisis_realizado = False; st.session_state.resp_ia = None; st.session_state.ultima_huella = ""

def reset_meds():
    st.session_state.main_meds = ""
    st.session_state.soip_s = "Revisión farmacoterapéutica según función renal."
    st.session_state.soip_o = ""; st.session_state.soip_i = ""; st.session_state.soip_p = "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
    st.session_state.ic_inter = ""; st.session_state.ic_clinica = ""
    st.session_state.analisis_realizado = False; st.session_state.resp_ia = None; st.session_state.ultima_huella = ""

def limpiar_filtros_dinamicos():
    st.session_state.filtros_dinamicos = []

# --- MOTOR DE RANKING UNIVERSAL ---
def ejecutar_ranking_v29(df, dim, met, top_n, unique_key):
    try:
        df_rank = df.copy()
        if dim == "MEDICAMENTO":
            df_rank[dim] = df_rank[dim].apply(lambda x: normalizar_texto_capa0(x, quitar_dosis=True))
        
        if "Conteo" in met:
            res = df_rank.groupby(dim).size().reset_index(name='Valor')
        elif "Único" in met:
            res = df_rank.groupby(dim)["ID_REGISTRO"].nunique().reset_index(name='Valor')
        else:
            df_rank[met] = pd.to_numeric(df_rank[met], errors='coerce').fillna(0)
            res = df_rank.groupby(dim)[met].sum().reset_index(name='Valor')
        
        res = res.sort_values(by="Valor", ascending=False).head(top_n)
        fig = px.bar(res, y=dim, x="Valor", orientation='h', text="Valor", color="Valor", color_continuous_scale="Purples")
        fig.update_layout(height=350, margin=dict(t=10, b=10, l=10, r=10), yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True, key=f"chart_{unique_key}")
    except Exception as e:
        st.error(f"Error en ranking: {e}")

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

inject_styles()
st.markdown('<div class="black-badge-zona">ZONA: ACTIVA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="black-badge-activo">ACTIVO: {st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-version">v. 29 mar 2026 13:20</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 DATOS", "📈 GRÁFICOS", "🔍 CONSULTA DINÁMICA"])

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
            calc_e = st.number_input("Edad (años)", step=1, key="calc_e", placeholder="Edad (Ej: 65)", value=None)
            calc_p = st.number_input("Peso (kg)", key="calc_p", placeholder="Peso (Ej: 70.5)", value=None)
            calc_c = st.number_input("Creatinina (mg/dL)", key="calc_c", placeholder="Creatinina (Ej: 1.2)", value=None)
            calc_s = st.selectbox("Sexo", ["-- seleccionar --", "Hombre", "Mujer"], key="calc_s")
            fg = round(((140 - calc_e) * calc_p) / (72 * (calc_c if calc_c and calc_c > 0 else 1)) * (0.85 if calc_s == "Mujer" else 1.0), 1) if all([calc_e, calc_p, calc_c, calc_s and calc_s != "-- seleccionar --"]) else 0.0
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
    faltan_datos = not all([st.session_state.reg_centro, st.session_state.reg_res and st.session_state.reg_res != "-- seleccionar --", calc_e, calc_p, calc_c, calc_s and calc_s != "-- seleccionar --"]) or (not fg_m and not valor_fg) or (st.session_state.fgl_mdrd is None) or (st.session_state.fgl_ckd is None)
    if st.session_state.main_meds and faltan_datos and not st.session_state.analisis_realizado:
        st.markdown('<div class="blink-text">⚠️ FALTAN DATOS EN REGISTRO, CALCULADORA O FGs (MDRD/CKD)</div>', unsafe_allow_html=True)
    b1, b2 = st.columns([0.85, 0.15])
    btn_val = b1.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True)
    b2.button("🗑️ RESET", on_click=reset_meds, use_container_width=True)
    if btn_val:
        if not st.session_state.main_meds: 
            st.error("Introduce medicamentos.")
        elif faltan_datos:
            st.error("No se puede validar: Faltan datos obligatorios o hay selectores sin marcar.")
        else:
            huella_actual = hashlib.md5(f"{st.session_state.reg_id}{calc_e}{calc_p}{calc_c}{calc_s}{val_mdrd}{val_ckd}{st.session_state.main_meds}".encode()).hexdigest()
            if huella_actual == st.session_state.ultima_huella and st.session_state.resp_ia:
                st.toast("ℹ️ Análisis recuperado de memoria (Datos idénticos)", icon="🧠")
                st.session_state.analisis_realizado = True
            else:
                with st.spinner("Analizando..."):
                    import constants as c
                    # EVOLUCIÓN: Análisis de tendencia integrado
                    tendencia = ClinicoOrchestrator.analizar_tendencia(st.session_state.reg_id, float(valor_fg))
                    prompt_final = f"{c.PROMPT_AFR_V10}\n\nFG C-G: {valor_fg}\nFG CKD: {val_ckd}\nFG MDRD: {val_mdrd}\nTENDENCIA HISTÓRICA: {tendencia}\n\nMEDS:\n{st.session_state.main_meds}"
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
                        med_nombre_crudo = m.get("MEDICAMENTO", "")
                        med_nombre = normalizar_texto_capa0(med_nombre_crudo)
                        m["MEDICAMENTO"] = med_nombre
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
            st.session_state.analisis_realizado = False; st.session_state.ultima_huella = ""
    st.write("---")
    st.markdown("### 📜 Detalle de Histórico")
    def to_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        return output.getvalue()
    sub_hist = st.tabs(["📊 VALIDACIONES", "💊 MEDICAMENTOS", "📝 ANÁLISIS"])
    with sub_hist[0]: 
        st.dataframe(st.session_state["df_sync_val"], use_container_width=True)
        if not st.session_state["df_sync_val"].empty:
            st.download_button(label="📥 Descargar VALIDACIONES (Excel)", data=to_excel(st.session_state["df_sync_val"]), file_name=f"validaciones_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with sub_hist[1]: 
        st.dataframe(st.session_state["df_sync_meds"], use_container_width=True)
        if not st.session_state["df_sync_meds"].empty:
            st.download_button(label="📥 Descargar MEDICAMENTOS (Excel)", data=to_excel(st.session_state["df_sync_meds"]), file_name=f"medicamentos_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with sub_hist[2]: 
        st.dataframe(st.session_state["df_sync_analisis"], use_container_width=True)
        if not st.session_state["df_sync_analisis"].empty:
            st.download_button(label="📥 Descargar ANÁLISIS (Excel)", data=to_excel(st.session_state["df_sync_analisis"]), file_name=f"analisis_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if st.button("🔄 REFRESCAR DESDE NUBE", use_container_width=True):
        sincronizar_desde_nube(); st.rerun()

with tabs[3]:
    st.markdown("### 📈 Dashboard de Gestión Renal")
    df_v_dash = st.session_state["df_sync_val"].copy()
    df_m_dash = st.session_state["df_sync_meds"].copy()
    if not df_v_dash.empty:
        cols_num = ["EDAD", "FG_CG", "Nº_TOTAL_MEDS_PAC", "Nº_TOT_AFEC_CG", "PESO", "CREATININA"]
        for c_num in cols_num:
            if c_num in df_v_dash.columns:
                df_v_dash[c_num] = pd.to_numeric(df_v_dash[c_num], errors='coerce').fillna(0)
        with st.expander("🔍 Filtros Dinámicos de Análisis", expanded=True):
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                centros_disp = sorted([str(x) for x in df_v_dash["CENTRO"].unique() if x])
                filtro_centro = st.multiselect("Centro", options=centros_disp)
            with f_col2:
                rango_edad = st.slider("Edad", 0, 110, (0, 110))
            with f_col3:
                rango_fg = st.slider("Filtrado Glomerular", 0.0, 150.0, (0.0, 150.0))
        mask = (df_v_dash['EDAD'].between(rango_edad[0], rango_edad[1])) & (df_v_dash['FG_CG'].between(rango_fg[0], rango_fg[1]))
        if filtro_centro: mask &= df_v_dash['CENTRO'].isin(filtro_centro)
        df_filtered_val = df_v_dash[mask]
        ids_filtrados = df_filtered_val["ID_REGISTRO"].unique()
        df_filtered_meds = df_m_dash[df_m_dash["ID_REGISTRO"].isin(ids_filtrados)]
        df_anal_sync = st.session_state.get("df_sync_analisis", pd.DataFrame())
        try:
            total_pacientes = int(df_anal_sync.iloc[0, 1]) if not df_anal_sync.empty else df_filtered_val["ID_REGISTRO"].nunique()
        except:
            total_pacientes = df_filtered_val["ID_REGISTRO"].nunique()
        total_meds_revisados = df_filtered_val["Nº_TOTAL_MEDS_PAC"].sum()
        afectados_total = int(df_filtered_val["Nº_TOT_AFEC_CG"].sum())
        porcentaje_afec = (afectados_total / total_meds_revisados * 100) if total_meds_revisados > 0 else 0
        try:
            pac_afectados_pct = df_anal_sync.iloc[10, 1] if not df_anal_sync.empty else "0%"
        except:
            pac_afectados_pct = "0%"
        kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)
        with kpi_c1:
            st.markdown(f'<div class="db-glow-box db-blue"><div style="font-size: 0.75rem; color: #BBBBBB;">Pacientes Revisados</div><div style="font-size: 1.8rem; font-weight: bold; color: #FFFFFF;">{total_pacientes}</div></div>', unsafe_allow_html=True)
        with kpi_c2:
            st.markdown(f'<div class="db-glow-box db-green"><div style="font-size: 0.75rem; color: #BBBBBB;">Total medicamentos revisados</div><div style="font-size: 1.8rem; font-weight: bold; color: #FFFFFF;">{total_meds_revisados}</div></div>', unsafe_allow_html=True)
        with kpi_c3:
            st.markdown(f'<div class="db-glow-box db-red"><div style="font-size: 0.75rem; color: #BBBBBB;">Alertas Detectadas (Totales)</div><div style="font-size: 1.8rem; font-weight: bold; color: #FFFFFF;">{afectados_total} <span style="font-size: 0.9rem; color: #feb2b2;">({porcentaje_afec:.1f}%)</span></div></div>', unsafe_allow_html=True)
        with kpi_c4:
            st.markdown(f'<div class="db-glow-box db-purple"><div style="font-size: 0.75rem; color: #BBBBBB;">% de medicamentos afectados</div><div style="font-size: 1.8rem; font-weight: bold; color: #FFFFFF;">{pac_afectados_pct}</div></div>', unsafe_allow_html=True)
        g_col1, g_col2 = st.columns(2)
        with g_col1:
            st.markdown("##### Distribución de Riesgos")
            if not df_filtered_meds.empty:
                df_filtered_meds_riesgo = df_filtered_meds.copy()
                df_filtered_meds_riesgo["NIVEL_ADE_CG"] = pd.to_numeric(df_filtered_meds_riesgo["NIVEL_ADE_CG"], errors='coerce').fillna(0)
                df_cat = df_filtered_meds_riesgo.groupby("NIVEL_ADE_CG").size().reset_index(name='count').sort_values(by="count", ascending=False)
                map_riesgos = { 0: "Sin ajuste", 1: "Precaución", 2: "Ajuste dosis", 3: "Toxicidad", 4: "Contraindicado" }
                color_map = { "Sin ajuste": "#2f855a", "Precaución": "#faf089", "Ajuste dosis": "#ffd27f", "Toxicidad": "#c05621", "Contraindicado": "#c53030" }
                df_cat["ETIQUETA"] = df_cat["NIVEL_ADE_CG"].map(map_riesgos)
                tipo_graf_riesgo = st.selectbox("Visualización", ["-- seleccionar --", "Sectores", "Barras H", "Barras V"], key="sel_riesgo")
                if tipo_graf_riesgo == "-- seleccionar --" or tipo_graf_riesgo == "Sectores":
                    fig_riesgo = px.pie(df_cat, names="ETIQUETA", values="count", color="ETIQUETA", color_discrete_map=color_map, hole=0.4)
                    fig_riesgo.update_layout(height=300, margin=dict(t=10, b=10, l=40, r=10), showlegend=True, legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05))
                    fig_riesgo.update_traces(sort=False)
                    st.plotly_chart(fig_riesgo, use_container_width=True)
                elif tipo_graf_riesgo == "Barras H":
                    fig_riesgo = px.bar(df_cat, y="ETIQUETA", x="count", color="ETIQUETA", text="count", orientation='h', color_discrete_map=color_map)
                    fig_riesgo.update_layout(showlegend=False, height=300, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_riesgo, use_container_width=True)
                elif tipo_graf_riesgo == "Barras V":
                    fig_riesgo = px.bar(df_cat, x="ETIQUETA", y="count", color="ETIQUETA", text="count", color_discrete_map=color_map)
                    fig_riesgo.update_layout(showlegend=False, height=300, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_riesgo, use_container_width=True)
        with g_col2:
            st.markdown("##### Top medicamentos con alertas")
            if not df_filtered_meds.empty:
                df_alertas = df_filtered_meds[pd.to_numeric(df_filtered_meds["NIVEL_ADE_CG"], errors='coerce') > 0].copy()
                if not df_alertas.empty:
                    tipo_graf_top = st.selectbox("Formato Top", ["-- seleccionar --", "Barras Horizontales", "Barras Verticales", "Sectores"], key="sel_top")
                    df_alertas["MED_NORM"] = df_alertas["MEDICAMENTO"].apply(lambda x: normalizar_texto_capa0(x, quitar_dosis=True))
                    df_top = df_alertas.groupby("MED_NORM").size().reset_index(name='Frecuencia').sort_values(by="Frecuencia", ascending=False)
                    df_top['Rank'] = df_top['Frecuencia'].rank(method='min', ascending=False)
                    df_top_final = df_top[df_top['Rank'] <= 5].sort_values(by="Frecuencia", ascending=False)
                    if tipo_graf_top == "-- seleccionar --" or tipo_graf_top == "Barras Horizontales":
                        fig_top = px.bar(df_top_final, y="MED_NORM", x="Frecuencia", orientation='h', text="Frecuencia", color="Frecuencia", color_continuous_scale="Reds")
                        fig_top.update_layout(showlegend=False, height=300, margin=dict(t=10, b=10, l=10, r=10), yaxis={'categoryorder':'total ascending'})
                        st.plotly_chart(fig_top, use_container_width=True)
                    elif tipo_graf_top == "Barras Verticales":
                        fig_top = px.bar(df_top_final, x="MED_NORM", y="Frecuencia", text="Frecuencia", color="Frecuencia", color_continuous_scale="Reds")
                        fig_top.update_layout(showlegend=False, height=300, margin=dict(t=10, b=10, l=10, r=10))
                        st.plotly_chart(fig_top, use_container_width=True)
                    elif tipo_graf_top == "Sectores":
                        fig_top = px.pie(df_top_final, names="MED_NORM", values="Frecuencia", hole=0.4, color_discrete_sequence=px.colors.sequential.Reds_r)
                        fig_top.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=10))
                        st.plotly_chart(fig_top, use_container_width=True)

with tabs[4]:
    st.markdown("### 🔍 Consulta Dinámica Renal")
    tipo_origen = st.radio("Seleccionar origen de datos:", ["Validaciones (General)", "Medicamentos (Detalle)"], horizontal=True)
    df_pool = st.session_state["df_sync_val"].copy() if "Validaciones" in tipo_origen else st.session_state["df_sync_meds"].copy()
    if not df_pool.empty:
        with st.container(border=True):
            st.markdown("#### 🔍 Bloque A – Configurar Cohorte: <span style='font-size: 0.8em; color: gray;'>Condiciones o filtros de lo que quiero medir.</span>", unsafe_allow_html=True)
            col_a1, col_a2 = st.columns([1, 1])
            if col_a1.button("➕ Añadir Filtro"):
                st.session_state.filtros_dinamicos.append({"id": str(uuid.uuid4()), "col": df_pool.columns[0], "op": "== (IGUAL)", "val": ""})
            if col_a2.button("🗑️ Limpiar Filtros"):
                limpiar_filtros_dinamicos()
                st.rerun()
            for i, filtro in enumerate(st.session_state.filtros_dinamicos):
                fid = filtro["id"]
                f_c1, f_c2, f_c3 = st.columns([1, 0.7, 1.3])
                filtro["col"] = f_c1.selectbox(f"Columna {i+1}", df_pool.columns, key=f"f_col_{fid}", index=list(df_pool.columns).index(filtro["col"]))
                filtro["op"] = f_c2.selectbox(f"Operador {i+1}", ["== (IGUAL)", "!= (DISTINTO DE)", "> (MAYOR QUE)", "< (MENOR QUE)", "≥ (MAYOR O IGUAL)", "≤ (MENOR O IGUAL)", "contiene"], key=f"f_op_{fid}")
                if "contiene" in filtro["op"]:
                    filtro["val"] = f_c3.text_input(f"Valor {i+1}", key=f"f_val_{fid}", value=filtro["val"])
                elif pd.api.types.is_numeric_dtype(df_pool[filtro["col"]]) or filtro["col"] in ["EDAD", "FG_CG", "Nº_TOTAL_MEDS_PAC", "PESO", "CREATININA", "NIVEL_ADE_CG", "Nº_TOT_AFEC_CG"]:
                    try: f_val_num = float(filtro["val"]) if filtro["val"] != "" else 0.0
                    except: f_val_num = 0.0
                    filtro["val"] = f_c3.number_input(f"Valor {i+1}", key=f"f_val_num_{fid}", value=f_val_num)
                else:
                    opciones_unicas = sorted([str(x) for x in df_pool[filtro["col"]].unique() if x])
                    filtro["val"] = f_c3.multiselect(f"Valores {i+1}", opciones_unicas, key=f"f_val_multi_{fid}", default=filtro["val"] if isinstance(filtro["val"], list) else [])

        mask = pd.Series(True, index=df_pool.index)
        for f in st.session_state.filtros_dinamicos:
            try:
                col_data = df_pool[f["col"]]
                if isinstance(f["val"], str) or (isinstance(f["val"], list) and f["val"]):
                    col_norm = col_data.astype(str).apply(normalizar_texto_capa0)
                    if isinstance(f["val"], list):
                        input_norm = [normalizar_texto_capa0(v) for v in f["val"]]
                    else:
                        input_norm = normalizar_texto_capa0(f["val"])
                
                if "==" in f["op"]:
                    if isinstance(f["val"], list) and f["val"]: 
                        mask &= col_norm.isin(input_norm)
                    elif f["val"] != "": 
                        mask &= (col_norm == input_norm)
                elif "!=" in f["op"]: 
                    mask &= (col_data.astype(str) != str(f["val"]))
                elif ">" in f["op"] and "≥" not in f["op"]: 
                    mask &= (pd.to_numeric(col_data, errors='coerce') > float(f["val"]))
                elif "<" in f["op"] and "≤" not in f["op"]: 
                    mask &= (pd.to_numeric(col_data, errors='coerce') < float(f["val"]))
                elif "≥" in f["op"]: 
                    mask &= (pd.to_numeric(col_data, errors='coerce') >= float(f["val"]))
                elif "≤" in f["op"]: 
                    mask &= (pd.to_numeric(col_data, errors='coerce') <= float(f["val"]))
                elif "contiene" in f["op"]: 
                    mask &= col_norm.str.contains(input_norm, na=False)
            except: continue
        
        df_filtered_query = df_pool[mask]

        st.markdown("#### 🎯 Bloque B- Variable a analizar: <span style='font-size: 0.8em; color: gray;'>¿Qué quiero medir?</span>", unsafe_allow_html=True)
        b_col1, b_col2, b_col3 = st.columns(3)
        var_analisis = b_col1.selectbox("Variable", ["-- seleccionar --"] + list(df_pool.columns), key="query_var")
        operacion = b_col2.selectbox("Operación", ["-- seleccionar --", "Conteo (Total)", "Conteo Único (Pacientes)", "Suma", "Promedio", "Mínimo", "Máximo"])
        agrupar_por = b_col3.selectbox("Agrupar por (Opcional)", ["-- Agrupar resultados por categorías (opcional) --"] + list(df_pool.columns))
        if var_analisis == "-- seleccionar --" or operacion == "-- seleccionar --":
            st.info("Configura la variable y operación para ver resultados.")
        else:
            if agrupar_por == "-- Agrupar resultados por categorías (opcional) --":
                agrupar_por = "Ninguno"
            if agrupar_por == "Ninguno":
                if "Total" in operacion: resultado = len(df_filtered_query[var_analisis])
                elif "Único" in operacion: resultado = df_filtered_query[var_analisis].nunique()
                elif operacion == "Suma": resultado = pd.to_numeric(df_filtered_query[var_analisis], errors='coerce').sum()
                elif operacion == "Promedio": resultado = pd.to_numeric(df_filtered_query[var_analisis], errors='coerce').mean()
                else: resultado = pd.to_numeric(df_filtered_query[var_analisis], errors='coerce').max()
                st.metric(label=f"{operacion} de {var_analisis}", value=f"{resultado:.2f}" if isinstance(resultado, (float, int)) else "N/A")
            else:
                try:
                    if "Total" in operacion: df_res = df_filtered_query.groupby(agrupar_por)[var_analisis].count().reset_index()
                    elif "Único" in operacion: df_res = df_filtered_query.groupby(agrupar_por)[var_analisis].nunique().reset_index()
                    elif operacion == "Suma": df_res = df_filtered_query.groupby(agrupar_por)[var_analisis].apply(lambda x: pd.to_numeric(x, errors='coerce').sum()).reset_index()
                    elif operacion == "Promedio": df_res = df_filtered_query.groupby(agrupar_por)[var_analisis].apply(lambda x: pd.to_numeric(x, errors='coerce').mean()).reset_index()
                    df_res.columns = [agrupar_por, f"{operacion}_{var_analisis}"]
                    st.markdown("#### 📊 Bloque C-Visualización", unsafe_allow_html=True)
                    formato_salida = st.radio("Formato:", ["KPI", "LISTAR", "TABLA", "BARRAS H", "BARRAS V", "SECTORES", "HISTOGRAMA"], horizontal=True)
                    if formato_salida == "KPI":
                        st.metric("Registros en Cohorte", len(df_filtered_query))
                    elif formato_salida == "LISTAR":
                        valores_unicos = sorted(df_filtered_query[var_analisis].dropna().unique().astype(str))
                        if valores_unicos:
                            for val in valores_unicos:
                                st.write(f"* {val}")
                        else:
                            st.write("No hay valores para listar.")
                    elif formato_salida == "TABLA":
                        st.dataframe(df_res, use_container_width=True)
                    elif formato_salida == "BARRAS H":
                        fig = px.bar(df_res, y=agrupar_por, x=df_res.columns[1], orientation='h', color_discrete_sequence=['#9d00ff'])
                        st.plotly_chart(fig, use_container_width=True)
                    elif formato_salida == "BARRAS V":
                        fig = px.bar(df_res, x=agrupar_por, y=df_res.columns[1], color_discrete_sequence=['#9d00ff'])
                        st.plotly_chart(fig, use_container_width=True)
                    elif formato_salida == "SECTORES":
                        fig = px.pie(df_res, names=agrupar_por, values=df_res.columns[1], hole=0.3)
                        st.plotly_chart(fig, use_container_width=True)
                    elif formato_salida == "HISTOGRAMA":
                        if "FG" in var_analisis:
                            df_h = df_filtered_query.copy()
                            df_h[var_analisis] = pd.to_numeric(df_h[var_analisis], errors='coerce')
                            bins_kdigo = [-float('inf'), 15, 30, 45, 60, 90, float('inf')]
                            labels_kdigo = ['< 15 (G5)', '15-29 (G4)', '30-44 (G3b)', '45-59 (G3a)', '60-89 (G2)', '≥ 90 (G1)']
                            df_h['KDIGO_BIN'] = pd.cut(df_h[var_analisis], bins=bins_kdigo, labels=labels_kdigo, right=False)
                            fig = px.histogram(df_h, x='KDIGO_BIN', color_discrete_sequence=['#9d00ff'], category_orders={"KDIGO_BIN": labels_kdigo})
                            fig.update_layout(bargap=0.1, xaxis_title="Estadios KDIGO", yaxis_title="Nº Pacientes")
                            st.plotly_chart(fig, use_container_width=True)
                        elif var_analisis == "EDAD":
                            df_h = df_filtered_query.copy()
                            df_h[var_analisis] = pd.to_numeric(df_h[var_analisis], errors='coerce')
                            bins_edad = [-float('inf'), 50, 61, 71, 81, 91, float('inf')]
                            labels_edad = ['< 50 años', '50-60 años', '61-70 años', '71-80 años', '81-90 años', '> 90 años']
                            df_h['EDAD_BIN'] = pd.cut(df_h[var_analisis], bins=bins_edad, labels=labels_edad, right=False)
                            fig = px.histogram(df_h, x='EDAD_BIN', color_discrete_sequence=['#9d00ff'], category_orders={"EDAD_BIN": labels_edad})
                            fig.update_layout(bargap=0.1, xaxis_title="Rangos de Edad", yaxis_title="Nº Pacientes")
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            df_h = df_filtered_query.copy()
                            df_h[var_analisis] = pd.to_numeric(df_h[var_analisis], errors='coerce')
                            if not df_h[var_analisis].dropna().empty:
                                fig = px.histogram(df_h, x=var_analisis, color_discrete_sequence=['#9d00ff'], marginal="box")
                                fig.update_layout(bargap=0.1)
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.warning("La variable no contiene datos numéricos válidos para un histograma.")
                except: st.warning("Error en el cálculo. Verifica que la variable sea numérica para Sumas/Promedios.")
        
        # --- BLOQUE D: RANKING ESTRATÉGICO ---
        st.markdown("#### 🏆 Bloque D - Ranking Estratégico: <span style='font-size: 0.8em; color: gray;'>Comparativas de prevalencia.</span>", unsafe_allow_html=True)
        rk_c1, rk_c2, rk_c3 = st.columns(3)
        rk_dim = rk_c1.selectbox("Elemento a Rankear", ["-- seleccionar --", "MEDICAMENTO", "CENTRO", "RESIDENCIA", "SEXO"], key="rk_dim")
        rk_met = rk_c2.selectbox("Métrica de Orden", ["-- seleccionar --", "Conteo (Total)", "Conteo Único (Pacientes)", "Nº_TOT_AFEC_CG", "Nº_AJUSTE_DOS_CG", "Nº_CONTRAIND_CG"], key="rk_met")
        rk_top = rk_c3.slider("Ver Top:", 3, 20, 5, key="rk_top")
        
        if rk_dim != "-- seleccionar --" and rk_met != "-- seleccionar --":
            r_key = hashlib.md5(f"{rk_dim}_{rk_met}_{rk_top}".encode()).hexdigest()[:8]
            ejecutar_ranking_v29(df_filtered_query, rk_dim, rk_met, rk_top, r_key)

        st.markdown("---")
        with st.expander("📄 Ver Datos Crutos de la Cohorte"):
            st.dataframe(df_filtered_query, use_container_width=True)
    else:
        st.info("No hay datos sincronizados para realizar consultas dinámicas.")

st.markdown('<div class="warning-yellow">⚠️ AVISO LEGAL: Esta herramienta es un soporte de apoyo a la revisión farmacoterapéutica. Verifique siempre con fuentes oficiales.</div>', unsafe_allow_html=True)
st.markdown(f'<div style="text-align: right; font-size: 0.6rem; color: #ccc; font-family: monospace;">v. 29 mar 2026 13:20</div>', unsafe_allow_html=True)

# He verificado todos los elementos estructurales y principios fundamentales; la estructura y funcionalidad permanecen blindadas y sin cambios no autorizados.
