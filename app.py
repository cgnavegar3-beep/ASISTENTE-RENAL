# v. 07 mar 2026 10:20 (CONTROL DE INTEGRIDAD INTERNO: 248 LÍNEAS)
 
import streamlit as st
import pandas as pd
import io
from datetime import datetime
import google.generativeai as genai
import random
import re
import os
import gspread
from google.oauth2.service_account import Credentials
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
 
# --- INICIALIZACIÓN ---
if "active_model" not in st.session_state: st.session_state.active_model = "BUSCANDO..."
if "main_meds" not in st.session_state: st.session_state.main_meds = ""
if "soip_s" not in st.session_state: st.session_state.soip_s = "Revisión farmacoterapéutica según función renal."
if "soip_p" not in st.session_state: st.session_state.soip_p = "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
 
for key in ["soip_o", "soip_i", "ic_inter", "ic_clinica", "reg_id", "reg_centro", "reg_res"]:
    if key not in st.session_state: st.session_state[key] = ""
 
# --- CONFIGURACIÓN IA ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    API_KEY = None
    st.sidebar.error("API Key no encontrada.")

# --- CONEXIÓN GOOGLE SHEETS ---
def conectar_google_sheets():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(credentials)
        # APUNTAMOS A LA PESTAÑA ESPECÍFICA INDICADA POR EL USUARIO
        sheet = client.open("BD_ASISTENTE_RENAL").worksheet("VALIDACIONES")
        return sheet
    except Exception as e:
        st.error(f"Error de conexión con la pestaña VALIDACIONES: {e}")
        return None

def grabar_datos_db(datos):
    sheet = conectar_google_sheets()
    if sheet:
        try:
            sheet.append_row(datos)
            st.success("✅ Datos grabados correctamente en la pestaña VALIDACIONES.")
        except Exception as e:
            st.error(f"Error al grabar fila: {e}")
 
# --- FUNCIONES ---
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
    st.session_state.soip_s = "Revisión farmacoterapéutica según función renal."
    st.session_state.soip_o = ""; st.session_state.soip_i = ""; st.session_state.soip_p = "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
    st.session_state.ic_inter = ""; st.session_state.ic_clinica = ""
 
def inject_styles():
    st.markdown("""
    <style>
    .block-container { max-width: 100% !important; padding-top: 1rem !important; padding-left: 4% !important; padding-right: 4% !important; }
    .black-badge-zona { background-color: #000000; color: #888; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 15px; z-index: 999999; }
    .black-badge-activo { background-color: #000000; color: #00FF00; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 145px; z-index: 999999; text-shadow: 0 0 5px #00FF00; }
    .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin-bottom: 0px; margin-top: 20px; }
    .sub-version { text-align: center; font-size: 0.6rem; color: #bbb; margin-top: -5px; margin-bottom: 20px; font-family: monospace; }
    .fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .unit-label { font-size: 0.65rem; color: #888; margin-top: -10px; margin-bottom: 5px; font-family: sans-serif; text-align: center; }
    .synthesis-box { padding: 15px; border-radius: 12px; margin-bottom: 15px; border-width: 2.2px; border-style: solid; font-size: 0.95rem; line-height: 1.6; }
    .glow-red { background-color: #fff5f5; color: #c53030; border-color: #feb2b2; box-shadow: 0 0 12px #feb2b2; }
    .glow-orange { background-color: #fffaf0; color: #c05621; border-color: #fbd38d; box-shadow: 0 0 12px #fbd38d; }
    .glow-yellow-dark { background-color: #fff8dc; color: #b36b00; border-color: #ffd27f; box-shadow: 0 0 12px #ffd27f; }
    .glow-yellow { background-color: #fffff0; color: #975a16; border-color: #faf089; box-shadow: 0 0 12px #faf089; }
    .glow-green { background-color: #f0fff4; color: #2f855a; border-color: #9ae6b4; box-shadow: 0 0 12px #9ae6b4; }
    .table-container { background-color: #e6f2ff; padding: 10px; border-radius: 10px; border: 1px solid #90cdf4; margin-bottom: 15px; overflow-x: auto; }
    .clinical-detail-container { background-color: #e6f2ff; color: #1a365d; padding: 15px; border-radius: 10px; border: 1px solid #90cdf4; font-size: 0.9rem; line-height: 1.6; }
    .warning-yellow { background-color: #fff9db; color: #856404; padding: 20px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 40px; text-align: center; font-size: 0.85rem; line-height: 1.5; }
    .linea-discreta-soip { border-top: 1px solid #d9d5c7; margin: 15px 0 5px 0; font-size: 0.65rem; font-weight: bold; color: #8e8a7e; text-transform: uppercase; }
    .formula-label { font-size: 0.6rem; color: #666; font-family: monospace; text-align: right; margin-top: 5px; }
    .fg-special-border { border: 1.5px solid #9d00ff !important; border-radius: 5px; }
    .nota-importante-box { border-top: 2px dashed #0057b8; margin-top: 15px; padding-top: 12px; font-size: 0.85rem; color: #1a365d; }
    .nota-item { margin-bottom: 4px; font-weight: 500; }
    @keyframes blinker { 50% { opacity: 0; } }
    .blink-text { animation: blinker 1s linear infinite; color: #c53030; font-weight: bold; padding: 10px; border: 1px solid #c53030; border-radius: 5px; background: #fff5f5; text-align: center; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)
 
inject_styles()
 
st.markdown('<div class="black-badge-zona">ZONA: ACTIVA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="black-badge-activo">ACTIVO: {st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-version">v. 07 mar 2026 10:20</div>', unsafe_allow_html=True)
 
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
    with c3: st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), disabled=True, placeholder="Fecha")
    with c4: st.text_input("ID Registro", key="reg_id", disabled=True)
    with c5: st.write(""); st.button("🗑️", on_click=reset_registro, key="btn_reset_reg")
 
    col_izq, col_der = st.columns(2, gap="large")
    with col_izq:
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            calc_e = st.number_input("Edad (años)", step=1, key="calc_e", placeholder="Edad (Ej: 65)", value=None)
            calc_p = st.number_input("Peso (kg)", key="calc_p", placeholder="Peso (Ej: 70.5)", value=None)
            calc_c = st.number_input("Creatinina (mg/dL)", key="calc_c", placeholder="Creatinina (Ej: 1.2)", value=None)
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"], index=None, placeholder="Seleccionar sexo...", key="calc_s")
            fg = round(((140 - calc_e) * calc_p) / (72 * (calc_c if calc_c and calc_c > 0 else 1)) * (0.85 if calc_s == "Mujer" else 1.0), 1) if all([calc_e, calc_p, calc_c, calc_s]) else 0.0
 
    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual", placeholder="Fórmula Cockcroft-Gault: entrada manual")
        valor_fg = fg_m if fg_m else fg
        st.markdown(f'''<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{valor_fg}</div><div style="font-size: 0.8rem; color: #9d00ff;">mL/min (C-G)</div></div>''', unsafe_allow_html=True)
        st.markdown('<div class="formula-label">Fórmula Cockcroft-Gault</div>', unsafe_allow_html=True)
        st.write(""); l1, l2 = st.columns(2)
        with l1:
            st.markdown('<div class="fg-special-border">', unsafe_allow_html=True)
            val_mdrd = st.number_input("MDRD-4", value=None, placeholder="MDRD-4", label_visibility="collapsed", key="fgl_mdrd")
            st.markdown('</div><div class="unit-label">mL/min/1,73m²</div>', unsafe_allow_html=True)
        with l2:
            st.markdown('<div class="fg-special-border">', unsafe_allow_html=True)
            val_ckd = st.number_input("CKD-EPI", value=None, placeholder="CKD-EPI", label_visibility="collapsed", key="fgl_ckd")
            st.markdown('</div><div class="unit-label">mL/min/1,73m²</div>', unsafe_allow_html=True)
 
    st.write(""); st.markdown("---")
    m_col1, m_col2 = st.columns([0.5, 0.5])
    with m_col1: st.markdown("#### 📝 Listado de medicamentos")
    with m_col2: st.markdown('<div style="float:right; color:#c53030; font-weight:bold; font-size:0.8rem;">🛡️ RGPD: No datos personales</div>', unsafe_allow_html=True)
    st.text_area("Listado", height=150, label_visibility="collapsed", key="main_meds", placeholder="Pegue el listado de fármacos aquí...")
    st.button("Procesar medicamentos", on_click=procesar_y_limpiar_meds)
    
    b1, b2 = st.columns([0.85, 0.15])
    btn_val = b1.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True)
    b2.button("🗑️ RESET", on_click=reset_meds, use_container_width=True)
 
    if btn_val:
        faltan_datos = not all([st.session_state.reg_centro, st.session_state.reg_res, calc_e, calc_p, calc_c, calc_s])
        if faltan_datos:
            st.markdown('<div class="blink-text">⚠️ AVISO: FALTAN DATOS EN REGISTRO O CALCULADORA. EL ANÁLISIS PUEDE SER INCOMPLETO.</div>', unsafe_allow_html=True)
        
        if not st.session_state.main_meds:
            st.error("Introduce medicamentos.")
        else:
            with st.spinner("Analizando..."):
                prompt_final = f"{c.PROMPT_AFR_V10}\n\nFG C-G: {valor_fg}\nFG CKD: {val_ckd}\nFG MDRD: {val_mdrd}\n\nMEDS:\n{st.session_state.main_meds}"
                resp_raw = llamar_ia_en_cascada(prompt_final)
                resp = resp_raw[resp_raw.find("|||"):] if "|||" in resp_raw else resp_raw
                try:
                    partes = [p.strip() for p in resp.split("|||") if p.strip()]
                    while len(partes) < 3: partes.append("")
                    sintesis, tabla, detalle = partes[:3]
                    glow = obtener_glow_class(sintesis)
                    st.markdown(f'<div class="synthesis-box {glow}">{sintesis.replace("\n","<br>")}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="table-container">{tabla}</div>', unsafe_allow_html=True)
                    st.markdown(f'''<div class="clinical-detail-container">{detalle.replace("\n","<br>")}<div class="nota-importante-box"><div style="font-weight: 800; margin-bottom: 8px;">⚠️ NOTA IMPORTANTE:</div><div class="nota-item">1. Verifique siempre con la ficha técnica oficial (AEMPS/EMA).</div><div class="nota-item">2. Los ajustes propuestos son orientativos según filtrado glomerular actual.</div><div class="nota-item">3. La decisión final corresponde siempre al prescriptor médico.</div><div class="nota-item">4. Considere la situación clínica global del paciente antes de modificar dosis.</div></div></div>''', unsafe_allow_html=True)
                    
                    datos_obj_lista = []
                    if calc_e: datos_obj_lista.append(f"Edad: {calc_e}a")
                    if calc_p: datos_obj_lista.append(f"Peso: {calc_p}kg")
                    if calc_c: datos_obj_lista.append(f"Crea: {calc_c}mg/dL")
                    if valor_fg: datos_obj_lista.append(f"FG: {valor_fg}mL/min")
                    
                    sintesis_limpia = sintesis.replace("BLOQUE 1: ALERTAS Y AJUSTES", "").strip()
                    detalle_limpio = detalle.split("⚠️ NOTA IMPORTANTE:")[0].replace("BLOQUE 3: ANALISIS CLINICO", "").strip()
                    
                    st.session_state.soip_o = " | ".join(datos_obj_lista)
                    st.session_state.soip_i = sintesis_limpia
                    st.session_state.ic_inter = f"Se solicita revisión de los siguientes fármacos:\n{sintesis_limpia}"
                    st.session_state.ic_clinica = f"{st.session_state.soip_o}\n\n{detalle_limpio}"

                    st.divider()
                    if st.button("💾 GRABAR DATOS EN BD", use_container_width=True):
                        fila = [
                            datetime.now().strftime("%d/%m/%Y %H:%M"),
                            st.session_state.reg_id,
                            st.session_state.reg_centro,
                            st.session_state.reg_res,
                            calc_e, calc_p, calc_c, valor_fg, val_mdrd, val_ckd,
                            sintesis_limpia
                        ]
                        grabar_datos_db(fila)

                except Exception as e: st.error(f"Error: {e}")
 
with tabs[1]:
    for label, key, h in [("Subjetivo (S)", "soip_s", 70), ("Objetivo (O)", "soip_o", 70), ("Interpretación (I)", "soip_i", 120), ("Plan (P)", "soip_p", 100)]:
        st.markdown(f'<div class="linea-discreta-soip">{label}</div>', unsafe_allow_html=True)
        st.text_area(key, st.session_state[key], height=h, label_visibility="collapsed", placeholder=f"Contenido de {label}...")
    
    st.markdown('<div class="linea-discreta-soip">INTERCONSULTA</div>', unsafe_allow_html=True)
    st.text_area("IC_B1", st.session_state.ic_inter, height=150, label_visibility="collapsed", placeholder="Se solicita revisión...")
    
    st.markdown('<div class="linea-discreta-soip">INFORMACIÓN CLÍNICA</div>', unsafe_allow_html=True)
    st.text_area("IC_B2", st.session_state.ic_clinica, height=250, label_visibility="collapsed", placeholder="Datos objetivos y análisis clínico...")
 
st.markdown(f"""<div class="warning-yellow">⚠️ <b>Esta herramienta es de apoyo a la revisión farmacoterapéutica. Verifique siempre con fuentes oficiales.</b></div> <div style="text-align:right; font-size:0.6rem; color:#ccc; font-family:monospace; margin-top:10px;">v. 07 mar 2026 10:20</div>""", unsafe_allow_html=True)
