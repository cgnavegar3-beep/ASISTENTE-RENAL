# v. 01 mar 2026 09:30

import streamlit as st
import pandas as pd
import io
from datetime import datetime
import google.generativeai as genai
import random
import re
import os # Paso 2: Importar la librería necesaria

# =================================================================
# PRINCIPIOS FUNDAMENTALES:
# #
# # GEMINI SIEMPRE TENDRA RIGOR, RESPETARA Y VERIFICARA QUE SE CUMPLAN
# # ESTOS PRINCIPIOS ANTES Y DESPUES DE REALIZAR CUALQUIER CAMBIO.
# #
# 1. NUNCA BORRAR NI MODIFICAR ESTA CLÁUSULA. 
# #
# # 2. No puedes mover nada, ni cambiar ni una sola línea de la
# # estructura visual (RIGOR Y SERIEDAD). Cero modificaciones sin
# autorización.
# #
# # 3. Antes de cualquier evolución técnica, explicar el "qué",
# # "por qué" y "cómo", and esperar aprobación
# # ("adelante" o "procede").
# #
# #
# # I. ESTRUCTURA VISUAL PROTEGIDA:
# #
#    1. Cuadros negros superiores (ZONA y ACTIVO).
# #
#    2. Título "ASISTENTE RENAL" y Versión inmediatamente
# debajo (Blindado).
# #
#    3. Título principal y pestañas (Tabs).
# #
#    4. Registro de paciente y función: TODO EN UNA LÍNEA (Centro,
# Residencia, Fecha, ID Automatizado, Botón Borrado Registro).
# #
#    5. Interfaz Dual (Calculadora y caja de FG (Purple Glow): lógica
# Cockcroft-Gault.
# #
#        -> REFUERZO: NO SE TOCA LA CALCULADORA, NO SE TOCA EL GLOW
# MORADO.
# #
#        -> REFUERZO: LOS CUADROS DE ENTRADA DE DATOS DEBEN MANTENER
# SU BORDE MORADO Y BRILLO ASOCIADO.
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
# # II. FUNCIONALIDADES CRÍTICAS PROTEGIDAS:
# #
#    1. Cascada de Modelos (2.5 Flash > flash-latest > 1.5 Pro >
# Otros).
# #
#    2. Detección dinámica de modelos vivos en la cuenta.
# #
#    3. Actualización de feedback neón en tiempo real (Badge ACTIVO).
# #
# # III. BLINDAJE DE SÍNTESIS DINÁMICA (Glow System) - ANTI-ALUCINACIONES:
# #
#    1. Títulos Permitidos: SOLO "Medicamentos afectados:" o
# "Fármacos correctamente dosificados".
# #
#    2. Prohibición Textual: Prohibido usar "SÍNTESIS", "DETALLE", "RESUMEN" o similares.
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
#    6. Formato de Línea (OBLIGATORIO): [Icono ⚠️ o ⛔]
# + [Nombre] + [Frase corta] + [Siglas Fuente: AEMPS, FDA, EMA, etc]. 
# #
#    7. Lógica de Color (Jerarquía de Gravedad):
# #
#        7.1. ROJO (glow-red): Si aparece al menos un icono ⛔
# (Contraindicado).
# #
#        7.2. NARANJA (glow-orange): Si no hay ⛔ pero aparece al menos un icono⚠️ (Ajuste).
# #
#        7.3. VERDE (glow-green): Si no hay iconos ⚠️ ni ⛔
# (Todo correcto).
# #
#    8. REGLA DE FUENTES Y ALCANCE: El análisis debe centrarse ÚNICA Y EXCLUSIVAMENTE
# en la adecuación del fármaco según el Filtrado Glomerular (FG) del
# paciente.
# Se deben priorizar fuentes oficiales (.gov, AEMPS, FDA) and Open Evidence.
# Cada línea DEBE terminar con la sigla de la fuente oficial consultada.
# #
# # IV. BLINDAJE DEL BLOQUE AZUL (blue-detail-container):
# #
#    1. Prohibición de Fragmentación: Detalle y Nota en el mismo div
# CSS.
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
# # V. PROTECCIÓN INTEGRAL PESTAÑA 1 (💊 VALIDACIÓN):
# #
#    1. Blindaje Total: Prohibida cualquier modificación en el layout,
# orden de columnas o funciones.
# #
#    2. Componentes Congelados: Registro de paciente (fila única),
# Calculadora dual (Glow morado), Área de texto y Botonera.
# #
#    3. Lógica Funcional: El sistema de callbacks y el prompt de IA
# no admiten cambios de sintaxis.
# #
# # VI. BLINDAJE PESTAÑA 2 (📄 INFORME - SOIP & IC):
# #
#    1. ESTRUCTURA SOIP: 4 cuadros de texto verticales con etiquetas de
# cabecera discretas.
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
#    4.1. [Se listará automáticamente lo que aparezca en la sección "I"].
# #
# # VII. BLINDAJE ENTRADA MANUAL LAB Y VOLCADO EXCEL:
# #
#    1. Se protegen los campos FG CKD-EPI y FG MDRD-4 situados bajo el Glow Morado.
# #
#    2. El texto del placeholder debe desaparecer al escribir y mostrar la unidad 
# "mL/min/1,73m²" de forma discreta.
# #
#    3. Se blinda el botón "GUARDAR CAMBIOS EN EXCEL" centrado en la base de la Pestaña 2.
# #
# =================================================================

st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

if "active_model" not in st.session_state:
    st.session_state.active_model = "BUSCANDO..."

# INICIALIZACIÓN DE VARIABLES DE SESIÓN
for key in ["soip_s", "soip_o", "soip_i", "soip_p", "ic_motivo", "ic_info", "main_meds", "reg_id", "reg_centro"]:
    if key not in st.session_state:
        if key == "soip_s": st.session_state[key] = "Revisión farmacoterapéutica según función renal."
        elif key == "soip_p": st.session_state[key] = "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
        elif key == "ic_motivo": st.session_state[key] = "Se solicita valoración médica tras la revisión de la adecuación del tratamiento a la función renal del paciente."
        else: st.session_state[key] = ""

# Paso 2: Función para cargar el prompt desde el archivo en la carpeta prompts/
def cargar_prompt_clinico():
    try:
        with open(os.path.join("prompts", "categorizador.txt"), "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Error: No se encontró el archivo de prompt."

# --- FUNCION DE PROCESAMIENTO HÍBRIDO (RegEx + IA) ---
def procesar_y_limpiar_meds():
    texto = st.session_state.main_meds
    if texto:
        # 1. Limpieza inicial rápida con RegEx
        texto_limpio = re.sub(r"\s*-\s*|;\s*", "\n", texto)
        texto_limpio = re.sub(r"\n+", "\n", texto_limpio).strip()
        
        # --- NUEVA LÓGICA DE LIMPIEZA DE DOSIS ---
        # Detecta patrones como 80.0000 mg -> 80 mg
        texto_limpio = re.sub(r"(\d+)\.0+\s*(mg|g|mcg|ml)", r"\1 \2", texto_limpio, flags=re.IGNORECASE)
        # ------------------------------------------

        # 2. Prompt IA modificado para incluir Principio Activo, Dosis y Marca
        prompt = f"""
        Actúa como farmacéutico clínico. Reescribe el siguiente listado de medicamentos siguiendo estas reglas estrictas:
        1. Estructura cada línea como: [Principio Activo] + [Dosis] + (Marca Comercial).
        2. Si no identificas la marca, omite el paréntesis.
        3. Coloca cada medicamento en una línea independiente.
        4. Mantén exactamente el mismo texto original si no es necesario reestructurar, sin añadir ni inventar información.
        5. No agregues numeración ni explicaciones.
        Texto a procesar:
        {texto_limpio}
        """
        
        # 3. Llamada a la IA (en cascada)
        resultado = llamar_ia_en_cascada(prompt)
        
        # 4. Actualiza el mismo cuadro
        st.session_state.main_meds = resultado
# ----------------------------------------------------

def reset_registro():
    st.session_state["reg_centro"] = ""; st.session_state["reg_edad"] = None
    st.session_state["reg_res"] = None; st.session_state["reg_id"] = ""
    if "calc_e" in st.session_state: st.session_state.calc_e = None
    if "calc_s" in st.session_state: st.session_state.calc_s = None

def reset_meds():
    st.session_state.main_meds = ""
    st.session_state.soip_s = "Revisión farmacoterapéutica según función renal."
    st.session_state.soip_o = ""; st.session_state.soip_i = ""
    st.session_state.soip_p = "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
    st.session_state.ic_motivo = "Se solicita valoración médica tras la revisión de la adecuación del tratamiento a la función renal del paciente."
    st.session_state.ic_info = ""

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    API_KEY = None

def verificar_datos_completos():
    campos = {
        "Centro": "reg_centro", "Residencia": "reg_res", "ID Registro": "reg_id",
        "Edad (Calc)": "calc_e", "Peso (Calc)": "calc_p", "Creatinina (Calc)": "calc_c",
        "Sexo (Calc)": "calc_s", "FG CKD-EPI": "fgl_ckd", "FG MDRD-4": "fgl_mdrd"
    }
    vacios = [nombre for nombre, key in campos.items() if st.session_state.get(key) in [None, "", "Seleccionar..."]]
    return vacios

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

def inject_styles():
    st.markdown("""
    <style>
    /* ANIMACIÓN DE PARPADEO PARA AVISOS */
    @keyframes blinker {
        50% { opacity: 0; }
    }
    .blink-text { animation: blinker 1s linear infinite; }
         
    .block-container { max-width: 100% !important; padding-top: 1rem !important; padding-left: 4% !important; padding-right: 4% !important; }
    .black-badge-zona { background-color: #000000; color: #888; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 15px; z-index: 999999; }
    .black-badge-activo { background-color: #000000; color: #00FF00; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 145px; z-index: 999999; text-shadow: 0 0 5px #00FF00; }
    .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin-bottom: 0px; margin-top: 20px; }
    .sub-version { text-align: center; font-size: 0.6rem; color: #bbb; margin-top: -5px; margin-bottom: 20px; font-family: monospace; }
    .fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .unit-label { font-size: 0.65rem; color: #888; margin-top: -10px; margin-bottom: 5px; font-family: sans-serif; text-align: center; }
    .synthesis-box { padding: 15px; border-radius: 12px; margin-bottom: 15px; border-width: 2.2px; border-style: solid; font-size: 0.95rem; }
    .glow-green { background-color: #f1f8e9; color: #2e7d32; border-color: #a5d6a7; box-shadow: 0 0 12px #a5d6a7; }
    .glow-orange { background-color: #fff3e0; color: #e65100; border-color: #ffcc80; box-shadow: 0 0 12px #ffcc80; }
    .glow-red { background-color: #fff5f5; color: #c53030; border-color: #feb2b2; box-shadow: 0 0 18px #feb2b2; }
    .blue-detail-container { background-color: #f0f7ff; color: #2c5282; padding: 20px; border-radius: 10px; border: 1px solid #bee3f8; margin-top: 10px; }
    .warning-yellow { background-color: #fff9db; color: #856404; padding: 20px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 40px; text-align: center; font-size: 0.85rem; line-height: 1.5; }
    .linea-discreta-soip { border-top: 1px solid #d9d5c7; margin: 15px 0 5px 0; font-size: 0.65rem; font-weight: bold; color: #8e8a7e; text-transform: uppercase; }
    .header-capsule { background-color: #e2e8f0; color: #2d3748; padding: 10px 30px; border-radius: 50px; display: inline-block; font-weight: 800; font-size: 0.9rem; margin-bottom: 20px; }
    .formula-label { font-size: 0.6rem; color: #666; font-family: monospace; text-align: right; margin-top: 5px; }
    .fg-special-border { border: 1.5px solid #9d00ff !important; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)
inject_styles()

st.markdown('<div class="black-badge-zona">ZONA: ACTIVA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="black-badge-activo">ACTIVO: {st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-version">v. 01 mar 2026 09:30</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 DATOS", "📈 GRÁFICOS"])

with tabs[0]:
    st.markdown("### Registro de Paciente")
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1.5, 0.4])
    def on_centro_change():
        centro_val = st.session_state.reg_centro.strip()
        if centro_val.lower() == "m": st.session_state.reg_centro = "Marín"
        elif centro_val.lower() == "o": st.session_state.reg_centro = "O Grove"
        
        if not st.session_state.reg_centro: st.session_state.reg_id = ""
        else:
            final_centro = st.session_state.reg_centro
            iniciales = "".join([word[0] for word in final_centro.split()]).upper()[:3]
            st.session_state.reg_id = f"PAC-{iniciales if iniciales else 'GEN'}{random.randint(10000, 99999)}"
    
    with c1: st.text_input("Centro", placeholder="M / G", key="reg_centro", on_change=on_centro_change)
    with c2: st.selectbox("¿Residencia?", ["No", "Sí"], index=None, placeholder="Sí / No", key="reg_res")
    with c3: st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)
    with c4: st.text_input("ID Registro", key="reg_id")
    with c5: st.write(""); st.button("🗑️", on_click=reset_registro)
    
    col_izq, col_der = st.columns(2, gap="large")
    with col_izq:
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            calc_e = st.number
