import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

# Estilos CSS con Colores Suaves y sin cuadros agresivos
st.markdown("""
    <style>
    .header-counter { background: #000000; padding: 10px; border-radius: 5px; margin-bottom: 20px; border: 1px solid #00ff00; width: fit-content; }
    .counter-text { font-family: monospace; font-weight: bold; font-size: 0.85rem; color: #00ff00; }
    .fg-glow-purple { padding: 20px; border-radius: 15px; border: 1px solid #a020f0; box-shadow: 0 0 15px #a020f0; background: #0e1117; text-align: center; color: white; margin-top: 10px; }
    
    /* Estilos de Lista Suaves */
    .resumen-lista { padding: 15px; border-radius: 10px; margin-top: 20px; border-left: 10px solid; }
    .verde-suave { background-color: #e8f5e9; color: #2e7d32; border-color: #a5d6a7; }
    .naranja-suave { background-color: #fff3e0; color: #ef6c00; border-color: #ffcc80; }
    .rojo-suave { background-color: #ffeef0; color: #c62828; border-color: #ffcdd2; }
    
    .med-item { margin-bottom: 10px; padding: 5px 0; border-bottom: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONTADOR DISCRETO (ESQUINA SUPERIOR IZQUIERDA) ---
st.markdown('<div class="header-counter"><span class="counter-text">INTENTOS: 1500 DÍA | 15 MIN</span></div>', unsafe_allow_html=True)

# --- 3. INTERFAZ ---
col_izq, col_der = st.columns([1, 1], gap="large")

with col_izq:
    st.subheader("📋 Parámetros")
    edad = st.number_input("Edad", 18, 110, 70)
    peso = st.number_input("Peso (kg)", 35, 200, 75)
    crea = st.number_input("Creatinina", 0.4, 15.0, 1.2)
    sexo = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
    fg_calc = round((((140 - edad) * peso) / (72 * crea)) * (0.85 if sexo == "Mujer" else 1.0), 1)

with col_der:
    st.subheader("⚡ Filtrado Glomerular")
    fg_manual = st.number_input("FG Directo:", 0.0, 200.0, 0.0)
    fg_final = fg_manual if fg_manual > 0 else fg_calc
    st.markdown(f'<div class="fg-glow-purple"><h1 style="margin:0;">{fg_final} ml/min</h1><small>Cockcroft-Gault</small></div>', unsafe_allow_html=True)

st.divider()

# --- 4. ENTRADA ---
img_up = st.file_uploader("📷 Imagen/Recorte", type=['png', 'jpg', 'jpeg'])
med_input = st.text_area("Lista de medicamentos:", height=150)

# --- 5. LÓGICA CON VERSIÓN 2.5 ---
if st.button("🚀 VALIDAR SEGURIDAD RENAL", use_container_width=True):
    if "API_KEY" not in st.secrets:
        st.error("fallo de conexión")
    else:
        with st.spinner("Analizando..."):
            try:
                genai.configure(api_key=st.secrets["API_KEY"])
                # Mantenemos la versión 2.5 como pediste
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                doc = fitz.open("vademecum_renal.pdf")
                pdf_text = "".join([p.get_text() for p in doc])
                
                prompt = f"""
                Actúa como ASISTENTE RENAL. FG: {fg_final}. Vademécum: {pdf_text[:8000]}. 
                Medicamentos: {med_input}. 
                Reglas: 
                - No uses la palabra 'Informe'. 
                - Usa solo: VERDE, NARANJA o ROJO para el estado.
                - Lista solo los medicamentos afectados.
                - Formato: [Medicamento] | [Breve explicación clínica]
                """
                
                res = model.generate_content([prompt, Image.open(img_up)] if img_up else prompt).text
                
                # Determinar color suave
                clase_color = "verde-suave"
                if "ROJO" in res.upper(): clase_color = "rojo-suave"
                elif "NARANJA" in res.upper(): clase_color = "naranja-suave"
                
                # Presentación limpia sin cuadros agresivos
                st.markdown(f"""
                    <div class="resumen-lista {clase_color}">
                        <h3 style="margin-top:0;">Lista de medicamentos afectados</h3>
                        <div style="white-space: pre-wrap;">{res.replace("ROJO", "").replace("NARANJA", "").replace("VERDE", "").strip()}</div>
                    </div>
                """, unsafe_allow_html=True)
                
            except:
                st.error("fallo de conexión o superado el número de intentos")

st.info("⚠️ Aviso: Apoyo profesional. Verificar resultados.")
