# v. 20 feb 18:45
import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai

# =================================================================
# PRINCIPIOS FUNDAMENTALES:
# 1. NUNCA BORRAR NI MODIFICAR ESTA CLÁUSULA. 
# 2. No puedes mover nada, ni cambiar ni una sola línea de la estructura 
#    visual (RIGOR Y SERIEDAD). Cero modificaciones sin autorización.
# 3. Antes de cualquier evolución técnica, explicar el "qué", "por qué" 
#    y "cómo", y esperar aprobación ("adelante" o "procede").
# #
# I. ESTRUCTURA VISUAL PROTEGIDA:
#    1. Cuadros negros superiores (ZONA y ACTIVO).
#    2. Título "ASISTENTE RENAL" y Versión inmediatamente debajo (Blindado).
#    3. Título principal y pestañas (Tabs).
#    4. Registro de paciente y función: TODO EN UNA LÍNEA (Centro, Edad, ID Alfa, 
#       Res, Fecha + Botón Borrado Registro).
#    5. Interfaz Dual (Calculadora y caja de FG (Purple Glow): lógica Cockcroft-Gault.
#       -> REFUERZO: NO SE TOCA LA CALCULADORA, NO SE TOCA EL GLOW MORADO.
#    6. Layout Medicamentos: Título y Aviso RGPD (estilo ampliado) en la misma línea.
#    7. Cuadro de listado de medicamentos (TextArea).
#    8. Barra dual de botones (VALIDAR / RESET TOTAL) y Reset de Registro.
#    9. Aviso amarillo de apoyo legal inferior.
# #
# II. FUNCIONALIDADES CRÍTICAS PROTEGIDAS:
#    1. Cascada de Modelos (2.5 Flash > 1.5 Pro > Otros).
#    2. Detección dinámica de modelos vivos en la cuenta.
#    3. Actualización de feedback neón en tiempo real (Badge ACTIVO).
# #
# III. BLINDAJE DEL BLOQUE AZUL (blue-detail-container):
#    - Prohibición de Fragmentación: Detalle y Nota en el mismo div CSS.
#    - Estilo Fijo: Fondo (#f0f7ff), borde (#bee3f8).
#    - NOTA IMPORTANTE: Texto estático (4 puntos) en negrita y azul intenso (Blindado).
# #
# IV. BLINDAJE DE SÍNTESIS DINÁMICA (Glow System):
#    - Formato Rígido: Solo se permite "Medicamentos afectados:" o "Fármacos correctamente dosificados".
#    - Prohibición Textual: No pueden aparecer las palabras "SÍNTESIS", "DETALLE" o similares.
#    - Regla de Iconos: [Icono] + [Nombre] + [Frase corta]. Prohibido texto adicional.
#    - Lógica de Color (Glow): 
#        * Sin iconos = Verde (glow-green).
#        * Con ⚠️ = Naranja (glow-orange).
#        * Con ⛔ = Rojo (glow-red).
# #
# V. PROTECCIÓN INTEGRAL PESTAÑA 1 (💊 VALIDACIÓN):
#    - Blindaje Total: Prohibida cualquier modificación en el layout, orden de columnas o funciones de la Pestaña 1.
#    - Componentes Congelados: Registro de paciente (fila única), Calculadora dual (Glow morado), Área de texto y Botonera (Validar/Reset).
#    - Lógica Funcional: El sistema de callbacks y el prompt de IA de esta pestaña no admiten cambios de sintaxis.
# =================================================================

st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

# Inicialización de estados persistentes
if "auto_soip_o" not in st.session_state: st.session_state.auto_soip_o = ""
if "auto_soip_i" not in st.session_state: st.session_state.auto_soip_i = ""
if "auto_ic_info" not in st.session_state: st.session_state.auto_ic_info = ""
if 'active_model' not in st.session_state: st.session_state.active_model = "ESPERANDO..."

def reset_registro():
    st.session_state["reg_centro"] = ""
    st.session_state["reg_edad"] = None
    st.session_state["reg_id"] = ""
    st.session_state["reg_res"] = "No"

def reset_meds():
    st.session_state["main_meds"] = ""
    st.session_state.auto_soip_o = ""
    st.session_state.auto_soip_i = ""
    st.session_state.auto_ic_info = ""

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    API_KEY = None

def obtener_modelos_vivos():
    try:
        if not API_KEY: return []
        return [m.name.replace('models/', '').replace('gemini-', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    except:
        return ["2.5-flash", "1.5-pro"]

def llamar_ia_en_cascada(prompt):
    disponibles = obtener_modelos_vivos()
    for mod_name in ['2.5-flash', '1.5-pro']:
        if mod_name in disponibles:
            try:
                st.session_state.active_model = mod_name.upper()
                model = genai.GenerativeModel(f'models/gemini-{mod_name}')
                return model.generate_content(prompt).text
            except: continue
    return "⚠️ Error: Sin respuesta."

# Inyección de Estilos Blindados y Eye-Care
st.markdown('<style>'
    '.block-container { max-width: 100% !important; padding-top: 2.5rem !important; padding-left: 4% !important; padding-right: 4% !important; }'
    '.availability-badge { background-color: #1a1a1a !important; color: #888 !important; padding: 4px 10px; border-radius: 3px; font-family: monospace; font-size: 0.65rem; position: fixed; top: 15px; left: 15px; z-index: 1000000; border: 1px solid #333; width: 180px; }'
    '.model-badge { background-color: #000000 !important; color: #00FF00 !important; padding: 4px 10px; border-radius: 3px; font-family: monospace; font-size: 0.75rem; position: fixed; top: 15px; left: 205px; z-index: 1000000; }'
    '.main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin-bottom: 0px; }'
    '.sub-version { text-align: center; font-size: 0.8rem; color: #666; margin-top: -10px; margin-bottom: 20px; }'
    '.version-display { text-align: right; font-size: 0.6rem; color: #bbb; position: fixed; bottom: 10px; right: 10px; }'
    '.fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }'
    '.synthesis-box { padding: 15px; border-radius: 12px; margin-bottom: 15px; border-width: 2px; border-style: solid; font-size: 0.95rem; }'
    '.glow-green { background-color: #f1f8e9; color: #2e7d32; border-color: #a5d6a7; box-shadow: 0 0 12px #a5d6a7; }'
    '.glow-orange { background-color: #fff3e0; color: #e65100; border-color: #ffcc80; box-shadow: 0 0 12px #ffcc80; }'
    '.glow-red { background-color: #fff5f5; color: #c53030; border-color: #feb2b2; box-shadow: 0 0 18px #feb2b2; }'
    '.blue-detail-container { background-color: #f0f7ff; color: #2c5282; padding: 20px; border-radius: 10px; border: 1px solid #bee3f8; margin-top: 10px; }'
    '.seccion-label-grande { text-align: center; font-weight: 900; color: #4a4a3a; margin: 30px 0 15px 0; font-size: 1.4rem; text-transform: uppercase; }'
    '.surco-uniforme { background: #f4f1ea; border-radius: 20px; margin-bottom: 12px; padding: 2px 18px; box-shadow: inset 5px 5px 10px #d9d5c7, inset -5px -5px 10px #ffffff; }'
    '.contenedor-informe-unificado { background: #f4f1ea; border-radius: 15px; padding: 20px; box-shadow: inset 4px 4px 8px #d9d5c7, inset -4px -4px 8px #ffffff; }'
    '.stTextArea textarea, .stTextInput input { background-color: transparent !important; border: none !important; color: #2d2d24 !important; }'
    '.warning-yellow { background-color: #fdfde0; color: #856404; padding: 15px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 40px; text-align: center; }'
'</style>', unsafe_allow_html=True)

st.markdown(f'<div class="availability-badge">ZONA: {" | ".join(obtener_modelos_vivos())}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="model-badge">{st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-version">v. 20 feb 18:45</div>', unsafe_allow_html=True)
st.markdown('<div class="version-display">v. 20 feb 18:45</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 EXCEL", "📈 GRÁFICOS"])

with tabs[0]:
    st.markdown("### Registro de Paciente")
    c1, c2, c3, c4, c5, c_del = st.columns([1, 1, 1, 1, 1, 0.4])
    with c1: centro = st.text_input("Centro", placeholder="G/M", key="reg_centro")
    with c2: edad_reg = st.number_input("Edad", value=None, key="reg_edad")
    with c3: alfa = st.text_input("ID", placeholder="ABC-123", key="reg_id")
    with c4: res = st.selectbox("¿Res?", ["No", "Sí"], key="reg_res")
    with c5: st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)
    with c_del: st.button("🗑️", on_click=reset_registro, key="cl_reg")

    id_final = f"{centro if centro else '---'}-{str(int(edad_reg)) if edad_reg else '00'}-{alfa if alfa else '---'}"
    
    col_izq, col_der = st.columns(2, gap="large")
    with col_izq:
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            calc_e = st.number_input("Edad", value=edad_reg if edad_reg else 65)
            calc_p = st.number_input("Peso", value=70.0)
            calc_c = st.number_input("Crea", value=1.0)
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"])
            fg_calc = round(((140-calc_e)*calc_p)/(72*calc_c)*(0.85 if calc_s=="Mujer" else 1.0), 1)

    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual", key="fg_manual")
        valor_fg = fg_m if fg_m else fg_calc
        st.markdown(f'<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{valor_fg}</div><div style="font-size: 1rem;">mL/min</div></div>', unsafe_allow_html=True)

    txt_meds = st.text_area("Listado Medicamentos", height=150, key="main_meds")

    if st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True):
        if txt_meds:
            with st.spinner("Consultando evidencia..."):
                p = f"Experto renal. Analiza FG {valor_fg}: {txt_meds}. REGLA ICONOS: Usa ⛔ solo para contraindicado y ⚠️ para ajuste necesario. Inicia con 'Medicamentos afectados:' o 'Fármacos correctamente dosificados'. Luego detalla tras 'A continuación, se detallan los ajustes:'"
                resp = llamar_ia_en_cascada(p)
                
                glow = "glow-red" if "⛔" in resp else ("glow-orange" if "⚠️" in resp else "glow-green")
                
                try:
                    partes = resp.split("A continuación, se detallan los ajustes")
                    sintesis = partes[0].strip()
                    
                    # Carga de datos para Informes
                    st.session_state.auto_soip_o = f"FG: {valor_fg} mL/min. ID: {id_final}."
                    st.session_state.auto_soip_i = sintesis.replace("Medicamentos afectados:", "").replace("Fármacos correctamente dosificados", "Dosis correctas").strip()
                    st.session_state.auto_ic_info = f"Revisión renal ({valor_fg} mL/min): {st.session_state.auto_soip_i}"
                    
                    st.session_state.last_resp = resp
                    st.session_state.last_glow = glow
                    st.rerun()
                except: st.error("Error al procesar respuesta.")

    if "last_resp" in st.session_state:
        partes = st.session_state.last_resp.split("A continuación, se detallan los ajustes")
        st.markdown(f'<div class="synthesis-box {st.session_state.last_glow}"><b>{partes[0].strip().replace("\n", "<br>")}</b></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="blue-detail-container">A continuación, se detallan los ajustes{partes[1].replace("\n", "<br>")}</div>', unsafe_allow_html=True)

    st.button("🗑️ RESET TOTAL", use_container_width=True, on_click=reset_meds, key="res_tot")

with tabs[1]:
    st.markdown('<p class="seccion-label-grande">NOTA SOIP</p>', unsafe_allow_html=True)
    for l, v, k in [("S", "", "S"), ("O", st.session_state.auto_soip_o, "O"), ("I", st.session_state.auto_soip_i, "I"), ("P", "", "P")]:
        st.markdown('<div class="surco-uniforme">', unsafe_allow_html=True)
        st.text_input(l, value=v, key=f"soip_{k}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<p class="seccion-label-grande">INTERCONSULTA</p>', unsafe_allow_html=True)
    ca, cb = st.columns(2)
    with ca:
        st.markdown('<div class="contenedor-informe-unificado"><p>Motivo</p>', unsafe_allow_html=True)
        st.text_area("Motivo", height=120, key="ic_mot_txt")
        st.markdown('</div>', unsafe_allow_html=True)
    with cb:
        st.markdown('<div class="contenedor-informe-unificado"><p>Información</p>', unsafe_allow_html=True)
        st.text_area("Información", value=st.session_state.auto_ic_info, height=120, key="ic_inf_txt")
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="warning-yellow">⚠️ Apoyo a la revisión farmacoterapéutica. Verifique siempre con fuentes oficiales.</div>', unsafe_allow_html=True)
