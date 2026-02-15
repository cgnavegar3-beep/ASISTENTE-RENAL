import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import datetime
import time

# ==============================================================================
# 0. CONFIGURACIÓN E INICIALIZACIÓN
# ==============================================================================
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide", page_icon="💊")

# --- GESTIÓN DE SECRETOS (API KEY) ---
# Asegúrate de tener tu API Key en .streamlit/secrets.toml o configúrala aquí temporalmente
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    # Fallback para pruebas locales si no hay secrets
    API_KEY = "TU_API_KEY_AQUI" 

genai.configure(api_key=API_KEY)

# --- INICIALIZACIÓN DE SESSION STATE (MEMORIA) ---
if 'meds_input' not in st.session_state:
    st.session_state.meds_input = ""
if 'cache_result' not in st.session_state:
    st.session_state.cache_result = None # Almacena el resultado validado
if 'memoria_farmacos' not in st.session_state:
    st.session_state.memoria_farmacos = {} # FASE 2: Diccionario Local de fármacos
if 'active_model_name' not in st.session_state:
    st.session_state.active_model_name = "1.5 Pro" # Defecto inicial
if 'reset_counter' not in st.session_state:
    st.session_state.reset_counter = 0

# ==============================================================================
# 1. ESTILO Y BLINDAJE VISUAL (CSS)
# ==============================================================================
def inject_ui_styles():
    st.markdown("""
    <style>
    /* BLINDAJE: Indicador de Modelo */
    .model-indicator {
        position: fixed;
        top: 60px;
        left: 20px;
        background-color: #000000;
        color: #0F0;
        padding: 5px 10px;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        border: 1px solid #0F0;
        z-index: 9999;
        box-shadow: 0 0 5px #0F0;
    }
    
    /* BLINDAJE: Pestañas (Línea Roja y Negrita) */
    div[data-baseweb="tab-list"] button[aria-selected="true"] {
        border-bottom: 3px solid red !important;
        font-weight: bold !important;
        color: white !important;
    }
    div[data-baseweb="tab-list"] button {
        font-weight: normal;
    }

    /* BLINDAJE: Cuadro FG Glow Morado */
    .fg-glow-box {
        background-color: #000;
        border: 2px solid #A020F0;
        color: white;
        padding: 15px;
        text-align: center;
        border-radius: 8px;
        box-shadow: 0 0 15px #A020F0;
        margin-bottom: 10px;
    }
    .fg-value { font-size: 24px; font-weight: bold; }
    .fg-label { font-size: 12px; color: #ccc; }

    /* BLINDAJE: Resultados Flash (Verde/Naranja/Rojo) */
    @keyframes flashGreen { 0% { box-shadow: 0 0 30px #0F0; } 100% { box-shadow: 0 0 10px #0F0; } }
    @keyframes flashOrange { 0% { box-shadow: 0 0 30px #FFA500; } 100% { box-shadow: 0 0 10px #FFA500; } }
    @keyframes flashRed { 0% { box-shadow: 0 0 30px #F00; } 100% { box-shadow: 0 0 10px #F00; } }

    .flash-verde {
        border: 2px solid #0F0;
        background-color: rgba(0, 255, 0, 0.1);
        padding: 15px;
        border-radius: 5px;
        animation: flashGreen 1s ease-out;
    }
    .flash-naranja {
        border: 2px solid #FFA500;
        background-color: rgba(255, 165, 0, 0.1);
        padding: 15px;
        border-radius: 5px;
        animation: flashOrange 1s ease-out;
    }
    .flash-rojo {
        border: 2px solid #F00;
        background-color: rgba(255, 0, 0, 0.1);
        padding: 15px;
        border-radius: 5px;
        animation: flashRed 1s ease-out;
    }
    
    /* Separador Hendidura */
    .separator-groove {
        border-top: 1px solid #444;
        border-bottom: 1px solid #222;
        margin: 20px 0;
        height: 2px;
    }
    
    /* Aviso Seguridad Footer */
    .footer-warning {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #FFFACD; /* Amarillo pálido */
        color: #333;
        text-align: center;
        padding: 5px;
        font-size: 12px;
        border-top: 1px solid #DDD;
        z-index: 1000;
    }
    /* Ajuste para que el footer no tape contenido */
    .block-container { padding-bottom: 50px; }
    </style>
    """, unsafe_allow_html=True)

    # Indicador Inteligente de Modelo (Dinámico)
    clean_model_name = st.session_state.active_model_name.replace("gemini-", "").replace("models/", "")
    st.markdown(f'<div class="model-indicator">MODEL: {clean_model_name}</div>', unsafe_allow_html=True)

# ==============================================================================
# 2. LÓGICA DE NEGOCIO Y CÁLCULO (BLINDADA)
# ==============================================================================

# --- CÁLCULO DE FG (CKD-EPI 2021) ---
def calculate_fg(creatinine, age, sex, weight):
    """
    Calcula el Filtrado Glomerular usando CKD-EPI (2021).
    BLINDAJE: Lógica matemática estricta.
    """
    try:
        if not creatinine or creatinine <= 0: return 0
        
        # Ajuste por sexo
        if sex == "Mujer":
            kappa = 0.7
            alpha = -0.241
            factor_sexo = 1.012 # Revisión 2021 sin raza
        else: # Hombre
            kappa = 0.9
            alpha = -0.302
            factor_sexo = 1.0

        scr_k = creatinine / kappa
        min_val = min(scr_k, 1)
        max_val = max(scr_k, 1)
        
        egfr = 142 * (min_val ** alpha) * (max_val ** -1.200) * (0.9938 ** age) * factor_sexo
        return round(egfr, 1)
    except:
        return 0

# --- CARGA DEL VADEMÉCUM (CACHE) ---
@st.cache_resource
def get_vademecum_data():
    """
    BLINDAJE: Carga única del PDF a memoria.
    Aquí simularemos la carga ya que no tengo el archivo físico.
    En producción: leer el PDF real.
    """
    try:
        # En un entorno real: text = extract_text_from_pdf("vademecum_renal.pdf")
        # Simulamos que tenemos el texto cargado para evitar errores si falta el archivo
        return "Contenido del Vademécum Renal cargado en memoria."
    except Exception as e:
        return f"Error cargando vademécum: {str(e)}"

# --- PROCESAMIENTO DE IMAGEN (IA) ---
def run_ia_transcription(image_bytes):
    """
    Transcribe medicamentos desde imagen.
    Usa Cascada de Modelos: 1.5 Pro -> 2.5 Flash
    """
    models_to_try = ["gemini-1.5-pro", "gemini-2.5-flash"]
    
    prompt = """
    Analiza esta imagen médica. Extrae SOLO la lista de medicamentos visibles.
    Devuelve un listado en texto plano, un medicamento por línea.
    Si no hay medicamentos, responde "No se detectaron medicamentos".
    NO incluyas saludos ni explicaciones.
    """
    
    for model_id in models_to_try:
        try:
            model = genai.GenerativeModel(model_id)
            # BLINDAJE: Envío de bytes de imagen
            response = model.generate_content([
                prompt,
                {"mime_type": "image/png", "data": image_bytes}
            ])
            
            # Actualizar indicador visual
            st.session_state.active_model_name = model_id
            return response.text
        except Exception as e:
            # Fallback silencioso
            continue
    
    return "Error: No se pudo transcribir la imagen tras intentar con todos los modelos."

# --- PROCESAMIENTO DE VALIDACIÓN (IA) ---
def run_ia_validation(med_list, fg_value, vademecum_text):
    """
    Valida medicamentos contra FG.
    FASE 2: Verifica caché local antes de llamar API.
    """
    models_to_try = ["gemini-1.5-pro", "gemini-2.5-flash"]
    
    # Construcción de Prompt Maestro de Validación
    prompt = f"""
    Actúa como experto nefrólogo.
    PACIENTE CON FG: {fg_value} mL/min.
    
    LISTA MEDICAMENTOS:
    {med_list}
    
    VADEMÉCUM (Contexto):
    {vademecum_text[:5000]} (Fragmento representativo)
    
    INSTRUCCIONES:
    1. Para cada fármaco, busca su ajuste renal.
    2. Si está en el vademecum, usa esa info.
    3. Si NO está, usa tu conocimiento médico (IA de respaldo).
    4. FORMATO SALIDA: Nombre Fármaco (Grupo Terapéutico)
    5. Genera dos bloques separados por "|||":
       Bloque 1: Resumen con iconos (⚠️, ⛔, ✅).
       Bloque 2: Acciones Clínicas (Explicación breve).
    
    REGLA: Si hay datos personales (nombres, DNI), responde SOLAMENTE: "PROTECCION_DATOS".
    """

    # FASE 2: Chequeo de Caché (Simplificado para el ejemplo)
    # En producción, esto iteraría medicamento por medicamento
    cache_key = f"{med_list.strip()}_{fg_value}"
    if cache_key in st.session_state.memoria_farmacos:
        return st.session_state.memoria_farmacos[cache_key]

    for model_id in models_to_try:
        try:
            model = genai.GenerativeModel(model_id)
            response = model.generate_content(prompt)
            result = response.text
            
            # Actualizar indicador
            st.session_state.active_model_name = model_id
            
            # FASE 2: Guardar en caché
            st.session_state.memoria_farmacos[cache_key] = result
            return result
        except:
            continue
            
    return "Error de conexión o cuota superada."

# ==============================================================================
# 3. INTERFAZ DE USUARIO (UI)
# ==============================================================================

def main():
    inject_ui_styles()
    
    # Cabecera
    st.title("ASISTENTE RENAL")
    
    # Pestañas
    tab_validacion, tab_informe, tab_excel, tab_graficos = st.tabs(
        ["💊 VALIDACIÓN", "📄 INFORME", "📊 EXCEL", "📈 GRÁFICOS"]
    )
    
    # --- PESTAÑA VALIDACIÓN (ACTIVA) ---
    with tab_validacion:
        
        # FASE 2: Bloque de Registro (Campos Silenciosos)
        st.markdown("### Datos del Paciente")
        col_reg1, col_reg2, col_reg3, col_reg4 = st.columns([2, 1, 1, 2])
        
        with col_reg1:
            centro = st.text_input("Centro", key="reg_centro")
        with col_reg2:
            edad_reg = st.number_input("Edad", min_value=0, max_value=120, value=65, key="reg_edad")
        with col_reg3:
            residencia = st.checkbox("Residencia", key="reg_residencia")
            alfanum = st.text_input("Ref", placeholder="Alf", key="reg_alfa")
        with col_reg4:
            fecha_actual = datetime.date.today().strftime("%d/%m/%Y")
            st.text_input("Fecha", value=fecha_actual, disabled=True)
            
        # Generación dinámica de ID (Silenciosa)
        id_paciente = f"{centro or 'GEN'}-{edad_reg}-{alfanum or '000'}"
        st.caption(f"ID Registro: {id_paciente}")

        st.markdown("---")

        # --- ÁREA DE TRABAJO DUAL (CALCULADORA | AJUSTE) ---
        col_calc, col_adjust = st.columns(2)
        
        # 1. CALCULADORA (Izquierda)
        with col_calc:
            st.subheader("📋 Calculadora")
            st.caption("Método: CKD-EPI 2021")
            
            with st.container(border=True):
                c_age = st.number_input("Edad (años)", value=edad_reg, step=1)
                c_weight = st.number_input("Peso (kg)", value=70.0, step=0.1)
                c_creat = st.number_input("Creatinina (mg/dL)", value=1.0, step=0.01)
                c_sex = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
                
                fg_calculado = calculate_fg(c_creat, c_age, c_sex, c_weight)

        # 2. AJUSTE Y CAPTURA (Derecha - Simetría Blindada)
        with col_adjust:
            st.subheader("💊 Ajuste y Captura")
            
            # Input Manual (Prioritario)
            fg_manual_str = st.text_input("FG Manual (Opcional)", placeholder="Escribir valor...")
            
            # Lógica FG Final
            if fg_manual_str and fg_manual_str.isnumeric():
                fg_final = float(fg_manual_str)
                metodo_display = "Manual"
            else:
                fg_final = fg_calculado
                metodo_display = "Fórmula CKD-EPI"
            
            # Espaciador
            st.write("")
            
            # Display FG Glow Morado
            st.markdown(f"""
            <div class="fg-glow-box">
                <div class="fg-value">{fg_final} mL/min</div>
                <div class="fg-label">{metodo_display}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("") # Espaciador
            
            # Zona de Carga Multimodal
            upload_col, paste_col = st.columns([0.7, 0.3])
            
            # Subida Archivo
            with upload_col:
                uploaded_file = st.file_uploader("Subir imagen", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
            
            # Pegado (Simulado con botón, requiere componente extra en prod, aquí simplificado)
            # Nota: Streamlit nativo no soporta paste directo sin componentes custom,
            # pero simulamos la lógica con el file uploader como entrada principal.
            
            # LÓGICA DE PROCESAMIENTO DE IMAGEN
            # BLINDAJE: Conversión RGB y Transcripción
            if uploaded_file is not None:
                try:
                    # 1. Image Open
                    image = Image.open(uploaded_file)
                    # 2. Convert RGB (SAGRADO)
                    img_rgb = image.convert("RGB")
                    
                    # Preparar bytes para API
                    buf = io.BytesIO()
                    img_rgb.save(buf, format="PNG")
                    img_bytes = buf.getvalue()
                    
                    # Llamada a IA (Solo si cambió la imagen)
                    # Usamos un hash simple o flag para no re-procesar en cada rerun
                    file_id = uploaded_file.file_id
                    if 'last_processed_file' not in st.session_state or st.session_state.last_processed_file != file_id:
                        with st.spinner("🧠 IA Transcribiendo..."):
                            transcripcion = run_ia_transcription(img_bytes)
                            st.session_state.meds_input = transcripcion
                            st.session_state.last_processed_file = file_id
                            st.rerun() # Blindaje de flujo
                except Exception as e:
                    st.error(f"Error procesando imagen: {e}")

        # 3. HENDIDURA DE SEPARACIÓN
        st.markdown('<div class="separator-groove"></div>', unsafe_allow_html=True)
        
        # 4. LISTADO DE MEDICAMENTOS
        st.subheader("📝 Listado de medicamentos")
        meds_text = st.text_area(
            "Escribe o edita la lista...",
            value=st.session_state.meds_input,
            height=150,
            key="meds_area"
        )
        # Sincronización bidireccional
        st.session_state.meds_input = meds_text

        # 5. BOTONERA DUAL (85/15)
        btn_col1, btn_col2 = st.columns([0.85, 0.15])
        
        run_validation = False
        reset_app = False
        
        with btn_col1:
            run_validation = st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True)
        
        with btn_col2:
            reset_app = st.button("🗑️ RESET", use_container_width=True)
            
        if reset_app:
            st.session_state.meds_input = ""
            st.session_state.cache_result = None
            st.session_state.reset_counter += 1 # Truco para limpiar estado
            st.rerun()

        # 6. RESULTADOS
        # Si se pulsa validar o ya hay resultado en caché
        if run_validation or st.session_state.cache_result:
            
            if not meds_text.strip():
                st.warning("Por favor, introduce medicamentos.")
            else:
                # Si es una nueva validación (botón pulsado), ejecutar IA
                if run_validation:
                    with st.spinner("Analizando Vademécum y Guías..."):
                        vademecum_data = get_vademecum_data()
                        resultado_raw = run_ia_validation(meds_text, fg_final, vademecum_data)
                        st.session_state.cache_result = resultado_raw
                
                # Mostrar Resultado
                res = st.session_state.cache_result
                
                if "PROTECCION_DATOS" in res:
                    st.error("🔒 No se puede mostrar el resultado al encontrar datos personales.")
                elif "|||" in res:
                    parts = res.split("|||")
                    resumen = parts[0]
                    acciones = parts[1] if len(parts) > 1 else ""
                    
                    # Determinar color del cuadro (Lógica simple basada en iconos)
                    if "⛔" in resumen:
                        class_css = "flash-rojo"
                    elif "⚠️" in resumen:
                        class_css = "flash-naranja"
                    else:
                        class_css = "flash-verde"
                    
                    st.markdown("### 📊 Resultado del Análisis")
                    
                    # Cuadro 1: Resumen
                    st.markdown(f"""
                    <div class="{class_css}">
                        <strong>RESUMEN DE AFECTACIÓN:</strong><br>
                        {resumen.replace(chr(10), '<br>')}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Cuadro 2: Acciones Clínicas
                    st.markdown("### 🩺 Acciones Clínicas Sugeridas")
                    st.info(acciones)
                    
                    # Botón Excel (Visual)
                    st.button("💾 GUARDAR EN EXCEL (Pendiente)")
                    
                else:
                    # Fallback si el formato no es perfecto
                    st.write(res)

    # --- FOOTER PERMANENTE ---
    st.markdown("""
    <div class="footer-warning">
        ⚠️ Aviso: Esta herramienta es un apoyo a la revisión farmacoterapéutica. Puede contener errores. Verifique con fuentes oficiales.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
