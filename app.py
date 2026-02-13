import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import io
import numpy as np

# --- 1. CONFIGURACIÓN E INICIALIZACIÓN ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

if 'meds_input' not in st.session_state:
    st.session_state.meds_input = ""
if 'active_model_name' not in st.session_state:
    st.session_state.active_model_name = "1.5 Pro"
if 'reset_counter' not in st.session_state:
    st.session_state.reset_counter = 0

# --- 2. FUNCIÓN IA ---
def process_ocr():
    # Esta función se ejecuta AUTOMÁTICAMENTE al subir el archivo
    uploaded_file = st.session_state.get(f"u_{st.session_state.reset_counter}")
    if uploaded_file:
        try:
            genai.configure(api_key=st.secrets["API_KEY"])
            model = genai.GenerativeModel("gemini-1.5-pro")
            img = Image.open(uploaded_file).convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            
            response = model.generate_content([
                "Extrae nombres de fármacos y dosis. Solo texto plano.",
                {'mime_type': 'image/png', 'data': buf.getvalue()}
            ])
            # ACTUALIZACIÓN DIRECTA AL STATE
            st.session_state.meds_input = response.text
        except Exception as e:
            st.error(f"Error en OCR: {e}")

# --- 3. ESTILOS (Mantenidos intactos) ---
def inject_ui_styles():
    st.markdown(f"""
    <style>
        .model-indicator {{
            position: fixed; top: 10px; left: 10px; background-color: #000; color: #0F0;
            padding: 5px 15px; font-family: monospace; font-size: 13px; font-weight: bold;
            border-radius: 5px; z-index: 999999; border: 1px solid #333;
        }}
        .fg-glow-box {{
            background-color: #000; color: #fff; border-radius: 12px; padding: 15px;
            text-align: center; border: 2px solid #6a0dad; box-shadow: 0 0 20px #a020f0;
        }}
        .result-flash {{ padding: 20px; border-radius: 15px; margin-top: 20px; }}
        .aviso-prof {{ background-color: #fff9c4; padding: 12px; border-radius: 8px; border: 1px solid #fbc02d; font-size: 13px; text-align: center; }}
    </style>
    <div class="model-indicator">{st.session_state.active_model_name}</div>
    """, unsafe_allow_html=True)

# --- 4. LÓGICA DE VALIDACIÓN ---
def render_tab_validacion():
    col_izq, col_der = st.columns(2, gap="large")
    
    with col_izq:
        st.subheader("📋 Calculadora")
        with st.container(border=True):
            ed = st.number_input("Edad", 18, 110, 75)
            ps = st.number_input("Peso (kg)", 35, 180, 70)
            cr = st.number_input("Creatinina (mg/dL)", 0.4, 15.0, 1.1)
            sx = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
            f_sex = 0.85 if sx == "Mujer" else 1.0
            fg_calc = round((((140 - ed) * ps) / (72 * cr)) * f_sex, 1)

    with col_der:
        st.subheader("💊 Ajuste y Captura")
        fg_man = st.text_input("Introducir FG Manual", placeholder="Vacío para auto-cálculo")
        fg_final = float(fg_man.replace(",", ".")) if fg_man and fg_man.replace(",",".").replace(".","").isdigit() else fg_calc
        
        st.markdown(f'<div class="fg-glow-box"><h1>{fg_final}</h1><div style="font-size: 10px; color: #aaa;">mL/min (FG)</div></div>', unsafe_allow_html=True)

        c_file, c_paste = st.columns([0.6, 0.4])
        with c_file:
            # ON_CHANGE es la clave: ejecuta el OCR en cuanto subes el archivo
            st.file_uploader("Subir", type=['png','jpg','jpeg'], 
                             label_visibility="collapsed", 
                             key=f"u_{st.session_state.reset_counter}",
                             on_change=process_ocr) 
        with c_paste:
            try:
                from streamlit_paste_button import paste_image_button
                p = paste_image_button("📋 Pegar Recorte", key=f"p_{st.session_state.reset_counter}")
                if p and p.image_data is not None:
                    # Lógica especial para el botón de pegado
                    st.session_state.meds_input = "Procesando pegado..." # Feedback visual
                    # (Aquí se llamaría a la función de IA similar a process_ocr)
            except: pass

    st.write("---")
    # El text_area usa la variable de session_state directamente
    meds_text = st.text_area(
        "Listado de medicamentos",
        value=st.session_state.meds_input,
        height=180,
        key=f"area_{st.session_state.reset_counter}"
    )
    st.session_state.meds_input = meds_text

    c_act1, c_act2 = st.columns([0.85, 0.15])
    with c_act1:
        if st.button("🚀 VALIDAR ADECUACIÓN FARMACOLÓGICA", use_container_width=True):
            st.write("Analizando...") # Aquí iría tu lógica de validación
    with c_act2:
        if st.button("🗑️ RESET", use_container_width=True):
            st.session_state.meds_input = ""
            st.session_state.reset_counter += 1
            st.rerun()

    st.markdown('<div class="aviso-prof">⚠️ Aviso: Esta herramienta es un apoyo profesional...</div>', unsafe_allow_html=True)

def main():
    inject_ui_styles()
    st.title("ASISTENTE RENAL")
    t1, t2, t3, t4 = st.tabs(["💊 VALIDACION", "📄 INFORME", "📊 EXCEL", "📈 GRAFICOS"])
    with t1: render_tab_validacion()

if __name__ == "__main__":
    main()
