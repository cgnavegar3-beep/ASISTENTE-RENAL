# v. 22 feb 12:15
import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import google.generativeai as genai
import io

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
#   
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
#        * Sin iconos = Verde (glow-green).
# #
#        * Con ⚠️ = Naranja (glow-orange).
# #
#        * Con ⛔ = Rojo (glow-red).
# #
# #
# V. PROTECCIÓN INTEGRAL PESTAÑA 1 (💊 VALIDACIÓN):
# #
#    - Blindaje Total: Prohibida cualquier modificación en el layout, orden de columnas o funciones de la Pestaña 1.
# #
#    - Componentes Congelados: Registro de paciente (fila única), Calculadora dual (Glow morado), Área de texto y Botonera (Validar/Reset).
# #
#    - Lógica Funcional: El sistema de callbacks y el prompt de IA de esta pestaña no admiten cambios de sintaxis.
# #
# =================================================================

st.set_page_config(page_title='Asistente Renal', layout='wide', initial_sidebar_state='collapsed')

def reset_registro():
   st.session_state['reg_centro'] = ''
   st.session_state['reg_edad'] = None
   st.session_state['reg_id'] = ''
   st.session_state['reg_res'] = 'No'

def reset_meds():
   st.session_state['main_meds'] = ''

if 'active_model' not in st.session_state: st.session_state.active_model = 'ESPERANDO...'

try:
    API_KEY = st.secrets['GEMINI_API_KEY']
    genai.configure(api_key=API_KEY)
except:
    API_KEY = None

def obtener_modelos_vivos():
    try:
        if not API_KEY: return []
        return [m.name.replace('models/', '').replace('gemini-', '') 
                for m in genai.list_models() 
                if 'generateContent' in m.supported_generation_methods]
    except:
        return ['2.5-flash', '1.5-pro']

def llamar_ia_en_cascada(prompt):
    disponibles = obtener_modelos_vivos()
    preferencia = ['2.5-flash', '1.5-pro', '1.5-flash']
    modelos_a_intentar = [m for m in preferencia if m in disponibles]
    for mod_name in modelos_a_intentar:
        try:
            st.session_state.active_model = mod_name.upper()
            model = genai.GenerativeModel(f'models/gemini-{mod_name}')
            response = model.generate_content(prompt)
            return response.text
        except: continue
    return '⚠️ Error: Sin respuesta.'

def inject_ui_styles():
    css = '<style>'
    # CAPA 0: REHABILITAR SCROLL DEL CONTENIDO
    css += 'html, body, [data-testid="stAppViewContainer"] { overflow-y: auto !important; }'
    css += '.block-container { max-width: 100% !important; padding-top: 13.5rem !important; padding-left: 4% !important; padding-right: 4% !important; }'
    
    # CAPA 1: CUADROS NEGROS (MÁXIMO NIVEL)
    css += '.availability-badge { background-color: #1a1a1a !important; color: #888 !important; padding: 4px 10px; border-radius: 3px; font-family: monospace !important; font-size: 0.65rem; position: fixed; top: 15px; left: 15px; z-index: 1000002; border: 1px solid #333; width: 180px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }'
    css += '.model-badge { background-color: #000000 !important; color: #00FF00 !important; padding: 4px 10px; border-radius: 3px; font-family: monospace !important; font-size: 0.75rem; position: fixed; top: 15px; left: 205px; z-index: 1000002; box-shadow: 0 0 5px #00FF0033; }'
    
    # CAPA 2: TITULO Y VERSION (FIJO)
    css += '.fixed-header-block { position: fixed; top: 0; left: 0; right: 0; background-color: white; z-index: 1000001; height: 110px; padding-top: 20px; border-bottom: 1px solid #eee; }'
    css += '.main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin: 0; }'
    css += '.sub-version { text-align: center; font-size: 0.8rem; color: #666; margin-top: -5px; font-family: sans-serif; }'
    
    # CAPA 3: PESTAÑAS (FIJO BAJO TITULO)
    css += 'div[data-testid="stTabs"] { position: fixed !important; top: 110px !important; left: 0; right: 0; background-color: white !important; z-index: 1000000 !important; padding-left: 4%; padding-right: 4%; border-bottom: 1px solid #eee; }'
    
    # ESTILOS BLINDADOS DE PESTAÑA 1
    css += '.version-display { text-align: right; font-size: 0.6rem; color: #bbb; font-family: monospace; position: fixed; bottom: 10px; right: 10px; }'
    css += '.id-display { color: #666; font-family: monospace; font-size: 0.85rem; margin-top: -5px; margin-bottom: 20px; }'
    css += '.fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }'
    css += '.rgpd-inline { background-color: #fff5f5; color: #c53030; padding: 8px 16px; border-radius: 8px; border: 1.5px solid #feb2b2; font-size: 0.85rem; display: inline-block; float: right; }'
    css += '.synthesis-box { padding: 15px; border-radius: 12px; margin-bottom: 15px; text-align: left; border-width: 2px; border-style: solid; font-size: 0.95rem; }'
    css += '.glow-green { background-color: #f1f8e9; color: #2e7d32; border-color: #a5d6a7; box-shadow: 0 0 12px #a5d6a7; }'
    css += '.glow-orange { background-color: #fff3e0; color: #e65100; border-color: #ffcc80; box-shadow: 0 0 12px #ffcc80; }'
    css += '.glow-red { background-color: #fff5f5; color: #c53030; border-color: #feb2b2; box-shadow: 0 0 18px #feb2b2; }'
    css += '.blue-detail-container { background-color: #f0f7ff; color: #2c5282; padding: 20px; border-radius: 10px; border: 1px solid #bee3f8; margin-top: 10px; line-height: 1.6; }'
    css += '.nota-line { border-top: 2px solid #aec6cf; margin-top: 15px; padding-top: 15px; font-size: 0.95rem; font-weight: 700; color: #003366; }'
    css += '.warning-yellow { background-color: #fdfde0; color: #856404; padding: 15px; border-radius: 10px; border: 1px solid #f9f9c5; margin-top: 40px; text-align: center; }'
    css += '</style>'
    st.markdown(css, unsafe_allow_html=True)

inject_ui_styles()

# RENDERIZADO DE CAPAS FIJAS
st.markdown(f'<div class="availability-badge">ZONA: {" | ".join(obtener_modelos_vivos())}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="model-badge">{st.session_state.active_model}</div>', unsafe_allow_html=True)
st.markdown('<div class="fixed-header-block"><div class="main-title">ASISTENTE RENAL</div><div class="sub-version">v. 22 feb 12:15</div></div>', unsafe_allow_html=True)
st.markdown('<div class="version-display">v. 22 feb 12:15</div>', unsafe_allow_html=True)

tabs = st.tabs(['💊 VALIDACIÓN', '📄 INFORME', '📊 EXCEL', '📈 GRÁFICOS'])

with tabs[0]:
    st.markdown('### Registro de Paciente')
    c1, c2, c3, c4, c5, c_del = st.columns([1, 1, 1, 1, 1, 0.4])
    with c1: centro = st.text_input('Centro', placeholder='G/M', key='reg_centro')
    with c2: edad_reg = st.number_input('Edad', value=None, placeholder='0', key='reg_edad')
    with c3: alfa = st.text_input('ID Alfanumérico', placeholder='ABC-123', key='reg_id')
    with c4: res = st.selectbox('¿Residencia?', ['No', 'Sí'], key='reg_res')
    with c5: st.text_input('Fecha', value=datetime.now().strftime('%d/%m/%Y'), disabled=True)
    with c_del:
        st.write('')
        st.button('🗑️', on_click=reset_registro)

    id_final = f"{centro if centro else '---'}-{str(int(edad_reg)) if edad_reg else '00'}-{alfa if alfa else '---'}"
    st.markdown(f'<div class="id-display">ID Registro: {id_final}</div>', unsafe_allow_html=True)

    col_izq, col_der = st.columns(2, gap='large')
    with col_izq:
        st.markdown('#### 📋 Calculadora')
        with st.container(border=True):
            calc_e = st.number_input('Edad (años)', value=edad_reg if edad_reg else 65)
            calc_p = st.number_input('Peso (kg)', value=70.0)
            calc_c = st.number_input('Creatinina (mg/dL)', value=1.0)
            calc_s = st.selectbox('Sexo', ['Hombre', 'Mujer'])
            fg = round(((140 - calc_e) * calc_p) / (72 * calc_c) * (0.85 if calc_s == 'Mujer' else 1.0), 1)

    with col_der:
        st.markdown('#### 💊 Filtrado Glomerular')
        fg_m = st.text_input('Ajuste Manual')
        valor_fg = fg_m if fg_m else fg
        st.markdown(f'<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{valor_fg}</div><div style="font-size: 1rem; color: #9d00ff;">mL/min</div></div>', unsafe_allow_html=True)

    st.write(''); st.markdown('---')
    m_col1, m_col2 = st.columns([0.5, 0.5])
    with m_col1: st.markdown('#### 📝 Listado de medicamentos')
    with m_col2: st.markdown('<div class="rgpd-inline">🛡️ <b>PROTECCIÓN DE DATOS:</b> No introduzca datos personales identificativos</div>', unsafe_allow_html=True)
    
    txt_meds = st.text_area('Listado', height=150, label_visibility='collapsed', key='main_meds')

    b_val, b_res = st.columns([0.85, 0.15])
    with b_val:
        if st.button('🚀 VALIDAR ADECUACIÓN', use_container_width=True):
            if txt_meds:
                with st.spinner('Consultando evidencia clínica...'):
                    prompt = f"Experto farmacia renal. Analiza FG {valor_fg}: {txt_meds}. Sigue el formato estricto blindado."
                    resp = llamar_ia_en_cascada(prompt)
                    glow_class = 'glow-red' if '⛔' in resp else ('glow-orange' if '⚠️' in resp else 'glow-green')
                    try:
                       partes = resp.split('A continuación, se detallan los ajustes')
                       sintesis = partes[0].strip()
                       detalle_clinico = 'A continuación, se detallan los ajustes' + partes[1]
                       st.markdown(f'<div class="synthesis-box {glow_class}"><b>{sintesis.replace("\n", "<br>")}</b></div>', unsafe_allow_html=True)
                       st.markdown(f'<div class="blue-detail-container">{detalle_clinico.replace("\n", "<br>")}<div class="nota-line">Nota Importante:<br>· Estas son recomendaciones generales.<br>· Siempre se debe consultar la ficha técnica actualizada.</div></div>', unsafe_allow_html=True)
                    except: st.info(resp)

    with b_res:
        st.button('🗑️ RESET', use_container_width=True, on_click=reset_meds)

st.markdown('<div class="warning-yellow">⚠️ Apoyo a la revisión farmacoterapéutica. Verifique siempre con fuentes oficiales.</div>', unsafe_allow_html=True)
