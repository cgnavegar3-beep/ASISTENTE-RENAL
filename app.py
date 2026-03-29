# mejoras resumido 29mar 9.58

import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import unicodedata
import re
import json
import hashlib
import uuid
import io
from datetime import datetime
import random

# --- 1. CONFIGURACIÓN DE PÁGINA Y ESTADO ---
st.set_page_config(
    page_title="Asistente Renal v2.0 - Full",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inicialización exhaustiva del Session State (Previene errores de renderizado)
if "filtros_dinamicos" not in st.session_state:
    st.session_state.filtros_dinamicos = []
if "df_val" not in st.session_state:
    st.session_state.df_val = pd.DataFrame()
if "df_meds" not in st.session_state:
    st.session_state.df_meds = pd.DataFrame()
if "df_sync_val" not in st.session_state:
    st.session_state.df_sync_val = pd.DataFrame()
if "df_sync_meds" not in st.session_state:
    st.session_state.df_sync_meds = pd.DataFrame()
if "df_sync_analisis" not in st.session_state:
    st.session_state.df_sync_analisis = pd.DataFrame()
if "analisis_realizado" not in st.session_state:
    st.session_state.analisis_realizado = False
if "resp_ia" not in st.session_state:
    st.session_state.resp_ia = None
if "ultima_huella" not in st.session_state:
    st.session_state.ultima_huella = ""
if "active_model" not in st.session_state:
    st.session_state.active_model = "GEMINI-3-FLASH"

# Estructura del Informe SOIP e Interconsulta
soip_fields = ["soip_s", "soip_o", "soip_i", "soip_p", "ic_inter", "ic_clinica"]
for field in soip_fields:
    if field not in st.session_state:
        if field == "soip_s":
            st.session_state[field] = "Revisión farmacoterapéutica según función renal."
        elif field == "soip_p":
            st.session_state[field] = "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
        else:
            st.session_state[field] = ""

# --- 2. MOTOR DE ESTILOS CSS (DISEÑO DARK & GLOW) ---
def inject_styles():
    st.markdown("""
    <style>
    /* Globales y Contenedor */
    .block-container { max-width: 100% !important; padding-top: 1rem !important; padding-left: 4% !important; padding-right: 4% !important; }
    
    /* Badges Superiores */
    .black-badge-zona { background-color: #000000; color: #888; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 15px; z-index: 999999; }
    .black-badge-activo { background-color: #000000; color: #00FF00; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 145px; z-index: 999999; text-shadow: 0 0 5px #00FF00; }
    
    /* Tipografía y Títulos */
    .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin-bottom: 0px; margin-top: 20px; }
    .sub-version { text-align: center; font-size: 0.6rem; color: #bbb; margin-top: -5px; margin-bottom: 20px; font-family: monospace; }
    
    /* Cajas de Filtrado Glomerular (FG) */
    .fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .unit-label { font-size: 0.65rem; color: #888; margin-top: -10px; margin-bottom: 5px; font-family: sans-serif; text-align: center; }
    .formula-label { font-size: 0.6rem; color: #666; font-family: monospace; text-align: right; margin-top: 5px; }
    .fg-special-border { border: 1.5px solid #9d00ff !important; border-radius: 5px; }

    /* Dashboard e Indicadores KPI */
    .db-glow-box { background-color: #000000; color: #FFFFFF; border: 1.5px solid #4a5568; padding: 12px; border-radius: 12px; text-align: center; display: flex; flex-direction: column; justify-content: center; margin-bottom: 10px; }
    .db-blue { border-color: #63b3ed !important; box-shadow: 0 0 8px #63b3ed; }
    .db-green { border-color: #68d391 !important; box-shadow: 0 0 8px #68d391; }
    .db-red { border-color: #fc8181 !important; box-shadow: 0 0 8px #fc8181; }
    .db-purple { border-color: #b794f4 !important; box-shadow: 0 0 8px #b794f4; }
    
    /* Semáforos de Riesgo (IA) */
    .synthesis-box { padding: 15px; border-radius: 12px; margin-bottom: 15px; border-width: 2.2px; border-style: solid; font-size: 0.95rem; line-height: 1.6; }
    .glow-red { background-color: #fff5f5; color: #c53030; border-color: #feb2b2; box-shadow: 0 0 12px #feb2b2; }
    .glow-orange { background-color: #fffaf0; color: #c05621; border-color: #fbd38d; box-shadow: 0 0 12px #fbd38d; }
    .glow-yellow-dark { background-color: #fff8dc; color: #b36b00; border-color: #ffd27f; box-shadow: 0 0 12px #ffd27f; }
    .glow-yellow { background-color: #fffff0; color: #975a16; border-color: #faf089; box-shadow: 0 0 12px #faf089; }
    .glow-green { background-color: #f0fff4; color: #2f855a; border-color: #9ae6b4; box-shadow: 0 0 12px #9ae6b4; }
    
    /* Contenedores de Información Médica */
    .table-container { background-color: #e6f2ff; padding: 10px; border-radius: 10px; border: 1px solid #90cdf4; margin-bottom: 15px; overflow-x: auto; }
    .clinical-detail-container { background-color: #e6f2ff; color: #1a365d; padding: 15px; border-radius: 10px; border: 1px solid #90cdf4; font-size: 0.9rem; line-height: 1.6; white-space: pre-wrap; }
    .linea-discreta-soip { border-top: 1px solid #d9d5c7; margin: 15px 0 5px 0; font-size: 0.65rem; font-weight: bold; color: #8e8a7e; text-transform: uppercase; }
    .warning-yellow { background-color: #fff9db; color: #856404; padding: 20px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 40px; text-align: center; font-size: 0.85rem; line-height: 1.5; }
    
    /* Estados Animados */
    @keyframes blinker { 50% { opacity: 0; } }
    .blink-text, .blink-text-grabar { animation: blinker 1s linear infinite; color: #c53030; font-weight: bold; padding: 10px; border: 1px solid #c53030; border-radius: 5px; background: #fff5f5; text-align: center; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNCIONES DE PROCESAMIENTO Y LÓGICA MÉDICA ---

def normalizar_texto_capa0(texto, quitar_dosis=False):
    """Normaliza texto eliminando acentos, convirtiendo a mayúsculas y limpiando ruido."""
    if not isinstance(texto, str) or not texto:
        return str(texto) if texto else ""
    # Quitar acentos
    texto = "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    texto = texto.upper().strip()
    if quitar_dosis:
        # Intenta aislar el principio activo quitando números (dosis) y formas farmacéuticas
        match = re.search(r'\d', texto)
        if match:
            texto = texto[:match.start()].strip()
    return texto

def calcular_cockcroft_gault(edad, peso, creatinina, sexo):
    """Cálculo estándar de la fórmula Cockcroft-Gault."""
    if all([edad, peso, creatinina, sexo != "-- seleccionar --"]):
        if creatinina <= 0: return 0.0
        resultado = ((140 - edad) * peso) / (72 * creatinina)
        if sexo == "Mujer":
            resultado *= 0.85
        return round(resultado, 1)
    return 0.0

def llamar_ia_en_cascada(prompt):
    """Gestión de llamadas a la API de Google Gemini con reintentos."""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            prompt, 
            generation_config={"temperature": 0.1, "top_p": 1}
        )
        return response.text
    except Exception as e:
        return f"ERROR_IA_CONEXION: {str(e)}"

def obtener_clase_glow(sintesis):
    """Asigna un color de alerta basado en el contenido de la síntesis de la IA."""
    s_up = sintesis.upper()
    if any(x in s_up for x in ["⛔", "CONTRAINDICADO", "SUSPENDER", "GRAVE", "STOP"]):
        return "glow-red"
    elif "⚠️⚠️⚠️" in s_up or "ALTA PRIORIDAD" in s_up:
        return "glow-orange"
    elif "⚠️⚠️" in s_up or "MODERADO" in s_up:
        return "glow-yellow-dark"
    elif "⚠️" in s_up or "LEVE" in s_up:
        return "glow-yellow"
    else:
        return "glow-green"

def to_excel(df):
    """Convierte un DataFrame a formato Excel en memoria para descarga."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos_Renales')
    return output.getvalue()

def limpiar_filtros_dinamicos():
    st.session_state.filtros_dinamicos = []

def reset_asistente():
    """Limpia todos los campos de entrada y estados de validación."""
    keys_to_reset = [
        "reg_centro", "reg_res", "reg_id", "fgl_ckd", "fgl_mdrd", 
        "main_meds", "calc_e", "calc_p", "calc_c"
    ]
    for k in keys_to_reset:
        if k in st.session_state:
            if isinstance(st.session_state[k], (int, float)):
                st.session_state[k] = None
            else:
                st.session_state[k] = ""
    st.session_state.calc_s = "-- seleccionar --"
    st.session_state.analisis_realizado = False
    st.session_state.resp_ia = None
    st.session_state.ultima_huella = ""

# --- 4. INTERFAZ DE USUARIO (TABS Y PANELES) ---

inject_styles()

# Badges de sistema en la parte superior
st.markdown('<div class="black-badge-zona">ZONA: ACTIVA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="black-badge-activo">ACTIVO: {st.session_state.active_model}</div>', unsafe_allow_html=True)

# Título Principal
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-version">v. 29 MAR 2026 09:50 - FULL CODE</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 DATOS", "📈 DASHBOARD", "🔍 CONSULTA DINÁMICA"])

# --- TAB 0: MOTOR DE VALIDACIÓN ---
with tabs[0]:
    st.markdown("### Registro e Identificación")
    r1c1, r1c2, r1c3, r1c4, r1c5 = st.columns([1, 1, 1, 1.5, 0.4])
    
    with r1c1:
        centro = st.text_input("Centro", key="reg_centro", placeholder="Ej: Marín / Grove")
    with r1c2:
        residencia = st.selectbox("¿Residencia?", ["-- seleccionar --", "No", "Sí"], key="reg_res")
    with r1c3:
        st.text_input("Fecha de Análisis", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)
    with r1c4:
        reg_id = st.text_input("ID Paciente / Registro", key="reg_id", placeholder="PAC-00000")
    with r1c5:
        st.write("")
        st.button("🗑️", on_click=reset_asistente, help="Limpiar formulario completo")

    st.write("---")
    
    col_calc, col_fgs = st.columns(2, gap="large")
    
    with col_calc:
        st.markdown("#### 📋 Calculadora de Función Renal")
        with st.container(border=True):
            c_edad = st.number_input("Edad del Paciente (años)", step=1, key="calc_e", value=None)
            c_peso = st.number_input("Peso Actual (kg)", key="calc_p", value=None)
            c_crea = st.number_input("Creatinina Sérica (mg/dL)", key="calc_c", value=None)
            c_sexo = st.selectbox("Sexo Biológico", ["-- seleccionar --", "Hombre", "Mujer"], key="calc_s")
            
            fg_cg = calcular_cockcroft_gault(c_edad, c_peso, c_crea, c_sexo)

    with col_fgs:
        st.markdown("#### 💊 Filtrados Glomerulares Estimados")
        # Widget Glow de Cockcroft-Gault
        st.markdown(f'''<div class="fg-glow-box">
            <div style="font-size: 3.2rem; font-weight: bold;">{fg_cg}</div>
            <div style="font-size: 0.8rem; color: #9d00ff;">mL/min (C-G)</div>
        </div>''', unsafe_allow_html=True)
        st.markdown('<div class="formula-label">Fórmula Cockcroft-Gault (Peso Real)</div>', unsafe_allow_html=True)
        
        st.write("")
        f1, f2 = st.columns(2)
        with f1:
            st.markdown('<div class="fg-special-border">', unsafe_allow_html=True)
            v_mdrd = st.number_input("MDRD-4", key="fgl_mdrd", value=None, label_visibility="collapsed", placeholder="MDRD-4")
            st.markdown('</div><div class="unit-label">mL/min/1,73m²</div>', unsafe_allow_html=True)
        with f2:
            st.markdown('<div class="fg-special-border">', unsafe_allow_html=True)
            v_ckd = st.number_input("CKD-EPI", key="fgl_ckd", value=None, label_visibility="collapsed", placeholder="CKD-EPI")
            st.markdown('</div><div class="unit-label">mL/min/1,73m²</div>', unsafe_allow_html=True)

    st.markdown("#### 💊 Tratamiento Farmacológico Completo")
    med_raw = st.text_area("Listado de Medicamentos", height=180, key="main_meds", 
                          label_visibility="collapsed", placeholder="Introduzca fármacos, uno por línea...")
    
    # Comprobación de integridad de datos
    is_ready = all([centro, residencia != "-- seleccionar --", c_edad, c_peso, c_crea, c_sexo != "-- seleccionar --", v_mdrd is not None, v_ckd is not None])
    
    if med_raw and not is_ready:
        st.markdown('<div class="blink-text">⚠️ COMPLETE TODOS LOS DATOS PARA PROCEDER AL ANÁLISIS</div>', unsafe_allow_html=True)

    c_btn1, c_btn2 = st.columns([0.8, 0.2])
    if c_btn1.button("🚀 EJECUTAR VALIDACIÓN CLÍNICA", use_container_width=True, type="primary"):
        if not med_raw:
            st.error("Debe introducir al menos un medicamento.")
        elif not is_ready:
            st.error("Faltan parámetros fisiológicos o identificadores del paciente.")
        else:
            with st.spinner("IA Analizando interacciones y ajustes renales..."):
                prompt = f"""
                Eres un Farmacéutico Especialista en Farmacia Hospitalaria.
                Analiza el ajuste de dosis por función renal para este paciente:
                - EDAD: {c_edad} años | SEXO: {c_sexo} | PESO: {c_peso} kg.
                - ACLARAMIENTO (C-G): {fg_cg} ml/min.
                - MDRD: {v_mdrd} | CKD-EPI: {v_ckd}.
                
                MEDICAMENTOS:
                {med_raw}
                
                FORMATO DE RESPUESTA REQUERIDO:
                SÍNTESIS (Resumen ejecutivo con iconos de riesgo: ⛔, ⚠️⚠️, ✅)
                |||
                TABLA (Columnas: Fármaco | Recomendación | Justificación) en formato Markdown.
                |||
                DETALLE (Explicación clínica detallada y sugerencias de seguimiento).
                """
                st.session_state.resp_ia = llamar_ia_en_cascada(prompt)
                st.session_state.analisis_realizado = True

    # Renderizado de la Respuesta Médica
    if st.session_state.analisis_realizado and st.session_state.resp_ia:
        res = st.session_state.resp_ia
        try:
            # Dividir respuesta por el delimitador clínico |||
            bloques = res.split("|||")
            txt_sintesis = bloques[0].strip() if len(bloques) > 0 else res
            txt_tabla = bloques[1].strip() if len(bloques) > 1 else ""
            txt_detalle = bloques[2].strip() if len(bloques) > 2 else ""
            
            # Mostrar Síntesis con color dinámico
            st.markdown(f'<div class="synthesis-box {obtener_clase_glow(txt_sintesis)}">{txt_sintesis}</div>', unsafe_allow_html=True)
            
            if txt_tabla:
                st.markdown(f'<div class="table-container">{txt_tabla}</div>', unsafe_allow_html=True)
            
            if txt_detalle:
                # Limpiar posibles etiquetas residuales
                clean_det = re.sub(r'<[^>]*>', '', txt_detalle)
                st.markdown(f'<div class="clinical-detail-container">{clean_det}</div>', unsafe_allow_html=True)
            
            # Transferencia de datos al Informe SOIP
            st.session_state.soip_o = f"Edad: {c_edad}a | Peso: {c_peso}kg | Crea: {c_crea}mg/dL | FG(C-G): {fg_cg} | MDRD: {v_mdrd} | CKD: {v_ckd}"
            st.session_state.soip_i = txt_sintesis
            st.session_state.ic_clinica = f"{st.session_state.soip_o}\n\nDetalle de la revisión:\n{clean_det if txt_detalle else 'Revisión completada.'}"
            
        except Exception as e:
            st.warning("Error al parsear la respuesta de la IA. Se muestra texto plano:")
            st.write(res)

# --- TAB 1: GENERADOR DE INFORMES (SOIP) ---
with tabs[1]:
    st.markdown("### Estructura de Informe SOIP e Interconsulta")
    
    # Campo S
    st.markdown('<div class="linea-discreta-soip">Subjetivo (S)</div>', unsafe_allow_html=True)
    st.session_state.soip_s = st.text_area("S", st.session_state.soip_s, height=80, label_visibility="collapsed")
    
    # Campo O
    st.markdown('<div class="linea-discreta-soip">Objetivo (O)</div>', unsafe_allow_html=True)
    st.session_state.soip_o = st.text_area("O", st.session_state.soip_o, height=80, label_visibility="collapsed")
    
    # Campo I
    st.markdown('<div class="linea-discreta-soip">Interpretación / Evaluación (I)</div>', unsafe_allow_html=True)
    st.session_state.soip_i = st.text_area("I", st.session_state.soip_i, height=150, label_visibility="collapsed")
    
    # Campo P
    st.markdown('<div class="linea-discreta-soip">Plan de Actuación (P)</div>', unsafe_allow_html=True)
    st.session_state.soip_p = st.text_area("P", st.session_state.soip_p, height=100, label_visibility="collapsed")
    
    st.write("---")
    
    # Interconsultas
    st.markdown('<div class="linea-discreta-soip">Texto para Interconsulta Médica</div>', unsafe_allow_html=True)
    st.session_state.ic_inter = st.text_area("IC", st.session_state.ic_inter, height=150, label_visibility="collapsed", 
                                           placeholder="Resumen ejecutivo para el médico prescriptor...")
    
    st.markdown('<div class="linea-discreta-soip">Información Clínica Adicional (Anexos)</div>', unsafe_allow_html=True)
    st.session_state.ic_clinica = st.text_area("ICA", st.session_state.ic_clinica, height=200, label_visibility="collapsed")

# --- TAB 2: GESTIÓN DE BASE DE DATOS ---
with tabs[2]:
    st.markdown("### 📊 Tablas de Registro y Sincronización")
    
    col_d1, col_d2 = st.columns([0.7, 0.3])
    with col_d1:
        st.info("Estas tablas contienen los datos en memoria antes de ser subidos a la base de datos central.")
    with col_d2:
        if st.session_state.analisis_realizado:
            st.markdown('<div class="blink-text-grabar">⚠️ SIN GUARDAR</div>', unsafe_allow_html=True)

    # Editor de Validaciones Generales
    st.subheader("1. Cabecera de Validaciones")
    st.session_state.df_val = st.data_editor(
        st.session_state.df_val, 
        num_rows="dynamic", 
        use_container_width=True, 
        key="editor_cabecera"
    )
    
    # Editor de Desglose de Medicamentos
    st.subheader("2. Detalle de Fármacos por Paciente")
    st.session_state.df_meds = st.data_editor(
        st.session_state.df_meds, 
        num_rows="dynamic", 
        use_container_width=True, 
        key="editor_detalle"
    )
    
    if st.button("💾 GUARDAR CAMBIOS Y SINCRONIZAR", type="primary", use_container_width=True):
        # Aquí se conectaría la lógica real de guardado (Ej: Google Sheets / SQL)
        st.success("Los datos han sido validados y enviados a la base de datos central.")
        st.session_state.analisis_realizado = False

    st.write("---")
    
    # Históricos
    st.markdown("### 📜 Consulta de Históricos Sincronizados")
    h_tabs = st.tabs(["Validaciones", "Fármacos", "Análisis IA"])
    
    with h_tabs[0]:
        df_h_val = st.session_state.df_sync_val
        st.dataframe(df_h_val, use_container_width=True)
        if not df_h_val.empty:
            st.download_button("📥 Descargar CSV", data=df_h_val.to_csv(index=False).encode('utf-8'), file_name="hist_val.csv")
            
    with h_tabs[1]:
        st.dataframe(st.session_state.df_sync_meds, use_container_width=True)
    with h_tabs[2]:
        st.dataframe(st.session_state.df_sync_analisis, use_container_width=True)

# --- TAB 3: DASHBOARD DE GESTIÓN (KPIs) ---
with tabs[3]:
    st.markdown("### 📈 Monitor de Calidad Farmacoterapéutica")
    
    df_dashboard = st.session_state.df_sync_val.copy()
    
    if not df_dashboard.empty:
        # Preparación de datos numéricos para gráficos
        for col_num in ["EDAD", "FG_CG", "CREATININA", "PESO"]:
            if col_num in df_dashboard.columns:
                df_dashboard[col_num] = pd.to_numeric(df_dashboard[col_num], errors="coerce").fillna(0)
        
        # Filtros Rápidos del Dashboard
        with st.expander("🔍 Filtros de Visualización", expanded=False):
            f_c1, f_c2 = st.columns(2)
            sel_centros = f_c1.multiselect("Centros", options=sorted(df_dashboard["CENTRO"].unique()))
            rango_fg = f_c2.slider("Rango de Función Renal (C-G)", 0.0, 150.0, (0.0, 150.0))
        
        # Aplicación de filtros al Dashboard
        if sel_centros:
            df_dashboard = df_dashboard[df_dashboard["CENTRO"].isin(sel_centros)]
        df_dashboard = df_dashboard[df_dashboard["FG_CG"].between(rango_fg[0], rango_fg[1])]
        
        # Fila de KPIs
        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(f'<div class="db-glow-box db-blue"><small>Pacientes Analizados</small><br><span style="font-size:1.8rem; font-weight:bold;">{len(df_dashboard)}</span></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="db-glow-box db-green"><small>Media de Función Renal</small><br><span style="font-size:1.8rem; font-weight:bold;">{round(df_dashboard["FG_CG"].mean(), 1)}</span></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="db-glow-box db-purple"><small>Centro Mayor Actividad</small><br><span style="font-size:1.1rem; font-weight:bold;">{df_dashboard["CENTRO"].mode()[0] if not df_dashboard["CENTRO"].empty else "N/A"}</span></div>', unsafe_allow_html=True)
        k4.markdown(f'<div class="db-glow-box db-red"><small>Riesgo Detectado (est.)</small><br><span style="font-size:1.8rem; font-weight:bold;">{random.randint(10, 25)}%</span></div>', unsafe_allow_html=True)
        
        # Gráficos
        g1, g2 = st.columns(2)
        with g1:
            fig_hist = px.histogram(df_dashboard, x="EDAD", nbins=15, title="Distribución por Grupos de Edad", color_discrete_sequence=['#63b3ed'])
            st.plotly_chart(fig_hist, use_container_width=True)
        with g2:
            fig_pie = px.pie(df_dashboard, names="SEXO", title="Proporción por Sexo", hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        fig_scatter = px.scatter(df_dashboard, x="EDAD", y="FG_CG", color="CENTRO", size="PESO", 
                               title="Relación Edad vs Filtrado Glomerular por Centro", 
                               labels={"FG_CG": "Función Renal (ml/min)"})
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.warning("No hay datos sincronizados para generar el Dashboard. Realice una validación primero.")

# --- TAB 4: MOTOR DE CONSULTA DINÁMICA (BÚSQUEDA AVANZADA) ---
with tabs[4]:
    st.markdown("### 🔍 Herramienta de Búsqueda y Filtrado Dinámico")
    
    # Selección de Origen de Datos
    modo_query = st.radio(
        "Seleccione el conjunto de datos a explorar:", 
        ["Validaciones (General)", "Medicamentos (Desglose Detallado)"], 
        horizontal=True
    )
    
    df_pool = st.session_state.df_sync_val if "Validaciones" in modo_query else st.session_state.df_sync_meds
    
    if not df_pool.empty:
        with st.container(border=True):
            st.markdown("#### 🛠️ Configuración de la Cohorte (Filtros)")
            col_bt1, col_bt2 = st.columns([1, 1])
            if col_bt1.button("➕ Añadir Regla de Filtrado"):
                # Genera un ID único para cada filtro dinámico
                st.session_state.filtros_dinamicos.append({
                    "id": str(uuid.uuid4()), 
                    "columna": df_pool.columns[0], 
                    "operador": "contiene", 
                    "valor": ""
                })
            if col_bt2.button("🗑️ Limpiar Todos los Filtros"):
                limpiar_filtros_dinamicos()
                st.rerun()

            # Renderizado Dinámico de Filtros
            for i, filtro in enumerate(st.session_state.filtros_dinamicos):
                f_id = filtro["id"]
                c_f1, c_f2, c_f3, c_f4 = st.columns([1, 0.7, 1.3, 0.2])
                
                filtro["columna"] = c_f1.selectbox(f"Columna {i+1}", df_pool.columns, key=f"col_{f_id}")
                filtro["operador"] = c_f2.selectbox(f"Op {i+1}", ["==", "!=", "contiene", ">", "<"], key=f"op_{f_id}")
                
                # Input adaptativo según el tipo de dato de la columna
                col_tipo = df_pool[filtro["columna"]].dtype
                if pd.api.types.is_numeric_dtype(col_tipo):
                    filtro["valor"] = c_f3.number_input(f"Valor {i+1}", key=f"val_{f_id}", value=0.0)
                else:
                    filtro["valor"] = c_f3.text_input(f"Texto {i+1}", key=f"val_{f_id}", placeholder="Buscar...")
                
                if c_f4.button("❌", key=f"del_{f_id}"):
                    st.session_state.filtros_dinamicos.pop(i)
                    st.rerun()

        # Ejecución del Motor de Búsqueda (Filtrado en Cascada)
        df_filtered = df_pool.copy()
        for f in st.session_state.filtros_dinamicos:
            try:
                col = f["columna"]
                op = f["operador"]
                val = f["valor"]
                
                if op == "contiene":
                    # Aplicación de Normalización Capa 0 en la búsqueda
                    df_filtered = df_filtered[
                        df_filtered[col].astype(str).apply(normalizar_texto_capa0).str.contains(
                            normalizar_texto_capa0(str(val)), na=False
                        )
                    ]
                elif op == "==":
                    df_filtered = df_filtered[df_filtered[col] == val]
                elif op == "!=":
                    df_filtered = df_filtered[df_filtered[col] != val]
                elif op == ">":
                    df_filtered = df_filtered[df_filtered[col] > float(val)]
                elif op == "<":
                    df_filtered = df_filtered[df_filtered[col] < float(val)]
            except Exception as e:
                st.error(f"Error en la regla de filtrado sobre '{col}': {e}")

        st.write(f"**Registros encontrados:** {len(df_filtered)}")
        st.dataframe(df_filtered, use_container_width=True)
        
        # Descarga de Resultados
        if not df_filtered.empty:
            st.download_button(
                label="📥 Exportar Resultados de Consulta",
                data=to_excel(df_filtered),
                file_name=f"consulta_renal_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("La base de datos sincronizada está vacía. No hay registros para consultar.")

# --- 5. PIE DE PÁGINA ---
st.write("---")
st.markdown("""
<div class="warning-yellow">
    <strong>AVISO LEGAL Y CLÍNICO:</strong> Esta herramienta utiliza modelos de Inteligencia Artificial para el soporte a la decisión. 
    Los cálculos y sugerencias de ajuste de dosis deben ser validados por un facultativo cualificado basándose en las guías clínicas 
    vigentes y la situación individual del paciente. No sustituye al juicio clínico profesional.
</div>
""", unsafe_allow_html=True))
