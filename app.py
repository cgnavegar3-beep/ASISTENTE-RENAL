# v. 22 feb 17:15
import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai

# =================================================================
# # PRINCIPIOS FUNDAMENTALES:
# #
# 1. NUNCA BORRAR NI MODIFICAR ESTA CLÁUSULA. 
# #
# 2. No puedes mover nada, ni cambiar ni una sola línea de la estructura 
# #
#    visual (RIGOR Y SERIEDAD). Cero modificaciones sin autorización.
# #
# 3. Antes de cualquier evolución técnica, explicar el "qué", "por qué" 
# #
#    y "cómo", y esperar aprobación ("adelante" o "procede").
# #
# #
# I. ESTRUCTURA VISUAL PROTEGIDA:
# #
#    1. Cuadros negros superiores (ZONA y ACTIVO).
# #
#    2. Título "ASISTENTE RENAL" y Versión inmediatamente debajo (Blindado).
# #
#    2. Título principal y pestañas (Tabs).
# #
#    3. Registro de paciente y función: TODO EN UNA LÍNEA (Centro, Edad, ID Alfa, 
# #
#       Res, Fecha + Botón Borrado Registro).
# #
#    4. Interfaz Dual (Calculadora y caja de FG (Purple Glow): lógica Cockcroft-Gault.
# #
#       -> REFUERZO: NO SE TOCA LA CALCULADORA, NO SE TOCA EL GLOW MORADO.
# #
#    5. Layout Medicamentos: Título y Aviso RGPD (estilo ampliado) en la misma línea.
# #
#    6. Cuadro de listado de medicamentos (TextArea).
# #
#    7. Barra dual de botones (VALIDAR / RESET TOTAL) y Reset de Registro.
# #
#    8. Aviso amarillo de apoyo legal inferior.
# #
# #
# II. FUNCIONALIDADES CRÍTICAS PROTEGIDAS:
# #
#    1. Cascada de Modelos (2.5 Flash > 1.5 Pro > Otros).
# #
#    2. Detección dinámica de modelos vivos en la cuenta.
# #
#    3. Actualización de feedback neón en tiempo real (Badge ACTIVO).
# #
# #
# III. BLINDAJE DEL BLOQUE AZUL (blue-detail-container):
# #
#    - Prohibición de Fragmentación: Detalle y Nota en el mismo div CSS.
# #
#    - Estilo Fijo: Fondo (#f0f7ff), borde (#bee3f8).
# #
#    - NOTA IMPORTANTE: Texto estático (4 puntos) en negrita y azul intenso (Blindado).
# #
# #
# IV. BLINDAJE DE SÍNTESIS DINÁMICA (Glow System):
# #
#    - Formato Rígido: Solo se permite "Medicamentos afectados:" o "Fármacos correctamente dosificados".
# #
#    - Prohibición Textual: No pueden aparecer las palabras "SÍNTESIS", "DETALLE" o similares.
# #
#    - Regla de Iconos: [Icono] + [Nombre] + [Frase corta]. Prohibido texto adicional.
# #
#    - Lógica de Color (Glow): 
# #
#       * Sin iconos = Verde (glow-green).
# #
#       * Con ⚠️ = Naranja (glow-orange).
# #
#       * Con ⛔ = Rojo (glow-red).
# #
# #
# V. PROTECCIÓN INTEGRAL PESTAÑA 1 (💊 VALIDACIÓN):
# #
#    - Blindaje Total: Prohibida cualquier modificación en el layout, orden de columnas o funciones de la Pestaña 1.
# #
#    - Componentes Congelados: Registro de paciente (fila única), Calculadora dual (Glow morado), Área de texto y Botonera (Validar/Reset).
# #
#    - Lógica Funcional: El sistema de callbacks y el prompt de IA de esta pestaña no admiten cambios de sintaxis.
# =================================================================

st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

# Persistencia Pestaña 2
if "soip_s" not in st.session_state: st.session_state.soip_s = ""
if "soip_o" not in st.session_state: st.session_state.soip_o = ""
if "soip_i" not in st.session_state: st.session_state.soip_i = ""
if "soip_p" not in st.session_state: st.session_state.soip_p = ""
if "ic_motivo" not in st.session_state: st.session_state.ic_motivo = ""
if "ic_info" not in st.session_state: st.session_state.ic_info = ""

def reset_registro():
    st.session_state["reg_centro"] = ""; st.session_state["reg_edad"] = None
    st.session_state["reg_id"] = ""; st.session_state["reg_res"] = "No"

def reset_meds():
    st.session_state["main_meds"] = ""; st.rerun()

if 'active_model' not in st.session_state: st.session_state.active_model = "ESPERANDO..."

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except: API_KEY = None

def llamar_ia(prompt):
    try:
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        st.session_state.active_model = "1.5-FLASH"
        return model.generate_content(prompt).text
    except: return "⚠️ Error."

st.markdown("""
<style>
    .block-container { padding-top: 2rem !important; }
    .availability-badge { background-color: #000; color: #888; padding: 4px 10px; border-radius: 3px; font-family: monospace; font-size: 0.65rem; position: fixed; top: 15px; left: 15px; border: 1px solid #333; }
    .model-badge { background-color: #000; color: #00FF00; padding: 4px 10px; border-radius: 3px; font-family: monospace; font-size: 0.75rem; position: fixed; top: 15px; left: 200px; box-shadow: 0 0 5px #00FF0033; }
    .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin-bottom: 0px; }
    .sub-version { text-align: center; font-size: 0.8rem; color: #666; margin-top: -10px; margin-bottom: 20px; }
    .id-display { color: #666; font-family: monospace; font-size: 0.85rem; margin-top: -5px; margin-bottom: 20px; }
    .fg-glow-box { background-color: #000; color: #FFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .rgpd-inline { background-color: #fff5f5; color: #c53030; padding: 8px 16px; border-radius: 8px; border: 1.5px solid #feb2b2; font-size: 0.85rem; float: right; }
    .synthesis-box { padding: 15px; border-radius: 12px; margin-bottom: 15px; border-width: 2px; border-style: solid; }
    .glow-green { background-color: #f1f8e9; color: #2e7d32; border-color: #a5d6a7; }
    .glow-orange { background-color: #fff3e0; color: #e65100; border-color: #ffcc80; }
    .glow-red { background-color: #fff5f5; color: #c53030; border-color: #feb2b2; }
    .blue-detail-container { background-color: #f0f7ff; color: #2c5282; padding: 20px; border-radius: 10px; border: 1px solid #bee3f8; }
    .nota-line { border-top: 2px solid #aec6cf; margin-top: 15px; padding-top: 15px; font-weight: 700; color: #003366; }
    .linea-discreta-soip { border-top: 1px solid #d9d5c7; font-size: 0.65rem; font-weight: bold; color: #8e8a7e; text-transform: uppercase; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="availability-badge">ZONA: CLÍNICA</div>', unsafe_allow_html=True)
st.markdown(f'<div class="model-badge">{st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-version">v. 22 feb 17:15</div>', unsafe_allow_html=True)

tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 EXCEL", "📈 GRÁFICOS"])

with tabs[0]:
    st.markdown("### Registro de Paciente")
    r1, r2, r3, r4, r5, r6 = st.columns([1,1,1,1,1,0.4])
    with r1: centro = st.text_input("Centro", placeholder="G/M", key="reg_centro")
    with r2: edad_reg = st.number_input("Edad", value=None, placeholder="Años", key="reg_edad")
    with r3: alfa = st.text_input("ID Alfanumérico", key="reg_id")
    with r4: res = st.selectbox("¿Residencia?", ["No", "Sí"], key="reg_res")
    with r5: st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)
    with r6: st.write(""); st.button("🗑️", on_click=reset_registro)
    
    id_f = f"{centro if centro else '---'}-{str(int(edad_reg)) if edad_reg else '00'}-{alfa if alfa else '---'}"
    st.markdown(f'<div class="id-display">ID Registro: {id_f}</div>', unsafe_allow_html=True)

    c_izq, c_der = st.columns(2, gap="large")
    with c_izq:
        st.markdown("#### 📋 Calculadora")
        with st.container(border=True):
            calc_e = st.number_input("Edad", value=edad_reg, placeholder="Introduzca edad")
            calc_p = st.number_input("Peso (kg)", value=None, placeholder="Introduzca peso")
            calc_c = st.number_input("Creatinina", value=None, placeholder="Introduzca creatinina")
            calc_s = st.selectbox("Sexo", ["Hombre", "Mujer"])
            fg_c = round(((140-calc_e)*calc_p)/(72*calc_c)*(0.85 if calc_s=="Mujer" else 1.0), 1) if (calc_e and calc_p and calc_c) else 0.0
            st.markdown('<span style="font-size:0.7rem; color:grey; float:right;">Cockcroft-Gault</span>', unsafe_allow_html=True)
    with c_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual")
        v_fg = float(fg_m) if fg_m else fg_c
        st.markdown(f'<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{v_fg}</div><div style="color: #9d00ff;">mL/min</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    m1, m2 = st.columns([0.5, 0.5])
    with m1: st.markdown("#### 📝 Listado de medicamentos")
    with m2: st.markdown('<div class="rgpd-inline">🛡️ RGPD: No use datos identificativos</div>', unsafe_allow_html=True)
    txt_m = st.text_area("Meds", key="main_meds", height=120, label_visibility="collapsed")

    b_val, b_res = st.columns([0.8, 0.2])
    with b_val: btn = st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True)
    with b_res: st.button("🗑️ RESET TOTAL", use_container_width=True, on_click=reset_meds)

    if btn and txt_m:
        with st.spinner("Validando..."):
            prompt = f"Analiza FG {v_fg}: {txt_m}. Usa SOLO iconos ⛔, ⚠️, ✅. Si todo está bien: 'Fármacos correctamente dosificados'. Tras la lista, escribe 'A continuación, se detallan los ajustes de dosis para cada fármaco con este valor de FG:' y el detalle clínico."
            resp = llamar_ia(prompt)
            glow = "glow-red" if "⛔" in resp else ("glow-orange" if "⚠️" in resp else "glow-green")
            try:
                header, tecnico = resp.split("A continuación, se detallan los ajustes")
                header = header.replace("Medicamentos afectados:", "").strip()
                tecnico = tecnico.split("Nota Importante:")[0].strip()
                st.markdown(f'<div class="synthesis-box {glow}"><b>Medicamentos afectados:</b><br>{header.replace("\n", "<br>")}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="blue-detail-container">A continuación, se detallan los ajustes{tecnico.replace("\n", "<br>")}<div class="nota-line">Nota Importante:<br>· Consultar ficha técnica.<br>· Seguimiento de función renal.</div></div>', unsafe_allow_html=True)
                
                # Automatización Informe
                st.session_state.soip_s = "Revisión farmacoterapéutica por función renal."
                st.session_state.soip_o = " | ".join([f"{k}: {v}" for k,v in {"Edad":calc_e, "Creat":calc_c, "Peso":calc_p, "FG":v_fg}.items() if v])
                afectados = "\n".join([l for l in header.split("\n") if "⚠️" in l or "⛔" in l])
                st.session_state.soip_i = f"Fármacos con posible inadecuación:\n{afectados if afectados else 'Ninguno.'}"
                st.session_state.soip_p = "Se realiza interconsulta (IC) a su médico de atención primaria (MAP)."
                st.session_state.ic_motivo = f"Solicito valoración médica tras revisión farmacoterapéutica por función renal. Se detectan:\n{afectados}"
                st.session_state.ic_info = f"A continuación, se detallan los ajustes de dosis para cada fármaco con este valor de FG:\n{tecnico}"
                st.rerun()
            except: st.error("Error de formato.")

with tabs[1]:
    st.markdown('<div class="linea-discreta-soip">S</div>', unsafe_allow_html=True)
    st.text_area("S", st.session_state.soip_s, height=60, label_visibility="collapsed")
    st.markdown('<div class="linea-discreta-soip">O</div>', unsafe_allow_html=True)
    st.text_area("O", st.session_state.soip_o, height=60, label_visibility="collapsed")
    st.markdown('<div class="linea-discreta-soip">I</div>', unsafe_allow_html=True)
    st.text_area("I", st.session_state.soip_i, height=150, label_visibility="collapsed")
    st.markdown('<div class="linea-discreta-soip">P</div>', unsafe_allow_html=True)
    st.text_area("P", st.session_state.soip_p, height=60, label_visibility="collapsed")
    st.markdown("---")
    st.markdown("#### 📨 SOLICITUD DE INTERCONSULTA")
    i1, i2 = st.columns(2)
    with i1: st.text_area("Motivo", st.session_state.ic_motivo, height=200)
    with i2: st.text_area("Información Clínica", st.session_state.ic_info, height=200)

st.markdown('<div style="background-color:#fdfde0; padding:10px; border-radius:10px; text-align:center; border:1px solid #f9f9c5;">⚠️ Apoyo a la revisión farmacoterapéutica. Verifique con fuentes oficiales.</div>', unsafe_allow_html=True)
