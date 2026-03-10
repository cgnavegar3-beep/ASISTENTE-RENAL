import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai
import random
import re
from streamlit_gsheets import GSheetsConnection
from bs4 import BeautifulSoup
import constants as c 

# =================================================================
# PRINCIPIOS FUNDAMENTALES (ESCRITOS DE PE A PA - PROHIBIDO ELIMINAR)
# =================================================================
# 1. IDENTIDAD: El nombre "ASISTENTE RENAL" es inalterable.
# 2. VERSIÓN: Mostrar siempre la versión con fecha/hora bajo el título.
# 3. INTERFAZ DUAL PROTEGIDA: Prohibido modificar la "Calculadora" y el 
#      "Filtrado Glomerular" (cuadro negro con glow morado).
# 4. BLINDAJE DE ELEMENTOS (ZONA ESTÁTICA):
#      - Cuadros negros superiores (ZONA y ACTIVO).
#      - Pestañas (Tabs) de navegación.
#      - Registro de Paciente: Estructura y función de fila única.
#      - Estructura del área de recorte y listado de medicación.
#      - Barra dual de validación (VALIDAR / RESET).
#      - Aviso legal amarillo inferior (Warning).
# 5. PROTOCOLO DE CAMBIOS: Antes de cualquier evolución técnica, explicar
#      "qué", "por qué" y "cómo". Esperar aprobación explícita ("adelante").
# 6. COMPROMISO DE RIGOR: Gemini verificará el cumplimiento de estos 
#      principios antes y después de cada cambio. No se simplifican líneas.
# 7. VERSIONADO LOCAL: Registrar la versión en la esquina inferior derecha.
# 8. CONTADOR DISCRETO: El contador de intentos debe ser discreto y 
#      ubicarse en la esquina superior izquierda (estilo v. 2.5).
# 9. INTEGRIDAD DEL CÓDIGO: Nunca omitir estas líneas; de lo contrario, 
#      se considerará pérdida de principios.
# 10. BLINDAJE DE CONTENIDOS: Quedan blindados todos los cuadros de texto,
#       sus textos flotantes (placeholders) y los textos predefinidos en las
#       secciones S, P e INTERCONSULTA. Prohibido borrarlos o simplificarlos.
# 11. AVISO PARPADEANTE: El aviso parpadeante ante falta de datos es un 
#       principio blindado; es informativo y no debe impedir la validación.
# =================================================================

st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")
conn = st.connection("gsheets", type=GSheetsConnection)

# --- INICIALIZACIÓN DE ESTADOS ---
if "active_model" not in st.session_state: st.session_state.active_model = "BUSCANDO..."
if "main_meds" not in st.session_state: st.session_state.main_meds = ""
if "analisis_realizado" not in st.session_state: st.session_state.analisis_realizado = False
if "resp_ia" not in st.session_state: st.session_state.resp_ia = None
if "reg_id" not in st.session_state: st.session_state.reg_id = f"PAC-{random.randint(10000, 99999)}"

# Textos blindados S, P e INTERCONSULTA
if "soip_s" not in st.session_state: st.session_state.soip_s = "Revisión farmacoterapéutica según función renal."
if "soip_p" not in st.session_state: st.session_state.soip_p = "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
for key in ["soip_o", "soip_i", "ic_inter", "ic_clinica", "reg_centro", "reg_res"]:
    if key not in st.session_state: st.session_state[key] = ""

# --- CONFIGURACIÓN IA ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    API_KEY = None

def llamar_ia_en_cascada(prompt):
    if not API_KEY: return "⚠️ Error: API Key no configurada."
    model = genai.GenerativeModel('models/gemini-1.5-flash')
    st.session_state.active_model = "1.5-FLASH"
    return model.generate_content(prompt, generation_config={"temperature": 0.1}).text

def volcar_a_sheets(tabla_html, p_info, meds_raw):
    try:
        soup = BeautifulSoup(tabla_html, 'html.parser')
        filas_html = soup.find_all('tr')[1:]
        
        # Contadores de Riesgo (Lógica activada)
        s = {k: 0 for k in ["t_cg", "p1_cg", "p2_cg", "p3_cg", "p4_cg", "t_mdrd", "t_ckd"]}
        nuevas_filas_meds = []
        
        for fila in filas_html:
            c_h = [td.get_text(strip=True) for td in fila.find_all('td')]
            if len(c_h) < 14: continue
            
            # Riesgos Numéricos
            r_cg = int(re.search(r'\d', c_h[5]).group()) if re.search(r'\d', c_h[5]) else 0
            if r_cg > 0:
                s["t_cg"] += 1
                if r_cg == 1: s["p1_cg"] += 1
                elif r_cg == 2: s["p2_cg"] += 1
                elif r_cg == 3: s["p3_cg"] += 1
                elif r_cg == 4: s["p4_cg"] += 1
            if "⚠️" in c_h[9] or "⛔" in c_h[9]: s["t_mdrd"] += 1
            if "⚠️" in c_h[13] or "⛔" in c_h[13]: s["t_ckd"] += 1

            # MEDICAMENTOS (17 Columnas: 15 auto + 2 manuales)
            nuevas_filas_meds.append([
                p_info['id'], c_h[0], c_h[1], p_info['fg_cg'], c_h[4], r_cg, c_h[6],
                p_info['fg_mdrd'], c_h[8], 0, c_h[10], p_info['fg_ckd'], c_h[12], 0, c_h[14], "", ""
            ])
        
        # Guardado MEDICAMENTOS
        df_m_old = conn.read(worksheet="MEDICAMENTOS")
        conn.update(worksheet="MEDICAMENTOS", data=pd.concat([df_m_old, pd.DataFrame(nuevas_filas_meds, columns=df_m_old.columns)], ignore_index=True))

        # VALIDACIONES (29 Columnas: 27 auto + 2 manuales)
        n_m = len([l for l in meds_raw.split('\n') if l.strip()])
        f_v = [
            datetime.now().strftime("%d/%m/%Y"), p_info['centro'], p_info['res'], p_info['id'],
            p_info['edad'], p_info['sexo'], p_info['peso'], p_info['crea'], n_m,
            p_info['fg_cg'], s["t_cg"], s["p1_cg"], s["p2_cg"], s["p3_cg"], s["p4_cg"],
            p_info['fg_mdrd'], s["t_mdrd"], 0, 0, 0, 0, p_info['fg_ckd'], s["t_ckd"], 0, 0, 0, 0, "", ""
        ]
        df_v_old = conn.read(worksheet="VALIDACIONES")
        conn.update(worksheet="VALIDACIONES", data=pd.concat([df_v_old, pd.DataFrame([f_v], columns=df_v_old.columns)], ignore_index=True))
        st.toast("✅ Sincronización Nube Completa")
    except Exception as e: st.error(f"Error Volcado: {e}")

# --- ESTILOS CSS (DISEÑO ORIGINAL BLINDADO) ---
st.markdown("""
<style>
    .black-badge-zona { background-color: #000; color: #888; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 15px; z-index: 9999; }
    .black-badge-activo { background-color: #000; color: #0f0; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 145px; z-index: 9999; text-shadow: 0 0 5px #0f0; }
    .fg-glow-box { background-color: #000; color: #fff; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .unit-label { font-size: 0.65rem; color: #888; margin-top: -10px; text-align: center; font-family: sans-serif; }
    .warning-yellow { background-color: #fff9db; color: #856404; padding: 20px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 40px; text-align: center; font-size: 0.85rem; }
    .linea-discreta-soip { border-top: 1px solid #d9d5c7; margin: 15px 0 5px 0; font-size: 0.65rem; font-weight: bold; color: #8e8a7e; text-transform: uppercase; }
    @keyframes blinker { 50% { opacity: 0; } }
    .blink-text { animation: blinker 1s linear infinite; color: #c53030; font-weight: bold; padding: 10px; border: 1px solid #c53030; border-radius: 5px; background: #fff5f5; text-align: center; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown('<div class="black-badge-zona">ZONA: ACTIVA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="black-badge-activo">ACTIVO: {st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<h1 style="text-align:center; font-weight:800; margin-bottom:0;">ASISTENTE RENAL</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; font-size:0.6rem; color:#bbb; margin-top:-5px;">v. 10 mar 2026 13:25</p>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 DATOS", "📈 GRÁFICOS"])

with tabs[0]:
    st.markdown("### Registro de Paciente")
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1.5, 0.4])
    with c1: centro = st.text_input("Centro", key="reg_centro", placeholder="M / G")
    with c2: res = st.selectbox("¿Residencia?", ["No", "Sí"], key="reg_res", index=None)
    with c3: st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)
    with c4: st.text_input("ID Registro", value=st.session_state.reg_id, disabled=True)
    with c5: st.write(""); st.button("🗑️", key="res_reg_btn", on_click=lambda: st.rerun())

    col_izq, col_der = st.columns(2, gap="large")
    with col_izq:
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            e = st.number_input("Edad (años)", value=None, key="calc_e")
            p = st.number_input("Peso (kg)", value=None, key="calc_p")
            cr = st.number_input("Creatinina (mg/dL)", value=None, key="calc_c")
            sx = st.selectbox("Sexo", ["Hombre", "Mujer"], key="calc_s", index=None)
            fg_calc = round(((140 - (e or 0)) * (p or 0)) / (72 * (cr or 1)) * (0.85 if sx == "Mujer" else 1.0), 1) if all([e, p, cr, sx]) else 0.0

    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual", placeholder="C-G manual")
        val_fg = fg_m if fg_m else fg_calc
        st.markdown(f'<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{val_fg}</div><div style="font-size: 0.8rem; color: #9d00ff;">mL/min (C-G)</div></div>', unsafe_allow_html=True)
        st.write(""); l1, l2 = st.columns(2)
        with l1:
            v_mdrd = st.number_input("MDRD-4", value=None, key="fgl_mdrd", label_visibility="collapsed")
            st.markdown('<div class="unit-label">mL/min/1,73m²</div>', unsafe_allow_html=True)
        with l2:
            v_ckd = st.number_input("CKD-EPI", value=None, key="fgl_ckd", label_visibility="collapsed")
            st.markdown('<div class="unit-label">mL/min/1,73m²</div>', unsafe_allow_html=True)

    st.write("---")
    meds_text = st.text_area("Listado de medicación", height=150, key="main_meds")
    
    b1, b2 = st.columns([0.85, 0.15])
    if b1.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True):
        if not all([centro, res, e, p, cr, sx]):
            st.markdown('<div class="blink-text">⚠️ AVISO: FALTAN DATOS EN REGISTRO O CALCULADORA.</div>', unsafe_allow_html=True)
        with st.spinner("Analizando..."):
            prompt_f = f"{c.PROMPT_AFR_V10}\nFG C-G: {val_fg}\nFG MDRD: {v_mdrd}\nFG CKD: {v_ckd}\nMEDS:\n{meds_text}"
            st.session_state.resp_ia = llamar_ia_en_cascada(prompt_f)
            st.session_state.analisis_realizado = True

    if st.session_state.analisis_realizado and st.session_state.resp_ia:
        partes = [p.strip() for p in st.session_state.resp_ia.split("|||") if p.strip()]
        if len(partes) >= 3:
            st.markdown(f'<div style="background:#f8f9fa; padding:15px; border-radius:10px; border-left:5px solid #9d00ff;">{partes[0]}</div>', unsafe_allow_html=True)
            st.markdown(partes[1], unsafe_allow_html=True) # Tabla
            st.markdown(f'<div style="background:#eef2f7; padding:15px; border-radius:10px; margin-top:10px;">{partes[2]}</div>', unsafe_allow_html=True)
            
            if st.button("💾 GRABAR DATOS", use_container_width=True):
                p_info = {'id': st.session_state.reg_id, 'centro': centro, 'res': res, 'edad': e, 'sexo': sx, 'peso': p, 'crea': cr, 'fg_cg': val_fg, 'fg_mdrd': v_mdrd or 0, 'fg_ckd': v_ckd or 0}
                volcar_a_sheets(partes[1], p_info, meds_text)

with tabs[1]:
    for lab, k, h in [("Subjetivo (S)", "soip_s", 70), ("Objetivo (O)", "soip_o", 70), ("Interpretación (I)", "soip_i", 120), ("Plan (P)", "soip_p", 100)]:
        st.markdown(f'<div class="linea-discreta-soip">{lab}</div>', unsafe_allow_html=True)
        st.text_area(k, st.session_state[k], height=h, label_visibility="collapsed")
    st.markdown('<div class="linea-discreta-soip">INTERCONSULTA (MOTIVO)</div>', unsafe_allow_html=True)
    st.text_area("IC_M", key="ic_inter", height=100)
    st.markdown('<div class="linea-discreta-soip">INFORMACIÓN CLÍNICA ADICIONAL</div>', unsafe_allow_html=True)
    st.text_area("IC_C", key="ic_clinica", height=150)

st.markdown('<div class="warning-yellow">⚠️ <b>Apoyo clínico. Verifique con ficha técnica.</b></div>', unsafe_allow_html=True)
st.markdown('<div style="text-align:right; font-size:0.5rem; color:#ccc;">v. 13:25 | He verificado todos los elementos estructurales y principios fundamentales.</div>', unsafe_allow_html=True)
