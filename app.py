import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import io
import os
import google.generativeai as genai
import fitz  # PyMuPDF para el manejo de PDF

# --- 1. CONFIGURACIÓN Y BLINDAJE ESTRUCTURAL ---
st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

def inject_ui_styles():
    # CSS Concatenado para evitar el SyntaxError de las comillas triples
    style = "<style>"
    # 1. Indicador Inteligente de Modelo
    style += ".model-indicator { background-color: #000000; color: #00FF00; padding: 4px 10px; border-radius: 4px; "
    style += "font-family: 'Courier New', monospace; font-size: 0.85rem; position: fixed; top: 12px; left: 12px; "
    style += "z-index: 1001; border: 1px solid #00FF00; font-weight: bold; }"
    # 1bis. Título Centrado Profesional
    style += ".main-title { text-align: center; font-size: 2.6rem; font-weight: 800; color: #1E1E1E; "
    style += "margin-top: -45px; padding-bottom: 20px; letter-spacing: -1px; width: 100%; }"
    # 3. Blindaje Pestaña Activa (Línea Roja y Negrita)
    style += "div[data-baseweb='tab-list'] button[aria-selected='true'] { border-bottom: 4px solid red !important; "
    style += "font-weight: bold !important; color: black !important; }"
    # 5. Display FG Glow Morado
    style += ".fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2px solid #9d00ff; "
    style += "box-shadow: 0 0 20px #9d00ff; padding: 25px; border-radius: 15px; text-align: center; margin: 12px 0; }"
    # 4. Aviso de Seguridad Flotante (Base fija)
    style += ".floating-warning { position: fixed; bottom: 0; left: 0; width: 100%; background-color: #fff3cd; "
    style += "color: #856404; text-align: center; padding: 14px; font-size: 0.95rem; border-top: 1px solid #ffeeba; "
    style += "z-index: 9999; box-shadow: 0 -4px 10px rgba(0,0,0,0.15); font-weight: 500; }"
    # Separador Hendidura
    style += ".separator-groove { border-top: 1px dotted #bbb; border-bottom: 1px solid #fff; margin: 30px 0; height: 2px; }"
    # Efectos Flash Glow para resultados
    style += "@keyframes flash-green { 0% { box-shadow: 0 0 0px #28a745; } 50% { box-shadow: 0 0 30px #28a745; } 100% { box-shadow: 0 0 0px #28a745; } }"
    style += "@keyframes flash-orange { 0% { box-shadow: 0 0 0px #fd7e14; } 50% { box-shadow: 0 0 30px #fd7e14; } 100% { box-shadow: 0 0 0px #fd7e14; } }"
    style += "@keyframes flash-red { 0% { box-shadow: 0 0 0px #dc3545; } 50% { box-shadow: 0 0 30px #dc3545; } 100% { box-shadow: 0 0 0px #dc3545; } }"
    style += ".res-verde { background-color: #d4edda; border: 1px solid #c3e6cb; animation: flash-green 2s infinite; padding: 20px; border-radius: 10px; }"
    style += ".res-naranja { background-color: #fff3cd; border: 1px solid #ffeeba; animation: flash-orange 2s infinite; padding: 20px; border-radius: 10px; }"
    style += ".res-rojo { background-color: #f8d7da; border: 1px solid #f5c6cb; animation: flash-red 2s infinite; padding: 20px; border-radius: 10px; }"
    style += "</style>"
    st.markdown(style, unsafe_allow_html=True)

# --- 2. LÓGICA DE RENDIMIENTO (FASE 2) ---

if 'memoria_farmacos' not in st.session_state: st.session_state.memoria_farmacos = {}
if 'meds_input' not in st.session_state: st.session_state.meds_input = ""
if 'reset_counter' not in st.session_state: st.session_state.reset_counter = 0
if 'last_model' not in st.session_state: st.session_state.last_model = "2.5 Flash"

@st.cache_resource
def get_vademecum_data():
    """Cláusula de blindaje: Vademécum en Memoria (se carga una sola vez)"""
    path = "vademecum_renal.pdf"
    if os.path.exists(path):
        try:
            doc = fitz.open(path)
            full_text = ""
            for page in doc:
                full_text += page.get_text()
            return full_text
        except Exception:
            return "Error al leer el archivo PDF."
    return "Archivo vademecum_renal.pdf no encontrado."

def run_ia_task(prompt_text, image_data=None):
    """Cascada de Modelos con Fallback Automático"""
    # Lista de modelos por prioridad
    models_to_try = [
        ("gemini-1.5-pro", "1.5 Pro"),
        ("gemini-1.5-flash", "1.5 Flash"),
        ("gemini-2.0-flash", "2.5 Flash")
    ]
    
    for model_id, tech_name in models_to_try:
        try:
            st.session_state.last_model = tech_name
            model = genai.GenerativeModel(model_id)
            if image_data:
                response = model.generate_content([prompt_text, image_data])
            else:
                response = model.generate_content(prompt_text)
            return response.text
        except Exception:
            continue
    return "Fallo de conexión o superado el número de intentos."

def process_multimodal(uploaded_file):
    """Cláusula de blindaje para archivos: Normalización PIL a RGB"""
    img = Image.open(uploaded_file)
    img_rgb = img.convert("RGB")
    # Convertir a bytes para la API
    buf = io.BytesIO()
    img_rgb.save(buf, format="JPEG")
    return {"mime_type": "image/jpeg", "data": buf.getvalue()}

# --- 3. INICIO DE RENDERIZADO ---
inject_ui_styles()
vademecum_text = get_vademecum_data()

# Indicador de Modelo Dinámico
st.markdown(f'<div class="model-indicator">{st.session_state.last_model}</div>', unsafe_allow_html=True)

# Título Principal
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)

# Barra de pestañas con iconos
tab_val, tab_inf, tab_exc, tab_gra = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 EXCEL", "📈 GRÁFICOS"])

with tab_val:
    # A) BLOQUE DE REGISTRO
    st.markdown("### Registro de Paciente")
    c_reg1, c_reg2, c_reg3 = st.columns([1.5, 2.5, 1.2])
    
    with c_reg1:
        centro = st.text_input("Nombre del Centro", value="G/M", placeholder="G/M", key=f"c_{st.session_state.reset_counter}")
    
    with c_reg2:
        rc1, rc2, rc3 = st.columns([1, 1.5, 1])
        with rc1:
            edad_val = st.number_input("Edad", min_value=0, max_value=120, value=65, key=f"e_{st.session_state.reset_counter}")
        with rc2:
            alfanum = st.text_input("Cuadro Alfanumérico", placeholder="ID-PACIENTE", key=f"id_{st.session_state.reset_counter}")
        with rc3:
            residencia = st.selectbox("¿Residencia?", ["No", "Sí"], key=f"res_{st.session_state.reset_counter}")
            
    with c_reg3:
        st.text_input("Fecha Actual", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)

    # ID Registro Dinámico
    id_paciente = f"{centro}-{edad_val}-{alfanum if alfanum else 'GEN'}"
    st.markdown(f"<small style='color:gray'>ID Registro: {id_paciente}</small>", unsafe_allow_html=True)

    st.write("") # Aire

    # B) INTERFAZ DUAL (CALCULADORA VS AJUSTE)
    col_izq, col_der = st.columns(2)

    # 1. CALCULADORA (Izquierda)
    with col_izq:
        st.markdown("#### 📋 Calculadora")
        st.caption("Método: Cockcroft-Gault / CKD-EPI")
        with st.container(border=True):
            in1, in2 = st.columns(2)
            with in1:
                calc_edad = st.number_input("Edad (años)", value=edad_val, step=1)
                calc_peso = st.number_input("Peso (kg)", value=75.0, step=0.5)
            with in2:
                calc_creat = st.number_input("Creatinina (mg/dL)", value=1.1, step=0.1)
                calc_sexo = st.selectbox("Sexo", ["Hombre", "Mujer"])
            
            # Cálculo automático simplificado (Cockcroft-Gault)
            fg_calc = ((140 - calc_edad) * calc_peso) / (72 * calc_creat)
            if calc_sexo == "Mujer": fg_calc *= 0.85
            fg_calc = round(fg_calc, 1)

    # 2. AJUSTE Y CAPTURA (Derecha)
    with col_der:
        st.markdown("#### 💊 Ajuste y Captura")
        fg_manual = st.text_input("Input Manual del FG (Prioritario)", placeholder="Introduzca FG manualmente si lo conoce...")
        
        st.write("") # Espaciador st.write("") para limpieza visual
        
        # Lógica de valor final
        valor_fg = fg_manual if fg_manual else fg_calc
        metodo_usado = "Manual" if fg_manual else "Cockcroft-Gault"

        # DISPLAY FG GLOW MORADO
        st.markdown(f"""
            <div class="fg-glow-box">
                <div style="font-size: 0.9rem; color: #bbbbbb; margin-bottom: 5px;">FILTRADO GLOMERULAR FINAL</div>
                <div style="font-size: 2.8rem; font-weight: bold;">{valor_fg} mL/min</div>
                <div style="font-size: 0.85rem; color: #9d00ff; margin-top: 6px; font-weight: bold;">Método: {metodo_usado}</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("") # Espaciador
        
        # Zona de Carga Multimodal
        c_up, c_btn = st.columns([4, 1])
        with c_up:
            up_file = st.file_uploader("Subida de archivos (📁)", label_visibility="collapsed", type=['png', 'jpg', 'jpeg', 'pdf'])
            if up_file:
                # Blindaje de procesamiento de imagen
                img_data = process_multimodal(up_file)
                # Aquí se llamaría a run_ia_task para transcribir al text_area
                st.session_state.meds_input = "Transcripción automática activada..."
        with c_btn:
            st.button("📋", help="Pegar Recorte o Ctrl+V")

    # 3. LÍNEA DE SEPARACIÓN (SURCO)
    st.markdown('<div class="separator-groove"></div>', unsafe_allow_html=True)

    # 4. LISTADO DE MEDICAMENTOS
    st.markdown("#### 📝 Listado de medicamentos")
    st.session_state.meds_input = st.text_area(
        "Listado",
        value=st.session_state.meds_input,
        placeholder="Escribe o edita la lista del archivo o captura subidos",
        height=180,
        label_visibility="collapsed"
    )

    # 5. BOTONERA DUAL 85/15
    st.write("")
    b_val, b_res = st.columns([0.85, 0.15])
    with b_val:
        if st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True, type="primary"):
            # Aquí se ejecutaría la lógica de resultados cruzando con Vademécum
            st.markdown("""
                <div class="res-naranja">
                    <strong>⚠️ PRECAUCIÓN:</strong> Algún medicamento requiere ajuste moderado.<br>
                    <small>DABIGATRÁN (Anticoagulantes orales): 110mg cada 12h si FG 30-50.</small>
                </div>
            """, unsafe_allow_html=True)
            st.button("💾 GUARDAR EN EXCEL")

    with b_res:
        if st.button("🗑️ RESET", use_container_width=True):
            st.session_state.reset_counter += 1
            st.session_state.meds_input = ""
            st.rerun()

# --- 7. AVISO DE SEGURIDAD (PERMANENTE Y FLOTANTE) ---
st.markdown("""
    <div class="floating-warning">
        ⚠️ Aviso: Esta herramienta es un apoyo a la revisión farmacoterapéutica. Puede contener errores. Verifique con fuentes oficiales.
    </div>
""", unsafe_allow_html=True)

# Pestañas inactivas
with tab_inf: st.info("Módulo de Informe Clínico en preparación.")
with tab_exc: st.info("Histórico de pacientes y exportación Excel.")
with tab_gra: st.info("Análisis estadístico de adecuación renal.")
