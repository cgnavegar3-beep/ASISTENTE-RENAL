import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import io
import numpy as np

# --- 1. CONFIGURACIÓN E INICIALIZACIÓN ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

if 'active_model_name' not in st.session_state:
    st.session_state.active_model_name = "1.5 Pro"
if 'meds_input' not in st.session_state:
    st.session_state.meds_input = ""
if 'cache_result' not in st.session_state:
    st.session_state.cache_result = None
if 'last_query' not in st.session_state:
    st.session_state.last_query = ""
if 'reset_counter' not in st.session_state:
    st.session_state.reset_counter = 0

# --- 2. GESTIÓN DE MODELOS (CASCADA CON FALLBACK) ---
def run_ia_task(prompt, image_bytes=None):
    models_to_try = [
        ("gemini-1.5-pro", "1.5 Pro"),
        ("gemini-2.5-flash", "2.5 Flash")
    ]
    for model_id, tech_name in models_to_try:
        try:
            # Actualizamos nombre para el indicador (sin gemini-)
            clean_name = tech_name.replace("gemini-", "")
            st.session_state.active_model_name = clean_name
            
            genai.configure(api_key=st.secrets["API_KEY"])
            model = genai.GenerativeModel(model_id)
            content = [prompt] if prompt else []
            if image_bytes:
                content.append({'mime_type': 'image/png', 'data': image_bytes})
            
            response = model.generate_content(content)
            return response.text
        except Exception:
            continue
    return "Fallo de conexión o superado el número de intentos"

# --- 3. LECTURA DE PDF (BLINDADO) ---
@st.cache_resource
def get_vademecum_data():
    try:
        doc = fitz.open("vademecum_renal.pdf")
        return "".join([page.get_text() for page in doc])
    except: return ""

# --- 4. ESTILOS CSS (ESTRUCTURA BLINDADA Y ACTUALIZADA) ---
def inject_ui_styles():
    # Limpiamos el nombre del modelo para el display
    display_model = st.session_state.active_model_name.replace("gemini-", "")
    
    st.markdown(f"""
    <style>
        /* 1. INDICADOR INTELIGENTE DE MODELO */
        .model-indicator {{
            position: fixed; top: 50px; left: 10px; background-color: #000; color: #0F0;
            padding: 5px 15px; font-family: 'Courier New', monospace; font-size: 13px;
            font-weight: bold; border-radius: 5px; z-index: 999999; border: 1px solid #333;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.5);
        }}
        
        /* Pestañas: Activa con línea ROJA y negrita */
        div[role="tablist"] {{ gap: 10px; }}
        div[role="tab"][aria-selected="true"] {{
            color: #000 !important; 
            font-weight: bold !important; 
            border-bottom: 3px solid red !important;
        }}
        
        /* Display FG Glow Morado */
        .fg-glow-box {{
            background-color: #000; color: #fff; border-radius: 12px;
            padding: 15px; text-align: center; border: 2px solid #6a0dad;
            box-shadow: 0 0 20px #a020f0; margin: 5px 0; display: flex;
            flex-direction: column; justify-content: center;
        }}
        .fg-glow-box h1 {{ margin: 0; font-size: 45px; color: #fff !important; line-height: 1; }}
        
        /* Animación Flash Glow */
        @keyframes flash-glow {{
            0% {{ filter: brightness(1); }}
            50% {{ filter: brightness(1.6); }}
            100% {{ filter: brightness(1); }}
        }}
        
        /* Clases para resultados dinámicos */
        .flash-verde {{
            background-color: #e8f5e9; border: 2px solid #4caf50; color: #1b5e20;
            animation: flash-glow 0.8s ease-in-out;
            padding: 15px; border-radius: 10px; margin-bottom: 15px;
            box-shadow: 0 0 15px #4caf50;
        }}
        .flash-naranja {{
            background-color: #fff3e0; border: 2px solid #ff9800; color: #e65100;
            animation: flash-glow 0.8s ease-in-out;
            padding: 15px; border-radius: 10px; margin-bottom: 15px;
            box-shadow: 0 0 15px #ff9800;
        }}
        .flash-rojo {{
            background-color: #ffebee; border: 2px solid #f44336; color: #b71c1c;
            animation: flash-glow 0.8s ease-in-out;
            padding: 15px; border-radius: 10px; margin-bottom: 15px;
            box-shadow: 0 0 15px #f44336;
        }}
        
        /* Cuadro Acciones Clínicas */
        .acciones-clinicas {{
            background-color: #f5f5f5; border-left: 5px solid #333;
            padding: 15px; border-radius: 5px; margin-top: 10px;
        }}
        
        /* Aviso Seguridad Footer */
        .aviso-prof {{
            background-color: #fff9c4; padding: 12px; border-radius: 8px;
            border: 1px solid #fbc02d; font-size: 13px; margin-top: 25px;
            text-align: center; box-shadow: 2px 2px 8px rgba(0,0,0,0.05);
        }}
        
        [data-testid="column"] {{ display: flex; flex-direction: column; justify-content: space-between; }}
    </style>
    <div class="model-indicator">{display_model}</div>
    """, unsafe_allow_html=True)

# --- 5. LÓGICA DE VALIDACIÓN ---
def render_tab_validacion():
    col_izq, col_der = st.columns(2, gap="large")
    
    # --- COLUMNA IZQUIERDA: CALCULADORA ---
    with col_izq:
        st.subheader("📋 Calculadora")
        st.caption("Método: Cockcroft-Gault") 
        with st.container(border=True):
            ed = st.number_input("Edad", 18, 110, 75)
            ps = st.number_input("Peso (kg)", 35, 180, 70)
            cr = st.number_input("Creatinina (mg/dL)", 0.4, 15.0, 1.1)
            sx = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
            
            # --- Lógica de cálculo blindada (NO TOCAR) ---
            f_sex = 0.85 if sx == "Mujer" else 1.0
            fg_calc = round((((140 - ed) * ps) / (72 * cr)) * f_sex, 1)
            # ---------------------------------------------

    # --- COLUMNA DERECHA: AJUSTE Y CAPTURA ---
    with col_der:
        st.subheader("💊 Ajuste y Captura")
        fg_man = st.text_input("Introducir FG Manual", placeholder="Vacío para auto-cálculo")
        
        # Prioridad Manual > Calculado
        fg_final = float(fg_man.replace(",", ".")) if fg_man and fg_man.replace(",",".").replace(".","").isdigit() else fg_calc
        metodo = "Manual" if fg_man else "Cockcroft-Gault" # Ajustado etiqueta
        
        # Separador visual
        st.write("")
        
        # Display Glow Morado
        st.markdown(f"""
            <div class="fg-glow-box" style="height: 120px;">
                <h1>{fg_final}</h1>
                <div style="font-size: 10px; color: #aaa; margin-top: 5px;">mL/min (FG) - {metodo}</div>
            </div>
        """, unsafe_allow_html=True)

        st.write("") # Separador
        
        # --- ZONA DE CARGA MULTIMODAL (CORREGIDA) ---
        c_file, c_paste = st.columns([0.6, 0.4])
        img_processed = None
        
        with c_file:
            uploaded_file = st.file_uploader("Subir", type=['png','jpg','jpeg'], label_visibility="collapsed", key=f"up_{st.session_state.reset_counter}")
            if uploaded_file:
                img_processed = Image.open(uploaded_file).convert("RGB")
        
        with c_paste:
            try:
                from streamlit_paste_button import paste_image_button
                p = paste_image_button("📋 Pegar Recorte", key=f"paste_{st.session_state.reset_counter}")
                if p and p.image_data is not None:
                    # Blindaje: conversión a RGB
                    if isinstance(p.image_data, Image.Image):
                         img_processed = p.image_data.convert("RGB")
                    else:
                         img_processed = Image.fromarray(np.uint8(p.image_data)).convert("RGB")
            except Exception as e:
                pass

        # --- LÓGICA DE PROCESAMIENTO INMEDIATO ---
        # Si hay imagen, procesamos ANTES de pintar el text_area y hacemos rerun
        if img_processed:
            buf = io.BytesIO()
            img_processed.save(buf, format="PNG")
            with st.spinner("TRANSCRIBIENDO MEDICAMENTOS..."):
                # Prompt específico para transcripción
                prompt_ocr = "Actúa como transcriptor médico. Extrae el listado de medicamentos y dosis de esta imagen. Devuelve SOLO la lista en texto plano, uno por línea. Si detectas nombres de pacientes o DNI, devuelve ERROR_PRIVACIDAD."
                res_ocr = run_ia_task(prompt_ocr, buf.getvalue())
                
                if "ERROR_PRIVACIDAD" in res_ocr:
                    st.error("⚠️ No se puede mostrar el resultado al encontrar datos personales.")
                elif "Fallo" not in res_ocr:
                    st.session_state.meds_input = res_ocr
                    st.rerun()

    # --- LÍNEA DE SEPARACIÓN ---
    st.markdown("---")

    # --- LISTADO DE MEDICAMENTOS ---
    meds_text = st.text_area(
        "Listado de medicamentos",
        value=st.session_state.meds_input,
        placeholder="Escribe o edita la lista del archivo o captura subidos...",
        height=180,
        key=f"meds_area_{st.session_state.reset_counter}"
    )
    # Sincronizar estado manual
    st.session_state.meds_input = meds_text

    # --- BOTONERA DUAL (85/15) ---
    c_act1, c_act2 = st.columns([0.85, 0.15])
    with c_act1:
        validar_click = st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True)
    with c_act2:
        if st.button("🗑️ RESET", use_container_width=True):
            st.session_state.meds_input = ""
            st.session_state.cache_result = None
            st.session_state.reset_counter += 1
            st.rerun()

    # --- LÓGICA DE RESULTADOS ---
    if validar_click:
        if not meds_text.strip():
            st.warning("Por favor, introduce o carga un listado de medicamentos.")
        else:
            query_id = f"{fg_final}-{meds_text}"
            
            # Comprobar Caché
            if query_id == st.session_state.last_query and st.session_state.cache_result:
                final_response = st.session_state.cache_result
            else:
                v_data = get_vademecum_data()
                # PROMPT MAESTRO CONSTRUIDO
                prompt_maestro = f"""
                ERES UN ASISTENTE DE ADECUACIÓN RENAL.
                DATOS PACIENTE: FG = {fg_final} mL/min.
                LISTADO MEDICAMENTOS:
                {meds_text}

                INSTRUCCIONES:
                1. Busca cada fármaco en el siguiente TEXTO DEL VADEMÉCUM (Lee solo una vez):
                --- INICIO VADEMECUM FRAGMENTO ---
                {v_data[:10000]} 
                --- FIN VADEMECUM ---
                (Nota: El PDF tiene columnas: Fármaco | Dosis | Método | ... | 100-50 | 50-10 | <10).
                Selecciona la columna correcta según el FG del paciente ({fg_final}).

                2. Si el fármaco NO está en el texto, usa tu conocimiento médico oficial.
                
                3. FORMATO DE RESPUESTA ESTRICTO (JSON IMPLÍCITO):
                Debes devolver la respuesta en dos partes separadas por la cadena "||SEPARATOR||".
                
                PARTE 1: RESUMEN
                Determina el color global: VERDE (todo bien), NARANJA (ajustes moderados), ROJO (contraindicación).
                Lista los medicamentos con iconos:
                - (Sin icono) si está bien.
                - ⚠️ si requiere precaución/ajuste.
                - ⛔ si está contraindicado.
                SOLO NOMBRES Y DOSIS RECOMENDADA CORTA.

                PARTE 2: ACCIONES CLÍNICAS
                Texto explicativo breve, directo y profesional. Sin saludos. Explicación clínica.

                EJEMPLO SALIDA:
                COLOR: ROJO
                * ⛔ Metformina: Contraindicado con FG < 30.
                * ⚠️ Digoxina: Reducir dosis.
                ||SEPARATOR||
                **Metformina**: Riesgo de acidosis láctica. Suspender.
                **Digoxina**: Rango terapéutico estrecho, monitorizar niveles.
                """
                
                with st.spinner("ANALIZANDO VADEMÉCUM Y GUÍAS..."):
                    final_response = run_ia_task(prompt_maestro)
                    st.session_state.cache_result = final_response
                    st.session_state.last_query = query_id

            # --- RENDERIZADO DE RESULTADOS (2 CUADROS) ---
            try:
                if "||SEPARATOR||" in final_response:
                    part_resumen, part_acciones = final_response.split("||SEPARATOR||")
                else:
                    part_resumen = final_response
                    part_acciones = "No se generaron acciones específicas."

                # Determinar Estilo (Parsing simple del texto)
                clase_css = "flash-verde" # Default
                if "ROJO" in part_resumen or "⛔" in part_resumen:
                    clase_css = "flash-rojo"
                elif "NARANJA" in part_resumen or "⚠️" in part_resumen:
                    clase_css = "flash-naranja"
                
                # Limpiar texto de control "COLOR: ..."
                part_resumen = part_resumen.replace("COLOR: ROJO", "").replace("COLOR: NARANJA", "").replace("COLOR: VERDE", "")

                # 1. CUADRO RESUMEN (GLOW)
                st.markdown(f'<div class="{clase_css}"><h3>RESUMEN DE ADECUACIÓN</h3>{part_resumen}</div>', unsafe_allow_html=True)
                
                # 2. CUADRO ACCIONES CLÍNICAS
                st.markdown(f'<div class="acciones-clinicas"><h4>📋 ACCIONES CLÍNICAS</h4>{part_acciones}</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error("Error al procesar formato de respuesta. Intente de nuevo.")
                st.write(final_response)

    # --- 4. AVISO DE SEGURIDAD (PERMANENTE) ---
    st.markdown('<div class="aviso-prof">⚠️ Aviso: Esta herramienta es un apoyo a la revisión farmacoterapéutica. Puede contener errores. Verifique con fuentes oficiales.</div>', unsafe_allow_html=True)

# --- 6. ESTRUCTURA PRINCIPAL ---
def main():
    inject_ui_styles()
    st.title("ASISTENTE RENAL")
    
    t1, t2, t3, t4 = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 EXCEL", "📈 GRÁFICOS"])
    
    with t1:
        render_tab_validacion()
    with t2:
        st.info("Pestaña Informe...")
    with t3:
        st.info("Pestaña Excel...")
    with t4:
        st.info("Pestaña Gráficos...")

if __name__ == "__main__":
    main()



