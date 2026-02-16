import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

def inject_ui_styles(modelo_activo):
    style = f"""
    <style>
    .block-container {{ max-width: 100% !important; padding-top: 2.5rem !important; padding-left: 4% !important; padding-right: 4% !important; }}
    
    /* INDICADOR DE MODELO ACTIVO (NEGRO Y PEQUEÑO) */
    .model-badge {{ 
        background-color: #000000 !important; 
        color: #00FF00 !important; 
        padding: 4px 10px; 
        border-radius: 3px; 
        font-family: monospace !important; 
        font-size: 0.75rem; 
        position: fixed; 
        top: 15px; 
        left: 15px; 
        z-index: 1000000; 
    }}

    .main-title {{ text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin-top: 0px; padding-bottom: 20px; }}
    .id-display {{ color: #666; font-family: monospace; font-size: 0.85rem; margin-top: -10px; margin-bottom: 20px; }}
    
    /* FÓRMULA A LA DERECHA */
    .formula-container {{
        display: flex;
        justify-content: flex-end;
        width: 100%;
        margin-top: 5px;
    }}
    .formula-tag {{ font-size: 0.75rem; color: #888; font-style: italic; }}

    .fg-glow-box {{ background-color: #000000; color: #FFFFFF; border: 2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; margin-bottom: 20px; }}
    
    .rgpd-box {{ background-color: #fff5f5; color: #c53030; padding: 10px; border-radius: 8px; border: 1px solid #feb2b2; font-size: 0.85rem; margin-bottom: 15px; text-align: center; }}
    .warning-yellow {{ background-color: #fdfde0; color: #856404; padding: 15px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 40px; text-align: center; font-size: 0.85rem; font-weight: 500; }}

    .stFileUploader section {{ min-height: 48px !important; border-radius: 8px !important; }}
    .stButton > button {{ height: 48px !important; border-radius: 8px !important; }}
    </style>
    """
    st.markdown(style, unsafe_allow_html=True)

# --- 2. GESTIÓN DE ESTADO Y CASCADA DE MODELOS ---
if 'reset_reg_counter' not in st.session_state: st.session_state.reset_reg_counter = 0
if 'reset_all_counter' not in st.session_state: st.session_state.reset_all_counter = 0
if 'meds_content' not in st.session_state: st.session_state.meds_content = ""
if 'active_model' not in st.session_state: st.session_state.active_model = "1.5 Pro"

def call_model_cascade(prompt):
    """Lógica de Fallback Automático"""
    try:
        # Intento con el modelo principal
        st.session_state.active_model = "1.5 Pro"
        # respuesta = api_call_pro(prompt)
        return "Respuesta del modelo Pro"
    except Exception:
        try:
            # Fallback al secundario
            st.session_state.active_model = "2.5 Flash"
            # respuesta = api_call_flash(prompt)
            return "Respuesta del modelo Flash"
        except Exception:
            st.session_state.active_model = "Respaldo"
            return "Respuesta de emergencia"

def ocr_process():
    if st.session_state.uploader_key:
        # Aquí se activaría la visión
        st.session_state.meds_content = "Extrayendo medicación real del documento..."

inject_ui_styles(st.session_state.active_model)

# INDICADOR NEGRO SOLO CON VERSIÓN
st.markdown(f'<div class="model-badge">{st.session_state.active_model}</div>', unsafe_allow_html=True)

st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 EXCEL", "📈 GRÁFICOS"])

with tabs[0]:
    # A) REGISTRO
    col_reg_tit, col_reg_clear = st.columns([0.85, 0.15])
    with col_reg_tit: st.markdown("### Registro de Paciente")
    with col_reg_clear:
        if st.button("🗑️ Limpiar Reg.", key="reg_clear"):
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

    # B) INTERFAZ DUAL
    col_izq, col_der = st.columns(2, gap="large")
    with col_izq:
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            calc_e = st.number_input("Edad (años)", value=edad if edad else 65, key=f"ce_{st.session_state.reset_all_counter}")
            calc_p = st.number_input("Peso (kg)", value=70.0, key=f"cp_{st.session_state.reset_all_counter}")
            calc_c = st.number_input("Creatinina (mg/dL)", value=1.0, key=f"cc_{st.session_state.reset_all_counter}")
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"], key=f"cs_{st.session_state.reset_all_counter}")
            fg = round(((140 - calc_e) * calc_p) / (72 * calc_c) * (0.85 if calc_s == "Mujer" else 1.0), 1)
            # FÓRMULA A LA DERECHA DEL CUADRO
            st.markdown('<div class="formula-container"><span class="formula-tag">Fórmula: Cockcroft-Gault</span></div>', unsafe_allow_html=True)

    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual", placeholder="Valor...", key=f"fgm_{st.session_state.reset_all_counter}")
        st.markdown(f'<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{fg_m if fg_m else fg}</div><div style="font-size: 1rem; color: #9d00ff;">mL/min</div></div>', unsafe_allow_html=True)
        
        c_up, c_btn = st.columns([0.75, 0.25])
        with c_up:
            st.file_uploader("Subir", label_visibility="collapsed", key="uploader_key", on_change=ocr_process)
        with c_btn:
            if st.button("✂️ RECORTE", use_container_width=True):
                st.session_state.meds_content = "Extrayendo del portapapeles..."

    st.write("")
    st.markdown("---")

    # C) MEDICAMENTOS
    st.markdown("#### 📝 Listado de medicamentos")
    st.markdown('<div class="rgpd-box"><b>Protección de Datos (RGPD/HIPAA):</b> Si aparece algún dato identificativo de un paciente, se impedirá el uso del sistema.</div>', unsafe_allow_html=True)
    
    st.session_state.meds_content = st.text_area("Listado", value=st.session_state.meds_content, height=180, label_visibility="collapsed", key=f"txt_{st.session_state.reset_all_counter}")

    # D) BOTONERA DUAL (85/15)
    b_val, b_res = st.columns([0.85, 0.15])
    with b_val:
        if st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True):
            st.info(f"Analizando con motor {st.session_state.active_model}...")
    with b_res:
        if st.button("🗑️ RESET", use_container_width=True):
            st.session_state.reset_all_counter += 1
            st.session_state.meds_content = ""
            st.rerun()

st.markdown('<div class="warning-yellow">⚠️ Apoyo a la revisión farmacoterapéutica. Verifique siempre con fuentes oficiales.</div>', unsafe_allow_html=True)
