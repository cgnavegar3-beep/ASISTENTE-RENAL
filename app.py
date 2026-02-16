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
    """Detecta modelos en tu zona"""
    try:
        if not API_KEY: return ["Configurar API Key"]
        modelos = [m.name.replace('models/', '').replace('gemini-', '') 
                   for m in genai.list_models() 
                   if 'generateContent' in m.supported_generation_methods]
        return modelos if modelos else ["1.5-pro", "2.5-flash"]
    except:
        return ["1.5-pro", "2.5-flash", "2.5-pro"]

def llamar_ia_en_cascada(prompt, imagen=None):
    """Cascada inteligente: Pro -> Flash -> Fallback"""
    prioridad = ['1.5-pro', '2.5-flash', '2.5-pro', '1.5-flash']
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
    return "⚠️ Error: Modelos no disponibles."

# --- 1. CONFIGURACIÓN Y ESTILOS (TU INTERFAZ INTACTA) ---
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
    .id-display { color: #666; font-family: monospace; font-size: 0.85rem; margin-top: -10px; margin-bottom: 20px; }
    .formula-container { display: flex; justify-content: flex-end; width: 100%; margin-top: 5px; }
    .formula-tag { font-size: 0.75rem; color: #888; font-style: italic; }
    .fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; margin-bottom: 20px; }
    .rgpd-box { background-color: #fff5f5; color: #c53030; padding: 10px; border-radius: 8px; border: 1px solid #feb2b2; font-size: 0.85rem; margin-bottom: 15px; text-align: center; }
    .warning-yellow { background-color: #fdfde0; color: #856404; padding: 15px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 40px; text-align: center; font-size: 0.85rem; font-weight: 500; }
    .stFileUploader section { min-height: 48px !important; border-radius: 8px !important; }
    .stButton > button { height: 48px !important; border-radius: 8px !important; }
    </style>
    """
    st.markdown(style, unsafe_allow_html=True)

# --- 2. LÓGICA DE PROCESAMIENTO ---
if 'meds_content' not in st.session_state: st.session_state.meds_content = ""
if 'reset_reg_counter' not in st.session_state: st.session_state.reset_reg_counter = 0
if 'reset_all_counter' not in st.session_state: st.session_state.reset_all_counter = 0
if 'active_model' not in st.session_state: st.session_state.active_model = "ESPERANDO..."
if 'last_proc_id' not in st.session_state: st.session_state.last_proc_id = None

def es_seguro_rgpd(texto):
    disparadores = ["DNI", "NIF", "NIE", "PASAPORTE", "NOMBRE:", "PACIENTE:", "FECHA NACIMIENTO"]
    return not any(d in texto.upper() for d in disparadores)

def analizar_y_volcar(imagen):
    prompt = "Extrae lista de fármacos y dosis de esta imagen médica. Si ves datos personales, inclúyelos para el filtro."
    lectura = llamar_ia_en_cascada(prompt, imagen)
    if not es_seguro_rgpd(lectura):
        st.session_state.meds_content = "⚠️ BLOQUEO POR DATOS PERSONALES DETECTADOS"
    else:
        st.session_state.meds_content = lectura

inject_ui_styles()

# Indicadores de Neón
modelos_disponibles = obtener_modelos_disponibles()
st.markdown(f'<div class="availability-badge">ZONA: {" | ".join(modelos_disponibles)}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="model-badge">{st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)

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
    with c_reg1: 
        centro = st.text_input("Centro", placeholder="G/M", key=f"c_{st.session_state.reset_reg_counter}")
    with c_reg2:
        r1, r2, r3 = st.columns(3)
        edad = r1.number_input("Edad", value=None, placeholder="0", key=f"e_{st.session_state.reset_reg_counter}")
        alfa = r2.text_input("ID Alfanumérico", placeholder="Escriba...", key=f"id_{st.session_state.reset_reg_counter}")
        res = r3.selectbox("¿Residencia?", ["No", "Sí"], key=f"res_{st.session_state.reset_reg_counter}")
    with c_reg3: st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)

    id_final = f"{centro if centro else '---'}-{str(int(edad)) if edad else '00'}-{alfa if alfa else '---'}"
    st.markdown(f'<div class="id-display">ID Registro: {id_final}</div>', unsafe_allow_html=True)

    # B) CALCULADORA E INTERFAZ DUAL (AUTODETECTOR)
    col_izq, col_der = st.columns(2, gap="large")
    with col_izq:
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            calc_e = st.number_input("Edad (años)", value=edad if edad else 65, key=f"ce_{st.session_state.reset_all_counter}")
            calc_p = st.number_input("Peso (kg)", value=70.0, key=f"cp_{st.session_state.reset_all_counter}")
            calc_c = st.number_input("Creatinina (mg/dL)", value=1.0, key=f"cc_{st.session_state.reset_all_counter}")
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"], key=f"cs_{st.session_state.reset_all_counter}")
            fg = round(((140 - calc_e) * calc_p) / (72 * calc_c) * (0.85 if calc_s == "Mujer" else 1.0), 1)
            st.markdown('<div class="formula-container"><span class="formula-tag">Fórmula: Cockcroft-Gault</span></div>', unsafe_allow_html=True)

    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual", placeholder="Valor...", key=f"fgm_{st.session_state.reset_all_counter}")
        valor_fg = fg_m if fg_m else fg
        st.markdown(f'<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{valor_fg}</div><div style="font-size: 1rem; color: #9d00ff;">mL/min</div></div>', unsafe_allow_html=True)
        
        c_up, c_btn = st.columns([0.65, 0.35])
        with c_up:
            archivo = st.file_uploader("Subir", label_visibility="collapsed", key=f"up_{st.session_state.reset_all_counter}", type=['png', 'jpg', 'jpeg'])
            if archivo and st.session_state.last_proc_id != archivo.name:
                analizar_y_volcar(Image.open(archivo))
                st.session_state.last_proc_id = archivo.name
                st.rerun()
        with c_btn:
            pasted = paste_image_button(label="✂️ RECORTE", key=f"p_btn_{st.session_state.reset_all_counter}")
            if pasted.image_data is not None:
                # CORRECCIÓN DEL ERROR HASH (MemoryView a Bytes)
                p_id = hash(bytes(pasted.image_data))
                if st.session_state.last_proc_id != p_id:
                    analizar_y_volcar(Image.open(io.BytesIO(pasted.image_data)))
                    st.session_state.last_proc_id = p_id
                    st.rerun()

    st.write("")
    st.markdown("---")

    # C) MEDICAMENTOS
    st.markdown("#### 📝 Listado de medicamentos")
    st.markdown('<div class="rgpd-box"><b>Protección de Datos:</b> No use imágenes con datos personales.</div>', unsafe_allow_html=True)
    
    st.session_state.meds_content = st.text_area("Listado", value=st.session_state.meds_content, height=180, label_visibility="collapsed", key=f"txt_{st.session_state.reset_all_counter}")

    # D) BOTONERA DUAL
    b_val, b_res = st.columns([0.85, 0.15])
    with b_val:
        if st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True):
            if st.session_state.meds_content:
                with st.spinner("Analizando tratamiento..."):
                    p_val = f"FG: {valor_fg}. Valida estos fármacos: {st.session_state.meds_content}"
                    st.info(llamar_ia_en_cascada(p_val))
    with b_res:
        if st.button("🗑️ RESET", use_container_width=True):
            st.session_state.reset_all_counter += 1
            st.session_state.meds_content = ""
            st.session_state.last_proc_id = None
            st.rerun()

st.markdown('<div class="warning-yellow">⚠️ Apoyo a la revisión farmacoterapéutica. Verifique siempre con fuentes oficiales.</div>', unsafe_allow_html=True)
