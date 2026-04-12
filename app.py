import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import unicodedata
import re
import hashlib
import json
import uuid
import io
from datetime import datetime
import random

# --- REGLAS INMUTABLES Y CONFIGURACIÓN ---
# (Se asume la existencia de las funciones de Sheets y el orquestador en el entorno)

# --- BLOQUE 1: FUNCIONES NÚCLEO ---
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

# --- BLOQUE 2: DISEÑO E INTERFAZ ---
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
    .synthesis-box { padding: 15px; border-radius: 12px; margin-bottom: 15px; border-width: 2.2px; border-style: solid; font-size: 0.95rem; line-height: 1.6; }
    .glow-red { background-color: #fff5f5; color: #c53030; border-color: #feb2b2; box-shadow: 0 0 12px #feb2b2; }
    .glow-orange { background-color: #fffaf0; color: #c05621; border-color: #fbd38d; box-shadow: 0 0 12px #fbd38d; }
    .glow-yellow-dark { background-color: #fff8dc; color: #b36b00; border-color: #ffd27f; box-shadow: 0 0 12px #ffd27f; }
    .glow-yellow { background-color: #fffff0; color: #975a16; border-color: #faf089; box-shadow: 0 0 12px #faf089; }
    .glow-green { background-color: #f0fff4; color: #2f855a; border-color: #9ae6b4; box-shadow: 0 0 12px #9ae6b4; }
    .warning-yellow { background-color: #fff9db; color: #856404; padding: 20px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 40px; text-align: center; font-size: 0.85rem; line-height: 1.5; }
    </style>
    """, unsafe_allow_html=True)

inject_styles()
st.markdown('<div class="black-badge-zona">ZONA: ACTIVA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="black-badge-activo">ACTIVO: {st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-version">v. 29 mar 2026 13:20</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 DATOS", "📈 GRÁFICOS", "🔍 CONSULTA DINÁMICA"])

# --- (Tabs 0, 1, 2, 3 se mantienen con tu lógica original) ---

# --- BLOQUE 3: CONSULTA DINÁMICA (REESTRUCTURADO) ---
with tabs[4]:
    st.markdown("### 🔍 Consulta Dinámica Renal")
    
    tipo_origen = st.radio("Seleccionar origen de datos:", ["Validaciones (General)", "Medicamentos (Detalle)"], horizontal=True)

    df_pool = (st.session_state["df_sync_val"].copy() if "Validaciones" in tipo_origen else st.session_state["df_sync_meds"].copy())

    if not df_pool.empty:
        # 1. CARD BLOQUE A: VARIABLE A ANALIZAR (Intercambiado)
        with st.container():
            st.markdown("""<div style="border: 2px solid #63b3ed; padding: 20px; border-radius: 15px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); margin-bottom: 25px;">
                <h4 style="margin:0; color:#2b6cb0;">Variable a analizar: Qué quiero medir</h4></div>""", unsafe_allow_html=True)
            b_col1, b_col2, b_col3 = st.columns(3)
            var_analisis = b_col1.selectbox("Variable", ["-- seleccionar --"] + list(df_pool.columns), key="query_var")
            operacion = b_col2.selectbox("Operación", ["-- seleccionar --", "Conteo (Total)", "Conteo Único (Pacientes)", "Suma", "Promedio", "Mínimo", "Máximo"])
            agrupar_por = b_col3.selectbox("Agrupar por (Opcional)", ["-- Agrupar resultados por categorías (opcional) --"] + list(df_pool.columns))

        # 2. CARD BLOQUE B: FILTROS O CONDICIONES (Intercambiado)
        with st.container():
            st.markdown("""<div style="border: 2px solid #68d391; padding: 20px; border-radius: 15px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); margin-bottom: 25px;">
                <h4 style="margin:0; color:#2f855a;">Filtros o condiciones</h4></div>""", unsafe_allow_html=True)
            col_a1, col_a2 = st.columns([1, 1])
            if col_a1.button("➕ Añadir Filtro"):
                st.session_state.filtros_dinamicos.append({"id": str(uuid.uuid4()), "col": df_pool.columns[0], "op": "== (IGUAL)", "val": ""})
            if col_a2.button("🗑️ Limpiar Filtros"):
                limpiar_filtros_dinamicos(); st.rerun()
            
            for i, filtro in enumerate(st.session_state.filtros_dinamicos):
                fid = filtro["id"]
                f_c1, f_c2, f_c3 = st.columns([1, 0.7, 1.3])
                filtro["col"] = f_c1.selectbox(f"Columna {i+1}", df_pool.columns, key=f"f_col_{fid}", index=list(df_pool.columns).index(filtro["col"]))
                filtro["op"] = f_c2.selectbox(f"Operador {i+1}", ["== (IGUAL)", "!= (DISTINTO DE)", "> (MAYOR QUE)", "< (MENOR QUE)", "contiene"], key=f"f_op_{fid}")
                filtro["val"] = f_c3.text_input(f"Valor {i+1}", key=f"f_val_{fid}", value=filtro["val"])

        # Lógica de filtrado (Inmueble)
        mask = pd.Series(True, index=df_pool.index)
        # ... (Se aplica mask según filtros_dinamicos)
        df_filtered_query = df_pool[mask]

        # 3. CARD BLOQUE C: VISUALIZACIÓN
        with st.container():
            st.markdown("""<div style="border: 2px solid #b794f4; padding: 20px; border-radius: 15px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); margin-bottom: 25px;">
                <h4 style="margin:0; color:#6b46c1;">Visualización</h4></div>""", unsafe_allow_html=True)
            if var_analisis != "-- seleccionar --" and operacion != "-- seleccionar --":
                formato_salida = st.radio("Formato:", ["KPI", "LISTAR", "TABLA", "BARRAS H", "BARRAS V", "SECTORES", "HISTOGRAMA"], horizontal=True)
                # ... (Lógica de renderizado según formato_salida)
            else: st.info("Configura la variable y operación.")

        # 4. CARD BLOQUE D: RANKING/TOP
        with st.container():
            st.markdown("""<div style="border: 2px solid #fc8181; padding: 20px; border-radius: 15px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); margin-bottom: 25px;">
                <h4 style="margin:0; color:#c53030;">Ranking/Top</h4></div>""", unsafe_allow_html=True)
            rk_c1, rk_c2, rk_c3 = st.columns(3)
            rk_dim = rk_c1.selectbox("Elemento a Rankear", ["-- seleccionar --", "MEDICAMENTO", "CENTRO"], key="rk_dim")
            rk_met = rk_c2.selectbox("Métrica", ["-- seleccionar --", "Conteo (Total)", "Nº_TOT_AFEC_CG"], key="rk_met")
            rk_top = rk_c3.slider("Ver Top:", 3, 20, 5)
            if rk_dim != "-- seleccionar --" and rk_met != "-- seleccionar --":
                ejecutar_ranking_v29(df_filtered_query, rk_dim, rk_met, rk_top, "rk_tab4")

        # ZONA DE SEPARACIÓN DIFERENCIADA
        st.markdown("<br><div style='border-top: 3px dashed #9d00ff; margin: 20px 0; opacity: 0.5;'></div><br>", unsafe_allow_html=True)

        # 5. CARD VENTANA DE CHAT
        with st.container():
            st.markdown("""<div style="border: 2px solid #9d00ff; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(157,0,255,0.1); margin-bottom: 25px; background-color: #fdfaff;">
                <h4 style="margin:0; color:#9d00ff;">🤖 Consultas Rápidas</h4></div>""", unsafe_allow_html=True)
            query_text = st.text_input("Haz una pregunta sobre los datos:", placeholder="Ej: ¿Qué centro tiene más alertas?")
            if query_text:
                with st.spinner("IA analizando..."):
                    # ... (Lógica orquestador)
                    pass

    else: st.info("No hay datos sincronizados.")

st.markdown('<div class="warning-yellow">⚠️ AVISO LEGAL: Soporte a la revisión farmacoterapéutica. Verifique siempre con fuentes oficiales.</div>', unsafe_allow_html=True)
