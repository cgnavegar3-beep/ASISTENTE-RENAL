# v. 20 feb 10:55
import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import google.generativeai as genai
import io

# =================================================================
# 🛡️ SECCIÓN DE BLINDAJE (PROHIBIDO MODIFICAR SIN PERMISO)
# =================================================================
# PRINCIPIOS FUNDAMENTALES (PPIO FUNDAMENTAL):
# 1. NUNCA BORRAR NI MODIFICAR ESTA CLÁUSULA. 
# 2. NOMBRE SIEMPRE: "ASISTENTE RENAL" con la versión/fecha debajo.
# 3. Antes de cualquier evolución técnica, explicar: "QUÉ", "POR QUÉ" y "CÓMO" y esperar aprobación ("adelante").
# 
# I. ESTRUCTURA VISUAL PROTEGIDA:
#    - Cuadros negros superiores (ZONA y ACTIVO/CONECTADO).
#    - Registro de paciente: TODO EN UNA LÍNEA (Centro, Edad, ID Alfa, Res, Fecha).
#    - Interfaz Dual: Estructura de Calculadora y caja de FG (Purple Glow).
#    - Lógica Cockcroft-Gault y etiqueta "Fórmula: Cockcroft-Gault".
#    - Cuadro de medicamentos (TextArea) y aviso RGPD rojo.
#    - Aviso amarillo de apoyo legal inferior.
#
# II. BLINDAJE DEL BLOQUE AZUL (blue-detail-container):
#    - Prohibición de Fragmentación: El detalle y la Nota Importante deben vivir en el mismo div CSS.
#    - Estilo Fijo: Fondo (#f0f7ff), borde (#bee3f8) y esquinas redondeadas (10px).
#    - Texto Estático: La Nota Importante (4 puntos) es intocable y no se puede parafrasear.
#
# III. BLINDAJE DE SÍNTESIS DINÁMICA (Glow System):
#    - Formato Rígido: Solo se permite "Medicamentos afectados:" o "Fármacos correctamente dosificados".
#    - Regla de Iconos: [Icono] + [Nombre] + [Frase corta]. Prohibido texto adicional.
#    - Lógica de Color (Glow): 
#        * Sin iconos = Verde (glow-green).
#        * Con ⚠️ = Naranja (glow-orange).
#        * Con ⛔ = Rojo (glow-red).
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

def llamar_ia_en_cascada(prompt):
    disponibles = obtener_modelos_vivos()
    preferencia = ['2.5-flash', '1.5-pro', '1.5-flash']
    modelos_a_intentar = [m for m in preferencia if m in disponibles]
    for mod_name in modelos_a_intentar:
        try:
            st.session_state.active_model = mod_name.upper()
            model = genai.GenerativeModel(f'models/gemini-{mod_name}')
            response = model.generate_content(prompt)
            return response.text
        except: continue
    return "⚠️ Error: Sin respuesta."

st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

def inject_ui_styles():
    st.markdown("""
    <style>
    .block-container { max-width: 100% !important; padding-top: 2.5rem !important; padding-left: 4% !important; padding-right: 4% !important; }
    .availability-badge { background-color: #1a1a1a !important; color: #888 !important; padding: 4px 10px; border-radius: 3px; font-family: monospace !important; font-size: 0.65rem; position: fixed; top: 15px; left: 15px; z-index: 1000000; border: 1px solid #333; width: 180px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
    .model-badge { background-color: #000000 !important; color: #00FF00 !important; padding: 4px 10px; border-radius: 3px; font-family: monospace !important; font-size: 0.75rem; position: fixed; top: 15px; left: 205px; z-index: 1000000; box-shadow: 0 0 5px #00FF0033; }
    .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin-top: 0px; }
    .version-display { text-align: right; font-size: 0.6rem; color: #bbb; font-family: monospace; position: fixed; bottom: 10px; right: 10px; }
    .id-display { color: #666; font-family: monospace; font-size: 0.85rem; margin-top: -5px; margin-bottom: 20px; }
    .formula-tag { font-size: 0.75rem; color: #888; font-style: italic; text-align: right; width: 100%; display: block; margin-top: 5px; }
    .fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .rgpd-box { background-color: #fff5f5; color: #c53030; padding: 10px; border-radius: 8px; border: 1px solid #feb2b2; font-size: 0.85rem; margin-bottom: 15px; text-align: center; }
    
    /* CUADRO SÍNTESIS CON GLOW DINÁMICO BLINDADO */
    .synthesis-box { padding: 15px; border-radius: 12px; margin-bottom: 15px; text-align: left; border-width: 2px; border-style: solid; font-size: 0.95rem; }
    .glow-green { background-color: #f1f8e9; color: #2e7d32; border-color: #a5d6a7; box-shadow: 0 0 12px #a5d6a7; }
    .glow-orange { background-color: #fff3e0; color: #e65100; border-color: #ffcc80; box-shadow: 0 0 12px #ffcc80; }
    .glow-red { background-color: #fff5f5; color: #c53030; border-color: #feb2b2; box-shadow: 0 0 18px #feb2b2; }

    /* BLOQUE AZUL UNIFICADO BLINDADO */
    .blue-detail-container { background-color: #f0f7ff; color: #2c5282; padding: 20px; border-radius: 10px; border: 1px solid #bee3f8; margin-top: 10px; line-height: 1.6; }
    .nota-line { border-top: 1px solid #aec6cf; margin-top: 15px; padding-top: 15px; font-size: 0.9rem; }
    
    .warning-yellow { background-color: #fdfde0; color: #856404; padding: 15px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 40px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

if 'active_model' not in st.session_state: st.session_state.active_model = "ESPERANDO..."
if 'meds_content' not in st.session_state: st.session_state.meds_content = ""

inject_ui_styles()
st.markdown(f'<div class="availability-badge">ZONA: {" | ".join(obtener_modelos_vivos())}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="model-badge">{st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="version-display">v. 20 feb 10:55</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 EXCEL", "📈 GRÁFICOS"])

with tabs[0]:
    st.markdown("### Registro de Paciente")
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1])
    with c1: centro = st.text_input("Centro", placeholder="G/M")
    with c2: edad_reg = st.number_input("Edad", value=None, placeholder="0")
    with c3: alfa = st.text_input("ID Alfanumérico", placeholder="ABC-123")
    with c4: res = st.selectbox("¿Residencia?", ["No", "Sí"])
    with c5: st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)

    id_final = f"{centro if centro else '---'}-{str(int(edad_reg)) if edad_reg else '00'}-{alfa if alfa else '---'}"
    st.markdown(f'<div class="id-display">ID Registro: {id_final}</div>', unsafe_allow_html=True)

    col_izq, col_der = st.columns(2, gap="large")
    with col_izq:
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            calc_e = st.number_input("Edad (años)", value=edad_reg if edad_reg else 65)
            calc_p = st.number_input("Peso (kg)", value=70.0)
            calc_c = st.number_input("Creatinina (mg/dL)", value=1.0)
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"])
            fg = round(((140 - calc_e) * calc_p) / (72 * calc_c) * (0.85 if calc_s == "Mujer" else 1.0), 1)
            st.markdown('<span class="formula-tag">Fórmula: Cockcroft-Gault</span>', unsafe_allow_html=True)

    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual")
        valor_fg = fg_m if fg_m else fg
        st.markdown(f'<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{valor_fg}</div><div style="font-size: 1rem; color: #9d00ff;">mL/min</div></div>', unsafe_allow_html=True)

    st.write(""); st.markdown("---")
    st.markdown("#### 📝 Listado de medicamentos")
    st.markdown('<div class="rgpd-box"><b>Protección de Datos:</b> No procese datos personales identificables.</div>', unsafe_allow_html=True)
    st.session_state.meds_content = st.text_area("Listado", value=st.session_state.meds_content, height=150, label_visibility="collapsed")

    b_val, b_res = st.columns([0.85, 0.15])
    with b_val:
        if st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True):
            if st.session_state.meds_content:
                with st.spinner("Consultando evidencia clínica..."):
                    prompt = f"""Experto en farmacia renal. Analiza fármacos para FG {valor_fg}: {st.session_state.meds_content}.
                    INSTRUCCIONES DE SALIDA (SÍNTESIS):
                    - Si todos son correctos: "Fármacos correctamente dosificados".
                    - Si hay afectados: "Medicamentos afectados:" seguido de lista [Icono] [Nombre] - [Frase corta].
                    INSTRUCCIONES DE SALIDA (DETALLE):
                    - Empieza EXACTAMENTE con 'A continuación, se detallan los ajustes de dosis para cada fármaco con este valor de FG:'.
                    """
                    
                    resp = llamar_ia_en_cascada(prompt)
                    
                    # Lógica de Color Blindada
                    if "⛔" in resp: glow_class = "glow-red"
                    elif "⚠️" in resp: glow_class = "glow-orange"
                    else: glow_class = "glow-green"
                    
                    try:
                        partes = resp.split("A continuación")
                        sintesis = partes[0].strip()
                        detalle_clinico = "A continuación" + partes[1]
                        
                        st.markdown(f'<div class="synthesis-box {glow_class}"><b>{sintesis.replace("\n", "<br>")}</b></div>', unsafe_allow_html=True)
                        
                        st.markdown(f"""
                        <div class="blue-detail-container">
                            {detalle_clinico.replace("\n", "<br>")}
                            <div class="nota-line">
                                <b>Nota Importante:</b><br>
                                · Estas son recomendaciones generales.<br>
                                · Siempre se debe consultar la ficha técnica actualizada del medicamento y las guías clínicas locales.<br>
                                · Además del FG, se deben considerar otros factores individuales del paciente, como el peso, la edad, otras comorbilidades, la medicación concomitante y la respuesta clínica.<br>
                                · Es crucial realizar un seguimiento periódico de la función renal para detectar cualquier cambio que pueda requerir ajustes futuros.
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    except: st.info(resp)

    with b_res:
        if st.button("🗑️ RESET", use_container_width=True):
            st.session_state.meds_content = ""; st.rerun()

st.markdown('<div class="warning-yellow">⚠️ Apoyo a la revisión farmacoterapéutica. Verifique siempre con fuentes oficiales.</div>', unsafe_allow_html=True)
