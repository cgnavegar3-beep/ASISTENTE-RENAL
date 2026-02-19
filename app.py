# v. 19 feb 19:35
import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import google.generativeai as genai
import io

# =================================================================
# 🛡️ SECCIÓN DE BLINDAJE (PROHIBIDO MODIFICAR SIN PERMISO)
# =================================================================
# PRINCIPIOS FUNDAMENTALES:
# 1. NUNCA BORRAR ESTA CLÁUSULA DE ESTE CÓDIGO.
# 2. No puedes mover nada, ni cambiar ni una sola línea de la estructura 
#    visual (RIGOR Y SERIEDAD). Cero modificaciones sin autorización.
# 3. Antes de cualquier evolución técnica, explicar el "qué", "por qué" 
#    y "cómo", y esperar aprobación ("adelante" o "procede").
# 4. NO CAMBIAR EL NOMBRE "ASISTENTE RENAL". 
# 5. SIEMPRE MOSTRAR VERSIÓN CON ÚLTIMA FECHA DEBAJO DEL NOMBRE.
#
# I. ESTRUCTURA VISUAL PROTEGIDA:
#    1. Cuadros negros (ZONA y ACTIVO).
#    2. Título principal y pestañas (Tabs).
#    3. Registro de paciente: estructura y función.
#    4. Interfaz Dual (Calculadora y FG): lógica Cockcroft-Gault.
#       -> REFUERZO: NO SE TOCA LA CALCULADORA, NO SE TOCA EL GLOW MORADO.
#    5. Zona de recortes (Uploader + Botón 0.65/0.35).
#    6. Cuadro de listado de medicamentos (TextArea).
#    7. Barra dual de botones (VALIDAR / RESET).
#    8. Aviso amarillo inferior.
#
# II. FUNCIONALIDADES CRÍTICAS PROTEGIDAS:
#    1. Cascada de Modelos (2.5 Flash > 1.5 Pro > Otros).
#    2. Detección dinámica de modelos vivos en la cuenta.
#    3. Actualización de feedback neón en tiempo real (Badge ACTIVO).
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
        except:
            continue
    return "⚠️ Error: Sin respuesta de modelos."

# --- 1. CONFIGURACIÓN Y ESTILOS (BLINDADO) ---
st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

def inject_ui_styles():
    style = """
    <style>
    .block-container { max-width: 100% !important; padding-top: 2.5rem !important; padding-left: 4% !important; padding-right: 4% !important; }
    .availability-badge { background-color: #1a1a1a !important; color: #888 !important; padding: 4px 10px; border-radius: 3px; font-family: monospace !important; font-size: 0.65rem; position: fixed; top: 15px; left: 15px; z-index: 1000000; border: 1px solid #333; width: 180px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
    .model-badge { background-color: #000000 !important; color: #00FF00 !important; padding: 4px 10px; border-radius: 3px; font-family: monospace !important; font-size: 0.75rem; position: fixed; top: 15px; left: 205px; z-index: 1000000; box-shadow: 0 0 5px #00FF0033; }
    .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin-top: 0px; margin-bottom: 0px; }
    .version-display { text-align: center; font-size: 0.6rem; color: #bbb; font-family: monospace; margin-bottom: 15px; }
    .id-display { color: #666; font-family: monospace; font-size: 0.85rem; margin-top: -10px; margin-bottom: 20px; }
    .fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; margin-bottom: 20px; }
    
    .synthesis-box { padding: 15px; border-radius: 10px; margin-bottom: 15px; min-height: 100px; color: white; font-weight: 500; border: 2px solid transparent; }
    .status-green { background-color: #064e3b; border-color: #10b981; box-shadow: 0 0 15px #10b981; animation: pulse-green 2s infinite; }
    .status-orange { background-color: #7c2d12; border-color: #f97316; box-shadow: 0 0 15px #f97316; }
    .status-red { background-color: #7f1d1d; border-color: #ef4444; box-shadow: 0 0 15px #ef4444; }
    
    @keyframes pulse-green { 0% { box-shadow: 0 0 5px #10b981; } 50% { box-shadow: 0 0 20px #10b981; } 100% { box-shadow: 0 0 5px #10b981; } }

    .rgpd-box { background-color: #fff5f5; color: #c53030; padding: 10px; border-radius: 8px; border: 1px solid #feb2b2; font-size: 0.85rem; margin-bottom: 15px; text-align: center; }
    .warning-yellow { background-color: #fdfde0; color: #856404; padding: 15px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 40px; text-align: center; font-size: 0.85rem; font-weight: 500; }
    .stButton > button { height: 48px !important; border-radius: 8px !important; }
    </style>
    """
    st.markdown(style, unsafe_allow_html=True)

if 'meds_content' not in st.session_state: st.session_state.meds_content = ""
if 'reset_reg_counter' not in st.session_state: st.session_state.reset_reg_counter = 0
if 'reset_all_counter' not in st.session_state: st.session_state.reset_all_counter = 0
if 'active_model' not in st.session_state: st.session_state.active_model = "ESPERANDO..."

inject_ui_styles()
vivos = obtener_modelos_vivos()
st.markdown(f'<div class="availability-badge">ZONA: {" | ".join(vivos) if vivos else "Buscando..."}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="model-badge">{st.session_state.active_model}</div>', unsafe_allow_html=True)

st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="version-display">v. 19 feb 19:35</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 EXCEL", "📈 GRÁFICOS"])

with tabs[0]:
    # A) REGISTRO
    col_reg_tit, col_reg_clear = st.columns([0.85, 0.15])
    with col_reg_tit: st.markdown("### Registro de Paciente")
    with col_reg_clear:
        if st.button("🗑️ Limpiar Reg.", key="clr_reg"):
            st.session_state.reset_reg_counter += 1
            st.rerun()

    c_reg1, c_reg2, c_reg3 = st.columns([1, 2, 1])
    with c_reg1: centro = st.text_input("Centro", placeholder="G/M", key=f"c_{st.session_state.reset_reg_counter}")
    with c_reg2:
        r1, r2, r3 = st.columns(3)
        edad = r1.number_input("Edad", value=None, placeholder="0", key=f"e_{st.session_state.reset_reg_counter}")
        alfa = r2.text_input("ID Alfanumérico", placeholder="Escriba...", key=f"id_{st.session_state.reset_reg_counter}")
        res = r3.selectbox("¿Residencia?", ["No", "Sí"], key=f"res_{st.session_state.reset_reg_counter}")
    with c_reg3: st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)

    id_final = f"{centro if centro else '---'}-{str(int(edad)) if edad else '00'}-{alfa if alfa else '---'}"
    st.markdown(f'<div class="id-display">ID Registro: {id_final}</div>', unsafe_allow_html=True)

    # B) CALCULADORA E INTERFAZ DUAL
    col_izq, col_der = st.columns(2, gap="large")
    with col_izq:
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            calc_e = st.number_input("Edad (años)", value=edad if edad else 65, key=f"ce_{st.session_state.reset_all_counter}")
            calc_p = st.number_input("Peso (kg)", value=70.0, key=f"cp_{st.session_state.reset_all_counter}")
            calc_c = st.number_input("Creatinina (mg/dL)", value=1.0, key=f"cc_{st.session_state.reset_all_counter}")
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"], key=f"cs_{st.session_state.reset_all_counter}")
            fg = round(((140 - calc_e) * calc_p) / (72 * calc_c) * (0.85 if calc_s == "Mujer" else 1.0), 1)
            st.markdown('<div style="text-align:right; font-size:0.75rem; color:#888;"><i>Fórmula: Cockcroft-Gault</i></div>', unsafe_allow_html=True)

    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual", placeholder="Valor...", key=f"fgm_{st.session_state.reset_all_counter}")
        valor_fg = fg_m if fg_m else fg
        st.markdown(f'<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{valor_fg}</div><div style="font-size: 1rem; color: #9d00ff;">mL/min</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 📝 Listado de medicamentos")
    st.markdown('<div class="rgpd-box"><b>Protección de Datos:</b> No procese datos personales identificables.</div>', unsafe_allow_html=True)
    st.session_state.meds_content = st.text_area("Listado", value=st.session_state.meds_content, height=150, label_visibility="collapsed", key=f"txt_{st.session_state.reset_all_counter}")

    b_val, b_res = st.columns([0.85, 0.15])
    with b_val:
        if st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True):
            if st.session_state.meds_content:
                with st.spinner("Analizando fármacos..."):
                    prompt = f"""Actúa como experto en farmacia clínica renal. Analiza estos medicamentos para un FG de {valor_fg} mL/min: {st.session_state.meds_content}.
                    RESPUESTA DIVIDIDA EN DOS PARTES:
                    1. SINTESIS: Lista corta de fármacos afectados y su riesgo (Contraindicado, Ajuste dosis o Precaución).
                    2. EXPLICACIÓN: Detalle científico de cada uno, incluyendo la 'Nota Importante' obligatoria al final."""
                    resultado = llamar_ia_en_cascada(prompt)
                    clase_color = "status-green"
                    if "CONTRAINDICADO" in resultado.upper(): clase_color = "status-red"
