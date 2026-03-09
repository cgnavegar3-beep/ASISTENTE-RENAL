# v. 09 mar 2026 21:30 (CÓDIGO ÍNTEGRO TOTAL - PE A PA - SIN OMISIONES)
 
import streamlit as st
import pandas as pd
import io
from datetime import datetime
import google.generativeai as genai
import random
import re
import os
from streamlit_gsheets import GSheetsConnection 
import constants as c 
 
# =================================================================
# PRINCIPIOS FUNDAMENTALES (ESCRITOS DE PE A PA - PROHIBIDO ELIMINAR)
# =================================================================
# 1. IDENTIDAD: El nombre "ASISTENTE RENAL" es inalterable.
# 2. VERSIÓN: Mostrar siempre la versión con fecha/hora bajo el título.
# 3. INTERFAZ DUAL PROTEGIDA: Prohibido modificar la "Calculadora" y el 
#     "Filtrado Glomerular" (cuadro negro con glow morado).
# 4. BLINDAJE DE ELEMENTOS (ZONA ESTÁTICA):
#     - Cuadros negros superiores (ZONA y ACTIVO).
#     - Pestañas (Tabs) de navegación.
#     - Registro de Paciente: Estructura y función de fila única.
#     - Estructura del área de recorte y listado de medicación.
#     - Barra dual de validación (VALIDAR / RESET).
#     - Aviso legal amarillo inferior (Warning).
# 5. PROTOCOLO DE CAMBIOS: Antes de cualquier evolución técnica, explicar
#     "qué", "por qué" y "cómo". Esperar aprobación explícita ("adelante").
# 6. COMPROMISO DE RIGOR: Gemini verificará el cumplimiento de estos 
#     principios antes y después de cada cambio. No se simplifican líneas.
# 7. VERSIONADO LOCAL: Registrar la versión en la esquina inferior derecha.
# 8. CONTADOR DISCRETO: El contador de intentos debe ser discreto y 
#     ubicarse en la esquina superior izquierda (estilo v. 2.5).
# 9. INTEGRIDAD DEL CÓDIGO: Nunca omitir estas líneas; de lo contrario, 
#     se considerará pérdida de principios.
# 10. BLINDAJE DE CONTENIDOS: Quedan blindados todos los cuadros de texto,
#      sus textos flotantes (placeholders) y los textos predefinidos en las
#      secciones S, P e INTERCONSULTA. Prohibido borrarlos o simplificarlos.
# 11. AVISO PARPADEANTE: El aviso parpadeante ante falta de datos es un 
#      principio blindado; es informativo y no debe impedir la validación.
# =================================================================
 
st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")
 
# --- INICIALIZACIÓN DE ESTADOS ---
if "active_model" not in st.session_state: st.session_state.active_model = "BUSCANDO..."
if "main_meds" not in st.session_state: st.session_state.main_meds = ""
if "resultado_ia" not in st.session_state: st.session_state.resultado_ia = ""
if "soip_s" not in st.session_state: st.session_state.soip_s = "Revisión farmacoterapéutica según función renal."
if "soip_p" not in st.session_state: st.session_state.soip_p = "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
 
for key in ["soip_o", "soip_i", "ic_inter", "ic_clinica", "reg_id", "reg_centro", "reg_res", "valor_fg_final"]:
    if key not in st.session_state: st.session_state[key] = ""
 
# --- CONFIGURACIÓN IA ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    API_KEY = None
    st.sidebar.error("API Key no encontrada.")
 
# --- LÓGICA DE EXTRACCIÓN PARA GRABADO ---
def extraer_datos_resumen(html_tabla):
    res = {"CONTRA": [0,0,0], "TOX": [0,0,0], "DOSIS": [0,0,0], "PREC": [0,0,0]}
    mapeo = {"Contraindicados": "CONTRA", "toxicidad": "TOX", "ajuste dosis": "DOSIS", "precaucion": "PREC"}
    for texto, key in mapeo.items():
        match = re.search(rf"{texto}.*?<td.*?>(.*?)</td>.*?<td.*?>(.*?)</td>.*?<td.*?>(.*?)</td>", html_tabla, re.I | re.S)
        if match:
            res[key] = [int(re.sub(r'\D', '', match.group(i))) if match.group(i).strip() else 0 for i in range(1, 4)]
    # REGLA: Suma manual para "Total afectados" para corregir errores de la IA
    res["AFEC"] = [sum(res[cat][i] for cat in res) for i in range(3)]
    return res

def llamar_ia_en_cascada(prompt):
    if not API_KEY: return "⚠️ Error: API Key no configurada."
    try:
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        st.session_state.active_model = "1.5-FLASH"
        return model.generate_content(prompt, generation_config={"temperature": 0.1}).text
    except: return "⚠️ Error en la generación."
 
def obtener_glow_class(sintesis_texto):
    if "⛔" in sintesis_texto: return "glow-red"
    elif "⚠️⚠️⚠️" in sintesis_texto: return "glow-orange"
    elif "⚠️⚠️" in sintesis_texto: return "glow-yellow-dark"
    elif "⚠️" in sintesis_texto: return "glow-yellow"
    else: return "glow-green"
 
def procesar_y_limpiar_meds():
    texto = st.session_state.main_meds
    if texto:
        prompt = f"Actúa como farmacéutico clínico. Reescribe este listado: [Principio Activo] + [Dosis] + (Marca). Una línea por fármaco. Sin explicaciones:\n{texto}"
        st.session_state.main_meds = llamar_ia_en_cascada(prompt)
 
def reset_registro():
    for key in ["reg_centro", "reg_res", "reg_id", "fgl_ckd", "fgl_mdrd", "main_meds"]: st.session_state[key] = ""
    for key in ["calc_e", "calc_p", "calc_c", "calc_s"]: 
        if key in st.session_state: st.session_state[key] = None
 
def reset_meds():
    st.session_state.main_meds = ""
    st.session_state.resultado_ia = ""
    st.session_state.soip_s = "Revisión farmacoterapéutica según función renal."
    st.session_state.soip_o = ""; st.session_state.soip_i = ""; st.session_state.soip_p = "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
    st.session_state.ic_inter = ""; st.session_state.ic_clinica = ""
 
def inject_styles():
    st.markdown("""
    <style>
    .block-container { max-width: 100% !important; padding-top: 3.5rem !important; padding-left: 4% !important; padding-right: 4% !important; }
    .black-badge-zona { background-color: #000000; color: #888; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 15px; z-index: 999999; }
    .black-badge-activo { background-color: #000000; color: #00FF00; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 145px; z-index: 999999; text-shadow: 0 0 5px #00FF00; }
    .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin-bottom: 0px; margin-top: 15px; }
    .sub-version { text-align: center; font-size: 0.6rem; color: #bbb; margin-top: -5px; margin-bottom: 20px; font-family: monospace; }
    .fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .unit-label { font-size: 0.65rem; color: #888; margin-top: -10px; margin-bottom: 5px; text-align: center; }
    .synthesis-box { padding: 15px; border-radius: 12px; margin-bottom: 15px; border-width: 2.2px; border-style: solid; font-size: 0.95rem; }
    .glow-red { background-color: #fff5f5; color: #c53030; border-color: #feb2b2; }
    .glow-orange { background-color: #fffaf0; color: #c05621; border-color: #fbd38d; }
    .glow-yellow-dark { background-color: #fff8dc; color: #b36b00; border-color: #ffd27f; }
    .glow-yellow { background-color: #fffff0; color: #975a16; border-color: #faf089; }
    .glow-green { background-color: #f0fff4; color: #2f855a; border-color: #9ae6b4; }
    .table-container { background-color: #e6f2ff; padding: 10px; border-radius: 10px; border: 1px solid #90cdf4; margin-bottom: 15px; overflow-x: auto; }
    .clinical-detail-container { background-color: #e6f2ff; color: #1a365d; padding: 15px; border-radius: 10px; border: 1px solid #90cdf4; font-size: 0.9rem; }
    .warning-yellow { background-color: #fff9db; color: #856404; padding: 20px; border-radius: 10px; text-align: center; font-size: 0.85rem; margin-top: 20px; }
    .linea-discreta-soip { border-top: 1px solid #d9d5c7; margin: 15px 0 5px 0; font-size: 0.65rem; font-weight: bold; color: #8e8a7e; text-transform: uppercase; }
    .fg-special-border { border: 1.5px solid #9d00ff !important; border-radius: 5px; }
    @keyframes blinker { 50% { opacity: 0; } }
    .blink-text { animation: blinker 1s linear infinite; color: #c53030; font-weight: bold; padding: 10px; border: 1px solid #c53030; border-radius: 5px; background: #fff5f5; text-align: center; margin-bottom: 15px; }
    /* BOTÓN GRABAR: CENTRADO, PEQUEÑO Y PARPADEANTE */
    .save-btn-center { display: flex; justify-content: center; margin: 25px 0; }
    div.stButton > button[key="btn_grabar_fgl"] {
        animation: blinker 1.2s linear infinite !important;
        background-color: #2f855a !important;
        color: white !important;
        padding: 6px 22px !important;
        border-radius: 20px !important;
        font-size: 0.8rem !important;
        border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
 
inject_styles()
st.markdown('<div class="black-badge-zona">ZONA: ACTIVA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="black-badge-activo">ACTIVO: {st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-version">v. 09 mar 2026 21:30</div>', unsafe_allow_html=True)
 
tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 DATOS", "📈 GRÁFICOS"])
 
with tabs[0]:
    st.markdown("### Registro de Paciente")
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1.5, 0.4])
    def on_centro_change():
        centro_val = st.session_state.reg_centro.strip().lower()
        if centro_val == "m": st.session_state.reg_centro = "Marín"
        elif centro_val == "o": st.session_state.reg_centro = "O Grove"
        if st.session_state.reg_centro:
            iniciales = "".join([word[0] for word in st.session_state.reg_centro.split()]).upper()[:3]
            st.session_state.reg_id = f"PAC-{iniciales}{random.randint(10000, 99999)}"
 
    with c1: st.text_input("Centro", placeholder="M / G", key="reg_centro", on_change=on_centro_change)
    with c2: st.selectbox("¿Residencia?", ["No", "Sí"], index=None, placeholder="Sí / No", key="reg_res")
    with c3: st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)
    with c4: st.text_input("ID Registro", key="reg_id", disabled=True)
    with c5: st.write(""); st.button("🗑️", on_click=reset_registro, key="btn_clear_reg")
 
    col_izq, col_der = st.columns(2, gap="large")
    with col_izq:
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            calc_e = st.number_input("Edad (años)", step=1, key="calc_e", value=None)
            calc_p = st.number_input("Peso (kg)", key="calc_p", value=None)
            calc_c = st.number_input("Creatinina (mg/dL)", key="calc_c", value=None)
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"], index=None, key="calc_s")
            fg = round(((140 - calc_e) * calc_p) / (72 * (calc_c if calc_c and calc_c > 0 else 1)) * (0.85 if calc_s == "Mujer" else 1.0), 1) if all([calc_e, calc_p, calc_c, calc_s]) else 0.0
 
    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual", placeholder="Cockcroft-Gault manual")
        valor_fg = fg_m if fg_m else fg
        st.session_state.valor_fg_final = valor_fg
        st.markdown(f'''<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{valor_fg}</div><div style="font-size: 0.8rem; color: #9d00ff;">mL/min (C-G)</div></div>''', unsafe_allow_html=True)
        st.write(""); l1, l2 = st.columns(2)
        with l1:
            st.markdown('<div class="fg-special-border">', unsafe_allow_html=True)
            val_mdrd = st.number_input("MDRD-4", value=None, key="fgl_mdrd", label_visibility="collapsed")
            st.markdown('</div><div class="unit-label">mL/min/1,73m²</div>', unsafe_allow_html=True)
        with l2:
            st.markdown('<div class="fg-special-border">', unsafe_allow_html=True)
            val_ckd = st.number_input("CKD-EPI", value=None, key="fgl_ckd", label_visibility="collapsed")
            st.markdown('</div><div class="unit-label">mL/min/1,73m²</div>', unsafe_allow_html=True)
 
    st.write(""); st.markdown("---")
    st.markdown("#### 📝 Listado de medicamentos")
    st.text_area("Listado", height=150, key="main_meds", label_visibility="collapsed")
    st.button("Procesar medicamentos", on_click=procesar_y_limpiar_meds)
    
    b1, b2 = st.columns([0.85, 0.15])
    btn_val = b1.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True)
    b2.button("🗑️ RESET", on_click=reset_meds, use_container_width=True)
 
    if btn_val:
        if not all([st.session_state.reg_centro, st.session_state.reg_res, calc_e, calc_p, calc_c]):
            st.markdown('<div class="blink-text">⚠️ AVISO: FALTAN DATOS EN REGISTRO. EL ANÁLISIS PUEDE SER INCOMPLETO.</div>', unsafe_allow_html=True)
        
        with st.spinner("Analizando..."):
            prompt_final = f"{c.PROMPT_AFR}\n\nFG C-G: {valor_fg}\nFG CKD: {val_ckd}\nFG MDRD: {val_mdrd}\n\nMEDS:\n{st.session_state.main_meds}"
            resp = llamar_ia_en_cascada(prompt_final)
            st.session_state.resultado_ia = resp
            
    if st.session_state.resultado_ia:
        try:
            partes = st.session_state.resultado_ia.split("|||")
            if len(partes) >= 4:
                glow = obtener_glow_class(partes[1])
                st.markdown(f'<div class="synthesis-box {glow}">{partes[1]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="table-container">{partes[2]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="clinical-detail-container">{partes[3]}</div>', unsafe_allow_html=True)
                
                # Sincronización con Informe
                datos_obj = [f"Edad: {calc_e}a", f"Peso: {calc_p}kg", f"Crea: {calc_c}mg/dL", f"FG: {valor_fg}mL/min"]
                st.session_state.soip_o = " | ".join([d for d in datos_obj if d])
                st.session_state.soip_i = partes[1].replace("BLOQUE 1: ALERTAS Y AJUSTES", "").strip()
                st.session_state.ic_inter = f"Se solicita revisión de:\n{st.session_state.soip_i}"
                st.session_state.ic_clinica = f"{st.session_state.soip_o}\n\n{partes[3].replace('BLOQUE 3: ANALISIS CLINICO', '').strip()}"
        except: pass

        # BOTÓN GRABAR: CENTRADO, PEQUEÑO Y PARPADEANTE
        st.markdown('<div class="save-btn-center">', unsafe_allow_html=True)
        if st.button("📥 GRABAR DATOS EN NUBE", key="btn_grabar_fgl"):
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                res = extraer_datos_resumen(st.session_state.resultado_ia)
                nueva_f = {
                    "FECHA": datetime.now().strftime("%d/%m/%Y"), "ID": st.session_state.reg_id,
                    "CENTRO": st.session_state.reg_centro, "RESIDENCIA": st.session_state.reg_res,
                    "EDAD": st.session_state.calc_e, "PESO": st.session_state.calc_p, "CREA": st.session_state.calc_c,
                    "FG_CG": st.session_state.valor_fg_final, "Nº_TOT_AFEC_CG": res["AFEC"][0], "Nº_CONTRAIND_CG": res["CONTRA"][0],
                    "FG_MDRD": st.session_state.fgl_mdrd, "Nº_TOT_AFEC_MDRD": res["AFEC"][1], "Nº_CONTRAIND_MDRD": res["CONTRA"][1],
                    "FG_CKD": st.session_state.fgl_ckd, "Nº_TOT_AFEC_CKD": res["AFEC"][2], "Nº_CONTRAIND_CKD": res["CONTRA"][2]
                }
                df_act = conn.read(worksheet="VALIDACIONES")
                df_final = pd.concat([df_act, pd.DataFrame([nueva_f])], ignore_index=True)
                conn.update(worksheet="VALIDACIONES", data=df_final)
                st.toast("✅ Datos grabados exitosamente.")
            except Exception as e: st.error(f"Error: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="warning-yellow">⚠️ <b>Esta herramienta es de apoyo a la revisión farmacoterapéutica. Verifique siempre con fuentes oficiales.</b></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:right; font-size:0.6rem; color:#ccc; font-family:monospace; margin-top:10px;">v. 09 mar 2026 21:30</div>', unsafe_allow_html=True)

with tabs[1]:
    st.markdown("### 📄 Informe Farmacéutico")
    for label, key, h in [("Subjetivo (S)", "soip_s", 70), ("Objetivo (O)", "soip_o", 70), ("Interpretación (I)", "soip_i", 120), ("Plan (P)", "soip_p", 100)]:
        st.markdown(f'<div class="linea-discreta-soip">{label}</div>', unsafe_allow_html=True)
        st.text_area(key, st.session_state[key], height=h, label_visibility="collapsed")
    
    st.markdown('<div class="linea-discreta-soip">INTERCONSULTA</div>', unsafe_allow_html=True)
    st.text_area("IC_B1", st.session_state.ic_inter, height=150, label_visibility="collapsed")
    st.markdown('<div class="linea-discreta-soip">INFORMACIÓN CLÍNICA</div>', unsafe_allow_html=True)
    st.text_area("IC_B2", st.session_state.ic_clinica, height=250, label_visibility="collapsed")

with tabs[2]:
    st.markdown("### 📊 Espejo de Datos (Google Sheets)")
    sub_tabs = st.tabs(["📋 VALIDACIONES", "📧 INTERCONSULTAS", "📜 HISTÓRICO"])
    with sub_tabs[0]:
        try:
            conn = st.connection("gsheets", type=GSheetsConnection)
            df = conn.read(worksheet="VALIDACIONES")
            st.dataframe(df, use_container_width=True, hide_index=True)
        except: st.info("Cargue la hoja de Google Sheets para visualizar datos.")
    with sub_tabs[1]:
        try:
            df_ic = conn.read(worksheet="INTERCONSULTAS")
            st.dataframe(df_ic, use_container_width=True, hide_index=True)
        except: st.info("Sección de Interconsultas vacía o sin conexión.")
    with sub_tabs[2]: st.write("Histórico de auditoría y actividad general.")
