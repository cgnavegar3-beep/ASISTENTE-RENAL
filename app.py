# v. 19 feb 21:05
import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import google.generativeai as genai
import io
from streamlit_paste_button import paste_image_button

# =================================================================
# 🛡️ SECCIÓN DE BLINDAJE (PROHIBIDO MODIFICAR SIN PERMISO)
# I. ESTRUCTURA VISUAL PROTEGIDA:
#    1. Cuadros negros (ZONA y ACTIVO) - DISCRETOS SUPERIOR IZQ.
#    2. Título principal y pestañas (Tabs).
#    3. Registro de paciente: estructura y función.
#    4. Interfaz Dual (Calculadora y FG): lógica Cockcroft-Gault.
#    5. Zona de recortes (Uploader + Botón 0.65/0.35).
#    6. Cuadro de listado de medicamentos (TextArea).
#    7. Barra dual de botones (VALIDAR / RESET).
#    8. Aviso amarillo inferior.
# II. FUNCIONALIDADES CRÍTICAS:
#    1. Cascada de Modelos (2.5 Flash > 1.5 Pro).
#    2. Detección dinámica de modelos vivos.
#    3. PPIO FUNDAMENTAL: No mover ninguna línea sin autorización.
# =================================================================

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

def llamar_ia_en_cascada(prompt, imagen=None):
    disponibles = obtener_modelos_vivos()
    preferencia = ['2.5-flash', '1.5-pro', '1.5-flash']
    modelos_a_intentar = [m for m in preferencia if m in disponibles]
    for m in disponibles:
        if m not in modelos_a_intentar: modelos_a_intentar.append(m)
    
    for mod_name in modelos_a_intentar:
        try:
            st.session_state.active_model = mod_name.upper()
            model = genai.GenerativeModel(f'models/gemini-{mod_name}')
            contenido = [prompt, imagen] if imagen else [prompt]
            response = model.generate_content(contenido)
            return response.text
        except: continue
    return "⚠️ Error: Sin respuesta."

st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

def inject_ui_styles():
    style = """
    <style>
    .block-container { max-width: 100% !important; padding-top: 2.5rem !important; padding-left: 4% !important; padding-right: 4% !important; }
    
    /* CUADROS NEGROS DISCRETOS (VERSIÓN 18:55) */
    .availability-badge { 
        background-color: #1a1a1a !important; color: #888 !important; padding: 4px 10px; 
        border-radius: 3px; font-family: monospace !important; font-size: 0.65rem; 
        position: fixed; top: 15px; left: 15px; z-index: 1000000; border: 1px solid #333;
        width: 180px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;
    }
    .model-badge { 
        background-color: #000000 !important; color: #00FF00 !important; padding: 4px 10px; 
        border-radius: 3px; font-family: monospace !important; font-size: 0.75rem; 
        position: fixed; top: 15px; left: 205px; z-index: 1000000; box-shadow: 0 0 5px #00FF0033;
    }

    .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin-top: 0px; margin-bottom: 0px; }
    .version-display { text-align: center; font-size: 0.6rem; color: #bbb; font-family: monospace; margin-bottom: 15px; }
    .fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; margin-bottom: 20px; }
    
    /* SÍNTESIS CON JERARQUÍA DE COLOR Y GLOW */
    .synthesis-box { padding: 20px; border-radius: 12px; margin-bottom: 20px; text-align: left; line-height: 1.8; }
    .st-green { background-color: #f1f8e9; color: #2e7d32; border: 1px solid #a5d6a7; box-shadow: 0 0 10px #2e7d3222; }
    .st-orange { background-color: #fff3e0; color: #e65100; border: 1px solid #ffcc80; box-shadow: 0 0 10px #e6510022; }
    .st-red { background-color: #fff5f5; color: #c53030; border: 1px solid #feb2b2; box-shadow: 0 0 15px #c5303033; }

    /* DETALLE AZUL BLINDADO */
    .blue-detail-container { background-color: #f0f7ff; color: #2c5282; padding: 20px; border-radius: 10px; border: 1px solid #bee3f8; margin-top: 10px; }
    .nota-line { border-top: 1px solid #aec6cf; margin-top: 15px; padding-top: 15px; }
    
    .warning-yellow { background-color: #fdfde0; color: #856404; padding: 15px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 40px; text-align: center; font-size: 0.85rem; font-weight: 500; }
    .stButton > button { height: 48px !important; border-radius: 8px !important; }
    </style>
    """
    st.markdown(style, unsafe_allow_html=True)

if 'meds_content' not in st.session_state: st.session_state.meds_content = ""
if 'reset_all_counter' not in st.session_state: st.session_state.reset_all_counter = 0
if 'active_model' not in st.session_state: st.session_state.active_model = "ESPERANDO..."

inject_ui_styles()
st.markdown(f'<div class="availability-badge">ZONA: {" | ".join(obtener_modelos_vivos())}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="model-badge">{st.session_state.active_model}</div>', unsafe_allow_html=True)

st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="version-display">v. 19 feb 21:05</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 EXCEL", "📈 GRÁFICOS"])

with tabs[0]:
    # A) REGISTRO (Protegido)
    c_reg1, c_reg2, c_reg3 = st.columns([1, 2, 1])
    with c_reg1: centro = st.text_input("Centro", placeholder="G/M")
    with c_reg2:
        r1, r2, r3 = st.columns(3)
        edad = r1.number_input("Edad", value=None, placeholder="0")
        alfa = r2.text_input("ID Alfanumérico")
        res = r3.selectbox("¿Residencia?", ["No", "Sí"])
    with c_reg3: st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)

    # B) CALCULADORA DUAL (Protegida)
    col_izq, col_der = st.columns(2, gap="large")
    with col_izq:
        with st.container(border=True):
            calc_e = st.number_input("Edad (años)", value=edad if edad else 65)
            calc_p = st.number_input("Peso (kg)", value=70.0)
            calc_c = st.number_input("Creatinina (mg/dL)", value=1.0)
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"])
            fg = round(((140 - calc_e) * calc_p) / (72 * calc_c) * (0.85 if calc_s == "Mujer" else 1.0), 1)

    with col_der:
        fg_m = st.text_input("Ajuste Manual")
        valor_fg = fg_m if fg_m else fg
        st.markdown(f'<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{valor_fg}</div><div style="font-size: 1rem; color: #9d00ff;">mL/min</div></div>', unsafe_allow_html=True)

    st.session_state.meds_content = st.text_area("Listado de medicamentos", value=st.session_state.meds_content, height=150)

    # D) VALIDACIÓN CON NUEVA JERARQUÍA
    b_val, b_res = st.columns([0.85, 0.15])
    with b_val:
        if st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True):
            if st.session_state.meds_content:
                with st.spinner("Analizando..."):
                    prompt = f"""Experto en farmacia renal. Analiza estos fármacos para FG {valor_fg} mL/min: {st.session_state.meds_content}.
                    REGLAS RÍGIDAS:
                    1. PARTE SINTESIS: Solo fármacos que NO sean adecuados. CADA UNO EN UNA LÍNEA. Formato: [Icono ⚠️ o ⛔] [Nombre] - [Recomendación corta].
                    2. PARTE DETALLE: Empieza con 'A continuación, se detallan los ajustes de dosis para cada fármaco con este valor de FG:'.
                    3. Sin saludos."""
                    
                    resultado = llamar_ia_en_cascada(prompt)
                    
                    # Lógica de Color (Tu nueva jerarquía)
                    if "⛔" in resultado: color, msg = "st-red", "Presencia de fármacos contraindicados"
                    elif "⚠️" in resultado: color, msg = "st-orange", "Revisar adecuación / Precaución"
                    else: color, msg = "st-green", "Fármacos correctamente dosificados"

                    try:
                        partes = resultado.split("A continuación")
                        sintesis = partes[0].strip()
                        detalle = "A continuación" + partes[1] if len(partes) > 1 else resultado
                        
                        # Cuadro Síntesis
                        st.markdown(f'<div class="synthesis-box {color}"><b>SÍNTESIS:</b><br>{sintesis.replace("\n", "<br>")}<br><br><b>{msg}</b></div>', unsafe_allow_html=True)
                        
                        # Cuadro Azul Detalle
                        st.markdown(f"""
                        <div class="blue-detail-container">
                            {detalle.replace("\n", "<br>")}
                            <div class="nota-line"><b>Nota Importante:</b><br>
                            · Estas son recomendaciones generales.<br>
                            · Siempre se debe consultar la ficha técnica actualizada del medicamento y las guías clínicas locales.<br>
                            · Además del FG, se deben considerar otros factores individuales del paciente, como el peso, la edad, otras comorbilidades, la medicación concomitante y la respuesta clínica, para tomar decisiones terapéuticas.<br>
                            · Es crucial realizar un seguimiento periódico de la función renal para detectar cualquier cambio que pueda requerir ajustes futuros.
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    except: st.info(resultado)

    with b_res:
        if st.button("🗑️ RESET", use_container_width=True):
            st.session_state.meds_content = ""
            st.rerun()

st.markdown('<div class="warning-yellow">⚠️ Apoyo a la revisión farmacoterapéutica. Verifique siempre con fuentes oficiales.</div>', unsafe_allow_html=True)
