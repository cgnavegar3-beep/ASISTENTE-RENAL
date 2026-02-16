import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import google.generativeai as genai
import io
# Importamos la librería para el botón de pegado real
from streamlit_paste_button import paste_image_button

# --- 0. CONFIGURACIÓN DE IA (SECRETS) ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    API_KEY = None

def obtener_modelos_disponibles():
    try:
        if not API_KEY: return ["Configurar API Key"]
        modelos = [m.name.replace('models/', '').replace('gemini-', '') 
                   for m in genai.list_models() 
                   if 'generateContent' in m.supported_generation_methods]
        return modelos if modelos else ["1.5-pro", "2.5-flash"]
    except:
        return ["1.5-pro", "2.5-pro", "2.5-flash"]

def llamar_ia_en_cascada(prompt, imagen=None):
    prioridad = ['1.5-pro', '2.5-pro', '2.5-flash', '2.0-flash-exp']
    disponibles = obtener_modelos_disponibles()
    modelos_a_intentar = [m for m in prioridad if m in disponibles]
    
    if not modelos_a_intentar: modelos_a_intentar = ['1.5-pro']

    for mod_name in modelos_a_intentar:
        try:
            st.session_state.active_model = mod_name.upper()
            model = genai.GenerativeModel(f'models/gemini-{mod_name}')
            contenido = [prompt, imagen] if imagen else [prompt]
            response = model.generate_content(contenido)
            return response.text
        except:
            continue
    return "⚠️ Error de conexión con los modelos."

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

def inject_ui_styles():
    style = """
    <style>
    .block-container { max-width: 100% !important; padding-top: 2.5rem !important; padding-left: 4% !important; padding-right: 4% !important; }
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
    .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin-top: 0px; padding-bottom: 20px; }
    .fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; margin-bottom: 20px; }
    .rgpd-box { background-color: #fff5f5; color: #c53030; padding: 10px; border-radius: 8px; border: 1px solid #feb2b2; font-size: 0.85rem; margin-bottom: 15px; text-align: center; }
    /* Estilo para que el botón de pegado se vea integrado */
    div[data-testid="stHorizontalBlock"] button { width: 100% !important; }
    </style>
    """
    st.markdown(style, unsafe_allow_html=True)

# --- 2. LÓGICA DE PROCESAMIENTO ---
if 'meds_content' not in st.session_state: st.session_state.meds_content = ""
if 'reset_all_counter' not in st.session_state: st.session_state.reset_all_counter = 0
if 'active_model' not in st.session_state: st.session_state.active_model = "ESPERANDO..."

def es_seguro_rgpd(texto):
    disparadores = ["DNI", "NIF", "NIE", "PASAPORTE", "NOMBRE:", "PACIENTE:", "FECHA NACIMIENTO"]
    for d in disparadores:
        if d in texto.upper(): return False
    return True

def analizar_y_volcar(imagen):
    """Lógica centralizada para procesar imagen y actualizar el área de texto"""
    prompt = "Actúa como un OCR médico especializado. Extrae la lista de fármacos y dosis. Si ves datos personales, inclúyelos para activar mi filtro de seguridad."
    lectura = llamar_ia_en_cascada(prompt, imagen)
    
    if not es_seguro_rgpd(lectura):
        st.session_state.meds_content = "⚠️ BLOQUEADO: Se detectaron datos personales en la captura."
    else:
        st.session_state.meds_content = lectura
    st.rerun()

inject_ui_styles()

# Indicadores superiores
modelos_str = " | ".join(obtener_modelos_disponibles())
st.markdown(f'<div class="availability-badge">ZONA: {modelos_str}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="model-badge">{st.session_state.active_model}</div>', unsafe_allow_html=True)

st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 EXCEL", "📈 GRÁFICOS"])

with tabs[0]:
    # (Sección de Registro y Calculadora omitida por brevedad, se mantiene igual que tu original)
    # ... [Tu código de Registro y Columnas de Calculadora] ...

    # B) INTERFAZ DE CAPTURA AUTOMATIZADA
    col_izq, col_der = st.columns(2, gap="large")
    
    with col_izq:
        # Mantenemos tu calculadora
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            calc_e = st.number_input("Edad (años)", value=65, key=f"ce_{st.session_state.reset_all_counter}")
            calc_p = st.number_input("Peso (kg)", value=70.0, key=f"cp_{st.session_state.reset_all_counter}")
            calc_c = st.number_input("Creatinina (mg/dL)", value=1.0, key=f"cc_{st.session_state.reset_all_counter}")
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"], key=f"cs_{st.session_state.reset_all_counter}")
            fg = round(((140 - calc_e) * calc_p) / (72 * calc_c) * (0.85 if calc_s == "Mujer" else 1.0), 1)

    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual", key=f"fgm_{st.session_state.reset_all_counter}")
        st.markdown(f'<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{fg_m if fg_m else fg}</div><div style="font-size: 1rem; color: #9d00ff;">mL/min</div></div>', unsafe_allow_html=True)
        
        c_up, c_btn = st.columns([0.65, 0.35])
        with c_up:
            # OPCIÓN 1: Pegado directo Ctrl+V en el uploader (Automático)
            archivo = st.file_uploader("Pegar recorte aquí (Ctrl+V)", label_visibility="collapsed", key="uploader_auto", type=['png', 'jpg', 'jpeg'])
            if archivo:
                # Si detecta archivo nuevo, procesa inmediatamente
                img = Image.open(archivo)
                analizar_y_volcar(img)

        with c_btn:
            # OPCIÓN 2: Botón de recorte real
            paste_result = paste_image_button(
                label="✂️ RECORTE",
                key="paste_button",
                background_color="#FFFFFF",
            )
            if paste_result.image_data is not None:
                # Si el usuario clica el botón y hay algo en el portapapeles
                img_pasted = Image.open(io.BytesIO(paste_result.image_data))
                analizar_y_volcar(img_pasted)

    st.markdown("---")
    st.markdown("#### 📝 Listado de medicamentos")
    st.markdown('<div class="rgpd-box"><b>Protección de Datos:</b> Pegue el recorte y el sistema lo procesará automáticamente.</div>', unsafe_allow_html=True)
    
    # El área de texto se llena sola
    st.session_state.meds_content = st.text_area("Listado", value=st.session_state.meds_content, height=180, label_visibility="collapsed", key=f"txt_{st.session_state.reset_all_counter}")

    # Botones finales
    b_val, b_res = st.columns([0.85, 0.15])
    with b_val:
        if st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True):
            if st.session_state.meds_content:
                with st.spinner("Validando seguridad renal..."):
                    prompt_val = f"FG: {fg_m if fg_m else fg}. Valida estos fármacos: {st.session_state.meds_content}"
                    st.info(llamar_ia_en_cascada(prompt_val))
    with b_res:
        if st.button("🗑️ RESET", use_container_width=True):
            st.session_state.reset_all_counter += 1
            st.session_state.meds_content = ""
            st.rerun()

st.markdown('<div class="warning-yellow">⚠️ Apoyo a la revisión farmacoterapéutica. Verifique siempre con fuentes oficiales.</div>', unsafe_allow_html=True)
