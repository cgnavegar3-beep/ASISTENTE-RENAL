# v. 26 feb 22:55
import streamlit as st
import pandas as pd
import io
from datetime import datetime
import google.generativeai as genai

# =================================================================
#
# PRINCIPIOS FUNDAMENTALES:
#
#
# GEMINI SIEMPRE TENDRA RIGOR, RESPETARA Y VERIFICARA QUE SE CUMPLAN
# ESTOS PRINCIPIOS ANTES Y DESPUES DE REALIZAR CUALQUIER CAMBIO.
#
#
# 1. NUNCA BORRAR NI MODIFICAR ESTA CLÁUSULA. 
#
#
# 2. No puedes mover nada, ni cambiar ni una sola línea de la
# estructura visual (RIGOR Y SERIEDAD). Cero modificaciones sin
# autorización.
#
#
# 3. Antes de cualquier evolución técnica, explicar el "qué",
# "por qué" y "cómo", y esperar aprobación
# ("adelante" o "procede").
#
#
# #
# I. ESTRUCTURA VISUAL PROTEGADA:
# #
#    1. Cuadros negros superiores (ZONA y ACTIVO).
# #
#    2. Título "ASISTENTE RENAL" y Versión inmediatamente
# debajo (Blindado).
# #
#    3. Título principal y pestañas (Tabs).
# #
#    4. Registro de paciente y función: TODO EN UNA LÍNEA (Centro,
# Edad, ID Alfa, Res, Fecha + Botón Borrado Registro).
# #
#    -> REFUERZO: DEBAJO DE LA LÍNEA DE REGISTRO DEBE APARECER SIEMPRE 
# EL "ID REGISTRO" DINÁMICO (CENTRO-EDAD-ALFA).
# #
#    5. Interfaz Dual (Calculadora y caja de FG (Purple Glow): lógica
# Cockcroft-Gault.
# #
#        -> REFUERZO: EL NOMBRE "FG-Cockcroft-Gault" DEBE FIGURAR 
# SIEMPRE EN PEQUEÑO EN LA ESQUINA INFERIOR DERECHA DE LA CALCULADORA.
# #
#    6. Layout Medicamentos: Título y Aviso RGPD (estilo ampliado) en
# la misma línea.
# #
#    7. Cuadro de listado de medicamentos (TextArea).
# #
#    8. Barra dual de botones (VALIDAR / RESET TOTAL) y Reset de
# Registro.
# #
#    9. Aviso amarillo de apoyo legal inferior CON EL TEXTO: ⚠️
# Esta herramienta es de apoyo a la revisión farmacoterapéutica.
# Verifique siempre con fuentes oficiales.
# #
# #
# II. FUNCIONALIDADES CRÍTICAS PROTEGIDAS:
# #
#    1. Cascada de Modelos (2.5 Flash > flash-latest > 1.5 Pro >
# Otros).
# #
#    2. Detección dinámica de modelos vivos en la cuenta.
# #
#    3. Actualización de feedback neón en tiempo real (Badge ACTIVO).
# #
# #
# III. BLINDAJE DE SÍNTESIS DINÁMICA (Glow System) - ANTI-ALUCINACIONES:
# #
#    1. Títulos Permitidos: SOLO "Medicamentos afectados:" o
# "Fármacos correctamente dosificados".
# #
#    2. Prohibición Textual: Prohibido usar "SÍNTESIS",
# "DETALLE", "RESUMEN" o similares.
# #
#    3. RESTRICCIÓN AGRESIVA: Prohibido escribir sobre metabolismo o
# eliminación en este bloque.
# #
#    4. Regla de Contenido Estricta: Solo se listan medicamentos
# afectados (⚠️ o⛔).
# #
#    5. Exclusión: NUNCA listar nombres de fármacos correctamente
# dosificados en la síntesis.
# #
#    6. Formato de Línea (OBLIGATORIO): [Icono ⚠️ o ⛔] + [Nombre] + [Frase corta] + [Siglas Fuente: AEMPS, FDA, EMA, etc]. 
# #
#    7. Lógica de Color (Jerarquía de Gravedad):
# #
#        7.1. ROJO (glow-red): Si aparece al menos un icono ⛔ (Contraindicado).
# #
#        7.2. NARANJA (glow-orange): Si no hay ⛔ pero aparece al menos un icono ⚠️ (Ajuste).
# #
#        7.3. VERDE (glow-green): Si no hay iconos ⚠️ ni ⛔ (Todo correcto).
# #
#    8. REGLA DE FUENTES Y ALCANCE: El análisis debe centrarse ÚNICA Y EXCLUSIVAMENTE
# en la adecuación del fármaco según el Filtrado Glomerular (FG) del paciente.
# Se deben priorizar fuentes oficiales (.gov, AEMPS, FDA) y Open Evidence.
# Cada línea DEBE terminar con la sigla de la fuente oficial consultada.
# #
# #
# IV. BLINDAJE DEL BLOQUE AZUL (blue-detail-container):
# #
#    1. Prohibición de Fragmentación: Detalle y Nota en el mismo div CSS.
# #
#    2. Estilo Fijo: Fondo (#f0f7ff), borde (#bee3f8).
# #
#    3. NOTA IMPORTANTE (4 PUNTOS ESTÁTICOS):
# #
#      3.1. Verifique siempre con la ficha técnica oficial (AEMPS/EMA).
# #
#      3.2. Los ajustes propuestos son orientativos según filtrado glomerular actual.
# #
#      3.3. La decisión final corresponde siempre al prescriptor médico.
# #
#      3.4. Considere la situación clínica global del paciente antes de modificar dosis.
# #
# #
# V. PROTECCIÓN INTEGRAL PESTAÑA 1 (💊 VALIDACIÓN):
# #
#    1. Blindaje Total: Prohibida cualquier modificación en el layout,
# orden de columnas o funciones.
# #
#    2. Componentes Congelados: Registro de paciente (fila única),
# Calculadora dual (Glow morado), Área de texto y Botonera.
# #
#    3. Lógica Funcional: El sistema de callbacks y el prompt de IA no
# admiten cambios de sintaxis.
# #
# #
# VI. BLINDAJE PESTAÑA 2 (📄 INFORME - SOIP & IC):
# #
#    1. ESTRUCTURA SOIP: 4 cuadros de texto verticales con etiquetas de cabecera discretas.
# #
#    2. FRASES FIJAS POR DEFECTO:
# #
#      2.1. Subjetivo (S): "Revisión farmacoterapéutica según función renal."
# #
#      2.2. Objetivo (O): Solo valores > 0. Formato: "Edad: X | Peso: Y | Cr: Z | FG: W".
# #
#      2.3. Interpretación (I): Se anotará automáticamente la síntesis de medicamentos afectados.
# #
#      2.4. Plan (P): "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
# #
#    3. ESTRUCTURA INTERCONSULTA (IC): Un cuadro bajo el otro (Layout Vertical).
# #
#    4. TEXTO IC OBLIGATORIO: "Se solicita valoración médica tras la revisión de la adecuación del tratamiento a la función renal del paciente." 
# #
#      4.1. [Se listará automáticamente lo que aparezca en la sección "I"].
# #
# #
# VII. BLINDAJE ENTRADA MANUAL LAB Y VOLCADO EXCEL:
# #
#    1. Se protegen los campos FG CKD-EPI y FG MDRD-4 situados bajo el Glow Morado.
# #
#    2. El texto del placeholder debe desaparecer al escribir y mostrar la unidad 
# "mL/min/1,73m²" de forma discreta.
# #
#    3. El placeholder del campo FG (Ajuste Manual) DEBE ser siempre: 
# "Entrada Manual FG-Cockcroft-Gault".
# #
#    4. Se blinda el botón "GUARDAR CAMBIOS EN EXCEL" centrado en la base de la Pestaña 2.
# #
# =================================================================

st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

if "sync_edad" not in st.session_state: st.session_state.sync_edad = None
if "active_model" not in st.session_state: st.session_state.active_model = "BUSCANDO..."
if "soip_i" not in st.session_state: st.session_state.soip_i = ""

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except: API_KEY = None

def llamar_ia_en_cascada(prompt):
    disponibles = [m.name.replace('models/', '').replace('gemini-', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods] if API_KEY else ["2.5-flash"]
    orden = ['2.5-flash', 'flash-latest', '1.5-pro']
    for mod_name in orden:
        if mod_name in disponibles:
            try:
                st.session_state.active_model = mod_name.upper()
                model = genai.GenerativeModel(f'models/gemini-{mod_name}')
                return model.generate_content(prompt).text
            except: continue
    return "⚠️ Error."

st.markdown("""<style>
    .block-container { max-width: 100% !important; padding-top: 1rem !important; padding-left: 4% !important; padding-right: 4% !important; }
    .black-badge-zona { background-color: #000000; color: #888; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 15px; z-index: 999999; }
    .black-badge-activo { background-color: #000000; color: #00FF00; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 145px; z-index: 999999; text-shadow: 0 0 5px #00FF00; }
    .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin-bottom: 0px; margin-top: 20px; }
    .sub-version { text-align: center; font-size: 0.6rem; color: #bbb; margin-top: -5px; margin-bottom: 20px; font-family: monospace; }
    .fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .synthesis-box { padding: 15px; border-radius: 12px; margin-bottom: 15px; border-width: 2.2px; border-style: solid; }
    .glow-red { background-color: #fff5f5; color: #c53030; border-color: #feb2b2; }
    .glow-orange { background-color: #fff3e0; color: #e65100; border-color: #ffcc80; }
    .blue-detail-container { background-color: #f0f7ff; color: #2c5282; padding: 20px; border-radius: 10px; border: 1px solid #bee3f8; }
    .warning-yellow { background-color: #fff9db; color: #856404; padding: 20px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 40px; text-align: center; font-size: 0.85rem; }
    </style>""", unsafe_allow_html=True)

st.markdown('<div class="black-badge-zona">ZONA: ACTIVA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="black-badge-activo">ACTIVO: {st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-version">v. 26 feb 22:55</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 EXCEL", "📈 GRÁFICOS"])

with tabs[0]:
    st.markdown("### Registro de Paciente")
    c1, c2, c3, c4, c5, c_del = st.columns([1, 1, 1, 1, 1, 0.4])
    with c1: centro = st.text_input("Centro", placeholder="G/M", key="reg_centro")
    with c2: edad_reg = st.number_input("Edad", value=st.session_state.sync_edad, placeholder="0.0", key="sync_edad")
    with c3: alfa = st.text_input("ID Alfanumérico", placeholder="ABC-123", key="reg_id")
    with c4: res = st.selectbox("¿Residencia?", ["No", "Sí"], index=None, placeholder="Sel...", key="reg_res")
    with c5: st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)
    with c_del: st.write(""); st.button("🗑️", on_click=lambda: st.session_state.update({"sync_edad": None}))

    st.markdown(f'<div style="color:#888; font-family:monospace; font-size:0.75rem; margin-top:-15px; margin-bottom:20px;">ID REGISTRO: {centro if centro else "---"}-{int(edad_reg) if edad_reg else "00"}-{alfa if alfa else "---"}</div>', unsafe_allow_html=True)

    col_izq, col_der = st.columns(2, gap="large")
    with col_izq:
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            calc_e = st.number_input("Edad (años)", value=st.session_state.sync_edad, placeholder="0.0", key="calc_e_sync")
            calc_p = st.number_input("Peso (kg)", value=None, placeholder="0.0", key="calc_p")
            calc_c = st.number_input("Creatinina (mg/dL)", value=None, placeholder="0.0", key="calc_c")
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"], index=None, placeholder="Sel...", key="calc_s")
            fg_calc = round(((140-(calc_e or 0))*(calc_p or 0))/(72*(calc_c or 1))*(0.85 if calc_s=="Mujer" else 1.0),1) if calc_e and calc_p and calc_c else 0.0
            st.markdown('<div style="text-align:right; font-size:0.58rem; color:#888;">FG-Cockcroft-Gault</div>', unsafe_allow_html=True)

    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.number_input("FG", value=None, placeholder="Entrada Manual FG-Cockcroft-Gault")
        v_fg = fg_m if fg_m else fg_calc
        st.markdown(f'<div class="fg-glow-box"><div style="font-size:3.2rem; font-weight:bold;">{v_fg}</div><div style="font-size:0.8rem; color:#9d00ff;">mL/min (FG-Cockcroft-Gault)</div></div>', unsafe_allow_html=True)
        l1, l2 = st.columns(2)
        with l1: val_ckd = st.number_input("FG CKD-EPI", value=None, placeholder="0.0", label_visibility="collapsed", key="v_ckd")
        with l2: val_mdrd = st.number_input("FG MDRD-4", value=None, placeholder="0.0", label_visibility="collapsed", key="v_mdrd")

    st.markdown("#### 📝 Listado de medicamentos")
    txt_meds = st.text_area("Listado", height=150, label_visibility="collapsed", key="main_meds")

    if st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True):
        faltan = [n for n, v in zip(["Centro","Edad","ID","Residencia","Peso","Creatinina","Sexo","CKD-EPI","MDRD-4","Lista"],[centro,edad_reg,alfa,res,calc_p,calc_c,calc_s,val_ckd,val_mdrd,txt_meds]) if not v]
        if faltan:
            st.warning(f"⚠️ Faltan datos críticos ({len(faltan)}/10): {', '.join(faltan)}. ¿Desea continuar?")
        else:
            with st.spinner("Validando..."):
                prompt = f"FG: {v_fg}. Meds: {txt_meds}."
                st.session_state.soip_i = llamar_ia_en_cascada(prompt)
                st.rerun()

    if st.session_state.soip_i:
        color = "glow-red" if "⛔" in st.session_state.soip_i else "glow-orange"
        st.markdown(f'<div class="synthesis-box {color}"><b>Medicamentos afectados:</b><br>{st.session_state.soip_i}</div>', unsafe_allow_html=True)
        st.markdown('<div class="blue-detail-container">3.1 Verifique...<br>3.2 Ajustes...<br>3.3 Decisión médico...<br>3.4 Clínica global...</div>', unsafe_allow_html=True)

st.markdown('<div class="warning-yellow">⚠️ <b>Esta herramienta es de apoyo a la revisión farmacoterapéutica. Verifique siempre con fuentes oficiales.</b></div>', unsafe_allow_html=True)
