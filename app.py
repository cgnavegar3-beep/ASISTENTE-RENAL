import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# --- 1. CONFIGURACIÓN E INICIALIZACIÓN ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

# Inicialización de estados
if 'active_model_name' not in st.session_state:
    st.session_state.active_model_name = "2.5 Flash" # Siguiendo tu instrucción de counter discreto
if 'meds_input' not in st.session_state:
    st.session_state.meds_input = ""
if 'fg_final' not in st.session_state:
    st.session_state.fg_final = 0.0
if 'metodo_usado' not in st.session_state:
    st.session_state.metodo_usado = "Pendiente"

# --- 2. ESTILOS CSS (BLINDAJE VISUAL Y AIRE EN COLUMNA DERECHA) ---
def inject_ui_styles():
    st.markdown("""
    <style>
        /* Indicador de Modelo arriba a la izquierda */
        .model-indicator {
            position: fixed; top: 10px; left: 10px; background-color: #000; color: #0F0;
            padding: 5px 12px; font-family: 'Courier New', monospace; font-size: 12px;
            border-radius: 4px; z-index: 9999; border: 1px solid #333;
        }
        
        /* Pestañas con línea roja */
        div[role="tablist"] {{ gap: 20px; }}
        button[aria-selected="true"] {{
            border-bottom: 3px solid red !important;
            font-weight: bold !important;
        }}

        /* Recuadros y espaciado */
        .stColumn {{ padding: 10px; }}
        .custom-box {{
            border: 1px solid #ddd; border-radius: 10px; padding: 20px; height: 100%;
        }}
        
        /* Display FG Glow Morado */
        .fg-glow-box {{
            background-color: #000; color: #fff; border-radius: 12px;
            padding: 20px; text-align: center; border: 2px solid #6a0dad;
            box-shadow: 0 0 15px #a020f0; margin: 25px 0;
        }}
        
        /* Separador Hendidura */
        .hendidura {{
            height: 2px; background: linear-gradient(to bottom, #ccc, #eee);
            margin: 25px 0; border-radius: 50%; opacity: 0.5;
        }}

        /* Cuadros de Resultados con Flash Glow */
        .result-card {{ padding: 15px; border-radius: 10px; margin-bottom: 10px; color: #111; }}
        .flash-verde {{ background: #e6fffa; border: 2px solid #28a745; animation: glow-v 1s; }}
        .flash-naranja {{ background: #fffaf0; border: 2px solid #fd7e14; animation: glow-n 1s; }}
        .flash-rojo {{ background: #fff5f5; border: 2px solid #dc3545; animation: glow-r 1s; }}
        
        @keyframes glow-v {{ 0% {{ box-shadow: 0 0 20px #28a745; }} 100% {{ box-shadow: 0 0 0px; }} }}
        @keyframes glow-n {{ 0% {{ box-shadow: 0 0 20px #fd7e14; }} 100% {{ box-shadow: 0 0 0px; }} }}
        @keyframes glow-r {{ 0% {{ box-shadow: 0 0 20px #dc3545; }} 100% {{ box-shadow: 0 0 0px; }} }}

        /* Aviso Seguridad Fijo */
        .safety-footer {{
            position: fixed; bottom: 0; left: 0; width: 100%; background: #fff9c4;
            text-align: center; padding: 10px; font-size: 13px; border-top: 1px solid #fbc02d;
        }}
    </style>
    <div class="model-indicator">{st.session_state.active_model_name}</div>
    """, unsafe_allow_html=True)

inject_ui_styles()

# --- 3. LÓGICA DE IA Y PROCESAMIENTO ---
def run_ia_task(prompt, image=None):
    # Simulación de fallback y procesamiento (Blindado según prompt)
    try:
        genai.configure(api_key=st.secrets["API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        content = [prompt]
        if image:
            # Blindaje: Normalización RGB
            img_rgb = image.convert("RGB")
            content.append(img_rgb)
            
        response = model.generate_content(content)
        return response.text
    except:
        return "Fallo de conexión o superado el número de intentos"

# --- 4. ESTRUCTURA DE LA APP ---
st.title("ASISTENTE RENAL")

tab1, tab2, tab3, tab4 = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 EXCEL", "📈 GRÁFICOS"])

with tab1:
    col_calc, col_ajuste = st.columns(2)

    # 1. CALCULADORA (Izquierda)
    with col_calc:
        st.markdown(f"### 📋 Calculadora <br><small>Método: CKD-EPI</small>", import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# --- 1. CONFIGURACIÓN E INICIALIZACIÓN ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

# Inicialización de estados
if 'active_model_name' not in st.session_state:
    st.session_state.active_model_name = "2.5 Flash" # Siguiendo tu instrucción de counter discreto
if 'meds_input' not in st.session_state:
    st.session_state.meds_input = ""
if 'fg_final' not in st.session_state:
    st.session_state.fg_final = 0.0
if 'metodo_usado' not in st.session_state:
    st.session_state.metodo_usado = "Pendiente"

# --- 2. ESTILOS CSS (BLINDAJE VISUAL Y AIRE EN COLUMNA DERECHA) ---
def inject_ui_styles():
    st.markdown("""
    <style>
        /* Indicador de Modelo arriba a la izquierda */
        .model-indicator {
            position: fixed; top: 10px; left: 10px; background-color: #000; color: #0F0;
            padding: 5px 12px; font-family: 'Courier New', monospace; font-size: 12px;
            border-radius: 4px; z-index: 9999; border: 1px solid #333;
        }
        
        /* Pestañas con línea roja */
        div[role="tablist"] {{ gap: 20px; }}
        button[aria-selected="true"] {{
            border-bottom: 3px solid red !important;
            font-weight: bold !important;
        }}

        /* Recuadros y espaciado */
        .stColumn {{ padding: 10px; }}
        .custom-box {{
            border: 1px solid #ddd; border-radius: 10px; padding: 20px; height: 100%;
        }}
        
        /* Display FG Glow Morado */
        .fg-glow-box {{
            background-color: #000; color: #fff; border-radius: 12px;
            padding: 20px; text-align: center; border: 2px solid #6a0dad;
            box-shadow: 0 0 15px #a020f0; margin: 25px 0;
        }}
        
        /* Separador Hendidura */
        .hendidura {{
            height: 2px; background: linear-gradient(to bottom, #ccc, #eee);
            margin: 25px 0; border-radius: 50%; opacity: 0.5;
        }}

        /* Cuadros de Resultados con Flash Glow */
        .result-card {{ padding: 15px; border-radius: 10px; margin-bottom: 10px; color: #111; }}
        .flash-verde {{ background: #e6fffa; border: 2px solid #28a745; animation: glow-v 1s; }}
        .flash-naranja {{ background: #fffaf0; border: 2px solid #fd7e14; animation: glow-n 1s; }}
        .flash-rojo {{ background: #fff5f5; border: 2px solid #dc3545; animation: glow-r 1s; }}
        
        @keyframes glow-v {{ 0% {{ box-shadow: 0 0 20px #28a745; }} 100% {{ box-shadow: 0 0 0px; }} }}
        @keyframes glow-n {{ 0% {{ box-shadow: 0 0 20px #fd7e14; }} 100% {{ box-shadow: 0 0 0px; }} }}
        @keyframes glow-r {{ 0% {{ box-shadow: 0 0 20px #dc3545; }} 100% {{ box-shadow: 0 0 0px; }} }}

        /* Aviso Seguridad Fijo */
        .safety-footer {{
            position: fixed; bottom: 0; left: 0; width: 100%; background: #fff9c4;
            text-align: center; padding: 10px; font-size: 13px; border-top: 1px solid #fbc02d;
        }}
    </style>
    <div class="model-indicator">{st.session_state.active_model_name}</div>
    """, unsafe_allow_html=True)

inject_ui_styles()

# --- 3. LÓGICA DE IA Y PROCESAMIENTO ---
def run_ia_task(prompt, image=None):
    # Simulación de fallback y procesamiento (Blindado según prompt)
    try:
        genai.configure(api_key=st.secrets["API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        content = [prompt]
        if image:
            # Blindaje: Normalización RGB
            img_rgb = image.convert("RGB")
            content.append(img_rgb)
            
        response = model.generate_content(content)
        return response.text
    except:
        return "Fallo de conexión o superado el número de intentos"

# --- 4. ESTRUCTURA DE LA APP ---
st.title("ASISTENTE RENAL")

tab1, tab2, tab3, tab4 = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 EXCEL", "📈 GRÁFICOS"])

with tab1:
    col_calc, col_ajuste = st.columns(2)

    # 1. CALCULADORA (Izquierda)
    with col_calc:
        st.markdown(f"### 📋 Calculadora <br><small>Método: CKD-EPI</small>", import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# --- 1. CONFIGURACIÓN E INICIALIZACIÓN ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

# Inicialización de estados
if 'active_model_name' not in st.session_state:
    st.session_state.active_model_name = "2.5 Flash" # Siguiendo tu instrucción de counter discreto
if 'meds_input' not in st.session_state:
    st.session_state.meds_input = ""
if 'fg_final' not in st.session_state:
    st.session_state.fg_final = 0.0
if 'metodo_usado' not in st.session_state:
    st.session_state.metodo_usado = "Pendiente"

# --- 2. ESTILOS CSS (BLINDAJE VISUAL Y AIRE EN COLUMNA DERECHA) ---
def inject_ui_styles():
    st.markdown("""
    <style>
        /* Indicador de Modelo arriba a la izquierda */
        .model-indicator {
            position: fixed; top: 10px; left: 10px; background-color: #000; color: #0F0;
            padding: 5px 12px; font-family: 'Courier New', monospace; font-size: 12px;
            border-radius: 4px; z-index: 9999; border: 1px solid #333;
        }
        
        /* Pestañas con línea roja */
        div[role="tablist"] {{ gap: 20px; }}
        button[aria-selected="true"] {{
            border-bottom: 3px solid red !important;
            font-weight: bold !important;
        }}

        /* Recuadros y espaciado */
        .stColumn {{ padding: 10px; }}
        .custom-box {{
            border: 1px solid #ddd; border-radius: 10px; padding: 20px; height: 100%;
        }}
        
        /* Display FG Glow Morado */
        .fg-glow-box {{
            background-color: #000; color: #fff; border-radius: 12px;
            padding: 20px; text-align: center; border: 2px solid #6a0dad;
            box-shadow: 0 0 15px #a020f0; margin: 25px 0;
        }}
        
        /* Separador Hendidura */
        .hendidura {{
            height: 2px; background: linear-gradient(to bottom, #ccc, #eee);
            margin: 25px 0; border-radius: 50%; opacity: 0.5;
        }}

        /* Cuadros de Resultados con Flash Glow */
        .result-card {{ padding: 15px; border-radius: 10px; margin-bottom: 10px; color: #111; }}
        .flash-verde {{ background: #e6fffa; border: 2px solid #28a745; animation: glow-v 1s; }}
        .flash-naranja {{ background: #fffaf0; border: 2px solid #fd7e14; animation: glow-n 1s; }}
        .flash-rojo {{ background: #fff5f5; border: 2px solid #dc3545; animation: glow-r 1s; }}
        
        @keyframes glow-v {{ 0% {{ box-shadow: 0 0 20px #28a745; }} 100% {{ box-shadow: 0 0 0px; }} }}
        @keyframes glow-n {{ 0% {{ box-shadow: 0 0 20px #fd7e14; }} 100% {{ box-shadow: 0 0 0px; }} }}
        @keyframes glow-r {{ 0% {{ box-shadow: 0 0 20px #dc3545; }} 100% {{ box-shadow: 0 0 0px; }} }}

        /* Aviso Seguridad Fijo */
        .safety-footer {{
            position: fixed; bottom: 0; left: 0; width: 100%; background: #fff9c4;
            text-align: center; padding: 10px; font-size: 13px; border-top: 1px solid #fbc02d;
        }}
    </style>
    <div class="model-indicator">{st.session_state.active_model_name}</div>
    """, unsafe_allow_html=True)

inject_ui_styles()

# --- 3. LÓGICA DE IA Y PROCESAMIENTO ---
def run_ia_task(prompt, image=None):
    # Simulación de fallback y procesamiento (Blindado según prompt)
    try:
        genai.configure(api_key=st.secrets["API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        content = [prompt]
        if image:
            # Blindaje: Normalización RGB
            img_rgb = image.convert("RGB")
            content.append(img_rgb)
            
        response = model.generate_content(content)
        return response.text
    except:
        return "Fallo de conexión o superado el número de intentos"

# --- 4. ESTRUCTURA DE LA APP ---
st.title("ASISTENTE RENAL")

tab1, tab2, tab3, tab4 = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 EXCEL", "📈 GRÁFICOS"])

with tab1:
    col_calc, col_ajuste = st.columns(2)

    # 1. CALCULADORA (Izquierda)
    with col_calc:
        st.markdown(f"### 📋 Calculadora <br><small>Método: CKD-EPI</small>", unsafe_allow_html=True)
        with st.container(border=True):
            edad = st.number_input("Edad", 1, 120, 65)
            peso = st.number_input("Peso (kg)", 10, 250, 70)
            creatinina = st.number_input("Creatinina (mg/dL)", 0.1, 15.0, 1.2)
            sexo = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
            
            # Cálculo automático (simplificado para el ejemplo)
            fg_calc = 175 * (creatinina**-1.154) * (edad**-0.203)
            if sexo == "Mujer": fg_calc *= 0.742

    # 2. AJUSTE Y CAPTURA (Derecha - Con más "aire")
    with col_ajuste:
        st.markdown("### 💊 Ajuste y Captura", unsafe_allow_html=True)
        
        fg_manual = st.text_input("Input Manual del FG (Prioritario)", placeholder="Ej: 45")
        
        st.write("") # Espacio de separación
        
        # Lógica de prioridad de FG
        valor_fg = float(fg_manual) if fg_manual else fg_calc
        metodo = "Manual" if fg_manual else "CKD-EPI"
        
        # Display FG Glow Morado
        st.markdown(f"""
            <div class="fg-glow-box">
                <div style="font-size: 0.9em; opacity: 0.8;">Filtrado Glomerular Final</div>
                <div style="font-size: 2.5em; font-weight: bold;">{valor_fg:.1f}</div>
                <div style="font-size: 0.8em; margin-top:5px;">Método: {metodo}</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("") # Espacio de separación
        
        # Zona de carga
        uploaded_file = st.file_uploader("📁 Subir imagen de analítica/medicamentos", type=["png", "jpg", "jpeg"])
        if uploaded_file:
            if st.button("📋 Procesar Archivo Subido"):
                img = Image.open(uploaded_file)
                with st.spinner("IA transcribiendo..."):
                    st.session_state.meds_input = run_ia_task("Transcribe la lista de medicamentos:", img)
        
        st.button("📋 Pegar Recorte (Ctrl+V)")

    # 3. LÍNEA DE SEPARACIÓN (Hendidura)
    st.markdown('<div class="hendidura"></div>', unsafe_allow_html=True)

    # 4. LISTADO DE MEDICAMENTOS
    st.markdown("### 📝 Listado de medicamentos")
    meds_text = st.text_area(
        "Escribe o edita la lista del archivo o captura subidos",
        value=st.session_state.meds_input,
        height=150,
        placeholder="Escribe aquí los medicamentos..."
    )

    # 5. BOTONERA DUAL (85/15)
    col_btn_val, col_btn_res = st.columns([85, 15])
    with col_btn_val:
        if st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True):
            # Aquí iría la lógica de cruce con PDF
            st.session_state.validado = True
    with col_btn_res:
        if st.button("🗑️ RESET", use_container_width=True):
            st.session_state.meds_input = ""
            st.rerun()

    # 6. RESULTADOS (Simulados según reglas de color)
    if 'validado' in st.session_state:
        # Ejemplo de cuadro resumen (Naranja por defecto para test)
        st.markdown("""
            <div class="result-card flash-naranja">
                <strong>CUADRO RESUMEN</strong><br>
                ⚠️ Precaución: Ajuste moderado requerido.<br>
                • DABIGATRÁN: Revisar dosis.
            </div>
            
            <div class="result-card">
                <strong>ACCIONES CLÍNICAS</strong><br>
                Según fuentes oficiales, el uso de Dabigatrán con FG reducido requiere monitorización estrecha.
            </div>
        """, unsafe_allow_html=True)

# AVISO DE SEGURIDAD PERMANENTE
st.markdown("""
    <div class="safety-footer">
        ⚠️ Aviso: Esta herramienta es un apoyo a la revisión farmacoterapéutica. Puede contener errores. Verifique con fuentes oficiales.
    </div>
""", unsafe_allow_html=True)
        with st.container(border=True):
            edad = st.number_input("Edad", 1, 120, 65)
            peso = st.number_input("Peso (kg)", 10, 250, 70)
            creatinina = st.number_input("Creatinina (mg/dL)", 0.1, 15.0, 1.2)
            sexo = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
            
            # Cálculo automático (simplificado para el ejemplo)
            fg_calc = 175 * (creatinina**-1.154) * (edad**-0.203)
            if sexo == "Mujer": fg_calc *= 0.742

    # 2. AJUSTE Y CAPTURA (Derecha - Con más "aire")
    with col_ajuste:
        st.markdown("### 💊 Ajuste y Captura", unsafe_allow_value=True)
        
        fg_manual = st.text_input("Input Manual del FG (Prioritario)", placeholder="Ej: 45")
        
        st.write("") # Espacio de separación
        
        # Lógica de prioridad de FG
        valor_fg = float(fg_manual) if fg_manual else fg_calc
        metodo = "Manual" if fg_manual else "CKD-EPI"
        
        # Display FG Glow Morado
        st.markdown(f"""
            <div class="fg-glow-box">
                <div style="font-size: 0.9em; opacity: 0.8;">Filtrado Glomerular Final</div>
                <div style="font-size: 2.5em; font-weight: bold;">{valor_fg:.1f}</div>
                <div style="font-size: 0.8em; margin-top:5px;">Método: {metodo}</div>
            </div>
        """, unsafe_allow_value=True)
        
        st.write("") # Espacio de separación
        
        # Zona de carga
        uploaded_file = st.file_uploader("📁 Subir imagen de analítica/medicamentos", type=["png", "jpg", "jpeg"])
        if uploaded_file:
            if st.button("📋 Procesar Archivo Subido"):
                img = Image.open(uploaded_file)
                with st.spinner("IA transcribiendo..."):
                    st.session_state.meds_input = run_ia_task("Transcribe la lista de medicamentos:", img)
        
        st.button("📋 Pegar Recorte (Ctrl+V)")

    # 3. LÍNEA DE SEPARACIÓN (Hendidura)
    st.markdown('<div class="hendidura"></div>', unsafe_allow_value=True)

    # 4. LISTADO DE MEDICAMENTOS
    st.markdown("### 📝 Listado de medicamentos")
    meds_text = st.text_area(
        "Escribe o edita la lista del archivo o captura subidos",
        value=st.session_state.meds_input,
        height=150,
        placeholder="Escribe aquí los medicamentos..."
    )

    # 5. BOTONERA DUAL (85/15)
    col_btn_val, col_btn_res = st.columns([85, 15])
    with col_btn_val:
        if st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True):
            # Aquí iría la lógica de cruce con PDF
            st.session_state.validado = True
    with col_btn_res:
        if st.button("🗑️ RESET", use_container_width=True):
            st.session_state.meds_input = ""
            st.rerun()

    # 6. RESULTADOS (Simulados según reglas de color)
    if 'validado' in st.session_state:
        # Ejemplo de cuadro resumen (Naranja por defecto para test)
        st.markdown("""
            <div class="result-card flash-naranja">
                <strong>CUADRO RESUMEN</strong><br>
                ⚠️ Precaución: Ajuste moderado requerido.<br>
                • DABIGATRÁN: Revisar dosis.
            </div>
            
            <div class="result-card">
                <strong>ACCIONES CLÍNICAS</strong><br>
                Según fuentes oficiales, el uso de Dabigatrán con FG reducido requiere monitorización estrecha.
            </div>
        """, unsafe_allow_value=True)

# AVISO DE SEGURIDAD PERMANENTE
st.markdown("""
    <div class="safety-footer">
        ⚠️ Aviso: Esta herramienta es un apoyo a la revisión farmacoterapéutica. Puede contener errores. Verifique con fuentes oficiales.
    </div>
""", unsafe_allow_value=True)
unsafe_allow_value=True)
        with st.container(border=True):
            edad = st.number_input("Edad", 1, 120, 65)
            peso = st.number_input("Peso (kg)", 10, 250, 70)
            creatinina = st.number_input("Creatinina (mg/dL)", 0.1, 15.0, 1.2)
            sexo = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
            
            # Cálculo automático (simplificado para el ejemplo)
            fg_calc = 175 * (creatinina**-1.154) * (edad**-0.203)
            if sexo == "Mujer": fg_calc *= 0.742

    # 2. AJUSTE Y CAPTURA (Derecha - Con más "aire")
    with col_ajuste:
        st.markdown("### 💊 Ajuste y Captura", unsafe_allow_value=True)
        
        fg_manual = st.text_input("Input Manual del FG (Prioritario)", placeholder="Ej: 45")
        
        st.write("") # Espacio de separación
        
        # Lógica de prioridad de FG
        valor_fg = float(fg_manual) if fg_manual else fg_calc
        metodo = "Manual" if fg_manual else "CKD-EPI"
        
        # Display FG Glow Morado
        st.markdown(f"""
            <div class="fg-glow-box">
                <div style="font-size: 0.9em; opacity: 0.8;">Filtrado Glomerular Final</div>
                <div style="font-size: 2.5em; font-weight: bold;">{valor_fg:.1f}</div>
                <div style="font-size: 0.8em; margin-top:5px;">Método: {metodo}</div>
            </div>
        """, unsafe_allow_value=True)
        
        st.write("") # Espacio de separación
        
        # Zona de carga
        uploaded_file = st.file_uploader("📁 Subir imagen de analítica/medicamentos", type=["png", "jpg", "jpeg"])
        if uploaded_file:
            if st.button("📋 Procesar Archivo Subido"):
                img = Image.open(uploaded_file)
                with st.spinner("IA transcribiendo..."):
                    st.session_state.meds_input = run_ia_task("Transcribe la lista de medicamentos:", img)
        
        st.button("📋 Pegar Recorte (Ctrl+V)")

    # 3. LÍNEA DE SEPARACIÓN (Hendidura)
    st.markdown('<div class="hendidura"></div>', unsafe_allow_value=True)

    # 4. LISTADO DE MEDICAMENTOS
    st.markdown("### 📝 Listado de medicamentos")
    meds_text = st.text_area(
        "Escribe o edita la lista del archivo o captura subidos",
        value=st.session_state.meds_input,
        height=150,
        placeholder="Escribe aquí los medicamentos..."
    )

    # 5. BOTONERA DUAL (85/15)
    col_btn_val, col_btn_res = st.columns([85, 15])
    with col_btn_val:
        if st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True):
            # Aquí iría la lógica de cruce con PDF
            st.session_state.validado = True
    with col_btn_res:
        if st.button("🗑️ RESET", use_container_width=True):
            st.session_state.meds_input = ""
            st.rerun()

    # 6. RESULTADOS (Simulados según reglas de color)
    if 'validado' in st.session_state:
        # Ejemplo de cuadro resumen (Naranja por defecto para test)
        st.markdown("""
            <div class="result-card flash-naranja">
                <strong>CUADRO RESUMEN</strong><br>
                ⚠️ Precaución: Ajuste moderado requerido.<br>
                • DABIGATRÁN: Revisar dosis.
            </div>
            
            <div class="result-card">
                <strong>ACCIONES CLÍNICAS</strong><br>
                Según fuentes oficiales, el uso de Dabigatrán con FG reducido requiere monitorización estrecha.
            </div>
        """, unsafe_allow_value=True)

# AVISO DE SEGURIDAD PERMANENTE
st.markdown("""
    <div class="safety-footer">
        ⚠️ Aviso: Esta herramienta es un apoyo a la revisión farmacoterapéutica. Puede contener errores. Verifique con fuentes oficiales.
    </div>
""", unsafe_allow_value=True)
