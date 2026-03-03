# v. 03 mar 2026 11:30 (Evolución: Prompt V10 Refinado con Metformina y Tabla Filtrada)

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

# --- CONSTANTES (PROMPT ACTUALIZADO SEGÚN REQUERIMIENTO) ---
PROMPT_AFR_V10 = r"""Actúa como un Algoritmo Experto en Farmacoterapéutica Renal (AFR-V10).
[INSTRUCCIÓN DE SEGURIDAD: VERIFICA ESTRICTAMENTE LA ESTRUCTURA DE 3 BLOQUES SEPARADOS POR "|||". NO AÑADAS TEXTO FUERA DE ELLOS.]

Analiza la lista de medicamentos según los filtrados glomerulares proporcionados.
Usa exclusivamente ficha técnica oficial (AEMPS, EMA, FDA). NO inventar. NO inferir. NO extrapolar.
Cockcroft-Gault es la referencia principal.

---------------------------------------------------------------------
CATEGORIZACIÓN OBLIGATORIA:
⛔ Contraindicado | Riesgo: crítico| Nivel de riesgo: 4
Palabras clave: avoid use, contraindicado, contraindicated, CrCl < X contraindicated, discontinue if renal function < X, do not administer, do not use, must not be used, no administrar, no debe utilizarse, no usar, prohibido, severe renal impairment contraindicated, should not be used, use is contraindicated

⚠️⚠️⚠️ Requiere ajuste por riesgo de toxicidad | Riesgo: grave | Nivel de riesgo: 3
Palabras clave: acidosis láctica, accumulation, acumulación, alto riesgo de acumulación, avoid high doses, cardiotoxicidad, depresión respiratoria, do not exceed, dose must be reduced, dosis máxima, hemorragia grave, high risk of accumulation, hiperpotasemia severa, increase dosing interval to avoid toxicity, increased risk of serious adverse reactions, limit dose, maximum dose, nefrotoxicidad, neurotoxicidad, no exceder dosis, reduce dose by %, reduce dose by 50% or more, reduce dose significantly, reduce dose substantially, reduce initial dose, reducir dosis significativamente, requires major dose adjustment, requires strict adjustment, riesgo de acumulación, riesgo de toxicidad, risk of serious adverse effects, risk of toxicity increased, significant dose reduction required, toxicidad, toxicidad orgánica

⚠️⚠️ Requiere ajuste de dosis o intervalo | Riesgo: moderado| Nivel de riesgo: 2
Palabras clave: adjust dose, adjust dose to maintain effect, adjust dosage, adjust dosing interval, ajustar dosis, ajuste renal, consider dose adjustment, dose adjustment recommended, dose adjustment required, efecto terapéutico reducido, efectos adversos leves o moderados, ESPACIAR DOSIS, increase dosing interval, increased exposure without severe toxicity, loss of efficacy, maximum dose limit, may be less effective, modify dose, modificar intervalo, reduced efficacy, reduce dose, reducir dosis, renal dose adjustment, requiere ajuste, requires adjustment

⚠️ Precaución / monitorización | Riesgo: leve | Nivel de riesgo: 1
Palabras clave: careful monitoring recommended, caution, monitor creatinine, monitor potassium, monitor renal function, monitorizar, monitorizar función renal, no adjustment required but caution, precaution, precaución, renal function should be monitored, sin instrucciones concreatas de ajuste, use with caution, usar con precaución, vigilar función renal

✅ No requiere ajuste | Nivel de riesgo: 0
Palabras clave: no adjustment required, no clinically relevant change, no dosage adjustment needed, no dose adjustment necessary, no renal adjustment needed, no requiere ajuste, safe in renal impairment, sin ajuste, sin ajuste renal

---------------------------------------------------------------------
SALIDA OBLIGATORIA (3 BLOQUES SEPARADOS POR '|||')

|||
BLOQUE 1: ALERTAS Y AJUSTES
🔍 Medicamentos afectados:
• Cada medicamento en LÍNEA INDEPENDIENTE con su icono.
• Solo saltos de línea reales. NO "\n" literal.
• Formato: [ICONO] Medicamento — Categoría — "Frase literal" (Fuente)
Ejemplo: ⚠️ Metformina — Requiere ajuste de dosis — "TFG 45-59 ml/min: la dosis máxima diaria es 2000 mg." (AEMPS)

|||
BLOQUE 2: TABLA COMPARATIVA
Mostrar tabla HTML solo con medicamentos afectados (EXCLUIR categorizados con ✅).
<table style="width:100%; border-collapse: collapse; font-size: 0.8rem;">
<tr style="background-color: #0057b8; color: white;">
<th>Icono</th><th>Fármaco</th><th>Grupo ATC</th><th>C-G FG</th><th>C-G Cat</th><th>C-G Riesgo</th><th>CKD-EPI</th><th>MDRD-4</th>
</tr>
[Filas de medicamentos afectados]
</table>

|||
BLOQUE 3: ANALISIS CLINICO
A continuación se detallan los ajustes:
• Cada medicamento en LÍNEA INDEPENDIENTE con su icono.
Ejemplo: ⚠️ Metformina: Ajuste posológico recomendado — Reducir dosis a 500 mg/12h. Motivo: FG 45 ml/min → riesgo de acumulación y posibles efectos adversos. (AEMPS)
|||
"""

st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

# --- INICIALIZACIÓN ---
if "active_model" not in st.session_state: st.session_state.active_model = "BUSCANDO..."
if "main_meds" not in st.session_state: st.session_state.main_meds = ""
for key in ["soip_s", "soip_o", "soip_i", "soip_p", "ic_motivo", "ic_info", "reg_id", "reg_centro", "calc_e", "calc_p", "calc_c", "calc_s", "reg_res"]:
    if key not in st.session_state: st.session_state[key] = None

# --- IA ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    API_KEY = None

def llamar_ia_en_cascada(prompt):
    if not API_KEY: return "⚠️ Error: API Key no configurada."
    disponibles = [m.name.replace('models/', '').replace('gemini-', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    for mod_name in ['2.5-flash', 'flash-latest', '1.5-pro']:
        if mod_name in disponibles:
            try:
                st.session_state.active_model = mod_name.upper()
                return genai.GenerativeModel(f'models/gemini-{mod_name}').generate_content(prompt, generation_config={"temperature": 0.1}).text
            except: continue
    return "⚠️ Error."

def obtener_glow_class(sintesis_texto):
    if "⛔" in sintesis_texto: return "glow-red"
    if "⚠️⚠️⚠️" in sintesis_texto: return "glow-orange"
    if "⚠️⚠️" in sintesis_texto: return "glow-yellow-dark"
    if "⚠️" in sintesis_texto: return "glow-yellow"
    return "glow-green"

# --- UI STYLE ---
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
.synthesis-box { padding: 15px; border-radius: 12px; margin-bottom: 15px; border-width: 2.2px; border-style: solid; font-size: 0.95rem; line-height: 1.6; }
.glow-red { background-color: #fff5f5; color: #c53030; border-color: #feb2b2; box-shadow: 0 0 12px #feb2b2; }
.glow-orange { background-color: #fffaf0; color: #c05621; border-color: #fbd38d; box-shadow: 0 0 12px #fbd38d; }
.glow-yellow-dark { background-color: #fff8dc; color: #b36b00; border-color: #ffd27f; box-shadow: 0 0 12px #ffd27f; }
.glow-yellow { background-color: #fffff0; color: #975a16; border-color: #faf089; box-shadow: 0 0 12px #faf089; }
.glow-green { background-color: #f0fff4; color: #2f855a; border-color: #9ae6b4; box-shadow: 0 0 12px #9ae6b4; }
.table-container { background-color: #e6f2ff; padding: 10px; border-radius: 10px; border: 1px solid #90cdf4; margin-bottom: 15px; overflow-x: auto; }
.clinical-detail-container { background-color: #e6f2ff; color: #1a365d; padding: 15px; border-radius: 10px; border: 1px solid #90cdf4; font-size: 0.9rem; line-height: 1.6; }
.warning-yellow { background-color: #fff9db; color: #856404; padding: 20px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 40px; text-align: center; font-size: 0.85rem; }
.formula-label { font-size: 0.6rem; color: #666; font-family: monospace; text-align: right; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="black-badge-zona">ZONA: ACTIVA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="black-badge-activo">ACTIVO: {st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-version">v. 03 mar 2026 11:30</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 DATOS", "📈 GRÁFICOS"])

with tabs[0]:
    st.markdown("### Registro de Paciente")
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1.5])
    with c1: st.text_input("Centro", key="reg_centro")
    with c2: st.selectbox("¿Residencia?", ["No", "Sí"], key="reg_res")
    with c3: st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)
    with c4: st.text_input("ID Registro", key="reg_id")
    
    col_izq, col_der = st.columns(2, gap="large")
    with col_izq:
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            calc_e = st.number_input("Edad", key="calc_e_input")
            calc_p = st.number_input("Peso", key="calc_p_input")
            calc_c = st.number_input("Creatinina", key="calc_c_input")
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"], key="calc_s_input")
            fg = round(((140 - calc_e) * calc_p) / (72 * (calc_c if calc_c > 0 else 1)) * (0.85 if calc_s == "Mujer" else 1.0), 1) if all([calc_e, calc_p, calc_c]) else 0.0

    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual", placeholder="C-G manual")
        valor_fg = fg_m if fg_m else fg
        st.markdown(f'''<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{valor_fg}</div><div style="font-size: 0.8rem; color: #9d00ff;">mL/min (C-G)</div></div>''', unsafe_allow_html=True)
        st.markdown('<div class="formula-label">Fórmula Cockcroft-Gault</div>', unsafe_allow_html=True)

    st.markdown("#### 📝 Listado de medicamentos")
    st.text_area("Listado", height=100, label_visibility="collapsed", key="main_meds")
    
    if st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True):
        placeholder_salida = st.empty()
        with st.spinner("Analizando..."):
            prompt_final = f"{PROMPT_AFR_V10}\n\nFG C-G: {valor_fg}\nMEDICAMENTOS:\n{st.session_state.main_meds}"
            resp = llamar_ia_en_cascada(prompt_final)
            try:
                partes = [p.strip() for p in resp.split("|||") if p.strip()]
                sintesis, tabla_html, detalle = partes[:3]
                
                # Formateo de líneas para visualización
                sintesis_html = sintesis.replace("\n", "<br>")
                detalle_html = detalle.replace("\n", "<br>")
                glow = obtener_glow_class(sintesis)
                
                with placeholder_salida.container():
                    st.markdown(f'<div class="synthesis-box {glow}">{sintesis_html}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="table-container">{tabla_html}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="clinical-detail-container">{detalle_html}</div>', unsafe_allow_html=True)
            except: st.error("Error en formato de respuesta.")

st.markdown(f"""<div class="warning-yellow">⚠️ <b>Herramienta de apoyo. Verifique con fuentes oficiales.</b></div> <div style="text-align:right; font-size:0.6rem; color:#ccc; font-family:monospace;">v. 03 mar 2026 11:30</div>""", unsafe_allow_html=True)
