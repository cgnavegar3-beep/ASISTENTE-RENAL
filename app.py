# v. 01 mar 2026 21:55

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
# 1. RIGOR TÉCNICO: La seguridad y precisión de los datos es la máxima prioridad.
# 2. SEPARACIÓN DE BLOQUES: Los datos de la IA deben parsearse estrictamente usando |||.
# 3. SEGURIDAD TÉCNICA: Se deben proteger los elementos clave contra cambios accidentales.
# 4. NOTA IMPORTANTE: Se deben mostrar los 4 puntos de seguridad clínica obligatorios.
# =================================================================

st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

# --- INICIALIZACIÓN DE VARIABLES DE SESIÓN ---
if "active_model" not in st.session_state: st.session_state.active_model = "BUSCANDO..."
if "main_meds" not in st.session_state: st.session_state.main_meds = ""
# Inicialización de campos SOIP/IC
for key in ["soip_s", "soip_o", "soip_i", "soip_p", "ic_motivo", "ic_info", "reg_id", "reg_centro", "calc_e", "calc_p", "calc_c", "calc_s", "reg_res"]:
    if key not in st.session_state: st.session_state[key] = None

# --- CONFIGURACIÓN DE IA ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    API_KEY = None
    st.sidebar.error("API Key no encontrada.")

# --- FUNCIONES DE SOPORTE ---
def llamar_ia_en_cascada(prompt):
    if not API_KEY: return "⚠️ Error: API Key no configurada."
    disponibles = [m.name.replace('models/', '').replace('gemini-', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    orden = ['2.5-flash', 'flash-latest', '1.5-pro']
    for mod_name in orden:
        if mod_name in disponibles:
            try:
                st.session_state.active_model = mod_name.upper()
                model = genai.GenerativeModel(f'models/gemini-{mod_name}')
                return model.generate_content(prompt, generation_config={"temperature": 0.1}).text
            except: continue
    return "⚠️ Error en la generación."

def cargar_prompt_clinico():
    try:
        with open(os.path.join("prompts", "categorizador.txt"), "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError: return "Error: Archivo prompt no encontrado."

def procesar_y_limpiar_meds():
    texto = st.session_state.main_meds
    if texto:
        # Regex agresivo para forzar una línea por fármaco desde la entrada
        texto_limpio = re.sub(r"[,;:-]\s*", "\n", texto)
        texto_limpio = re.sub(r"\n+", "\n", texto_limpio).strip()
        
        # MEJORA: Prompt forzando el formato a la IA
        prompt = f"""
        Actúa como farmacéutico clínico. Reescribe el siguiente listado de medicamentos siguiendo estas reglas estrictas:
        1. Estructura cada línea como: [Principio Activo] + [Dosis] + (Marca Comercial).
        2. Si no identificas la marca, omite el paréntesis.
        3. OBLIGATORIO: Coloca cada medicamento en una línea independiente (UNA LÍNEA POR FÁRMACO).
        4. No uses numeración ni viñetas.
        Texto a procesar:
        {texto_limpio}
        """
        st.session_state.main_meds = llamar_ia_en_cascada(prompt)

def reset_registro():
    for key in ["reg_centro", "reg_res", "reg_id", "fgl_ckd", "fgl_mdrd"]: st.session_state[key] = ""
    for key in ["calc_e", "calc_p", "calc_c", "calc_s"]: st.session_state[key] = None

def reset_meds():
    st.session_state.main_meds = ""
    st.session_state.soip_s = "Revisión farmacoterapéutica según función renal."
    st.session_state.soip_o = ""
    st.session_state.soip_i = ""
    st.session_state.soip_p = "Se hace interconsulta al MAP para valoración de ajuste posológico."
    st.session_state.ic_motivo = "Se solicita valoración médica tras revisión de adecuación del tratamiento."
    st.session_state.ic_info = ""

def verificar_datos_completos():
    campos = {"Centro": "reg_centro", "Edad": "calc_e", "Peso": "calc_p", "Creatinina": "calc_c", "Sexo": "calc_s"}
    return [nombre for nombre, key in campos.items() if st.session_state.get(key) in [None, ""]]

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
    .glow-red { background-color: #fff5f5; color: #c53030; border-color: #feb2b2; box-shadow: 0 0 12px #feb2b2; }
    .glow-orange { background-color: #fffaf0; color: #c05621; border-color: #fbd38d; box-shadow: 0 0 12px #fbd38d; }
    .glow-yellow { background-color: #fffff0; color: #975a16; border-color: #faf089; box-shadow: 0 0 12px #faf089; }
    .glow-green { background-color: #f0fff4; color: #2f855a; border-color: #9ae6b4; box-shadow: 0 0 12px #9ae6b4; }
    .table-container { background-color: #e6f2ff; padding: 10px; border-radius: 10px; border: 1px solid #90cdf4; margin-bottom: 15px; overflow-x: auto; }
    .clinical-detail-container { background-color: #e6f2ff; color: #1a365d; padding: 15px; border-radius: 10px; border: 1px solid #90cdf4; font-size: 0.9rem; }
    .warning-yellow { background-color: #fff9db; color: #856404; padding: 20px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 40px; text-align: center; font-size: 0.85rem; line-height: 1.5; }
    .linea-discreta-soip { border-top: 1px solid #d9d5c7; margin: 15px 0 5px 0; font-size: 0.65rem; font-weight: bold; color: #8e8a7e; text-transform: uppercase; }
    .header-capsule { background-color: #e2e8f0; color: #2d3748; padding: 10px 30px; border-radius: 50px; display: inline-block; font-weight: 800; font-size: 0.9rem; margin-bottom: 20px; }
    .formula-label { font-size: 0.6rem; color: #666; font-family: monospace; text-align: right; margin-top: 5px; }
    .fg-special-border { border: 1.5px solid #9d00ff !important; border-radius: 5px; }
    .nota-importante-box { border-top: 2px dashed #0057b8; margin-top: 15px; padding-top: 10px; font-size: 0.8rem; color: #1a365d; }
    </style>
    """, unsafe_allow_html=True)
inject_styles()

st.markdown('<div class="black-badge-zona">ZONA: ACTIVA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="black-badge-activo">ACTIVO: {st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-version">v. 01 mar 2026 21:55</div>', unsafe_allow_html=True)

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
    
    with c1: st.text_input("Centro", placeholder="Marín / O Grove", key="reg_centro", on_change=on_centro_change)
    with c2: st.selectbox("¿Residencia?", ["No", "Sí"], index=None, placeholder="Sí / No", key="reg_res")
    with c3: st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)
    with c4: st.text_input("ID Registro", key="reg_id")
    with c5: st.write(""); st.button("🗑️", on_click=reset_registro)
    
    col_izq, col_der = st.columns(2, gap="large")
    with col_izq:
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            # Placeholders restaurados
            calc_e = st.number_input("Edad (años)", value=st.session_state.calc_e if st.session_state.calc_e is not None else 0, step=1, key="calc_e_input", placeholder="Ej: 65")
            calc_p = st.number_input("Peso (kg)", value=st.session_state.calc_p if st.session_state.calc_p is not None else 0.0, key="calc_p_input", placeholder="Ej: 70.5")
            calc_c = st.number_input("Creatinina (mg/dL)", value=st.session_state.calc_c if st.session_state.calc_c is not None else 0.0, key="calc_c_input", placeholder="Ej: 1.2")
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"], index=0 if st.session_state.calc_s == "Hombre" else (1 if st.session_state.calc_s == "Mujer" else None), key="calc_s_input", placeholder="Elegir...")
            
            st.session_state.calc_e = calc_e; st.session_state.calc_p = calc_p
            st.session_state.calc_c = calc_c; st.session_state.calc_s = calc_s
            
            st.markdown('<div class="formula-label" style="text-align:right;">Fórmula Cockcroft-Gault</div>', unsafe_allow_html=True)
            if calc_e is not None and calc_p is not None and calc_c is not None and calc_s is not None:
                fg = round(((140 - calc_e) * calc_p) / (72 * (calc_c if calc_c > 0 else 1)) * (0.85 if calc_s == "Mujer" else 1.0), 1)
            else: fg = 0.0

    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        # Placeholders restaurados
        fg_m = st.text_input("Ajuste Manual", placeholder="C-G manual")
        valor_fg = fg_m if fg_m else fg
        st.markdown(f'''<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{valor_fg}</div><div style="font-size: 0.8rem; color: #9d00ff;">mL/min (C-G)</div></div>''', unsafe_allow_html=True)
        st.write(""); l1, l2 = st.columns(2)
        with l1:
            st.markdown('<div class="fg-special-border">', unsafe_allow_html=True)
            val_ckd = st.number_input("FG CKD-EPI", value=None, label_visibility="collapsed", key="fgl_ckd", placeholder="CKD-EPI")
            st.markdown('</div>', unsafe_allow_html=True)
        with l2:
            st.markdown('<div class="fg-special-border">', unsafe_allow_html=True)
            val_mdrd = st.number_input("FG MDRD-4 IDMS", value=None, label_visibility="collapsed", key="fgl_mdrd", placeholder="MDRD-4")
            st.markdown('</div>', unsafe_allow_html=True)

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
        if faltantes: st.warning(f"⚠️ Nota: Faltan datos ({', '.join(faltantes)}).")
        
        if not st.session_state.main_meds: st.error("Introduce medicamentos.")
        else:
            placeholder_salida = st.empty()
            with st.spinner("Análisis clínico AFR-V10..."):
                prompt_final = f"{cargar_prompt_clinico()}\nFG: {valor_fg} mL/min\nMed: {st.session_state.main_meds}"
                resp = llamar_ia_en_cascada(prompt_final)
                
                try:
                    partes = [p.strip() for p in resp.split("|||") if p.strip()]
                    while len(partes) < 3: partes.append("")
                    sintesis, tabla_html, detalle_completo = partes[:3]
                    
                    # Lógica Glow
                    glow = "glow-green"
                    if "⛔" in sintesis: glow = "glow-red"
                    elif "⚠️⚠️⚠️" in sintesis: glow = "glow-orange"
                    elif "⚠️" in sintesis: glow = "glow-yellow"
                    
                    with placeholder_salida.container():
                        st.markdown(f'<div class="synthesis-box {glow}">{sintesis}</div>', unsafe_allow_html=True)
                        st.markdown("---")
                        st.markdown(f'<div class="table-container">{tabla_html}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="clinical-detail-container">{detalle_completo}</div>', unsafe_allow_html=True)
                        
                    # --- INYECCIÓN RIGUROSA DE DATOS (Mismo Código Anterior) ---
                    st.session_state.soip_s = "Revisión farmacoterapéutica según función renal."
                    st.session_state.soip_o = f"Edad: {calc_e} años | Peso: {calc_p} kg | Creatinina: {calc_c} mg/dL | FG (C-G): {valor_fg} mL/min"
                    st.session_state.soip_i = tabla_html
                    st.session_state.soip_p = f"Se sugiere: {sintesis}"
                    st.session_state.ic_motivo = "Se solicita valoración médica tras revisión de adecuación del tratamiento."
                    st.session_state.ic_info = tabla_html
                        
                except Exception as e: st.error(f"Error: {e}")

# --- TABS DE INFORME ---
with tabs[1]:
    st.markdown('<div style="text-align:center;"><div class="header-capsule">📄 Nota Evolutiva SOIP</div></div>', unsafe_allow_html=True)
    for label, key, h in [("Subjetivo (S)", "soip_s", 70), ("Objetivo (O)", "soip_o", 70), ("Interpretación (I)", "soip_i", 150), ("Plan (P)", "soip_p", 100)]:
        st.markdown(f'<div class="linea-discreta-soip">{label}</div>', unsafe_allow_html=True)
        st.text_area(key, st.session_state[key], height=h, label_visibility="collapsed")

    st.write(""); st.markdown('<div style="text-align:center;"><div class="header-capsule">📨 Solicitud de Interconsulta</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="linea-discreta-soip">Motivo de la Interconsulta</div>', unsafe_allow_html=True)
    st.text_area("ic_mot", st.session_state.ic_motivo, height=100, label_visibility="collapsed")
    st.markdown('<div class="linea-discreta-soip">Información Clínica</div>', unsafe_allow_html=True)
    st.text_area("ic_inf", st.session_state.ic_info, height=200, label_visibility="collapsed")

with tabs[2]:
    st.markdown('<div style="text-align:center;"><div class="header-capsule">📊 Gestión de Datos</div></div>', unsafe_allow_html=True)

st.markdown(f"""<div class="warning-yellow">⚠️ <b>Apoyo a la revisión farmacoterapéutica. Verifique fuentes oficiales.</b></div> <div style="text-align:right; font-size:0.6rem; color:#ccc; font-family:monospace; margin-top:10px;">v. 01 mar 2026 21:55</div>""", unsafe_allow_html=True)
