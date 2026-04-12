import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import uuid
import hashlib
import re

# =============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS (PRINCIPIOS FUNDAMENTALES)
# =============================================================================
st.set_page_config(page_title="Gestión Renal Avanzada", layout="wide", initial_sidebar_state="collapsed")

def local_css():
    st.markdown("""
        <style>
        /* Estilos Globales e Inmutables */
        .main { background-color: #0e1117; color: #ffffff; }
        .stMetric { background-color: #1e2130; border-radius: 10px; padding: 15px; border: 1px solid #3e4259; }
        .warning-yellow { background-color: #ffff00; color: #000000; padding: 10px; border-radius: 5px; font-weight: bold; margin: 10px 0; }
        .db-glow-box { border-radius: 10px; padding: 20px; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.1); }
        .db-blue { background: linear-gradient(135deg, #1e3a8a 0%, #1e293b 100%); box-shadow: 0 0 15px rgba(59,130,246,0.5); }
        .db-green { background: linear-gradient(135deg, #064e3b 0%, #1e293b 100%); box-shadow: 0 0 15px rgba(16,185,129,0.5); }
        .db-red { background: linear-gradient(135deg, #7f1d1d 0%, #1e293b 100%); box-shadow: 0 0 15px rgba(239,68,68,0.5); }
        .db-purple { background: linear-gradient(135deg, #581c87 0%, #1e293b 100%); box-shadow: 0 0 15px rgba(168,85,247,0.5); }
        
        /* BLOQUE CALCULADORA - DISEÑO INMUTABLE */
        .calc-container { background-color: #000000; padding: 25px; border-radius: 15px; border: 2px solid #9d00ff; box-shadow: 0 0 20px rgba(157, 0, 255, 0.3); }
        .fg-display { font-size: 3.5rem; font-weight: 800; color: #ffffff; text-shadow: 0 0 10px #9d00ff; text-align: center; }
        
        /* NUEVOS ESTILOS PARA CONSULTA DINÁMICA (CARDS) */
        .card-query-a { border: 2px solid #3b82f6; padding: 20px; border-radius: 15px; background-color: #161b22; box-shadow: 2px 2px 10px rgba(0,0,0,0.3); margin-bottom: 15px; }
        .card-query-b { border: 2px solid #10b981; padding: 20px; border-radius: 15px; background-color: #161b22; box-shadow: 2px 2px 10px rgba(0,0,0,0.3); margin-bottom: 15px; }
        .card-query-c { border: 2px solid #f59e0b; padding: 20px; border-radius: 15px; background-color: #161b22; box-shadow: 2px 2px 10px rgba(0,0,0,0.3); margin-bottom: 15px; }
        .card-query-d { border: 2px solid #ef4444; padding: 20px; border-radius: 15px; background-color: #161b22; box-shadow: 2px 2px 10px rgba(0,0,0,0.3); margin-bottom: 15px; }
        .card-chat { border: 2px solid #8b5cf6; padding: 20px; border-radius: 15px; background-color: #1e1e2e; box-shadow: 4px 4px 15px rgba(0,0,0,0.4); margin-top: 20px; }
        .sep-analisis { border-top: 3px dashed #3e4259; margin: 40px 0; opacity: 0.6; }
        </style>
    """, unsafe_allow_html=True)

local_css()

# =============================================================================
# 2. FUNCIONES DE LÓGICA Y UTILIDADES (INMUTABLES)
# =============================================================================
def normalizar_texto_capa0(texto, quitar_dosis=False):
    if not texto or not isinstance(texto, str): return ""
    t = texto.upper().strip()
    t = re.sub(r'[ÁÉÍÓÚÜ]', lambda m: {'Á':'A','É':'E','Í':'I','Ó':'O','Ú':'U','Ü':'U'}[m.group()], t)
    if quitar_dosis:
        patrones = [r'\d+\s*MG', r'\d+\s*G', r'\d+\s*ML', r'\d+\s*UI']
        for p in patrones: t = re.sub(p, '', t)
    return t.strip()

def calcular_fg_cockcroft(edad, peso, creatinina, sexo):
    try:
        if creatinina <= 0: return 0
        fg = ((140 - edad) * peso) / (72 * creatinina)
        if sexo == "Mujer": fg *= 0.85
        return round(fg, 2)
    except: return 0

def limpiar_filtros_dinamicos():
    st.session_state.filtros_dinamicos = []

# =============================================================================
# 3. ESTADO DE SESIÓN (SESSION STATE)
# =============================================================================
if "filtros_dinamicos" not in st.session_state:
    st.session_state.filtros_dinamicos = []

if "df_sync_val" not in st.session_state:
    st.session_state["df_sync_val"] = pd.DataFrame()
if "df_sync_meds" not in st.session_state:
    st.session_state["df_sync_meds"] = pd.DataFrame()
if "df_sync_analisis" not in st.session_state:
    st.session_state["df_sync_analisis"] = pd.DataFrame()

# Mock de funciones que el código original espera encontrar (simuladas para integridad)
def ejecutar_ranking_v29(df, dim, met, top, key):
    st.write(f"Ranking de {dim} por {met} (Top {top})")
    # Lógica de ranking interna...

# =============================================================================
# 4. INTERFAZ PRINCIPAL - TABS
# =============================================================================
st.title("🛡️ Sistema de Soporte Renal")

tabs = st.tabs(["🏠 Inicio", "🧮 Calculadora", "📋 Sincronización", "📈 Dashboard", "🔍 Consulta Dinámica"])

with tabs[0]:
    st.markdown("## Bienvenid@ al Sistema de Gestión Renal")
    st.info("Utilice las pestañas superiores para navegar por las herramientas.")

with tabs[1]:
    st.markdown("### 🧮 Calculadora de Función Renal")
    with st.container():
        st.markdown('<div class="calc-container">', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1: edad_c = st.number_input("Edad", 1, 120, 75)
        with c2: peso_c = st.number_input("Peso (kg)", 10, 250, 70)
        with c3: crea_c = st.number_input("Creatinina (mg/dL)", 0.1, 15.0, 1.2)
        with c4: sexo_c = st.selectbox("Sexo", ["Hombre", "Mujer"])
        
        fg_res = calcular_fg_cockcroft(edad_c, peso_c, crea_c, sexo_c)
        st.markdown(f'<div class="fg-display">{fg_res}</div>', unsafe_allow_html=True)
        st.markdown('<p style="text-align:center; color:#9d00ff;">mL/min (Cockcroft-Gault)</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

with tabs[2]:
    st.markdown("### 📋 Sincronización de Datos")
    st.warning("Conecte con su fuente de datos (Google Sheets / Excel) para habilitar los análisis.")
    if st.button("Simular Carga de Datos (v29)"):
        # Generación de datos simulados para permitir que las pestañas 3 y 4 funcionen
        data_val = {
            "ID_REGISTRO": range(1, 11),
            "CENTRO": ["Centro A", "Centro B"] * 5,
            "EDAD": [70, 82, 65, 90, 75, 88, 54, 77, 81, 69],
            "FG_CG": [45, 32, 58, 12, 44, 28, 95, 33, 21, 50],
            "PESO": [70, 65, 80, 55, 72, 68, 85, 60, 74, 70],
            "CREATININA": [1.2, 1.5, 0.9, 2.5, 1.3, 1.8, 0.8, 1.6, 2.1, 1.1],
            "Nº_TOTAL_MEDS_PAC": [8, 12, 5, 15, 9, 11, 4, 13, 10, 7],
            "Nº_TOT_AFEC_CG": [1, 3, 0, 5, 2, 2, 0, 4, 3, 1],
            "RESIDENCIA": ["Res1", "Res2"] * 5,
            "SEXO": ["H", "M"] * 5
        }
        data_meds = {
            "ID_REGISTRO": [1, 2, 4, 4, 4, 5, 5, 8, 9, 10],
            "MEDICAMENTO": ["METFORMINA", "ENALAPRIL", "IBUPROFENO", "METFORMINA", "DIGOXINA", "ALOPURINOL", "LIRAGLUTIDA", "ESPIRONOLACTONA", "RIVAROXABAN", "GABAPENTINA"],
            "NIVEL_ADE_CG": [2, 1, 4, 2, 3, 2, 2, 2, 3, 1],
            "CENTRO": ["Centro A", "Centro B", "Centro B", "Centro B", "Centro B", "Centro A", "Centro A", "Centro B", "Centro A", "Centro B"]
        }
        st.session_state["df_sync_val"] = pd.DataFrame(data_val)
        st.session_state["df_sync_meds"] = pd.DataFrame(data_meds)
        st.success("Datos cargados correctamente.")

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
                if tipo_graf_riesgo == "-- seleccionar --":
                    fig_riesgo = px.pie(df_cat, names="ETIQUETA", values="count", color="ETIQUETA", color_discrete_map=color_map, hole=0.4)
                    fig_riesgo.update_layout(height=300, margin=dict(t=10, b=10, l=40, r=10), showlegend=True, legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05))
                    fig_riesgo.update_traces(sort=False)
                    st.plotly_chart(fig_riesgo, use_container_width=True)
                elif tipo_graf_riesgo == "Sectores":
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
                    if tipo_graf_top == "-- seleccionar --":
                        fig_top = px.bar(df_top_final, y="MED_NORM", x="Frecuencia", orientation='h', text="Frecuencia", color="Frecuencia", color_continuous_scale="Reds")
                        fig_top.update_layout(showlegend=False, height=300, margin=dict(t=10, b=10, l=10, r=10), yaxis={'categoryorder':'total ascending'})
                        st.plotly_chart(fig_top, use_container_width=True)
                    elif tipo_graf_top == "Barras Horizontales":
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
    
    tipo_origen = st.radio(
        "Seleccionar origen de datos:",
        ["Validaciones (General)", "Medicamentos (Detalle)"],
        horizontal=True
    )

    df_pool = (
        st.session_state["df_sync_val"].copy()
        if "Validaciones" in tipo_origen
        else st.session_state["df_sync_meds"].copy()
    )

    if not df_pool.empty:
        # CONTENEDOR BLOQUE B (Ahora en posición A) - Variable a analizar
        st.markdown('<div class="card-query-b">', unsafe_allow_html=True)
        st.markdown("#### 🎯 Bloque B - Variable a analizar: <span style='font-size: 0.8em; color: gray;'>¿Qué quiero medir?</span>", unsafe_allow_html=True)
        b_col1, b_col2, b_col3 = st.columns(3)
        var_analisis = b_col1.selectbox("Variable", ["-- seleccionar --"] + list(df_pool.columns), key="query_var")
        operacion = b_col2.selectbox("Operación", ["-- seleccionar --", "Conteo (Total)", "Conteo Único (Pacientes)", "Suma", "Promedio", "Mínimo", "Máximo"])
        agrupar_por = b_col3.selectbox("Agrupar por (Opcional)", ["-- Agrupar resultados por categorías (opcional) --"] + list(df_pool.columns))
        st.markdown('</div>', unsafe_allow_html=True)

        # CONTENEDOR BLOQUE A (Ahora en posición B) - Filtros o condiciones
        st.markdown('<div class="card-query-a">', unsafe_allow_html=True)
        st.markdown("#### 🔍 Bloque A - Filtros o condiciones: <span style='font-size: 0.8em; color: gray;'>Condiciones de lo que quiero medir.</span>", unsafe_allow_html=True)
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
        st.markdown('</div>', unsafe_allow_html=True)

        # Lógica de Filtrado (Inmutable)
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
                    if isinstance(f["val"], list) and f["val"]: mask &= col_norm.isin(input_norm)
                    elif f["val"] != "": mask &= (col_norm == input_norm)
                elif "!=" in f["op"]: mask &= (col_data.astype(str) != str(f["val"]))
                elif ">" in f["op"] and "≥" not in f["op"]: mask &= (pd.to_numeric(col_data, errors='coerce') > float(f["val"]))
                elif "<" in f["op"] and "≤" not in f["op"]: mask &= (pd.to_numeric(col_data, errors='coerce') < float(f["val"]))
                elif "≥" in f["op"]: mask &= (pd.to_numeric(col_data, errors='coerce') >= float(f["val"]))
                elif "≤" in f["op"]: mask &= (pd.to_numeric(col_data, errors='coerce') <= float(f["val"]))
                elif "contiene" in f["op"]: mask &= col_norm.str.contains(input_norm, na=False)
            except: continue
        
        df_filtered_query = df_pool[mask]

        # CONTENEDOR BLOQUE C - Visualización
        st.markdown('<div class="card-query-c">', unsafe_allow_html=True)
        st.markdown("#### 📊 Bloque C - Visualización", unsafe_allow_html=True)
        if var_analisis == "-- seleccionar --" or operacion == "-- seleccionar --":
            st.info("Configura la variable y operación para ver resultados.")
        else:
            if agrupar_por == "-- Agrupar resultados por categorías (opcional) --": agrupar_por = "Ninguno"
            
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
                    
                    formato_salida = st.radio("Formato:", ["KPI", "LISTAR", "TABLA", "BARRAS H", "BARRAS V", "SECTORES", "HISTOGRAMA"], horizontal=True)
                    if formato_salida == "KPI":
                        st.metric("Registros en Cohorte", len(df_filtered_query))
                    elif formato_salida == "LISTAR":
                        valores_unicos = sorted(df_filtered_query[var_analisis].dropna().unique().astype(str))
                        if valores_unicos:
                            for val in valores_unicos: st.write(f"* {val}")
                        else: st.write("No hay valores para listar.")
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
                            else: st.warning("La variable no contiene datos numéricos válidos.")
                except: st.warning("Error en el cálculo.")
        st.markdown('</div>', unsafe_allow_html=True)

        # CONTENEDOR BLOQUE D - Ranking/Top
        st.markdown('<div class="card-query-d">', unsafe_allow_html=True)
        st.markdown("#### 🏆 Bloque D - Ranking/Top: <span style='font-size: 0.8em; color: gray;'>Comparativas de prevalencia.</span>", unsafe_allow_html=True)
        rk_c1, rk_c2, rk_c3 = st.columns(3)
        rk_dim = rk_c1.selectbox("Elemento a Rankear", ["-- seleccionar --", "MEDICAMENTO", "CENTRO", "RESIDENCIA", "SEXO"], key="rk_dim")
        rk_met = rk_c2.selectbox("Métrica de Orden", ["-- seleccionar --", "Conteo (Total)", "Conteo Único (Pacientes)", "Nº_TOT_AFEC_CG", "Nº_AJUSTE_DOS_CG", "Nº_CONTRAIND_CG"], key="rk_met")
        rk_top = rk_c3.slider("Ver Top:", 3, 20, 5, key="rk_top")
        
        if rk_dim != "-- seleccionar --" and rk_met != "-- seleccionar --":
            r_key = hashlib.md5(f"{rk_dim}_{rk_met}_{rk_top}".encode()).hexdigest()[:8]
            ejecutar_ranking_v29(df_filtered_query, rk_dim, rk_met, rk_top, r_key)
        st.markdown('</div>', unsafe_allow_html=True)

        # ZONA DE SEPARACIÓN VISIBLE
        st.markdown('<div class="sep-analisis"></div>', unsafe_allow_html=True)

        # VENTANA DE CHAT (Consultas Rápidas)
        st.markdown('<div class="card-chat">', unsafe_allow_html=True)
        st.markdown("#### 🤖 Ventana de chat")
        query_text = st.text_input("Haz una pregunta sobre los datos:", placeholder="Ej: Top 5 medicamentos, ¿Cuántos pacientes edad < 70 hay?", key="chat_input")
        if query_text:
            with st.spinner("IA analizando datos..."):
                # Mock de respuesta de orquestador para mantener integridad sin código externo
                st.write(f"Respuesta simulada para: '{query_text}'")
                st.info("El motor IA procesaría los datos filtrados en la cohorte actual.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")
        with st.expander("📄 Ver Datos Crutos de la Cohorte"):
            st.dataframe(df_filtered_query, use_container_width=True)

    else:
        st.info("No hay datos sincronizados para realizar consultas dinámicas.")

# =============================================================================
# 5. PIE DE PÁGINA (AVISOS LEGALES E INMUTABLES)
# =============================================================================
st.markdown('<div class="warning-yellow">⚠️ AVISO LEGAL: Esta herramienta es un soporte de apoyo a la revisión farmacoterapéutica. Verifique siempre con fuentes oficiales.</div>', unsafe_allow_html=True)
st.markdown(f'<div style="text-align: right; font-size: 0.6rem; color: #ccc; font-family: monospace;">v. 29 mar 2026 13:20</div>', unsafe_allow_html=True)
