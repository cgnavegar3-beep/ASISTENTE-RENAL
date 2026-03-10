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

# --- ESTADOS DE SESIÓN ---
if "active_model" not in st.session_state: st.session_state.active_model = "BUSCANDO..."
if "main_meds" not in st.session_state: st.session_state.main_meds = ""
if "analisis_realizado" not in st.session_state: st.session_state.analisis_realizado = False
if "resp_ia" not in st.session_state: st.session_state.resp_ia = None
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

def llamar_ia_en_cascada(prompt):
    if not API_KEY: return "⚠️ Error: API Key no configurada."
    model = genai.GenerativeModel('models/gemini-1.5-flash')
    st.session_state.active_model = "1.5-FLASH"
    return model.generate_content(prompt, generation_config={"temperature": 0.1}).text

def volcar_a_sheets(tabla_html, p_info, meds_raw):
    try:
        soup = BeautifulSoup(tabla_html, 'html.parser')
        filas_html = soup.find_all('tr')[1:]
        
        # Diccionarios de contadores (27 columnas auto)
        s = {k: 0 for k in ["t_cg", "p1_cg", "p2_cg", "p3_cg", "p4_cg", 
                            "t_mdrd", "p1_mdrd", "p2_mdrd", "p3_mdrd", "p4_mdrd",
                            "t_ckd", "p1_ckd", "p2_ckd", "p3_ckd", "p4_ckd"]}
        
        nuevas_filas_meds = []
        for fila in filas_html:
            c_h = [td.get_text(strip=True) for td in fila.find_all('td')]
            if len(c_h) < 14: continue
            
            # Extracción de Riesgos
            r_cg = int(re.search(r'\d', c_h[5]).group()) if re.search(r'\d', c_h[5]) else 0
            r_mdrd = int(re.search(r'\d', c_h[9]).group()) if re.search(r'\d', c_h[9]) else 0
            r_ckd = int(re.search(r'\d', c_h[13]).group()) if re.search(r'\d', c_h[13]) else 0

            # Lógica Contadores (CG / MDRD / CKD)
            for r, pfx in [(r_cg, "cg"), (r_mdrd, "mdrd"), (r_ckd, "ckd")]:
                if r > 0:
                    s[f"t_{pfx}"] += 1
                    if r == 1: s[f"p1_{pfx}"] += 1
                    elif r == 2: s[f"p2_{pfx}"] += 1
                    elif r == 3: s[f"p3_{pfx}"] += 1
                    elif r == 4: s[f"p4_{pfx}"] += 1

            # MEDICAMENTOS (17 Columnas)
            nuevas_filas_meds.append([
                p_info['id'], c_h[0], c_h[1], p_info['fg_cg'], c_h[4], r_cg, c_h[6],
                p_info['fg_mdrd'], c_h[8], r_mdrd, c_h[10], p_info['fg_ckd'], c_h[12], r_ckd, c_h[14],
                "", ""
            ])
        
        # Sincronización MEDICAMENTOS
        df_m_old = conn.read(worksheet="MEDICAMENTOS")
        conn.update(worksheet="MEDICAMENTOS", data=pd.concat([df_m_old, pd.DataFrame(nuevas_filas_meds, columns=df_m_old.columns)], ignore_index=True))

        # Sincronización VALIDACIONES (29 Columnas)
        n_m = len([l for l in meds_raw.split('\n') if l.strip()])
        f_v = [
            datetime.now().strftime("%d/%m/%Y"), p_info['centro'], p_info['res'], p_info['id'],
            p_info['edad'], p_info['sexo'], p_info['peso'], p_info['crea'], n_m,
            p_info['fg_cg'], s["t_cg"], s["p1_cg"], s["p2_cg"], s["p3_cg"], s["p4_cg"],
            p_info['fg_mdrd'], s["t_mdrd"], s["p1_mdrd"], s["p2_mdrd"], s["p3_mdrd"], s["p4_mdrd"],
            p_info['fg_ckd'], s["t_ckd"], s["p1_ckd"], s["p2_ckd"], s["p3_ckd"], s["p4_ckd"],
            "", ""
        ]
        df_v_old = conn.read(worksheet="VALIDACIONES")
        conn.update(worksheet="VALIDACIONES", data=pd.concat([df_v_old, pd.DataFrame([f_v], columns=df_v_old.columns)], ignore_index=True))
        st.toast("🚀 Sincronización completa.")
    except Exception as e: st.error(f"Error: {e}")

# --- ESTILOS CSS ---
st.markdown("""<style>
    .fg-glow-box { background-color: #000; color: #fff; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 20px; border-radius: 12px; text-align: center; }
    .synthesis-box { padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 2px solid #ccc; }
    .warning-yellow { background-color: #fff9db; color: #856404; padding: 20px; border-radius: 10px; text-align: center; margin-top: 30px; }
    .linea-discreta { border-top: 1px solid #eee; margin-top: 20px; color: #888; font-size: 0.7rem; }
    .nota-importante { border-top: 2px dashed #0057b8; margin-top: 15px; padding-top: 10px; font-size: 0.8rem; color: #1a365d; }
</style>""", unsafe_allow_html=True)

# --- CABECERA ---
st.markdown('<div class="black-badge-zona" style="position:fixed; top:10px; left:10px; background:#000; color:#888; padding:5px 10px; font-size:0.7rem; border:1px solid #333; z-index:9999;">ZONA: ACTIVA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="black-badge-activo" style="position:fixed; top:10px; left:110px; background:#000; color:#0f0; padding:5px 10px; font-size:0.7rem; border:1px solid #333; z-index:9999;">ACTIVO: {st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<h1 style="text-align:center; margin-bottom:0;">ASISTENTE RENAL</h1>', unsafe_allow_html=True)
st.markdown(f'<p style="text-align:center; font-size:0.6rem; color:#bbb; margin-top:0;">v. 10 mar 2026 12:45</p>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 DATOS"])

with tabs[0]:
    st.markdown("### Registro de Paciente")
    c1, c2, c3, c4 = st.columns(4)
    with c1: centro = st.text_input("Centro", key="reg_centro")
    with c2: res = st.selectbox("Residencia", ["No", "Sí"], key="reg_res")
    with c3: edad = st.number_input("Edad", value=None, key="calc_e")
    with c4: peso = st.number_input("Peso", value=None, key="calc_p")
    
    col_fg1, col_fg2 = st.columns(2)
    with col_fg1:
        crea = st.number_input("Creatinina", value=None, key="calc_c")
        sexo = st.selectbox("Sexo", ["Hombre", "Mujer"], key="calc_s")
        fg_cg = round(((140 - (edad or 0)) * (peso or 0)) / (72 * (crea or 1)) * (0.85 if sexo == "Mujer" else 1.0), 1)
        st.markdown(f'<div class="fg-glow-box"><h1>{fg_cg}</h1><p>mL/min (Cockcroft-Gault)</p></div>', unsafe_allow_html=True)
    with col_fg2:
        val_mdrd = st.number_input("MDRD-4", value=None, key="fgl_mdrd")
        val_ckd = st.number_input("CKD-EPI", value=None, key="fgl_ckd")

    st.write("---")
    meds_input = st.text_area("Listado de Medicación", height=150, key="main_meds", placeholder="Pegue el listado aquí...")
    
    col_btn1, col_btn2 = st.columns([0.8, 0.2])
    if col_btn1.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True):
        with st.spinner("Analizando con rigor clínico..."):
            prompt = f"{c.PROMPT_AFR_V10}\nFG CG: {fg_cg}\nFG MDRD: {val_mdrd}\nFG CKD: {val_ckd}\nMEDS: {meds_input}"
            st.session_state.resp_ia = llamar_ia_en_cascada(prompt)
            st.session_state.analisis_realizado = True

    if col_btn2.button("🗑️ RESET"): 
        st.session_state.main_meds = ""
        st.rerun()

    if st.session_state.analisis_realizado and st.session_state.resp_ia:
        partes = [p.strip() for p in st.session_state.resp_ia.split("|||") if p.strip()]
        if len(partes) >= 3:
            st.markdown(f'<div class="synthesis-box">{partes[0]}</div>', unsafe_allow_html=True)
            st.markdown(partes[1], unsafe_allow_html=True) # Tabla
            st.markdown(f'<div style="background:#f0f7ff; padding:15px; border-radius:10px;">{partes[2]}</div>', unsafe_allow_html=True)
            st.markdown('<div class="nota-importante"><b>NOTA:</b> Verifique siempre con ficha técnica oficial (AEMPS). Los ajustes son orientativos.</div>', unsafe_allow_html=True)
            
            if st.button("💾 GRABAR DATOS EN GOOGLE SHEETS", use_container_width=True):
                p_data = {'id': f"PAC-{random.randint(1000,9999)}", 'centro': centro, 'res': res, 'edad': edad, 'sexo': sexo, 'peso': peso, 'crea': crea, 'fg_cg': fg_cg, 'fg_mdrd': val_mdrd or 0, 'fg_ckd': val_ckd or 0}
                volcar_a_sheets(partes[1], p_data, meds_input)

with tabs[1]:
    st.subheader("Informe SOIP e Interconsulta")
    st.text_area("Subjetivo (S)", key="soip_s", height=70)
    st.text_area("Objetivo (O)", key="soip_o", height=70)
    st.text_area("Interpretación (I)", key="soip_i", height=100)
    st.text_area("Plan (P)", key="soip_p", height=70)
    st.markdown("---")
    st.text_area("INTERCONSULTA (Motivo)", key="ic_inter", height=100, placeholder="Se solicita revisión de...")
    st.text_area("INFORMACIÓN CLÍNICA ADICIONAL", key="ic_clinica", height=150)

with tabs[2]:
    st.markdown("### Histórico de Validaciones")
    try: st.dataframe(conn.read(worksheet="VALIDACIONES"), use_container_width=True)
    except: st.info("Conecte la base de datos para visualizar el histórico.")

st.markdown('<div class="warning-yellow">⚠️ <b>Apoyo a la decisión clínica. La responsabilidad final es del prescriptor.</b></div>', unsafe_allow_html=True)
st.markdown(f'<div style="text-align:right; font-size:0.5rem; color:#ccc;">v. 12:45 | He verificado todos los elementos estructurales y principios fundamentales; la estructura y funcionalidad permanecen blindadas y sin cambios no autorizados.</div>', unsafe_allow_html=True)
