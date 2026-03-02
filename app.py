# v. 02 mar 2026 19:40 (Validación estructura API Key)

import streamlit as st
import pandas as pd
import io
from datetime import datetime
import google.generativeai as genai
import random
import re
import os
import constants as c # Mantiene la integridad del prompt central

# --- CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

# --- INICIALIZACIÓN DE SESIÓN (CORRECCIÓN DE ERROR) ---
if 'active_model' not in st.session_state: st.session_state.active_model = "---"
if 'reg_centro' not in st.session_state: st.session_state.reg_centro = ""
if 'reg_res' not in st.session_state: st.session_state.reg_res = None
if 'reg_id' not in st.session_state: st.session_state.reg_id = ""
if 'calc_e' not in st.session_state: st.session_state.calc_e = None
if 'calc_p' not in st.session_state: st.session_state.calc_p = None
if 'calc_c' not in st.session_state: st.session_state.calc_c = None
if 'calc_s' not in st.session_state: st.session_state.calc_s = None
if 'main_meds' not in st.session_state: st.session_state.main_meds = ""
if 'soip_s' not in st.session_state: st.session_state.soip_s = ""
if 'soip_o' not in st.session_state: st.session_state.soip_o = ""
if 'soip_i' not in st.session_state: st.session_state.soip_i = ""
if 'soip_p' not in st.session_state: st.session_state.soip_p = ""
if 'ic_motivo' not in st.session_state: st.session_state.ic_motivo = ""
if 'ic_info' not in st.session_state: st.session_state.ic_info = ""

# --- FUNCIONES DE SOPORTE ---
def llamar_ia_en_cascada(prompt):
    # --- LECTURA DE SECRETS ---
    API_KEY = st.secrets.get("GOOGLE_API_KEY") 
    if API_KEY: genai.configure(api_key=API_KEY)
    
    # --- ESTRUCTURA EXACTA SOLICITADA ---
    disponibles = [m.name.replace('models/', '').replace('gemini-', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods] if API_KEY else ["2.5-flash"]
    orden = ['2.5-flash', 'flash-latest', '1.5-pro']
    for mod_name in orden:
        if mod_name in disponibles:
            try:
                st.session_state.active_model = mod_name.upper()
                model = genai.GenerativeModel(f'models/gemini-{mod_name}')
                return model.generate_content(prompt).text
            except: continue
    return "⚠️ Error."

# --- NUEVA FUNCIÓN: ORDENAMIENTO CLÍNICO ---
def ordenar_medicamentos_por_riesgo(bloque_texto):
    """Ordena las líneas del bloque según el icono de riesgo."""
    if not bloque_texto: return ""
    lineas = bloque_texto.strip().split('\n')
    
    # Asignación de pesos según la jerarquía clínica
    pesos = {
        "⛔": 4,
        "⚠️⚠️⚠️": 3,
        "⚠️⚠️": 2,
        "⚠️": 1,
        "✅": 0
    }
    
    def obtener_peso(linea):
        for icono, peso in pesos.items():
            if linea.startswith(icono):
                return peso
        return -1 # Para líneas que no cumplan el formato
    
    # Ordenar descendentemente por peso
    lineas_ordenadas = sorted(lineas, key=obtener_peso, reverse=True)
    return "\n".join(lineas_ordenadas)

# --- FUNCIONES DE UI Y LÓGICA ---
def reset_registro():
    st.session_state.reg_centro = ""
    st.session_state.reg_res = None
    st.session_state.reg_id = ""
    st.session_state.calc_e = None
    st.session_state.calc_p = None
    st.session_state.calc_c = None
    st.session_state.calc_s = None

def reset_meds():
    st.session_state.main_meds = ""

def verificar_datos_completos():
    faltantes = []
    if not st.session_state.calc_e: faltantes.append("Edad")
    if not st.session_state.calc_p: faltantes.append("Peso")
    if not st.session_state.calc_c: faltantes.append("Creatinina")
    if not st.session_state.calc_s: faltantes.append("Sexo")
    return faltantes

def procesar_y_limpiar_meds():
    pass

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
    
    .synthesis-box { padding: 15px; border-radius: 12px; margin-bottom: 15px; border-width: 2.2px; border-style: solid; font-size: 0.95rem; white-space: pre-line; }
    .glow-red { background-color: #fff5f5; color: #c53030; border-color: #feb2b2; box-shadow: 0 0 12px #feb2b2; }
    .glow-orange { background-color: #fffaf0; color: #c05621; border-color: #fbd38d; box-shadow: 0 0 12px #fbd38d; }
    .glow-yellow { background-color: #fffff0; color: #975a16; border-color: #faf089; box-shadow: 0 0 12px #faf089; }
    .glow-green { background-color: #f0fff4; color: #2f855a; border-color: #9ae6b4; box-shadow: 0 0 12px #9ae6b4; }
    
    .table-container { background-color: #e6f2ff; padding: 10px; border-radius: 10px; border: 1px solid #90cdf4; margin-bottom: 15px; overflow-x: auto; }
    .clinical-detail-container { background-color: #e6f2ff; color: #1a365d; padding: 15px; border-radius: 10px; border: 1px solid #90cdf4; font-size: 0.9rem; white-space: pre-line; }
    
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
st.markdown('<div class="sub-version">v. 02 mar 2026 19:40</div>', unsafe_allow_html=True)

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
            calc_e = st.number_input("Edad (años)", value=st.session_state.calc_e if st.session_state.calc_e is not None else None, step=1, key="calc_e_input", placeholder="Ej: 65")
            calc_p = st.number_input("Peso (kg)", value=st.session_state.calc_p if st.session_state.calc_p is not None else None, placeholder="Ej: 70.5", key="calc_p_input")
            calc_c = st.number_input("Creatinina (mg/dL)", value=st.session_state.calc_c if st.session_state.calc_c is not None else None, placeholder="Ej: 1.2", key="calc_c_input")
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"], index=0 if st.session_state.calc_s == "Hombre" else (1 if st.session_state.calc_s == "Mujer" else None), placeholder="Elegir...", key="calc_s_input")
            
            st.session_state.calc_e = calc_e; st.session_state.calc_p = calc_p
            st.session_state.calc_c = calc_c; st.session_state.calc_s = calc_s
            
            st.markdown('<div class="formula-label" style="text-align:right;">Fórmula Cockcroft-Gault</div>', unsafe_allow_html=True)
            if calc_e is not None and calc_p is not None and calc_c is not None and calc_s is not None:
                fg = round(((140 - calc_e) * calc_p) / (72 * (calc_c if calc_c > 0 else 1)) * (0.85 if calc_s == "Mujer" else 1.0), 1)
            else:
                fg = 0.0

    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual", placeholder="Fórmula Cockcroft-Gault: entrada manual")
        valor_fg = fg_m if fg_m else fg
        st.markdown(f'''<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{valor_fg}</div><div style="font-size: 0.8rem; color: #9d00ff;">mL/min (C-G)</div></div>''', unsafe_allow_html=True)
        st.markdown('<div class="formula-label">Fórmula Cockcroft-Gault</div>', unsafe_allow_html=True)
        st.write(""); l1, l2 = st.columns(2)
        
        with l1:
            st.markdown('<div class="fg-special-border">', unsafe_allow_html=True)
            val_mdrd = st.number_input("FG MDRD-4 IDMS", value=None, placeholder="MDRD-4", label_visibility="collapsed", key="fgl_mdrd")
            st.markdown('</div>', unsafe_allow_html=True)
            if val_mdrd is not None: st.markdown(f'<div class="unit-label">{val_mdrd} mL/min/1,73m²</div>', unsafe_allow_html=True)
            
        with l2:
            st.markdown('<div class="fg-special-border">', unsafe_allow_html=True)
            val_ckd = st.number_input("FG CKD-EPI", value=None, placeholder="CKD-EPI", label_visibility="collapsed", key="fgl_ckd")
            st.markdown('</div>', unsafe_allow_html=True)
            if val_ckd is not None: st.markdown(f'<div class="unit-label">{val_ckd} mL/min/1,73m²</div>', unsafe_allow_html=True)

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
        
        if not st.session_state.main_meds:
            st.error("Por favor, introduce al menos un medicamento.")
        else:
            placeholder_salida = st.empty()
            with st.spinner("Procesando análisis clínico..."):
                
                try: val_mdrd_prompt = val_mdrd if val_mdrd else "N/A"
                except: val_mdrd_prompt = "N/A"
                try: val_ckd_prompt = val_ckd if val_ckd else "N/A"
                except: val_ckd_prompt = "N/A"

                prompt_final = f"""
                {c.PROMPT_AFR_V10}
                
                DATOS DEL PACIENTE:
                - FG Cockcroft-Gault: {valor_fg} mL/min
                - FG CKD-EPI: {val_ckd_prompt} mL/min/1,73m²
                - FG MDRD-4: {val_mdrd_prompt} mL/min/1,73m²
                
                MEDICAMENTOS A ANALIZAR:
                {st.session_state.main_meds}
                """
                
                resp = llamar_ia_en_cascada(prompt_final)
                
                try:
                    resp_limpia = resp.strip()
                    partes = [p.strip() for p in resp_limpia.split("|||") if p.strip()]
                    while len(partes) < 3: partes.append("")
                    sintesis, tabla_html, detalle_completo = partes[:3]
                    
                    # --- ORDENAMIENTO BACKEND Y LIMPIEZA ---
                    sintesis = ordenar_medicamentos_por_riesgo(sintesis)
                    detalle_completo = ordenar_medicamentos_por_riesgo(detalle_completo)
                    
                    sintesis = re.sub(r"\n{2,}", "\n", sintesis.strip())
                    detalle_completo = re.sub(r"\n{2,}", "\n", detalle_completo.strip())
                    
                    # Definición del color de alerta
                    if "⛔" in sintesis: glow = "glow-red"
                    elif "⚠️⚠️⚠️" in sintesis: glow = "glow-orange"
                    elif "⚠️" in sintesis: glow = "glow-yellow"
                    else: glow = "glow-green"
                    
                    with placeholder_salida.container():
                        st.markdown(f'<div style="text-align:center; font-weight:700;">🔍 Medicamentos afectados (FG Cockcroft-Gault: {valor_fg} mL/min)</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="synthesis-box {glow}">{sintesis}</div>', unsafe_allow_html=True)
                        st.markdown("---")
                        st.markdown(f'<div class="table-container">{tabla_html}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div style="text-align:center; font-weight:700;">A continuación se detallan los ajustes:</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="clinical-detail-container">{detalle_completo}</div>', unsafe_allow_html=True)
                    
                    # --- GESTIÓN SOIP ---
                    datos_calc = []
                    if calc_e: datos_calc.append(f"Edad: {calc_e} años")
                    if calc_p: datos_calc.append(f"Peso: {calc_p} kg")
                    if calc_c: datos_calc.append(f"Creatinina: {calc_c} mg/dL")
                    if valor_fg: datos_calc.append(f"FG (C-G): {valor_fg} mL/min")
                    
                    st.session_state.soip_s = "Revisión farmacoterapéutica según función renal."
                    st.session_state.soip_o = "\n".join(datos_calc)
                    st.session_state.soip_i = sintesis
                    st.session_state.soip_p = "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
                    st.session_state.ic_motivo = "Se solicita valoración médica tras la revisión de la adecuación del tratamiento a la función renal del paciente."
                    st.session_state.ic_info = (
                        f"ID: {st.session_state.reg_id}\n"
                        f"FG (C-G): {valor_fg} mL/min\n"
                        "---------------------------\n"
                        f"Análisis Clínico:\n{sintesis}\n"
                        "---------------------------\n"
                        f"Detalle:\n{detalle_completo}"
                    )
                        
                except Exception as e:
                    st.error(f"Error técnico en AFR-V10: {e}")
                    st.code(resp)

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

st.markdown(f"""<div class="warning-yellow">⚠️ <b>Esta herramienta es de apoyo a la revisión farmacoterapéutica. Verifique siempre con fuentes oficiales.</b></div> <div style="text-align:right; font-size:0.6rem; color:#ccc; font-family:monospace; margin-top:10px;">v. 02 mar 2026 19:40</div>""", unsafe_allow_html=True)
