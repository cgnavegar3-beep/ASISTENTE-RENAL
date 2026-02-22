# v. 22 feb 19:45
import streamlit as st
import pandas as pd
import io
from datetime import datetime
import google.generativeai as genai

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
# #
# III. BLINDAJE DE SÍNTESIS DINÁMICA (Glow System):
# #
#    - Títulos Permitidos: SOLO "Medicamentos afectados:" o "Fármacos correctamente dosificados".
# #
#    - Prohibición Textual: Prohibido usar "SÍNTESIS", "DETALLE", "RESUMEN" o similares.
# #
#    - Regla de Contenido Estricta: Solo se listan medicamentos afectados (⚠️ o ⛔).
# #
#    - Exclusión: NUNCA listar nombres de fármacos correctamente dosificados en la síntesis.
# #
#    - Formato de Línea: [Icono ⚠️ o ⛔] + [Nombre] + [Frase corta]. Sin texto adicional.
# #
#    - Lógica de Color (Jerarquía de Gravedad): 
# #
#        1. ROJO (glow-red): Si aparece al menos un icono ⛔ (Contraindicado).
# #
#        2. NARANJA (glow-orange): Si no hay ⛔ pero aparece al menos un icono ⚠️ (Ajuste).
# #
#        3. VERDE (glow-green): Si no hay iconos ⚠️ ni ⛔ (Todo correcto).
# #
# #
# IV. BLINDAJE DEL BLOQUE AZUL (blue-detail-container):
# #
#    - Prohibición de Fragmentación: Detalle y Nota en el mismo div CSS.
# #
#    - Estilo Fijo: Fondo (#f0f7ff), borde (#bee3f8).
# #
#    - NOTA IMPORTANTE: Texto estático (4 puntos) en negrita y azul intenso (Blindado).
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

# Inicialización de estados de sesión
for key in ["soip_s", "soip_o", "soip_i", "soip_p", "ic_motivo", "ic_info", "main_meds", "active_model"]:
    if key not in st.session_state: st.session_state[key] = ""
if st.session_state.active_model == "": st.session_state.active_model = "ESPERANDO..."

def reset_registro():
    st.session_state["reg_centro"] = ""; st.session_state["reg_edad"] = None
    st.session_state["reg_id"] = ""; st.session_state["reg_res"] = "No"

def reset_meds():
    st.session_state.main_meds = ""
    for k in ["soip_s", "soip_o", "soip_i", "soip_p", "ic_motivo", "ic_info"]: st.session_state[k] = ""

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    API_KEY = None

def obtener_modelos_vivos():
    try:
        if not API_KEY: return []
        return [m.name.replace('models/', '').replace('gemini-', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    except: return ["2.5-flash", "1.5-pro"]

def llamar_ia_en_cascada(prompt):
    disponibles = obtener_modelos_vivos()
    for mod_name in ['2.5-flash', '1.5-pro']:
        if mod_name in disponibles:
            try:
                st.session_state.active_model = mod_name.upper()
                model = genai.GenerativeModel(f'models/gemini-{mod_name}')
                return model.generate_content(prompt).text
            except: continue
    return "⚠️ Error de conexión."

def inject_ui_styles():
    st.markdown("""
    <style>
    .block-container { max-width: 100% !important; padding-top: 2.5rem !important; padding-left: 4% !important; padding-right: 4% !important; }
    
    /* BLOQUE II: CUADROS NEGROS SUPERIORES */
    .availability-badge { background-color: #1a1a1a !important; color: #888 !important; padding: 4px 10px; border-radius: 3px; font-family: monospace !important; font-size: 0.65rem; position: fixed; top: 15px; left: 15px; z-index: 1000000; border: 1px solid #333; width: 100px; text-align: center; }
    .model-badge { background-color: #000000 !important; color: #00FF00 !important; padding: 4px 10px; border-radius: 3px; font-family: monospace !important; font-size: 0.75rem; position: fixed; top: 15px; left: 125px; z-index: 1000000; box-shadow: 0 0 5px #00FF0033; border: 1px solid #333; min-width: 90px; text-align: center; }
    
    .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin-bottom: 0px; }
    .sub-version { text-align: center; font-size: 0.6rem; color: #bbb; margin-top: -5px; margin-bottom: 20px; font-family: monospace; }
    .id-display { color: #666; font-family: monospace; font-size: 0.85rem; margin-top: -5px; margin-bottom: 20px; }
    .fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .rgpd-inline { background-color: #fff5f5; color: #c53030; padding: 8px 16px; border-radius: 8px; border: 1.5px solid #feb2b2; font-size: 0.85rem; display: inline-block; float: right; }
    .synthesis-box { padding: 15px; border-radius: 12px; margin-bottom: 15px; border-width: 2px; border-style: solid; font-size: 0.95rem; }
    .glow-green { background-color: #f1f8e9; color: #2e7d32; border-color: #a5d6a7; box-shadow: 0 0 12px #a5d6a7; }
    .glow-orange { background-color: #fff3e0; color: #e65100; border-color: #ffcc80; box-shadow: 0 0 12px #ffcc80; }
    .glow-red { background-color: #fff5f5; color: #c53030; border-color: #feb2b2; box-shadow: 0 0 18px #feb2b2; }
    .blue-detail-container { background-color: #f0f7ff; color: #2c5282; padding: 20px; border-radius: 10px; border: 1px solid #bee3f8; margin-top: 10px; }
    .nota-line { border-top: 2px solid #aec6cf; margin-top: 15px; padding-top: 15px; font-weight: 700; color: #003366; }
    .warning-yellow { background-color: #fdfde0; color: #856404; padding: 15px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 40px; text-align: center; }
    .linea-discreta-soip { border-top: 1px solid #d9d5c7; margin: 5px 0; font-size: 0.65rem; font-weight: bold; color: #8e8a7e; text-transform: uppercase; }
    .header-capsule { background-color: #e2e8f0; color: #2d3748; padding: 10px 30px; border-radius: 50px; display: inline-block; font-weight: 800; font-size: 0.9rem; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

inject_ui_styles()
st.markdown('<div class="availability-badge">ZONA ACTIVA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="model-badge">{st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-version">v. 22 feb 19:45</div>', unsafe_allow_html=True)

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
        st.write(""); st.button("🗑️", on_click=reset_registro)

    id_final = f"{centro if centro else '---'}-{str(int(edad_reg)) if edad_reg else '00'}-{alfa if alfa else '---'}"
    st.markdown(f'<div class="id-display">ID Registro: {id_final}</div>', unsafe_allow_html=True)

    col_izq, col_der = st.columns(2, gap="large")
    with col_izq:
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            calc_e = st.number_input("Edad (años)", value=edad_reg if edad_reg else None, placeholder="Ej: 65")
            calc_p = st.number_input("Peso (kg)", value=None, placeholder="Ej: 70.0")
            calc_c = st.number_input("Creatinina (mg/dL)", value=None, placeholder="Ej: 1.0")
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"])
            fg = round(((140 - calc_e) * calc_p) / (72 * calc_c) * (0.85 if calc_s == "Mujer" else 1.0), 1) if calc_e and calc_p and calc_c else 0.0
            st.markdown('<span style="font-size:0.7rem; color:#888; float:right;">Fórmula: Cockcroft-Gault</span>', unsafe_allow_html=True)

    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual")
        valor_fg = fg_m if fg_m else fg
        st.markdown(f'<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{valor_fg}</div><div style="font-size: 1rem; color: #9d00ff;">mL/min</div></div>', unsafe_allow_html=True)

    st.write(""); st.markdown("---")
    m_col1, m_col2 = st.columns([0.5, 0.5])
    with m_col1: st.markdown("#### 📝 Listado de medicamentos")
    with m_col2: st.markdown('<div class="rgpd-inline">🛡️ RGPD: No introduzca datos personales</div>', unsafe_allow_html=True)
    
    txt_meds = st.text_area("Listado", height=150, label_visibility="collapsed", key="main_meds")

    if st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True):
        if txt_meds:
            with st.spinner("Procesando..."):
                prompt = f"""Analiza FG {valor_fg}: {txt_meds}. 
                REGLA DE ORO SÍNTESIS: 
                1. Si hay afectados, título exacto: 'Se detectan medicamentos no ajustados al FG actual, con necesidad de adaptación posológica o reconsideración terapéutica'.
                2. Si no hay afectados, título exacto: 'MEDICAMENTOS CORRECTAMENTE DOSIFICADOS'.
                3. Debajo del título de afectados, SOLO líneas: [Icono ⚠️ o ⛔] [Nombre] - [Frase corta].
                4. PROHIBIDO: palabras como 'Bloque', metabolismo, eliminación o resúmenes adicionales en la síntesis.
                DETALLE: Inicia con 'A continuación, se detallan los ajustes de dosis para cada fármaco:'. Explica justificación técnica clínica."""
                
                resp = llamar_ia_en_cascada(prompt)
                if "⛔" in resp: glow_class = "glow-red"
                elif "⚠️" in resp: glow_class = "glow-orange"
                else: glow_class = "glow-green"
                
                try:
                    partes = resp.split("A continuación, se detallan los ajustes")
                    sintesis = partes[0].strip()
                    detalle = "A continuación, se detallan los ajustes" + partes[1]
                    st.markdown(f'<div class="synthesis-box {glow_class}"><b>{sintesis.replace("\n", "<br>")}</b></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="blue-detail-container">{detalle.replace("\n", "<br>")}<div class="nota-line">Nota: Consultar siempre ficha técnica oficial y ajustar según criterio clínico.</div></div>', unsafe_allow_html=True)
                    
                    # Volcado a Pestaña Informe
                    st.session_state.soip_s = "Revisión farmacoterapéutica orientada a identificar medicamentos que precisan ajuste de dosis por filtrado glomerular."
                    obj_items = []
                    if calc_e: obj_items.append(f"Edad: {calc_e} años")
                    if calc_p: obj_items.append(f"Peso: {calc_p} kg")
                    if calc_c: obj_items.append(f"Cr: {calc_c} mg/dL")
                    obj_items.append(f"FG: {valor_fg} mL/min")
                    st.session_state.soip_o = " | ".join(obj_items)
                    st.session_state.soip_i = sintesis
                    st.session_state.soip_p = "Se realiza interconsulta (IC) a su médico de atención primaria (MAP) para que valore adecuación terapéutica y se recomienda seguimiento de función renal."
                    st.session_state.ic_motivo = f"Solicito valoración médica tras revisión farmacoterapéutica por función renal...\n\n{sintesis}"
                    st.session_state.ic_info = (detalle[:700] + "...") if len(detalle) > 700 else detalle
                    st.rerun()
                except: st.error("Error en la estructura de respuesta de la IA.")

    st.button("🗑️ RESET TOTAL", on_click=reset_meds)

with tabs[1]:
    st.markdown('<div style="text-align:center;"><div class="header-capsule">📄 Nota Evolutiva SOIP</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="linea-discreta-soip">Subjetivo (S)</div>', unsafe_allow_html=True); st.text_area("s_t", st.session_state.soip_s, height=70, label_visibility="collapsed")
    st.markdown('<div class="linea-discreta-soip">Objetivo (O)</div>', unsafe_allow_html=True); st.text_area("o_t", st.session_state.soip_o, height=70, label_visibility="collapsed")
    st.markdown('<div class="linea-discreta-soip">Interpretación (I)</div>', unsafe_allow_html=True); st.text_area("i_t", st.session_state.soip_i, height=120, label_visibility="collapsed")
    st.markdown('<div class="linea-discreta-soip">Plan (P)</div>', unsafe_allow_html=True); st.text_area("p_t", st.session_state.soip_p, height=70, label_visibility="collapsed")
    
    st.markdown('<div style="text-align:center; margin-top:30px;"><div class="header-capsule">📨 Solicitud de Interconsulta</div></div>', unsafe_allow_html=True)
    c_i1, c_i2 = st.columns(2)
    with c_i1: st.markdown('<div class="linea-discreta-soip">Motivo</div>', unsafe_allow_html=True); st.text_area("m_t", st.session_state.ic_motivo, height=200, label_visibility="collapsed")
    with c_i2: st.markdown('<div class="linea-discreta-soip">Información Clínica</div>', unsafe_allow_html=True); st.text_area("in_t", st.session_state.ic_info, height=200, label_visibility="collapsed")

st.markdown('<div class="warning-yellow">⚠️ Apoyo a la revisión farmacoterapéutica. Verifique siempre con fuentes oficiales.</div>', unsafe_allow_html=True)
