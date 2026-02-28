# v. 27 feb 20:32
import streamlit as st
import pandas as pd
import io
from datetime import datetime
import google.generativeai as genai
import random
import string

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
# "por qué" y "cómo", and esperar aprobación
# ("adelante" o "procede").
#
#
# #
# I. ESTRUCTURA VISUAL PROTEGADA:
# #
#    1. Cuadros negros superiores (ZONA y ACTIVO).
# #
#    2. Título "ASISTENTE RENAL" y Versión inmediatamente
# debajo (Blindado).
# #
#    3. Título principal y pestañas (Tabs).
# #
#    4. Registro de paciente y función: TODO EN UNA LÍNEA (Centro,
# Edad, ID Alfa, Res, Fecha + Botón Borrado Registro).
# #
#    -> REFUERZO: DEBAJO DE LA LÍNEA DE REGISTRO DEBE APARECER SIEMPRE 
# EL "ID REGISTRO" DINÁMICO (CENTRO-EDAD-ALFA).
# #
#    5. Interfaz Dual (Calculadora y caja de FG (Purple Glow): lógica
# Cockcroft-Gault.
# #
#        -> REFUERZO: NO SE TOCA LA CALCULADORA, NO SE TOCA EL GLOW
# MORADO.
# #
#    6. Layout Medicamentos: Título y Aviso RGPD (estilo ampliado) en
# la misma línea.
# #
#    7. Cuadro de listado de medicamentos (TextArea).
# #
#    8. Barra dual de botones (VALIDAR / RESET TOTAL) y Reset de
# Registro.
# #
#    9. Aviso amarillo de apoyo legal inferior CON EL TEXTO: ⚠️
# Esta herramienta es de apoyo a la revisión farmacoterapéutica.
# Verifique siempre con fuentes oficiales.
# #
# #
# II. FUNCIONALIDADES CRÍTICAS PROTEGIDAS:
# #
#    1. Cascada de Modelos (2.5 Flash > flash-latest > 1.5 Pro >
# Otros).
# #
#    2. Detección dinámica de modelos vivos en la cuenta.
# #
#    3. Actualización de feedback neón en tiempo real (Badge ACTIVO).
# #
# #
# III. BLINDAJE DE SÍNTESIS DINÁMICA (Glow System) - ANTI-ALUCINACIONES:
# #
#    1. Títulos Permitidos: SOLO "Medicamentos afectados:" o
# "Fármacos correctamente dosificados".
# #
#    2. Prohibición Textual: Prohibido usar "SÍNTESIS",
# "DETALLE", "RESUMEN" o similares.
# #
#    3. RESTRICCIÓN AGRESIVA: Prohibido escribir sobre metabolismo o
# eliminación en este bloque.
# #
#    4. Regla de Contenido Estricta: Solo se listan medicamentos
# afectados (⚠️ o⛔).
# #
#    5. Exclusión: NUNCA listar nombres de fármacos correctamente
# dosificados en la síntesis.
# #
#    6. Formato de Línea (OBLIGATORIO): [Icono ⚠️ o ⛔] + [Nombre] + [Frase corta] + [Siglas Fuente: AEMPS, FDA, EMA, etc]. 
# #
#    7. Lógica de Color (Jerarquía de Gravedad):
# #
#        7.1. ROJO (glow-red): Si aparece al menos un icono ⛔ (Contraindicado).
# #
#        7.2. NARANJA (glow-orange): Si no hay ⛔ pero aparece al menos un icono ⚠️ (Ajuste).
# #
#        7.3. VERDE (glow-green): Si no hay iconos ⚠️ ni ⛔ (Todo correcto).
# #
#    8. REGLA DE FUENTES Y ALCANCE: El análisis debe centrarse ÚNICA Y EXCLUSIVAMENTE
# en la adecuación del fármaco según el Filtrado Glomerular (FG) del paciente.
# Se deben priorizar fuentes oficiales (.gov, AEMPS, FDA) and Open Evidence.
# Cada línea DEBE terminar con la sigla de la fuente oficial consultada.
# #
# #
# IV. BLINDAJE DEL BLOQUE AZUL (blue-detail-container):
# #
#    1. Prohibición de Fragmentación: Detalle y Nota en el mismo div CSS.
# #
#    2. Estilo Fijo: Fondo (#f0f7ff), borde (#bee3f8).
# #
#    3. NOTA IMPORTANTE (4 PUNTOS ESTÁTICOS):
# #
#      3.1. Verifique siempre con la ficha técnica oficial (AEMPS/EMA).
# #
#      3.2. Los ajustes propuestos son orientativos según filtrado glomerular actual.
# #
#      3.3. La decisión final corresponde siempre al prescriptor médico.
# #
#      3.4. Considere la situación clínica global del paciente antes de modificar dosis.
# #
# #
# V. PROTECCIÓN INTEGRAL PESTAÑA 1 (💊 VALIDACIÓN):
# #
#    1. Blindaje Total: Prohibida cualquier modificación en el layout,
# orden de columnas o funciones.
# #
#    2. Componentes Congelados: Registro de paciente (fila única),
# Calculadora dual (Glow morado), Área de texto y Botonera.
# #
#    3. Lógica Funcional: El sistema de callbacks y el prompt de IA no
# admiten cambios de sintaxis.
# #
# #
# VI. BLINDAJE PESTAÑA 2 (📄 INFORME - SOIP & IC):
# #
#    1. ESTRUCTURA SOIP: 4 cuadros de texto verticales con etiquetas de cabecera discretas.
# #
#    2. FRASES FIJAS POR DEFECTO:
# #
#      2.1. Subjetivo (S): "Revisión farmacoterapéutica según función renal."
# #
#      2.2. Objetivo (O): Solo valores > 0. Formato: "Edad: X | Peso: Y | Cr: Z | FG: W".
# #
#      2.3. Interpretación (I): Se anotará automáticamente la síntesis de medicamentos afectados.
# #
#      2.4. Plan (P): "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
# #
#    3. ESTRUCTURA INTERCONSULTA (IC): Un cuadro bajo el otro (Layout Vertical).
# #
#    4. TEXTO IC OBLIGATORIO: "Se solicita valoración médica tras la revisión de la adecuación del tratamiento a la función renal del paciente." 
# #
#      4.1. [Se listará automáticamente lo que aparezca en la sección "I"].
# #
# #
# VII. BLINDAJE ENTRADA MANUAL LAB Y VOLCADO EXCEL:
# #
#    1. Se protegen los campos FG CKD-EPI y FG MDRD-4 situados bajo el Glow Morado.
# #
#    2. El texto del placeholder debe desaparecer al escribir y mostrar la unidad 
# "mL/min/1,73m²" de forma discreta.
# #
#    3. Se blinda el botón "GUARDAR CAMBIOS EN EXCEL" centrado en la base de la Pestaña 2.
# #
# =================================================================

st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

if "active_model" not in st.session_state:
    st.session_state.active_model = "BUSCANDO..."

# Inicialización de estados con textos fijos (Principio VI)
if "soip_s" not in st.session_state: st.session_state.soip_s = "Revisión farmacoterapéutica según función renal."
if "soip_o" not in st.session_state: st.session_state.soip_o = ""
if "soip_i" not in st.session_state: st.session_state.soip_i = ""
if "soip_p" not in st.session_state: st.session_state.soip_p = "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
if "ic_motivo" not in st.session_state: st.session_state.ic_motivo = "Se solicita valoración médica tras la revisión de la adecuación del tratamiento a la función renal del paciente."
if "ic_info" not in st.session_state: st.session_state.ic_info = ""
if "main_meds" not in st.session_state: st.session_state.main_meds = ""
if "reg_id_display" not in st.session_state: st.session_state.reg_id_display = "PENDIENTE..."

def generar_id_registro_final(centro):
    inicial = centro[0].upper() if centro else "X"
    aleatorio = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"PAC-{inicial}-{aleatorio}"

def reset_registro():
    st.session_state["reg_centro"] = ""; st.session_state["reg_res"] = "No"
    st.session_state["reg_id_display"] = "PENDIENTE..."
    # Reset sincrónico campos calculadora
    if "calc_e" in st.session_state: st.session_state.calc_e = None
    if "calc_p" in st.session_state: st.session_state.calc_p = None
    if "calc_c" in st.session_state: st.session_state.calc_c = None
    if "fgl_ckd" in st.session_state: st.session_state.fgl_ckd = None
    if "fgl_mdrd" in st.session_state: st.session_state.fgl_mdrd = None

def reset_meds():
    st.session_state.main_meds = ""
    st.session_state.soip_s = "Revisión farmacoterapéutica según función renal."
    st.session_state.soip_o = ""
    st.session_state.soip_i = ""
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
        "Centro": "reg_centro",
        "Residencia": "reg_res",
        "Calc. Edad": "calc_e", 
        "Calc. Peso": "calc_p",
        "Calc. Creatinina": "calc_c",
        "Calc. Sexo": "calc_s",
        "FG CKD-EPI": "fgl_ckd",
        "FG MDRD-4": "fgl_mdrd"
    }
    campos_vacios = []
    for nombre, key in campos.items():
        valor = st.session_state.get(key)
        if valor is None or valor == "":
            campos_vacios.append(nombre)
    return campos_vacios

def llamar_ia_en_cascada(prompt):
    # Si no hay API_KEY, simulamos
    if not API_KEY:
        st.session_state.active_model = "SIMULADO"
        return "✅ Simulación: Todo correcto (AEMPS)."

    try:
        # Obtener todos los modelos disponibles en la cuenta
        all_models = genai.list_models()
        # Filtrar solo los capaces de generar contenido (chat/texto)
        modelos_disponibles = [m.name for m in all_models if 'generateContent' in m.supported_generation_methods]
        
        # Ordenar priorizando los modelos rápidos/nuevos si existen
        prioridad = ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']
        modelos_ordenados = sorted(modelos_disponibles, key=lambda x: (0 if any(p in x for p in prioridad) else 1, x))

        for model_name in modelos_ordenados:
            try:
                st.session_state.active_model = model_name.replace('models/', '').upper()
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                return response.text
            except Exception:
                # Si este modelo falla, intentamos el siguiente automáticamente
                continue
                
    except Exception as e:
        st.session_state.active_model = "ERROR_API"
        return f"⚠️ Error en la API: {str(e)}"
            
    st.session_state.active_model = "SIN_MODELOS"
    return "⚠️ Error: No se encontraron modelos disponibles."

def inject_styles():
    st.markdown("""
    <style>
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
    
    /* GLOW SUTIL: LÍNEA MORADA FINA */
    .glow-subtle-purple { border: 1px solid #9d00ff; border-radius: 4px; padding: 2px; }
    
    /* Ajuste para que el layout de la linea superior quede bien */
    div[data-testid="stHorizontalBlock"] { gap: 1rem; }
    </style>
    """, unsafe_allow_html=True)

inject_styles()
st.markdown('<div class="black-badge-zona">ZONA: ACTIVA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="black-badge-activo">ACTIVO: {st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-version">v. 27 feb 20:32</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 EXCEL", "📈 GRÁFICOS"])

with tabs[0]:
    st.markdown("### Registro de Paciente")
    
    # Columnas: Centro, Residencia, ID, Fecha, Botón
    c1, c2, c3, c4, c_del = st.columns([1, 1, 1.5, 1, 0.4])
    
    with c1: centro = st.text_input("Centro", placeholder="G/M", key="reg_centro")
    with c2: res = st.selectbox("¿Residencia?", ["No", "Sí"], key="reg_res")
    
    # ID Se muestra al validar
    with c3: 
        st.text_input("ID REGISTRO", value=st.session_state.reg_id_display, disabled=True, key="reg_id_display_input")

    with c4: st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)
    with c_del: st.write(""); st.button("🗑️", on_click=reset_registro)

    col_izq, col_der = st.columns(2, gap="large")
    with col_izq:
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            calc_e = st.number_input("Edad (años)", value=None, step=1, key="calc_e", placeholder="0.0")
            calc_p = st.number_input("Peso (kg)", value=None, placeholder="0.0", key="calc_p")
            calc_c = st.number_input("Creatinina (mg/dL)", value=None, placeholder="0.0", key="calc_c")
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"], key="calc_s")
            
            st.markdown('<div class="formula-label" style="text-align:right;">Fórmula Cockcroft-Gault</div>', unsafe_allow_html=True)
            
            fg = round(((140 - (calc_e or 0)) * (calc_p or 0)) / (72 * (calc_c or 1)) * (0.85 if calc_s == "Mujer" else 1.0), 1) if calc_e and calc_p and calc_c else 0.0

    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual", placeholder="Fórmula Cockcroft-Gault :entrada manual")
        valor_fg = fg_m if fg_m else fg
        st.markdown(f'''<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{valor_fg}</div><div style="font-size: 0.8rem; color: #9d00ff;">mL/min (C-G)</div></div>''', unsafe_allow_html=True)
        
        st.markdown('<div class="formula-label">Fórmula Cockcroft-Gault</div>', unsafe_allow_html=True)
        
        st.write("")
        l1, l2 = st.columns(2)
        with l1:
            st.markdown('<div class="glow-subtle-purple">', unsafe_allow_html=True)
            val_ckd = st.number_input("FG CKD-EPI", value=None, placeholder="FG CKD-EPI", label_visibility="collapsed", key="fgl_ckd")
            st.markdown('</div>', unsafe_allow_html=True)
            if val_ckd is not None: st.markdown(f'<div class="unit-label">{val_ckd} mL/min/1,73m²</div>', unsafe_allow_html=True)
        
        with l2:
            st.markdown('<div class="glow-subtle-purple">', unsafe_allow_html=True)
            val_mdrd = st.number_input("FG MDRD-4 IDMS", value=None, placeholder="FG MDRD-4 IDMS", label_visibility="collapsed", key="fgl_mdrd")
            st.markdown('</div>', unsafe_allow_html=True)
            if val_mdrd is not None: st.markdown(f'<div class="unit-label">{val_mdrd} mL/min/1,73m²</div>', unsafe_allow_html=True)

    st.write(""); st.markdown("---")
    m_col1, m_col2 = st.columns([0.5, 0.5])
    with m_col1: st.markdown("#### 📝 Listado de medicamentos")
    with m_col2: st.markdown('<div style="float:right; background-color:#fff5f5; color:#c53030; padding:8px 16px; border-radius:8px; border:1.5px solid #feb2b2; font-size:0.8rem;">🛡️ RGPD: No datos personales</div>', unsafe_allow_html=True)
    
    txt_meds = st.text_area("Listado", height=150, label_visibility="collapsed", key="main_meds")

    b1, b2 = st.columns([0.85, 0.15])
    with b1: btn_val = st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True)
    with b2: st.button("🗑️ RESET", on_click=reset_meds, use_container_width=True)

    if btn_val and txt_meds:
        # FASE DE VERIFICACIÓN
        campos_faltantes = verificar_datos_completos()
        
        proceder = True
        if campos_faltantes:
            st.warning(f"⚠️ Campos vacíos: {', '.join(campos_faltantes)}.")
            if not st.checkbox("Entendido, proceder sin estos datos"):
                proceder = False
                st.stop()
        
        if proceder:
            # GENERAR Y ACTUALIZAR ID AL VALIDAR
            nuevo_id = generar_id_registro_final(st.session_state['reg_centro'])
            st.session_state['reg_id'] = nuevo_id
            st.session_state['reg_id_display'] = nuevo_id
            
            # Forzar recarga para mostrar el ID inmediatamente
            st.rerun() 
            
            # Llamada a IA
            placeholder_salida = st.empty()
            with st.spinner("Procesando..."):
                prompt = f"""
                Analiza la adecuación de estos fármacos para FG: {valor_fg} mL/min.
                Usa fuentes: AEMPS, FDA, EMA.
                REGLAS OBLIGATORIAS:
                1. FORMATO: [Icono] Nombre - Ajuste - (Fuente).
                2. SÍNTESIS: Empieza con 'Medicamentos afectados:' o 'Fármacos correctamente dosificados:'.
                3. PROHIBICIONES: No inventar metabolismo. No usar 'Síntesis', 'Detalle' o 'Resumen'.
                4. SI NO HAY DATOS: Escribe '[Nombre] - Sin datos claros - (AEMPS)'.
                Fármacos: {txt_meds}
                """
                resp = llamar_ia_en_cascada(prompt)
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
                    
                    obj_parts = [f"Edad: {int(calc_e)}" if calc_e else "", f"Peso: {calc_p}" if calc_p else "", f"Cr: {calc_c}" if calc_c else "", f"FG: {valor_fg}" if float(valor_fg)>0 else ""]
                    st.session_state.soip_o = " | ".join(filter(None, obj_parts))
                    st.session_state.soip_i = sintesis
                    st.session_state.ic_info = detalle
                    st.session_state.ic_motivo = f"Se solicita valoración médica tras la revisión de la adecuación del tratamiento a la función renal del paciente.\n\nLISTADO DETECTADO:\n{sintesis}"
                except: st.error("Error en respuesta.")

with tabs[1]:
    st.markdown('<div style="text-align:center;"><div class="header-capsule">📄 Nota Evolutiva SOIP</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="linea-discreta-soip">Subjetivo (S)</div>', unsafe_allow_html=True)
    st.text_area("s_txt", st.session_state.soip_s, height=70, label_visibility="collapsed")
    st.markdown('<div class="linea-discreta-soip">Objetivo (O)</div>', unsafe_allow_html=True)
    st.text_area("o_txt", st.session_state.soip_o, height=70, label_visibility="collapsed")
    st.markdown('<div class="linea-discreta-soip">Interpretación (I)</div>', unsafe_allow_html=True)
    st.text_area("i_txt", st.session_state.soip_i, height=120, label_visibility="collapsed")
    st.markdown('<div class="linea-discreta-soip">Plan (P)</div>', unsafe_allow_html=True)
    st.text_area("p_txt", st.session_state.soip_p, height=100, label_visibility="collapsed")
    
    st.write(""); st.markdown('<div style="text-align:center;"><div class="header-capsule">📨 Solicitud de Interconsulta</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="linea-discreta-soip">Motivo de la Interconsulta</div>', unsafe_allow_html=True)
    st.text_area("ic_mot", st.session_state.ic_motivo, height=180, label_visibility="collapsed")
    st.markdown('<div class="linea-discreta-soip">Información Clínica</div>', unsafe_allow_html=True)
    st.text_area("ic_inf", st.session_state.ic_info, height=250, label_visibility="collapsed")

st.markdown(f"""<div class="warning-yellow">⚠️ <b>Esta herramienta es de apoyo a la revisión farmacoterapéutica. Verifique siempre con fuentes oficiales.</b></div>
<div style="text-align:right; font-size:0.6rem; color:#ccc; font-family:monospace; margin-top:10px;">v. 27 feb 20:32</div>""", unsafe_allow_html=True)
