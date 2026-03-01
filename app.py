# v. 01 mar 08:45
import streamlit as st
import pandas as pd
import io
from datetime import datetime
import google.generativeai as genai
import random
import re

# =================================================================
# # PRINCIPIOS FUNDAMENTALES:
# #
# # GEMINI SIEMPRE TENDRA RIGOR, RESPETARA Y VERIFICARA QUE SE CUMPLAN
# # ESTOS PRINCIPIOS ANTES Y DESPUES DE REALIZAR CUALQUIER CAMBIO.
# #
# # 1. NUNCA BORRAR NI MODIFICAR ESTA CLÁUSULA. 
# #
# # 2. No puedes mover nada, ni cambiar ni una sola línea de la
# # estructura visual (RIGOR Y SERIEDAD). Cero modificaciones sin
# # autorización.
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
# #
# # III. BLINDAJE DE SÍNTESIS DINÁMICA (Glow System) - ANTI-ALUCINACIONES:
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
#    6. Formato de Línea (OBLIGATORIO): [Icono ⚠️ o ⛔]
# + [Nombre] + [Frase corta] + [Siglas Fuente: AEMPS, FDA, EMA, etc]. 
# #
#    7. Lógica de Color (Jerarquía de Gravedad):
# #
#        7.1. ROJO (glow-red): Si aparece al menos un icono ⛔ (Contraindicado).
# #
#        7.2. NARANJA (glow-orange): Si no hay ⛔ pero aparece al menos un icono⚠️ (Ajuste).
# #
#        7.3. VERDE (glow-green): Si no hay iconos ⚠️ ni ⛔ (Todo correcto).
# #
#    8. REGLA DE FUENTES Y ALCANCE: El análisis debe centrarse ÚNICA Y EXCLUSIVAMENTE
# en la adecuación del fármaco según el Filtrado Glomerular (FG) del paciente.
# Se deben priorizar fuentes oficiales (.gov, AEMPS, FDA) and Open Evidence.
# Cada línea DEBE terminar con la sigla de la fuente oficial consultada.
# #
# #
# # IV. BLINDAJE DEL BLOQUE AZUL (blue-detail-container):
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
# # V. PROTECCIÓN INTEGRAL PESTAÑA 1 (💊 VALIDACIÓN):
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
# # VI. BLINDAJE PESTAÑA 2 (📄 INFORME - SOIP & IC):
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

# --- FUNCION DE PROCESAMIENTO HÍBRIDO (RegEx + IA) ---
def procesar_y_limpiar_meds():
    texto = st.session_state.main_meds
    if texto:
        # 1. Limpieza inicial rápida con RegEx
        texto_limpio = re.sub(r"\s*-\s*|;\s*", "\n", texto)
        texto_limpio = re.sub(r"\n+", "\n", texto_limpio).strip()
        
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
st.markdown('<div class="sub-version">v. 01 mar 08:45</div>', unsafe_allow_html=True)

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
            calc_e = st.number_input("Edad (años)", value=st.session_state.get("reg_edad", None), step=1, key="calc_e", placeholder="0.0")
            calc_p = st.number_input("Peso (kg)", value=None, placeholder="0.0", key="calc_p")
            calc_c = st.number_input("Creatinina (mg/dL)", value=None, placeholder="0.0", key="calc_c")
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"], index=None, placeholder="Elegir...", key="calc_s")
            st.markdown('<div class="formula-label" style="text-align:right;">Fórmula Cockcroft-Gault</div>', unsafe_allow_html=True)
            fg = round(((140 - (calc_e or 0)) * (calc_p or 0)) / (72 * (calc_c or 1)) * (0.85 if calc_s == "Mujer" else 1.0), 1) if calc_e and calc_p and calc_c and calc_s else 0.0
    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual", placeholder="Fórmula Cockcroft-Gault: entrada manual")
        valor_fg = fg_m if fg_m else fg
        st.markdown(f'''<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{valor_fg}</div><div style="font-size: 0.8rem; color: #9d00ff;">mL/min (C-G)</div></div>''', unsafe_allow_html=True)
        st.markdown('<div class="formula-label">Fórmula Cockcroft-Gault</div>', unsafe_allow_html=True)
        st.write(""); l1, l2 = st.columns(2)
        with l1:
            st.markdown('<div class="fg-special-border">', unsafe_allow_html=True)
            val_ckd = st.number_input("FG CKD-EPI", value=None, placeholder="FG CKD-EPI", label_visibility="collapsed", key="fgl_ckd")
            st.markdown('</div>', unsafe_allow_html=True)
            if val_ckd is not None: st.markdown(f'<div class="unit-label">{val_ckd} mL/min/1,73m²</div>', unsafe_allow_html=True)
        with l2:
            st.markdown('<div class="fg-special-border">', unsafe_allow_html=True)
            val_mdrd = st.number_input("FG MDRD-4 IDMS", value=None, placeholder="FG MDRD-4 IDMS", label_visibility="collapsed", key="fgl_mdrd")
            st.markdown('</div>', unsafe_allow_html=True)
            if val_mdrd is not None: st.markdown(f'<div class="unit-label">{val_mdrd} mL/min/1,73m²</div>', unsafe_allow_html=True)
    
    st.write(""); st.markdown("---")
    m_col1, m_col2 = st.columns([0.5, 0.5])
    with m_col1: st.markdown("#### 📝 Listado de medicamentos")
    with m_col2: st.markdown('<div style="float:right; background-color:#fff5f5; color:#c53030; padding:8px 16px; border-radius:8px; border:1.5px solid #feb2b2; font-size:0.8rem;">🛡️ RGPD: No datos personales</div>', unsafe_allow_html=True)
    
    txt_meds = st.text_area("Listado", height=150, label_visibility="collapsed", key="main_meds")
    
    st.button("Procesar medicamentos", on_click=procesar_y_limpiar_meds)
    
    b1, b2 = st.columns([0.85, 0.15])
    btn_val = b1.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True)
    b2.button("🗑️ RESET", on_click=reset_meds, use_container_width=True)

    if btn_val:
        faltantes = verificar_datos_completos()
        if faltantes:
            st.markdown(f'<div style="background-color: #fff3cd; color: #856404; padding: 1rem; border-radius: 0.5rem; border: 1px solid #ffeeba; margin-bottom: 1rem;"><span class="blink-text">⚠️ Nota: Faltan datos en el registro ({", ".join(faltantes)}). Se procede con validación de consulta rápida.</span></div>', unsafe_allow_html=True)
        
        if not txt_meds:
            st.error("Por favor, introduce al menos un medicamento.")
        else:
            placeholder_salida = st.empty()
            with st.spinner("Procesando análisis clínico..."):
                prompt_analisis = (f"Actúa como farmacéutico clínico experto. Analiza la adecuación de los siguientes medicamentos según el FG: {valor_fg}. "
                                   f"Listado: {txt_meds}. "
                                   f"FORMATO OBLIGATORIO DE LÍNEA: [Icono ⚠️ o ⛔] + [Nombre] + [Frase corta] + (Sigla fuente: AEMPS, FDA o EMA). "
                                   f"Título síntesis: Comienza directamente con 'Medicamentos afectados:' o 'Fármacos correctamente dosificados:'. "
                                   f"Separa detalle con: 'A continuación, se detallan los ajustes:'.")
                
                resp = llamar_ia_en_cascada(prompt_analisis)
                glow = "glow-red" if "⛔" in resp else ("glow-orange" if "⚠️" in resp else "glow-green")
                try:
                    partes = resp.split("A continuación, se detallan los ajustes")
                    sintesis, detalle = partes[0].strip(), "A continuación, se detallan los ajustes" + (partes[1] if len(partes)>1 else "")
                    with placeholder_salida.container():
                        st.markdown(f'<div class="synthesis-box {glow}"><b>{sintesis.replace("\n", "<br>")}</b></div>', unsafe_allow_html=True)
                        st.markdown(f"""<div class="blue-detail-container">{detalle.replace("\n", "<br>")}
                        <br><br><span style="color:#2c5282;"><b>NOTA IMPORTANTE:</b></span><br>
                        <b>3.1. Verifique siempre con la ficha técnica oficial (AEMPS/EMA).</b><br>
                        <b>3.2. Los ajustes propuestos son orientativos según filtrado glomerular actual.</b><br>
                        <b>3.3. La decisión final corresponde siempre al prescriptor médico.</b><br>
                        <b>3.4. Considere la situación clínica global del paciente antes de modificar dosis.</b></div>""", unsafe_allow_html=True)
                    st.session_state.soip_o = " | ".join(filter(None, [f"Edad: {int(calc_e)}" if calc_e else "", f"Peso: {calc_p}" if calc_p else "", f"Cr: {calc_c}" if calc_c else "", f"FG: {valor_fg}" if float(valor_fg or 0)>0 else ""]))
                    st.session_state.soip_i = sintesis
                    st.session_state.ic_info = detalle
                    st.session_state.ic_motivo = f"Se solicita valoración médica tras la revisión de la adecuación del tratamiento a la función renal del paciente.\n\nLISTADO DETECTADO:\n{sintesis}"
                except: st.error("Error en la estructura de respuesta.")

with tabs[1]:
    st.markdown('<div style="text-align:center;"><div class="header-capsule">📄 Nota Evolutiva SOIP</div></div>', unsafe_allow_html=True)
    for label, key, h in [("Subjetivo (S)", "soip_s", 70), ("Objetivo (O)", "soip_o", 70), ("Interpretación (I)", "soip_i", 120), ("Plan (P)", "soip_p", 100)]:
        st.markdown(f'<div class="linea-discreta-soip">{label}</div>', unsafe_allow_html=True)
        st.text_area(key, st.session_state[key], height=h, label_visibility="collapsed")
    st.write(""); st.markdown('<div style="text-align:center;"><div class="header-capsule">📨 Solicitud de Interconsulta</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="linea-discreta-soip">Motivo de la Interconsulta</div>', unsafe_allow_html=True)
    st.text_area("ic_mot", st.session_state.ic_motivo, height=180, label_visibility="collapsed")
    st.markdown('<div class="linea-discreta-soip">Información Clínica</div>', unsafe_allow_html=True)
    st.text_area("ic_inf", st.session_state.ic_info, height=250, label_visibility="collapsed")

with tabs[2]:
    st.markdown('<div style="text-align:center;"><div class="header-capsule">📊 Gestión de Datos y Volcado</div></div>', unsafe_allow_html=True)

st.markdown(f"""<div class="warning-yellow">⚠️ <b>Esta herramienta es de apoyo a la revisión farmacoterapéutica. Verifique siempre con fuentes oficiales.</b></div> <div style="text-align:right; font-size:0.6rem; color:#ccc; font-family:monospace; margin-top:10px;">v. 01 mar 08:45</div>""", unsafe_allow_html=True)
