import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import google.generativeai as genai
import io
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
        return ["2.5-pro", "2.5-flash", "1.5-pro"]

def llamar_ia_en_cascada(prompt, imagen=None):
    prioridad = ['2.5-pro', '2.5-flash', '1.5-pro', '1.5-flash']
    disponibles = obtener_modelos_disponibles()
    modelos_a_intentar = [m for m in prioridad if m in disponibles]
    
    for mod_name in modelos_a_intentar:
        try:
            st.session_state.active_model = mod_name.upper()
            model = genai.GenerativeModel(f'models/gemini-{mod_name}')
            contenido = [prompt, imagen] if imagen else [prompt]
            response = model.generate_content(contenido)
            return response.text
        except:
            continue
    return "⚠️ Error: Los modelos están saturados."

# --- 1. ESTILOS ---
st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

def inject_ui_styles():
    st.markdown("""
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
    .fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .rgpd-box { background-color: #fff5f5; color: #c53030; padding: 10px; border-radius: 8px; border: 1px solid #feb2b2; font-size: 0.85rem; margin-top: 15px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LÓGICA DE ESTADO ---
if 'meds_content' not in st.session_state: st.session_state.meds_content = ""
if 'active_model' not in st.session_state: st.session_state.active_model = "ESPERANDO..."
if 'last_processed_id' not in st.session_state: st.session_state.last_processed_id = None
if 'reset_counter' not in st.session_state: st.session_state.reset_counter = 0

def analizar_y_volcar(imagen):
    prompt = "Extrae lista de fármacos y dosis de esta imagen médica. Responde solo con la lista."
    lectura = llamar_ia_en_cascada(prompt, imagen)
    
    disparadores = ["DNI", "NIF", "NIE", "PACIENTE", "NOMBRE:"]
    if any(d in lectura.upper() for d in disparadores):
        st.session_state.meds_content = "⚠️ BLOQUEADO: Datos personales detectados."
    else:
        st.session_state.meds_content = lectura

inject_ui_styles()

# Indicadores
modelos_disponibles = obtener_modelos_disponibles()
st.markdown(f'<div class="availability-badge">ZONA: {" | ".join(modelos_disponibles)}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="model-badge">{st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 EXCEL", "📈 GRÁFICOS"])

with tabs[0]:
    col_izq, col_der = st.columns(2, gap="large")
    with col_izq:
        st.markdown("#### 📋 Datos Paciente")
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(1)
            edad = c1.number_input("Edad", 18, 110, 65, key=f"ed_{st.session_state.reset_counter}")
            peso = c2.number_input("Peso (kg)", 30.0, 200.0, 70.0, key=f"pe_{st.session_state.reset_counter}")
            crea = st.number_input("Creatinina (mg/dL)", 0.1, 15.0, 1.0, key=f"cr_{st.session_state.reset_counter}")
            sexo = st.selectbox("Sexo", ["Hombre", "Mujer"], key=f"sx_{st.session_state.reset_counter}")
            fg = round(((140 - edad) * peso) / (72 * crea) * (0.85 if sexo == "Mujer" else 1.0), 1)

    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual", placeholder="Valor...", key=f"fgm_{st.session_state.reset_counter}")
        valor_fg = fg_m if fg_m else fg
        st.markdown(f'<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{valor_fg}</div><div style="font-size: 1rem; color: #9d00ff;">mL/min</div></div>', unsafe_allow_html=True)
        
        c_up, c_btn = st.columns([0.65, 0.35])
        with c_up:
            archivo = st.file_uploader("Subir/Pegar", label_visibility="collapsed", type=['png', 'jpg', 'jpeg'], key=f"up_{st.session_state.reset_counter}")
            if archivo and st.session_state.last_processed_id != archivo.name:
                analizar_y_volcar(Image.open(archivo))
                st.session_state.last_processed_id = archivo.name
                st.rerun()
        
        with c_btn:
            pasted = paste_image_button(label="✂️ RECORTE", key=f"paste_{st.session_state.reset_counter}")
            if pasted.image_data is not None:
                # CORRECCIÓN AQUÍ: Convertimos a bytes antes de hacer el hash
                p_id = hash(bytes(pasted.image_data))
                if st.session_state.last_processed_id != p_id:
                    img_p = Image.open(io.BytesIO(pasted.image_data))
                    analizar_y_volcar(img_p)
                    st.session_state.last_processed_id = p_id
                    st.rerun()

    st.markdown('<div class="rgpd-box"><b>Protección de Datos:</b> No use imágenes con nombres reales.</div>', unsafe_allow_html=True)
    
    st.session_state.meds_content = st.text_area("Listado de fármacos", value=st.session_state.meds_content, height=150, key=f"ta_{st.session_state.reset_counter}")
    
    b_val, b_res = st.columns([0.8, 0.2])
    with b_val:
        if st.button("🚀 VALIDAR ADECUACIÓN RENAL", use_container_width=True):
            if st.session_state.meds_content:
                with st.spinner("Analizando..."):
                    p_med = f"FG: {valor_fg} mL/min. Valida estos fármacos y dosis: {st.session_state.meds_content}."
                    st.info(llamar_ia_en_cascada(p_med))
    with b_res:
        if st.button("🗑️ RESET", use_container_width=True):
            st.session_state.meds_content = ""
            st.session_state.last_processed_id = None
            st.session_state.reset_counter += 1
            st.rerun()
