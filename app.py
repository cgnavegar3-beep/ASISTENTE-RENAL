# v. 22 feb 10:35
import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import google.generativeai as genai
import io

# =================================================================
# # PRINCIPIOS FUNDAMENTALES:
# #
# 1. NUNCA BORRAR NI MODIFICAR ESTA CLÁUSULA. 
# #
# 2. No puedes mover nada, ni cambiar ni una sola línea de la estructura 
# #
#    visual (RIGOR Y SERIEDAD). Cero modificaciones sin autorización.
# #
# 3. Antes de cualquier evolución técnica, explicar el "qué", "por qué" 
# #
#    y "cómo", y esperar aprobación ("adelante" o "procede").
# #
# #
# I. ESTRUCTURA VISUAL PROTEGIDA:
# #
#    1. Cuadros negros superiores (ZONA y ACTIVO).
# #
#    2. Título "ASISTENTE RENAL" y Versión inmediatamente debajo (Blindado).
# #
#    2. Título principal y pestañas (Tabs).
# #
#    3. Registro de paciente y función: TODO EN UNA LÍNEA (Centro, Edad, ID Alfa, 
# #
#       Res, Fecha + Botón Borrado Registro).
# #
#    4. Interfaz Dual (Calculadora y caja de FG (Purple Glow): lógica Cockcroft-Gault.
# #
#       -> REFUERZO: NO SE TOCA LA CALCULADORA, NO SE TOCA EL GLOW MORADO.
# #
#    5. Layout Medicamentos: Título y Aviso RGPD (estilo ampliado) en la misma línea.
# #
#    6. Cuadro de listado de medicamentos (TextArea).
# #
#    7. Barra dual de botones (VALIDAR / RESET TOTAL) y Reset de Registro.
# #
#    8. Aviso amarillo de apoyo legal inferior.
# #
# #
# II. FUNCIONALIDADES CRÍTICAS PROTEGIDAS:
# #
#    1. Cascada de Modelos (2.5 Flash > 1.5 Pro > Otros).
# #
#    2. Detección dinámica de modelos vivos en la cuenta.
# #
#    3. Actualización de feedback neón en tiempo real (Badge ACTIVO).
# #
#    
# #
# III. BLINDAJE DEL BLOQUE AZUL (blue-detail-container):
# #
#    - Prohibición de Fragmentación: Detalle y Nota en el mismo div CSS.
# #
#    - Estilo Fijo: Fondo (#f0f7ff), borde (#bee3f8).
# #
#    - NOTA IMPORTANTE: Texto estático (4 puntos) en negrita y azul intenso (Blindado).
# #
# #
# IV. BLINDAJE DE SÍNTESIS DINÁMICA (Glow System):
# #
#    - Formato Rígido: Solo se permite "Medicamentos afectados:" o "Fármacos correctamente dosificados".
# #
#    - Prohibición Textual: No pueden aparecer las palabras "SÍNTESIS", "DETALLE" o similares.
# #
#    - Regla de Iconos: [Icono] + [Nombre] + [Frase corta]. Prohibido texto adicional.
# #
#    - Lógica de Color (Glow): 
# #
#        * Sin iconos = Verde (glow-green).
# #
#        * Con ⚠️ = Naranja (glow-orange).
# #
#        * Con ⛔ = Rojo (glow-red).
# #
# #
# V. PROTECCIÓN INTEGRAL PESTAÑA 1 (💊 VALIDACIÓN):
# #
#    - Blindaje Total: Prohibida cualquier modificación en el layout, orden de columnas o funciones de la Pestaña 1.
# #
#    - Componentes Congelados: Registro de paciente (fila única), Calculadora dual (Glow morado), Área de texto y Botonera (Validar/Reset).
# #
#    - Lógica Funcional: El sistema de callbacks y el prompt de IA de esta pestaña no admiten cambios de sintaxis.
# =================================================================

st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

# Persistencia de datos Pestaña 2
if "soip_s" not in st.session_state: st.session_state.soip_s = ""
if "soip_o" not in st.session_state: st.session_state.soip_o = ""
if "soip_i" not in st.session_state: st.session_state.soip_i = ""
if "soip_p" not in st.session_state: st.session_state.soip_p = ""
if "ic_motivo" not in st.session_state: st.session_state.ic_motivo = ""
if "ic_info" not in st.session_state: st.session_state.ic_info = ""

def reset_registro():
    st.session_state["reg_centro"] = ""
    st.session_state["reg_edad"] = None
    st.session_state["reg_id"] = ""
    st.session_state["reg_res"] = "No"

def reset_meds():
    st.session_state["main_meds"] = ""

if 'active_model' not in st.session_state: st.session_state.active_model = "ESPERANDO..."

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    API_KEY = None

def obtener_modelos_vivos():
    try:
        if not API_KEY: return []
        return [m.name.replace('models/', '').replace('gemini-', '') 
                for m in genai.list_models() 
                if 'generateContent' in m.supported_generation_methods]
    except:
        return ["2.5-flash", "1.5-pro"]

def llamar_ia_en_cascada(prompt):
    disponibles = obtener_modelos_vivos()
    preferencia = ['2.5-flash', '1.5-pro', '1.5-flash']
    modelos_a_intentar = [m for m in preferencia if m in disponibles]
    for mod_name in modelos_a_intentar:
        try:
            st.session_state.active_model = mod_name.upper()
            model = genai.GenerativeModel(f'models/gemini-{mod_name}')
            response = model.generate_content(prompt)
            return response.text
        except: continue
    return "⚠️ Error: Sin respuesta."

def inject_ui_styles():
    st.markdown("""
    <style>
    header[data-testid="stHeader"] { visibility: hidden; }
    .stApp { background-color: white; }
    
    /* INMOVILIZAR CABECERA (ESTILO EXCEL) */
    .stMainBlockContainer {
        padding-top: 0rem !important;
    }
    
    [data-testid="stVerticalBlock"] > div:first-child {
        position: sticky;
        top: 0;
        z-index: 1001;
        background-color: white;
        padding-top: 15px;
        padding-bottom: 0px;
    }

    /* BADGES DISCRETOS (Estilo original restaurado) */
    .availability-badge { 
        background-color: #000000 !important; 
        color: #888 !important; 
        padding: 4px 10px; 
        border-radius: 3px; 
        font-family: monospace !important; 
        font-size: 0.65rem; 
        border: 1px solid #333; 
        width: fit-content;
        max-width: 180px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        display: inline-block;
        margin-right: 5px;
    }
    .model-badge { 
        background-color: #000000 !important; 
        color: #00FF00 !important; 
        padding: 4px 10px; 
        border-radius: 3px; 
        font-family: monospace !important; 
        font-size: 0.75rem; 
        box-shadow: 0 0 5px #00FF0033; 
        display: inline-block;
    }
    
    .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin: 0; }
    .sub-version { text-align: center; font-size: 0.8rem; color: #666; margin-top: -5px; margin-bottom: 5px; }
    
    /* PESTAÑAS INMOVILIZADAS */
    div[data-testid="stTabs"] {
        position: sticky;
        top: 105px; /* Justo debajo del título */
        z-index: 1000;
        background-color: white;
        padding-top: 5px;
    }

    .block-container { max-width: 100% !important; padding-left: 4% !important; padding-right: 4% !important; }
    .version-display { text-align: right; font-size: 0.6rem; color: #bbb; font-family: monospace; position: fixed; bottom: 10px; right: 10px; }
    .id-display { color: #666; font-family: monospace; font-size: 0.85rem; margin-top: -5px; margin-bottom: 20px; }
    .formula-tag { font-size: 0.75rem; color: #888; font-style: italic; text-align: right; width: 100%; display: block; margin-top: 5px; }
    .fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .rgpd-inline { background-color: #fff5f5; color: #c53030; padding: 8px 16px; border-radius: 8px; border: 1.5px solid #feb2b2; font-size: 0.85rem; display: inline-block; float: right; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .synthesis-box { padding: 15px; border-radius: 12px; margin-bottom: 15px; text-align: left; border-width: 2px; border-style: solid; font-size: 0.95rem; }
    .glow-green { background-color: #f1f8e9; color: #2e7d32; border-color: #a5d6a7; box-shadow: 0 0 12px #a5d6a7; }
    .glow-orange { background-color: #fff3e0; color: #e65100; border-color: #ffcc80; box-shadow: 0 0 12px #ffcc80; }
    .glow-red { background-color: #fff5f5; color: #c53030; border-color: #feb2b2; box-shadow: 0 0 18px #feb2b2; }
    .blue-detail-container { background-color: #f0f7ff; color: #2c5282; padding: 20px; border-radius: 10px; border: 1px solid #bee3f8; margin-top: 10px; line-height: 1.6; }
    .nota-line { border-top: 2px solid #aec6cf; margin-top: 15px; padding-top: 15px; font-size: 0.95rem; font-weight: 700; color: #003366; }
    .warning-yellow { background-color: #fdfde0; color: #856404; padding: 15px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 40px; text-align: center; }
    
    /* ESTILOS PESTAÑA INFORME */
    .header-capsule { background-color: #e2e8f0; color: #2d3748; padding: 10px 30px; border-radius: 50px; display: inline-block; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; font-size: 0.9rem; margin-bottom: 20px; border: 1px solid #cbd5e0; }
    .divider-tecnico { border: 0; height: 2px; background-image: linear-gradient(to right, rgba(0,0,0,0), rgba(157, 0, 255, 0.4), rgba(0,0,0,0)); margin: 40px 0; }
    .linea-discreta-soip { border-top: 1px solid #d9d5c7; margin: 0 auto 5px auto; width: 98%; padding-top: 2px; font-size: 0.65rem; font-weight: bold; color: #8e8a7e; text-transform: uppercase; }
    div[data-baseweb="textarea"] { background-color: #f4f1ea !important; border: none !important; border-radius: 25px !important; box-shadow: inset 2px 2px 5px #d9d5c7 !important; padding: 5px 15px !important; }
    textarea { background-color: transparent !important; border: none !important; font-family: serif !important; color: #444 !important; }
    </style>
    """, unsafe_allow_html=True)

inject_ui_styles()

# FILA 1 Y 2: BADGES Y TÍTULO (INMOVILIZADOS)
with st.container():
    st.markdown(f'<div style="position: absolute; left: 15px; top: 15px;"><div class="availability-badge">ZONA: {" | ".join(obtener_modelos_vivos())}</div><div class="model-badge">{st.session_state.active_model}</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-version">v. 22 feb 10:35</div>', unsafe_allow_html=True)

st.markdown('<div class="version-display">v. 22 feb 10:35</div>', unsafe_allow_html=True)

# FILA 3: PESTAÑAS (INMOVILIZADAS)
tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 EXCEL", "📈 GRÁFICOS"])

with tabs[0]:
    st.markdown("### Registro de Paciente")
    c1, c2, c3, c4, c5, c_del = st.columns([1, 1, 1, 1, 1, 0.4])
    with c1: centro = st.text_input("Centro", placeholder="G/M", key="reg_centro")
    with c2: edad_reg = st.number_input("Edad", value=None, placeholder="0", key="reg_edad")
    with c3: alfa = st.text_input("ID Alfanumérico", placeholder="ABC-123", key="reg_id")
    with c4: res = st.selectbox("¿Residencia?", ["No", "Sí"], key="reg_res")
    with c5: st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)
    with c_del:
        st.write("")
        st.button("🗑️", help="Limpiar datos del paciente", on_click=reset_registro)

    id_final = f"{centro if centro else '---'}-{str(int(edad_reg)) if edad_reg else '00'}-{alfa if alfa else '---'}"
    st.markdown(f'<div class="id-display">ID Registro: {id_final}</div>', unsafe_allow_html=True)

    col_izq, col_der = st.columns(2, gap="large")
    with col_izq:
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            calc_e = st.number_input("Edad (años)", value=edad_reg if edad_reg else 65)
            calc_p = st.number_input("Peso (kg)", value=70.0)
            calc_c = st.number_input("Creatinina (mg/dL)", value=1.0)
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"])
            fg = round(((140 - calc_e) * calc_p) / (72 * calc_c) * (0.85 if calc_s == "Mujer" else 1.0), 1)
            st.markdown('<span class="formula-tag">Fórmula: Cockcroft-Gault</span>', unsafe_allow_html=True)

    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual")
        valor_fg = fg_m if fg_m else fg
        st.markdown(f'<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{valor_fg}</div><div style="font-size: 1rem; color: #9d00ff;">mL/min</div></div>', unsafe_allow_html=True)

    st.write(""); st.markdown("---")
    m_col1, m_col2 = st.columns([0.5, 0.5])
    with m_col1: st.markdown("#### 📝 Listado de medicamentos")
    with m_col2: st.markdown('<div class="rgpd-inline">🛡️ <b>PROTECCIÓN DE DATOS:</b> No introduzca datos personales identificativos</div>', unsafe_allow_html=True)
    
    txt_meds = st.text_area("Listado", height=150, label_visibility="collapsed", key="main_meds")

    b_val, b_res = st.columns([0.85, 0.15])
    with b_val:
        if st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True):
            if txt_meds:
                with st.spinner("Consultando evidencia clínica..."):
                    p1 = f"Experto farmacia renal. Analiza FG {valor_fg}: {txt_meds}. \n"
                    p2 = "INSTRUCCIONES RÍGIDAS DE FORMATO: \n 1. Encabezado SÍNTESIS: SOLO 'Medicamentos afectados:' o 'Fármacos correctamente dosificados'. \n"
                    p3 = "2. PROHIBIDO usar las palabras SÍNTESIS o DETALLE. \n 3. Lista: [Icono] [Nombre] - [Frase corta]. \n"
                    p4 = "4. Inicia el bloque técnico con: 'A continuación, se detallan los ajustes de dosis para cada fármaco con este valor de FG:'."
                    prompt = p1 + p2 + p3 + p4
                    resp = llamar_ia_en_cascada(prompt)
                    glow_class = "glow-red" if "⛔" in resp else ("glow-orange" if "⚠️" in resp else "glow-green")
                    try:
                        partes = resp.split("A continuación, se detallan los ajustes")
                        sintesis = partes[0].strip()
                        detalle_clinico = "A continuación, se detallan los ajustes" + partes[1]
                        st.markdown(f'<div class="synthesis-box {glow_class}"><b>{sintesis.replace("\n", "<br>")}</b></div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="blue-detail-container">{detalle_clinico.replace("\n", "<br>")}<div class="nota-line">Nota Importante:<br>· Estas son recomendaciones generales.<br>· Siempre se debe consultar la ficha técnica actualizada.<br>· Considerar peso, edad y comorbilidades.<br>· Seguimiento periódico de función renal.</div></div>', unsafe_allow_html=True)
                        
                        st.session_state.soip_o = f"ID: {id_final} | Peso: {calc_p}kg | FG: {valor_fg} mL/min"
                        st.session_state.soip_i = sintesis
                        st.session_state.ic_motivo = f"Paciente {id_final}. Resumen: {sintesis[:110]}..."
                        st.session_state.ic_info = detalle_clinico
                    except: st.info(resp)

    with b_res:
        st.button("🗑️ RESET", use_container_width=True, on_click=reset_meds)

with tabs[1]:
    st.markdown('<div style="text-align: center;"><div class="header-capsule">📄 Nota Evolutiva SOIP</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="linea-discreta-soip">Subjetivo (S)</div>', unsafe_allow_html=True)
    st.session_state.soip_s = st.text_area("S_label", value=st.session_state.soip_s, height=80, label_visibility="collapsed", key="s_input")
    st.markdown('<div class="linea-discreta-soip">Objetivo (O)</div>', unsafe_allow_html=True)
    st.session_state.soip_o = st.text_area("O_label", value=st.session_state.soip_o, height=80, label_visibility="collapsed", key="o_input")
    st.markdown('<div class="linea-discreta-soip">Interpretación (I)</div>', unsafe_allow_html=True)
    st.session_state.soip_i = st.text_area("I_label", value=st.session_state.soip_i, height=80, label_visibility="collapsed", key="i_input")
    st.markdown('<div class="linea-discreta-soip">Plan (P)</div>', unsafe_allow_html=True)
    st.session_state.soip_p = st.text_area("P_label", value=st.session_state.soip_p, height=80, label_visibility="collapsed", key="p_input")

    st.markdown('<div class="divider-tecnico"></div>', unsafe_allow_html=True)
    
    st.markdown('<div style="text-align: center;"><div class="header-capsule">📨 Solicitud de Interconsulta</div></div>', unsafe_allow_html=True)
    i_col1, i_col2 = st.columns(2)
    with i_col1:
        st.markdown('<div class="linea-discreta-soip">Motivo de Interconsulta</div>', unsafe_allow_html=True)
        st.session_state.ic_motivo = st.text_area("Mot_label", value=st.session_state.ic_motivo, height=220, label_visibility="collapsed", key="mot_input")
    with i_col2:
        st.markdown('<div class="linea-discreta-soip">Información Técnico-Clínica</div>', unsafe_allow_html=True)
        st.session_state.ic_info = st.text_area("Info_label", value=st.session_state.ic_info, height=220, label_visibility="collapsed", key="info_input")

st.markdown('<div class="warning-yellow">⚠️ Apoyo a la revisión farmacoterapéutica. Verifique siempre con fuentes oficiales.</div>', unsafe_allow_html=True)
