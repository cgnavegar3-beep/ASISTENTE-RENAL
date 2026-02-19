# v. 19 feb 21:00 (Restaurado y Blindado)
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
# 1. NUNCA BORRAR ESTA CLÁUSULA. 
# 2. No mover ni cambiar la estructura visual (RIGOR Y SERIEDAD).
# 3. Antes de evolucionar, explicar "qué", "por qué" y "cómo" (aprobación "adelante").
# 4. NOMBRE: "ASISTENTE RENAL" con fecha debajo.
# 
# I. ESTRUCTURA VISUAL PROTEGIDA:
#    - Cuadros negros (ZONA/ACTIVO), Título, Pestañas.
#    - Registro, Calculadora Dual (Cockcroft-Gault), Glow Morado.
#    - Uploader, TextArea de Medicación, Botones VALIDAR/RESET.
#
# II. BLINDAJE BLOQUE AZUL:
#    - Clase 'blue-detail-container' intocable.
#    - Nota Importante LITERAL (4 puntos con viñetas).
#    - Unificación total bajo el mismo sombreado azul.
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
    st.markdown("""
    <style>
    .block-container { max-width: 100% !important; padding-top: 2.5rem !important; padding-left: 4% !important; padding-right: 4% !important; }
    
    /* CUADROS NEGROS SUPERIORES (ZONA / ACTIVO) */
    .availability-badge { background-color: #1a1a1a !important; color: #888 !important; padding: 4px 10px; border-radius: 3px; font-family: monospace; font-size: 0.65rem; position: fixed; top: 15px; left: 15px; z-index: 1000; border: 1px solid #333; }
    .model-badge { background-color: #000 !important; color: #0f0 !important; padding: 4px 10px; border-radius: 3px; font-family: monospace; font-size: 0.75rem; position: fixed; top: 15px; left: 205px; z-index: 1000; box-shadow: 0 0 5px #0f03; border: 1px solid #333; }
    
    .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; }
    .version-display { text-align: center; font-size: 0.6rem; color: #bbb; margin-bottom: 15px; }
    .fg-glow-box { background-color: #000; color: #fff; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; margin-bottom: 20px; }
    
    /* SÍNTESIS CON GLOW SUAVE */
    .synthesis-box { padding: 20px; border-radius: 12px; margin-bottom: 20px; text-align: left; line-height: 1.8; }
    .st-green { background-color: #f1f8e9; color: #2e7d32; border: 1px solid #a5d6a7; box-shadow: 0 0 10px #2e7d3233; }
    .st-orange { background-color: #fff3e0; color: #e65100; border: 1px solid #ffcc80; box-shadow: 0 0 10px #e6510033; }
    .st-red { background-color: #fff5f5; color: #c53030; border: 1px solid #feb2b2; box-shadow: 0 0 15px #c5303044; }

    /* DETALLE AZUL BLINDADO */
    .blue-detail-container { background-color: #f0f7ff; color: #2c5282; padding: 20px; border-radius: 10px; border: 1px solid #bee3f8; }
    .nota-importante-text { border-top: 1px solid #aec6cf; margin-top: 15px; padding-top: 15px; font-size: 0.95rem; }
    
    .warning-yellow { background-color: #fdfde0; color: #856404; padding: 15px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 40px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

inject_ui_styles()

# Renderizado de cuadros negros superiores
st.markdown(f'<div class="availability-badge">ZONA: {" | ".join(obtener_modelos_vivos())}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="model-badge">{st.session_state.get("active_model", "ESPERANDO...")}</div>', unsafe_allow_html=True)

st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="version-display">v. 19 feb 21:00</div>', unsafe_allow_html=True)

# --- ESTRUCTURA DE PESTAÑAS ---
tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 EXCEL", "📈 GRÁFICOS"])
with tabs[0]:
    # REGISTRO
    c_reg1, c_reg2, c_reg3 = st.columns([1, 2, 1])
    with c_reg1: centro = st.text_input("Centro", placeholder="G/M")
    with c_reg2:
        r1, r2, r3 = st.columns(3)
        edad = r1.number_input("Edad", value=None, placeholder="0")
        alfa = r2.text_input("ID Alfanumérico")
        res = r3.selectbox("¿Residencia?", ["No", "Sí"])
    with c_reg3: st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)

    # CALCULADORA DUAL
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

    meds = st.text_area("Listado de medicamentos", height=150)
    
    if st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True):
        if meds:
            with st.spinner("Validando..."):
                prompt = f"""Experto en farmacia renal. Analiza estos fármacos para FG {valor_fg} mL/min: {meds}.
                REGLAS:
                1. PARTE SINTESIS: Solo fármacos que NO sean adecuados. CADA UNO EN UNA LÍNEA. Formato: [Icono ⚠️ o ⛔] [Nombre] - [Recomendación corta].
                2. PARTE DETALLE: Empieza con 'A continuación, se detallan los ajustes de dosis para cada fármaco con este valor de FG:'.
                3. Sin saludos."""
                
                resp = llamar_ia_en_cascada(prompt)
                
                # Lógica de Color de Alerta
                if "⛔" in resp: color, msg = "st-red", "Presencia de fármacos contraindicados"
                elif "⚠️" in resp: color, msg = "st-orange", "Revisar adecuación / Precaución"
                else: color, msg = "st-green", "Fármacos correctamente dosificados"

                try:
                    partes = resp.split("A continuación")
                    sintesis = partes[0].strip()
                    detalle = "A continuación" + partes[1] if len(partes) > 1 else resp
                    
                    # Cuadro de Síntesis dinámico
                    st.markdown(f'<div class="synthesis-box {color}"><b>SÍNTESIS:</b><br>{sintesis.replace("\n", "<br>")}<br><br><b>{msg}</b></div>', unsafe_allow_html=True)
                    
                    # Bloque Azul Detalle Científico
                    st.markdown(f"""
                    <div class="blue-detail-container">
                        {detalle.replace("\n", "<br>")}
                        <div class="nota-importante-text">
                            <b>Nota Importante:</b><br>
                            · Estas son recomendaciones generales.<br>
                            · Siempre se debe consultar la ficha técnica actualizada del medicamento y las guías clínicas locales.<br>
                            · Además del FG, se deben considerar otros factores individuales del paciente, como el peso, la edad, otras comorbilidades, la medicación concomitante y la respuesta clínica, para tomar decisiones terapéuticas.<br>
                            · Es crucial realizar un seguimiento periódico de la función renal para detectar cualquier cambio que pueda requerir ajustes futuros.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                except: st.info(resp)

st.markdown('<div class="warning-yellow">⚠️ Apoyo a la revisión farmacoterapéutica. Verifique siempre con fuentes oficiales.</div>', unsafe_allow_html=True)
