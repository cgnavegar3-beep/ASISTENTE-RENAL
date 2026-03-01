# v. 01 mar 2026 16:20

import streamlit as st
import pandas as pd
import io
from datetime import datetime
import google.generativeai as genai
import random
import re
import os

# =================================================================
# PRINCIPIOS FUNDAMENTALES:
# # ... (Mantener principios sin cambios)
# =================================================================

st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

if "active_model" not in st.session_state:
    st.session_state.active_model = "BUSCANDO..."

# INICIALIZACIÓN DE VARIABLES DE SESIÓN
for key in ["soip_s", "soip_o", "soip_i", "soip_p", "ic_motivo", "ic_info", "main_meds", "reg_id", "reg_centro", "calc_e", "calc_p", "calc_c", "calc_s"]:
    if key not in st.session_state: st.session_state[key] = None

# --- FUNCIONES DE SOPORTE ---
def cargar_prompt_clinico():
    try:
        with open(os.path.join("prompts", "categorizador.txt"), "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Error: No se encontró el archivo de prompt."

def llamar_ia_en_cascada(prompt):
    disponibles = [m.name.replace('models/', '').replace('gemini-', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods] if API_KEY else ["2.5-flash"]
    orden = ['2.5-flash', 'flash-latest', '1.5-pro']
    for mod_name in orden:
        if mod_name in disponibles:
            try:
                st.session_state.active_model = mod_name.upper()
                model = genai.GenerativeModel(f'models/gemini-{mod_name}')
                return model.generate_content(prompt).text
            except: continue
    return "⚠️ Error en la generación."

def procesar_y_limpiar_meds():
    texto = st.session_state.main_meds
    if texto:
        texto_limpio = re.sub(r"\s*-\s*|;\s*", "\n", texto)
        texto_limpio = re.sub(r"\n+", "\n", texto_limpio).strip()
        texto_limpio = re.sub(r"(\d+)\.0+\s*(mg|g|mcg|ml)", r"\1 \2", texto_limpio, flags=re.IGNORECASE)
        prompt = f"""
        Actúa como farmacéutico clínico. Reescribe el siguiente listado de medicamentos siguiendo estas reglas estrictas:
        1. Estructura cada línea como: [Principio Activo] + [Dosis] + (Marca Comercial).
        2. Si no identificas la marca, omite el paréntesis.
        3. Coloca cada medicamento en una línea independiente.
        4. No agregues numeración ni explicaciones.
        Texto a procesar:
        {texto_limpio}
        """
        st.session_state.main_meds = llamar_ia_en_cascada(prompt)

def reset_registro():
    for key in ["reg_centro", "reg_res", "reg_id", "fgl_ckd", "fgl_mdrd"]:
        st.session_state[key] = ""
    for key in ["calc_e", "calc_p", "calc_c", "calc_s"]:
        st.session_state[key] = None

def reset_meds():
    st.session_state.main_meds = ""
    st.session_state.soip_s = "Revisión farmacoterapéutica según función renal."
    st.session_state.soip_o = ""; st.session_state.soip_i = ""
    st.session_state.soip_p = "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
    st.session_state.ic_motivo = "Se solicita valoración médica tras la revisión de la adecuación del tratamiento a la función renal del paciente."
    st.session_state.ic_info = ""

def verificar_datos_completos():
    campos = {"Centro": "reg_centro", "Edad": "calc_e", "Peso": "calc_p", "Creatinina": "calc_c", "Sexo": "calc_s"}
    return [nombre for nombre, key in campos.items() if st.session_state.get(key) in [None, ""]]

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    API_KEY = None

# --- UI STYLE ---
def inject_styles():
    st.markdown("""
    <style>
    .blink-text { animation: blinker 1s linear infinite; }
    @keyframes blinker { 50% { opacity: 0; } }
    .block-container { max-width: 100% !important; padding-top: 1rem !important; padding-left: 4% !important; padding-right: 4% !important; }
    .black-badge-zona { background-color: #000000; color: #888; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 15px; z-index: 999999; }
    .black-badge-activo { background-color: #000000; color: #00FF00; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 145px; z-index: 999999; text-shadow: 0 0 5px #00FF00; }
    .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin-bottom: 0px; margin-top: 20px; }
    .sub-version { text-align: center; font-size: 0.6rem; color: #bbb; margin-top: -5px; margin-bottom: 20px; font-family: monospace; }
    .fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .unit-label { font-size: 0.65rem; color: #888; margin-top: -10px; margin-bottom: 5px; font-family: sans-serif; text-align: center; }
    .synthesis-box { padding: 15px; border-radius: 12px; margin-bottom: 15px; border-width: 2.2px; border-style: solid; font-size: 0.95rem; }
    .glow-orange { background-color: #fff3e0; color: #e65100; border-color: #ffcc80; box-shadow: 0 0 12px #ffcc80; }
    .blue-detail-container { background-color: #e6f0ff; color: #1a365d; padding: 20px; border-radius: 10px; border: 1px solid #90cdf4; margin-top: 10px; font-size: 0.9rem; }
    .warning-yellow { background-color: #fff9db; color: #856404; padding: 20px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 40px; text-align: center; font-size: 0.85rem; line-height: 1.5; }
    .linea-discreta-soip { border-top: 1px solid #d9d5c7; margin: 15px 0 5px 0; font-size: 0.65rem; font-weight: bold; color: #8e8a7e; text-transform: uppercase; }
    .header-capsule { background-color: #e2e8f0; color: #2d3748; padding: 10px 30px; border-radius: 50px; display: inline-block; font-weight: 800; font-size: 0.9rem; margin-bottom: 20px; }
    .formula-label { font-size: 0.6rem; color: #666; font-family: monospace; text-align: right; margin-top: 5px; }
    .fg-special-border { border: 1.5px solid #9d00ff !important; border-radius: 5px; }
    .important-note { background-color: #002244; color: #ffffff; padding: 20px; border-radius: 10px; font-weight: bold; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)
inject_styles()

st.markdown('<div class="black-badge-zona">ZONA: ACTIVA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="black-badge-activo">ACTIVO: {st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-version">v. 01 mar 2026 16:20</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 DATOS", "📈 GRÁFICOS"])

with tabs[0]:
    st.markdown("### Registro de Paciente")
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1.5, 0.4])
    def on_centro_change():
        centro_val = st.session_state.reg_centro.strip()
        if centro_val.lower() == "m": st.session_state.reg_centro = "Marín"
        elif centro_val.lower() == "o": st.session_state.reg_centro = "O Grove"
        if not st.session_state.reg_centro: st.session_state.reg_id = ""
        else:
            iniciales = "".join([word[0] for word in st.session_state.reg_centro.split()]).upper()[:3]
            st.session_state.reg_id = f"PAC-{iniciales if iniciales else 'GEN'}{random.randint(10000, 99999)}"
    
    with c1: st.text_input("Centro", placeholder="M / G", key="reg_centro", on_change=on_centro_change)
    with c2: st.selectbox("¿Residencia?", ["No", "Sí"], index=None, placeholder="Sí / No", key="reg_res")
    with c3: st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)
    with c4: st.text_input("ID Registro", key="reg_id")
    with c5: st.write(""); st.button("🗑️", on_click=reset_registro)
    
    col_izq, col_der = st.columns(2, gap="large")
    with col_izq:
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            calc_e = st.number_input("Edad (años)", value=st.session_state.calc_e if st.session_state.calc_e is not None else 0, step=1, key="calc_e_input", placeholder="0.0")
            calc_p = st.number_input("Peso (kg)", value=st.session_state.calc_p if st.session_state.calc_p is not None else 0.0, placeholder="0.0", key="calc_p_input")
            calc_c = st.number_input("Creatinina (mg/dL)", value=st.session_state.calc_c if st.session_state.calc_c is not None else 0.0, placeholder="0.0", key="calc_c_input")
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"], index=0 if st.session_state.calc_s == "Hombre" else (1 if st.session_state.calc_s == "Mujer" else None), placeholder="Elegir...", key="calc_s_input")
            
            st.session_state.calc_e = calc_e; st.session_state.calc_p = calc_p
            st.session_state.calc_c = calc_c; st.session_state.calc_s = calc_s
            
            st.markdown('<div class="formula-label" style="text-align:right;">Fórmula Cockcroft-Gault</div>', unsafe_allow_html=True)
            fg = round(((140 - calc_e) * calc_p) / (72 * (calc_c if calc_c > 0 else 1)) * (0.85 if calc_s == "Mujer" else 1.0), 1) if calc_e > 0 and calc_p > 0 and calc_c > 0 and calc_s else 0.0

    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual", placeholder="Fórmula Cockcroft-Gault: entrada manual")
        valor_fg = fg_m if fg_m else fg
        st.markdown(f'''<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{valor_fg}</div><div style="font-size: 0.8rem; color: #9d00ff;">mL/min (C-G)</div></div>''', unsafe_allow_html=True)
        st.markdown('<div class="formula-label">Fórmula Cockcroft-Gault</div>', unsafe_allow_html=True)
        st.write(""); l1, l2 = st.columns(2)
        with l1:
            st.markdown('<div class="fg-special-border">', unsafe_allow_html=True)
            val_ckd = st.number_input("FG CKD-EPI", value=None, placeholder="FG CKD-EPI", label_visibility="collapsed", key="fgl_ckd")
            st.markdown('</div>', unsafe_allow_html=True)
            if val_ckd is not None: st.markdown(f'<div class="unit-label">{val_ckd} mL/min/1,73m²</div>', unsafe_allow_html=True)
        with l2:
            st.markdown('<div class="fg-special-border">', unsafe_allow_html=True)
            val_mdrd = st.number_input("FG MDRD-4 IDMS", value=None, placeholder="FG MDRD-4 IDMS", label_visibility="collapsed", key="fgl_mdrd")
            st.markdown('</div>', unsafe_allow_html=True)
            if val_mdrd is not None: st.markdown(f'<div class="unit-label">{val_mdrd} mL/min/1,73m²</div>', unsafe_allow_html=True)

    st.write(""); st.markdown("---")
    m_col1, m_col2 = st.columns([0.5, 0.5])
    with m_col1: st.markdown("#### 📝 Listado de medicamentos")
    with m_col2: st.markdown('<div style="float:right; background-color:#fff5f5; color:#c53030; padding:8px 16px; border-radius:8px; border:1.5px solid #feb2b2; font-size:0.8rem;">🛡️ RGPD: No datos personales</div>', unsafe_allow_html=True)

    txt_meds = st.text_area("Listado", height=150, label_visibility="collapsed", key="main_meds")
    st.button("Procesar medicamentos", on_click=procesar_y_limpiar_meds)
    
    b1, b2 = st.columns([0.85, 0.15])
    btn_val = b1.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True)
    b2.button("🗑️ RESET", on_click=reset_meds, use_container_width=True)

    if btn_val:
        faltantes = verificar_datos_completos()
        if faltantes:
            st.markdown(f'<div style="background-color: #fff3cd; color: #856404; padding: 1rem; border-radius: 0.5rem; border: 1px solid #ffeeba; margin-bottom: 1rem;"><span class="blink-text">⚠️ Nota: Faltan datos en el registro ({", ".join(faltantes)}). Se procede con validación de consulta rápida.</span></div>', unsafe_allow_html=True)
        
        if not txt_meds:
            st.error("Por favor, introduce al menos un medicamento.")
        else:
            placeholder_salida = st.empty()
            with st.spinner("Procesando análisis clínico..."):
                prompt_base = cargar_prompt_clinico()
                datos_paciente = f"""
                DATOS DEL PACIENTE PARA LA AUDITORÍA:
                - FG Calculado (Cockcroft-Gault): {valor_fg} mL/min
                - Edad: {calc_e} años
                - Peso: {calc_p} kg
                - Creatinina: {calc_c} mg/dL
                - Sexo: {calc_s}
                """
                prompt_final = datos_paciente + "\n" + prompt_base + "\nLISTA DE MEDICAMENTOS:\n" + txt_meds
                
                resp = llamar_ia_en_cascada(prompt_final)
                
                try:
                    partes = resp.split("---")
                    sintesis = partes[0].replace("### BLOQUE 1: SÍNTESIS RÁPIDA", "").strip()
                    detalle_completo = partes[1].replace("### BLOQUE 2: DETALLE TÉCNICO", "").strip()
                    
                    with placeholder_salida.container():
                        st.markdown("#### 🔍 Medicamentos afectados", unsafe_allow_html=True)
                        st.markdown(f'<div class="synthesis-box glow-orange">{sintesis.replace("-", "•").replace("\n", "<br>")}</div>', unsafe_allow_html=True)
                        st.markdown("#### ⚙️ Detalle Técnico y Comparativa", unsafe_allow_html=True)
                        
                        # --- MODIFICACIÓN DE VISUALIZACIÓN ---
                        st.markdown(f'<div class="blue-detail-container">{detalle_completo.replace("A continuación se detallan los ajustes:", "<b>A continuación se detallan los ajustes:</b>").replace("\n", "<br>")}</div>', unsafe_allow_html=True)
                        
                        # NOTA IMPORTANTE FINAL
                        st.markdown("""
                        <div class="important-note">
                        NOTA IMPORTANTE:<br>
                        3.1. Verifique siempre con la ficha técnica oficial (AEMPS/EMA).<br>
                        3.2. Los ajustes propuestos son orientativos según filtrado glomerular actual.<br>
                        3.3. La decisión final corresponde siempre al prescriptor médico.<br>
                        3.4. Considere la situación clínica global del paciente antes de modificar dosis.
                        </div>
                        """, unsafe_allow_html=True)
                        # --------------------------------------

                    st.session_state.soip_o = f"Edad: {int(calc_e)} | Peso: {calc_p} | Cr: {calc_c} | FG: {valor_fg}"
                    st.session_state.soip_i = sintesis
                    st.session_state.ic_info = detalle_completo
                    st.session_state.ic_motivo = f"Se solicita valoración médica tras la revisión de la adecuación del tratamiento a la función renal del paciente.\n\nLISTADO DETECTADO:\n{sintesis}"
                except: st.error("Error en la estructura de respuesta de la IA.")

# ... (Resto de pestañas sin cambios)
with tabs[1]:
    st.markdown('<div style="text-align:center;"><div class="header-capsule">📄 Nota Evolutiva SOIP</div></div>', unsafe_allow_html=True)
    for label, key, h in [("Subjetivo (S)", "soip_s", 70), ("Objetivo (O)", "soip_o", 70), ("Interpretación (I)", "soip_i", 120), ("Plan (P)", "soip_p", 100)]:
        st.markdown(f'<div class="linea-discreta-soip">{label}</div>', unsafe_allow_html=True)
        st.text_area(key, st.session_state[key], height=h, label_visibility="collapsed")

    st.write(""); st.markdown('<div style="text-align:center;"><div class="header-capsule">📨 Solicitud de Interconsulta</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="linea-discreta-soip">Motivo de la Interconsulta</div>', unsafe_allow_html=True)
    st.text_area("ic_mot", st.session_state.ic_motivo, height=180, label_visibility="collapsed")
    st.markdown('<div class="linea-discreta-soip">Información Clínica</div>', unsafe_allow_html=True)
    st.text_area("ic_inf", st.session_state.ic_info, height=250, label_visibility="collapsed")

with tabs[2]:
    st.markdown('<div style="text-align:center;"><div class="header-capsule">📊 Gestión de Datos y Volcado</div></div>', unsafe_allow_html=True)

st.markdown(f"""<div class="warning-yellow">⚠️ <b>Esta herramienta es de apoyo a la revisión farmacoterapéutica. Verifique siempre con fuentes oficiales.</b></div> <div style="text-align:right; font-size:0.6rem; color:#ccc; font-family:monospace; margin-top:10px;">v. 01 mar 2026 16:20</div>""", unsafe_allow_html=True)
