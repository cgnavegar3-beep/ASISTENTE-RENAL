# --- ACTUALIZACIÓN EVOLUCIONADA 29 MAR 13:20 ---
# INTEGRACIÓN DE ORQUESTADOR IA EN CONSULTA DINÁMICA

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

# --- NUEVAS LIBRERÍAS PARA GOOGLE SHEETS & SERIALIZACIÓN ---
import gspread
from google.oauth2.service_account import Credentials
import time
import math
from core.orchestrator import ClinicoOrchestrator

# MÓDULO DE EVOLUCIÓN - NO AFECTA NÚCLEO (IMPORTACIONES VISUALIZACIÓN)
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

import streamlit as st

st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

# ============================================================
# ANIMACIÓN DE INAUGURACIÓN PRO (SOLO PRIMERA VEZ)
# ============================================================
import streamlit.components.v1 as components

if "inauguracion" not in st.session_state:
    st.session_state.inauguracion = True

    components.html(
        """
        <style>
        body {
            margin: 0;
            overflow: hidden;
        }

        #cinta-left, #cinta-right {
            position: fixed;
            top: 50%;
            transform: translateY(-50%);
            width: 50%;
            height: 40px;
            background: linear-gradient(90deg, #b30000, #ff0000);
            z-index: 9998;
            transition: transform 0.8s ease-out, opacity 1s ease-out;
        }

        #cinta-left {
            left: 0;
            border-right: 4px solid gold;
        }

        #cinta-right {
            right: 0;
            border-left: 4px solid gold;
        }

        #tijeras {
            position: fixed;
            font-size: 70px;
            z-index: 10000;
            pointer-events: none;
            transition: transform 0.05s linear, opacity 0.3s ease;
        }

        #humo {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 120px;
            opacity: 0;
            z-index: 10001;
            transition: opacity 0.4s ease-out, transform 0.6s ease-out;
        }

        .confeti {
            position: fixed;
            width: 10px;
            height: 14px;
            background: hsl(var(--hue), 90%, 60%);
            top: -20px;
            border-radius: 2px;
            animation: caer linear forwards;
            z-index: 10002;
        }

        @keyframes caer {
            to {
                transform: translateY(120vh) rotate(720deg);
            }
        }
        </style>

        <div id="cinta-left"></div>
        <div id="cinta-right"></div>
        <div id="tijeras">✂️</div>
        <div id="humo">💨</div>

        <script>
        const tijeras = document.getElementById("tijeras");
        const left = document.getElementById("cinta-left");
        const right = document.getElementById("cinta-right");
        const humo = document.getElementById("humo");

        let cortado = false;

        document.addEventListener("mousemove", (e) => {
            // Posición tijeras
            tijeras.style.left = (e.clientX - 30) + "px";
            tijeras.style.top = (e.clientY - 30) + "px";

            // Rotación natural
            const centro = window.innerWidth / 2;
            tijeras.style.transform = `rotate(${(e.clientX - centro)/20}deg)`;

            const tRect = tijeras.getBoundingClientRect();
            const lRect = left.getBoundingClientRect();

            // Corte solo en zona central (más realista)
            if (!cortado &&
                Math.abs(e.clientX - centro) < 80 &&
                tRect.top < lRect.bottom &&
                tRect.bottom > lRect.top) {

                cortado = true;

                // Animación cinta
                left.style.transform = "translateX(-120%) rotate(-10deg)";
                right.style.transform = "translateX(120%) rotate(10deg)";
                left.style.opacity = "0";
                right.style.opacity = "0";

                // HUMO
                humo.style.opacity = "1";
                humo.style.transform = "translate(-50%, -50%) scale(1.6)";
                setTimeout(() => humo.style.opacity = "0", 600);

                // CONFETI MÁS NATURAL
                for (let i = 0; i < 300; i++) {
                    let c = document.createElement("div");
                    c.classList.add("confeti");
                    c.style.left = Math.random() * 100 + "vw";
                    c.style.setProperty("--hue", Math.random() * 360);
                    c.style.animationDuration = (2 + Math.random() * 2) + "s";
                    document.body.appendChild(c);
                    setTimeout(() => c.remove(), 4000);
                }

                // Ocultar tijeras
                setTimeout(() => {
                    tijeras.style.opacity = "0";
                }, 800);

                // Limpieza
                setTimeout(() => {
                    left.remove();
                    right.remove();
                    tijeras.remove();
                    humo.remove();
                }, 2500);
            }
        });
        </script>
        """,
        height=1000,
    )
# ============================================================

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

if "orq" not in st.session_state:
    st.session_state.orq = ClinicoOrchestrator()

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

# --- INTEGRACIÓN DE CARGA (SUSTITUCIÓN PUNTO ÚNICO) ---
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

# --- EVOLUCIÓN: MOTOR DE RANKING UNIVERSAL ---
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
                # ---------------------------------------------------------
        # 🔥 BROMA PRO: HUMO + VIBRACIÓN + BLACKOUT + ERROR CRÍTICO
        # ---------------------------------------------------------
        import streamlit.components.v1 as components

        if st.button("🧪 Modo Diagnóstico Experimental"):
            components.html(
                """
                <style>
                body { overflow: hidden; }

                @keyframes shake {
                  0% { transform: translate(0px); }
                  25% { transform: translate(5px, -5px); }
                  50% { transform: translate(-5px, 5px); }
                  75% { transform: translate(5px, 5px); }
                  100% { transform: translate(0px); }
                }

                #blackout {
                    position: fixed;
                    top: 0; left: 0;
                    width: 100vw; height: 100vh;
                    background: black;
                    opacity: 0;
                    z-index: 99998;
                    transition: opacity 0.3s ease-out;
                }

                #humo {
                    position: fixed;
                    top: 40%; left: 45%;
                    font-size: 150px;
                    opacity: 0;
                    z-index: 99999;
                    transition: opacity 0.3s ease-out, transform 0.4s ease-out;
                }

                #error-msg {
                    position: fixed;
                    top: 50%; left: 50%;
                    transform: translate(-50%, -50%);
                    font-size: 50px;
                    color: red;
                    font-weight: bold;
                    opacity: 0;
                    z-index: 100000;
                    transition: opacity 0.4s ease-out;
                }
                </style>

                <div id="blackout"></div>
                <div id="humo">💨</div>
                <div id="error-msg">ERROR CRÍTICO 😂</div>

                <script>
                document.body.style.animation = "shake 0.4s";

                const audio = new Audio("https://www.myinstants.com/media/sounds/cartoon-fail.mp3");
                audio.play();

                setTimeout(() => {
                    document.getElementById("blackout").style.opacity = "1";
                }, 200);

                setTimeout(() => {
                    const h = document.getElementById("humo");
                    h.style.opacity = "1";
                    h.style.transform = "scale(1.4)";
                }, 400);

                setTimeout(() => {
                    document.getElementById("error-msg").style.opacity = "1";
                }, 700);

                setTimeout(() => {
                    document.getElementById("blackout").style.opacity = "0";
                    document.getElementById("humo").style.opacity = "0";
                    document.getElementById("error-msg").style.opacity = "0";
                }, 2000);
                </script>
                """,
                height=600,
            )
        # ---------------------------------------------------------

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
                    prompt_final = f"{c.PROMPT_AFR_V10}\n\nFG C-G: {valor_fg}\nFG CKD: {val_ckd}\nFG MDRD: {val_mdrd}\n\nMEDS:\n{st.session_state.main_meds}"
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
            except: 
                pass
        except: 
            pass

    st.markdown('<div class="warning-yellow">⚠️ AVISO LEGAL: Esta herramienta es un soporte de apoyo a la revisión farmacoterapéutica. Verifique siempre con fuentes oficiales.</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align: right; font-size: 0.6rem; color: #ccc; font-family: monospace;">v. 29 mar 2026 13:20</div>', unsafe_allow_html=True)
