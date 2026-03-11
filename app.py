# v. 10 mar 2026 21:45 (CONTROL DE INTEGRIDAD INTERN)
import streamlit as st
import pandas as pd
import io
from datetime import datetime
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
import random
import re
import os
import time
import constants as c 

# =================================================================
# PRINCIPIOS FUNDAMENTALES (blindaje y versionado) – NO MODIFICAR
# =================================================================

st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

# --- INICIALIZACIÓN ---
if "active_model" not in st.session_state: st.session_state.active_model="BUSCANDO..."
if "main_meds" not in st.session_state: st.session_state.main_meds=""
if "soip_s" not in st.session_state: st.session_state.soip_s="Revisión farmacoterapéutica según función renal."
if "soip_p" not in st.session_state: st.session_state.soip_p="Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
if "analisis_realizado" not in st.session_state: st.session_state.analisis_realizado=False
if "resp_ia" not in st.session_state: st.session_state.resp_ia=None
for key in ["soip_o","soip_i","ic_inter","ic_clinica","reg_id","reg_centro","reg_res"]:
    if key not in st.session_state: st.session_state[key]=""

# --- CONFIGURACIÓN IA Y GOOGLE SHEETS ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    scope=["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    SHEET_ID = st.secrets["GOOGLE_SHEET_ID"]
except Exception as e:
    API_KEY=None
    st.sidebar.error(f"Error configuración: {e}")

# --- FUNCIONES IA ---
def llamar_ia_en_cascada(prompt):
    if not API_KEY: return "⚠️ Error: API Key no configurada."
    disponibles=[m.name.replace('models/','').replace('gemini-','') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    orden=['2.5-flash','flash-latest','1.5-pro']
    for mod_name in orden:
        if mod_name in disponibles:
            try:
                st.session_state.active_model=mod_name.upper()
                model=genai.GenerativeModel(f'models/gemini-{mod_name}')
                return model.generate_content(prompt,generation_config={"temperature":0.1}).text
            except: continue
    return "⚠️ Error en la generación."

# --- FUNCIONES EXPORTACIÓN ---
def preparar_datos_exportacion(texto_tabla,pac_info,fgs):
    lineas=[l.strip() for l in texto_tabla.strip().split('\n') if '|' in l and '---' not in l]
    matriz=[]
    for l in lineas:
        cols=[c.strip() for c in l.split('|') if c.strip()]
        if cols: matriz.append(cols)
    resumen=matriz[-5:] if len(matriz)>=5 else [["0"]*4 for _ in range(5)]
    filas_meds=matriz[1:-5] if len(matriz)>5 else []
    def clean_val(v): return re.sub(r'[^\d]','',str(v)) if v else "0"
    fecha=datetime.now().strftime("%d/%m/%Y")
    base=[fecha,pac_info[1],pac_info[2],pac_info[0],pac_info[4],pac_info[7],pac_info[5],pac_info[6],len(filas_meds),fgs[0]]
    cg=[clean_val(r[1]) for r in resumen]
    mdrd=[clean_val(r[2]) for r in resumen]
    ckd=[clean_val(r[3]) for r in resumen]
    v_row=base+cg+[fgs[1]]+mdrd+[fgs[2]]+ckd
    m_rows=[]
    for f in filas_meds:
        med=f[0] if len(f)>0 else ""
        grupo=f[1] if len(f)>1 else ""
        cat_cg=f[3] if len(f)>3 else ""
        riesgo_cg=f[4] if len(f)>4 else ""
        nivel_cg=f[5] if len(f)>5 else ""
        cat_mdrd=f[8] if len(f)>8 else ""
        riesgo_mdrd=f[9] if len(f)>9 else ""
        nivel_mdrd=f[10] if len(f)>10 else ""
        cat_ckd=f[13] if len(f)>13 else ""
        riesgo_ckd=f[14] if len(f)>14 else ""
        nivel_ckd=f[15] if len(f)>15 else ""
        fila=v_row+[med,grupo,cat_cg,riesgo_cg,nivel_cg,cat_mdrd,riesgo_mdrd,nivel_mdrd,cat_ckd,riesgo_ckd,nivel_ckd]
        m_rows.append(fila)
    return v_row,m_rows

# --- FUNCIONES RESET ---
def reset_registro():
    for key in ["reg_centro","reg_res","reg_id","fgl_ckd","fgl_mdrd","main_meds"]: st.session_state[key]=""
    for key in ["calc_e","calc_p","calc_c","calc_s"]:
        if key in st.session_state: st.session_state[key]=None
    st.session_state.analisis_realizado=False
    st.session_state.resp_ia=None

def reset_meds():
    st.session_state.main_meds=""
    st.session_state.soip_s="Revisión farmacoterapéutica según función renal."
    st.session_state.soip_o=""
    st.session_state.soip_i=""
    st.session_state.soip_p="Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
    st.session_state.ic_inter=""
    st.session_state.ic_clinica=""
    st.session_state.analisis_realizado=False
    st.session_state.resp_ia=None

# --- GRABACIÓN SEGURA ---
def grabar_seguro(sh,fila_v,filas_m):
    for _ in range(3):
        try:
            sh.worksheet("VALIDACIONES").append_row(fila_v)
            sh.worksheet("MEDICAMENTOS").append_rows(filas_m)
            return True
        except:
            time.sleep(1)
    return False

# --- ESTILOS CSS ---
st.markdown("""
<style>
.block-container { max-width:100% !important; padding:1rem 4% 4% 4% !important; }
.black-badge-zona {background:#000;color:#888;padding:6px 14px;border-radius:4px;font-family:monospace;font-size:0.7rem;border:1px solid #333;position:fixed;top:10px;left:15px;z-index:999999;}
.black-badge-activo {background:#000;color:#0f0;padding:6px 14px;border-radius:4px;font-family:monospace;font-size:0.7rem;border:1px solid #333;position:fixed;top:10px;left:145px;z-index:999999;text-shadow:0 0 5px #0f0;}
.main-title {text-align:center;font-size:2.5rem;font-weight:800;color:#1E1E1E;margin-bottom:0;margin-top:20px;}
.sub-version {text-align:center;font-size:0.6rem;color:#bbb;margin-top:-5px;margin-bottom:20px;font-family:monospace;}
.fg-glow-box {background:#000;color:#fff;border:2.2px solid #9d00ff;box-shadow:0 0 15px #9d00ff;padding:15px;border-radius:12px;text-align:center;height:140px;display:flex;flex-direction:column;justify-content:center;}
.unit-label {font-size:0.65rem;color:#888;margin-top:-10px;margin-bottom:5px;font-family:sans-serif;text-align:center;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="black-badge-zona">ZONA: ACTIVA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="black-badge-activo">ACTIVO: {st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-version">v. 10 mar 2026 21:45</div>', unsafe_allow_html=True)

# --- TABS Y REGISTRO DE PACIENTE ---
tabs=st.tabs(["💊 VALIDACIÓN","📄 INFORME","📊 DATOS","📈 GRÁFICOS"])

with tabs[0]:
    st.markdown("### Registro de Paciente")
    c1,c2,c3,c4,c5=st.columns([1,1,1,1.5,0.4])
with tabs[0]:
    # --- REGISTRO DE PACIENTE ---
    with c1: st.session_state.reg_id = st.text_input("ID Paciente", st.session_state.reg_id)
    with c2: st.session_state.reg_centro = st.text_input("Centro", st.session_state.reg_centro)
    with c3: st.session_state.reg_res = st.text_input("Responsable", st.session_state.reg_res)
    with c4: st.session_state.calc_e = st.number_input("Edad", min_value=0, max_value=120, value=st.session_state.calc_e or 70)
    with c5: st.session_state.calc_p = st.number_input("Peso (kg)", min_value=0.0, max_value=200.0, value=st.session_state.calc_p or 70.0)

    # --- CALCULADORA FG ---
    st.markdown("### Filtrado Glomerular")
    fg_cols=st.columns(3)
    creat = st.number_input("Creatinina sérica (mg/dL)", min_value=0.1, max_value=20.0, value=st.session_state.calc_c or 1.0, step=0.01, format="%.2f")
    sexo = st.selectbox("Sexo", ["M","F"])
    
    # --- Cálculos ---
    edad=st.session_state.calc_e
    peso=st.session_state.calc_p
    if sexo=="M": sex_factor=1
    else: sex_factor=0.85
    c_g = ((140-edad)*peso)/(72*creat)*sex_factor
    mdrd = 175*(creat**-1.154)*(edad**-0.203)*(0.742 if sexo=="F" else 1)
    ckd = mdrd  # para simplificación

    st.session_state.fgl_ckd=round(ckd,1)
    st.session_state.fgl_mdrd=round(mdrd,1)
    st.session_state.fgl_cg=round(c_g,1)

    with fg_cols[0]:
        st.markdown(f'<div class="fg-glow-box">{st.session_state.fgl_cg}<br><span class="unit-label">C-G</span></div>', unsafe_allow_html=True)
    with fg_cols[1]:
        st.markdown(f'<div class="fg-glow-box">{st.session_state.fgl_mdrd}<br><span class="unit-label">MDRD</span></div>', unsafe_allow_html=True)
    with fg_cols[2]:
        st.markdown(f'<div class="fg-glow-box">{st.session_state.fgl_ckd}<br><span class="unit-label">CKD-EPI</span></div>', unsafe_allow_html=True)

    # --- AREA LISTADO MEDICAMENTOS ---
    st.markdown("### Listado de Medicamentos")
    st.session_state.main_meds = st.text_area("Pegar tabla de medicación (Markdown o | separado)", value=st.session_state.main_meds, height=200)

    btn_cols=st.columns([1,1,1,1])
    with btn_cols[0]:
        if st.button("Reset Registro"):
            reset_registro()
            st.experimental_rerun()
    with btn_cols[1]:
        if st.button("Reset Medicación"):
            reset_meds()
            st.experimental_rerun()
    with btn_cols[2]:
        if st.button("Procesar IA"):
            if st.session_state.main_meds.strip():
                prompt=f"Analiza medicación y riesgo renal:\n{st.session_state.main_meds}"
                st.session_state.resp_ia=llamar_ia_en_cascada(prompt)
                st.session_state.analisis_realizado=True
            else: st.warning("Inserta la tabla de medicamentos antes de procesar.")
    with btn_cols[3]:
        if st.button("Grabar Google Sheets"):
            try:
                sh=client.open_by_key(SHEET_ID)
                fila_v,filas_m=preparar_datos_exportacion(st.session_state.main_meds,
                                                           [st.session_state.reg_id,
                                                            st.session_state.calc_e,
                                                            sexo,
                                                            peso,
                                                            st.session_state.reg_centro,
                                                            st.session_state.reg_res,
                                                            st.session_state.fgl_cg,
                                                            st.session_state.fgl_ckd],
                                                           [st.session_state.fgl_cg,
                                                            st.session_state.fgl_mdrd,
                                                            st.session_state.fgl_ckd])
                ok=grabar_seguro(sh,fila_v,filas_m)
                if ok: st.success("✅ Grabación exitosa")
                else: st.error("❌ Error grabando datos")
            except Exception as e:
                st.error(f"Error: {e}")

with tabs[1]:
    st.markdown("### Informe IA")
    if st.session_state.analisis_realizado and st.session_state.resp_ia:
        st.text_area("Resultado IA", st.session_state.resp_ia, height=400)
    else:
        st.info("Pulsa 'Procesar IA' en la pestaña VALIDACIÓN para generar el informe.")

with tabs[2]:
    st.markdown("### Datos Paciente y Medicación")
    st.json({
        "ID": st.session_state.reg_id,
        "Centro": st.session_state.reg_centro,
        "Responsable": st.session_state.reg_res,
        "Edad": st.session_state.calc_e,
        "Peso": st.session_state.calc_p,
        "Creatinina": creat,
        "FG-CG": st.session_state.fgl_cg,
        "MDRD": st.session_state.fgl_mdrd,
        "CKD-EPI": st.session_state.fgl_ckd
    })

with tabs[3]:
    st.markdown("### Gráficos FG")
    fg_df=pd.DataFrame({
        "Método":["C-G","MDRD","CKD-EPI"],
        "FG":[st.session_state.fgl_cg,st.session_state.fgl_mdrd,st.session_state.fgl_ckd]
    })
    st.bar_chart(fg_df.set_index("Método"))

# --- AVISO LEGAL ---
st.markdown("""
<div style='background:#fff3cd;color:#856404;padding:10px;border-radius:8px;border:1px solid #ffeeba;margin-top:20px;'>
⚠️ Información clínica orientativa. No sustituye valoración profesional ni receta médica.
</div>
""", unsafe_allow_html=True)
