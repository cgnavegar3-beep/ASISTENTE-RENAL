import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import io
import hashlib

# --- 1. CONFIGURACIÓN Y GESTIÓN DE MODELOS (CASCADA) ---
MODELS = ["gemini-1.5-pro", "gemini-1.5-flash"]

def get_model_display_name():
    """Detecta el modelo activo y limpia el nombre para el indicador."""
    if 'active_model_idx' not in st.session_state:
        st.session_state.active_model_idx = 0
    # Elimina "gemini-" y formatea (ej. 1.5 Flash)
    return MODELS[st.session_state.active_model_idx].replace("gemini-", "").replace("-", " ").title()

def run_ia_task(prompt, image=None):
    """Ejecuta tareas de IA con fallback automático ante errores o cuotas."""
    for i in range(st.session_state.active_model_idx, len(MODELS)):
        try:
            current_model_id = MODELS[i]
            genai.configure(api_key=st.secrets["API_KEY"])
            model = genai.GenerativeModel(current_model_id)
            
            content = [prompt, image] if image else [prompt]
            response = model.generate_content(content)
            
            # Si tiene éxito, guardamos este índice como el activo
            st.session_state.active_model_idx = i 
            return response.text
        except Exception:
            continue
    return "Fallo de conexión o superado el número de intentos"

# --- 2. RECURSOS Y CACHÉ ---
@st.cache_resource
def load_vademecum():
    try:
        with fitz.open("vademecum_renal.pdf") as doc:
            return "".join([page.get_text() for page in doc])
    except:
        return "Error: Archivo 'vademecum_renal.pdf' no encontrado."

# --- 3. ESTILOS CSS (GLOW, DESTELLO Y SIMETRÍA) ---
def inject_custom_styles():
    st.markdown(f"""
    <style>
        /* Indicador de Versión Dinámico y Discreto */
        .discreet-v {{
            position: fixed; top: 0; left: 0;
            background-color: #000; color: #0F0;
            padding: 5px 15px; font-family: monospace; font-size: 11px;
            z-index: 999999; border-bottom-right-radius: 10px; border: 1px solid #333;
        }}
        
        /* Cuadro FG Negro con Glow Morado */
        .fg-glow-box {{
            background-color: #000 !important; color: #fff !important;
            padding: 20px; border-radius: 12px; text-align: center;
            border: 2px solid #6a0dad; box-shadow: 0 0 20px #a020f0;
            margin: 10px 0;
        }}
        .fg-glow-box h1 {{ font-size: 50px !important; margin: 0 !important; line-height: 1; color: #fff !important; }}
        .fg-glow-box p {{ font-size: 13px; margin: 5px 0 0 0; opacity: 0.8; }}

        /* Animación de Destello (Flash Glow) al aparecer resultados */
        @keyframes flash-glow {{
            0% {{ opacity: 0; filter: brightness(3) cubic-bezier(0.1, 0.7, 1.0, 0.1); }}
            100% {{ opacity: 1; filter: brightness(1); }}
        }}
        .result-card {{
            animation: flash-glow 0.8s ease-out;
            padding: 20px; border-radius: 15px; margin-top: 15px; color: #000;
            border: 1px solid rgba(0,0,0,0.1);
        }}

        /* Alineación superior forzada de columnas */
        [data-testid="column"] {{ display: flex; flex-direction: column; justify-content: flex-start !important; }}
        
        /* Aviso Profesional */
        .aviso-prof {{
            background-color: #fffde7; padding: 12px; border-radius: 8px;
            border-left: 5px solid #ffd600; font-size: 13px; margin: 20px 0;
        }}
    </style>
    <div class="discreet-v">{get_model_display_name()}</div>
    """, unsafe_allow_html=True)

# --- 4. MÓDULOS DE INTERFAZ ---
def modulo_calculadora_fg():
    col_izq, col_der = st.columns([0.4, 0.6], gap="large")
    
    with col_izq:
        st.subheader("📋 Calculadora")
        ed = st.number_input("Edad", 18, 110, 75, key="ed")
        ps = st.number_input("Peso (kg)", 35, 180, 70, key="ps")
        cr = st.number_input("Creatinina (mg/dL)", 0.4, 15.0, 1.1, key="cr")
        sx = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True, key="sx")
        
        # Ecuación Cockcroft-Gault (o CKD-EPI)
        f_sex = 0.85 if sx == "Mujer" else 1.0
        fg_auto = round((((140 - ed) * ps) / (72 * cr)) * f_sex, 1)

    with col_der:
        # Espejo nativo para alineación perfecta
        st.subheader(" ") 
        fg_man = st.text_input("Filtrado Glomerular Manual (opcional)", 
                              placeholder=f"Auto: {fg_auto}")
        
        # Lógica robusta de entrada (comas/puntos)
        try:
            fg_final = round(float(fg_man.replace(",", ".").strip()), 1) if fg_man else fg_auto
        except:
            fg_final = fg_auto
            
        st.markdown(f"""
            <div class="fg-glow-box">
                <h1>{fg_final}</h1>
                <p>mL/min (FG Final) <br> <small>Método: {"Manual" if fg_man else "Cockcroft-Gault"}</small></p>
            </div>
        """, unsafe_allow_html=True)
        
        # Carga de Medicación
        st.write("**Listado / Recorte de Medicación**")
        c1, c2 = st.columns([0.7, 0.3])
        img_input = None
        with c1:
            f = st.file_uploader("Subir imagen", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
            if f: img_input = Image.open(f).convert("RGB")
        with c2:
            try:
                from streamlit_paste_button import paste_image_button
                p = paste_image_button("📋 Pegar")
                if p and p.image_data: img_input = p.image_data.convert("RGB")
            except ImportError: pass

    return fg_final, img_input

def validar_medicacion(fg, meds_text, v_text):
    if not meds_text:
        st.warning("Escribe o carga una lista de medicamentos primero.")
        return

    # Protección de datos sensibles
    if any(k in meds_text.lower() for k in ["dni", "nombre:", "tel:", "dirección"]):
        st.error("Fallo de conexión o superado el número de intentos")
        return

    # Caché por Hash
    cache_key = hashlib.md5(f"{fg}{meds_text}".encode()).hexdigest()
    if 'cache' not in st.session_state: st.session_state.cache = {}
    
    if cache_key in st.session_state.cache:
        resultado = st.session_state.cache[cache_key]
    else:
        with st.spinner("Analizando seguridad renal..."):
            prompt = f"""
            FG Paciente: {fg} mL/min.
            Vademécum (fragmento): {v_text[:7000]}
            Lista: {meds_text}
            
            Tarea:
            1. Cruza cada fármaco con el FG. 
            2. Clasifica el riesgo: VERDE (Dosis estándar), NARANJA (Ajustar dosis ⚠️), ROJO (Contraindicado ⛔).
            3. Devuelve primero el color predominante (ROJO, NARANJA o VERDE).
            4. Genera un resumen clínico directo por cada fármaco afectado.
            """
            resultado = run_ia_task(prompt)
            st.session_state.cache[cache_key] = resultado

    # Renderizado con Destello (Flash Glow)
    if "Fallo" in resultado:
        st.error(resultado)
    else:
        color_map = {"ROJO": "#ffcdd2", "NARANJA": "#ffe0b2", "AMARILLO": "#ffe0b2", "VERDE": "#c8e6c9"}
        bg = "#f0f2f6"
        for k, v in color_map.items():
            if k in resultado.upper()[:20]: bg = v; break
            
        st.markdown(f"""<div class="result-card" style="background-color: {bg};">{resultado}</div>""", unsafe_allow_html=True)

# --- 5. APP PRINCIPAL ---
def main():
    inject_custom_styles()
    v_text = load_vademecum()
    
    st.title("ASISTENTE RENAL")
    
    tab1, tab2 = st.tabs(["💊 Validación Renal", "📊 Otras Consultas"])
    
    with tab1:
        fg_final, img_obj = modulo_calculadora_fg()
        
        # Si hay imagen, la IA extrae el texto
        if img_obj:
            with st.spinner("Leyendo medicamentos..."):
                extracted = run_ia_task("Extrae solo nombres y dosis de medicamentos de esta imagen:", img_obj)
                if "Fallo" not in extracted:
                    st.session_state.meds_input = extracted

        st.write("---")
        meds_final = st.text_area("Listado de medicamentos", 
                                 value=st.session_state.get('meds_input', ""),
                                 placeholder="Escribe o edita la lista que se reproducirá aquí si se ha pegado un RECORTE...",
                                 height=180)
        
        if st.button("🚀 VALIDAR MEDICACIÓN", use_container_width=True):
            validar_medicacion(fg_final, meds_final, v_text)

    with tab2:
        st.info("Módulos adicionales de interacciones y adecuación geriátrica en desarrollo.")

    # Footer y Reset
    st.markdown("""<div class="aviso-prof">⚠️ Aviso: Esta herramienta es un apoyo a la revisión farmacoterapéutica. Verifique siempre con fuentes oficiales.</div>""", unsafe_allow_html=True)
    
    if st.button("🗑️ Reset Paciente"):
        for k in ["meds_input", "cache"]: 
            if k in st.session_state: del st.session_state[k]
        st.rerun()

if __name__ == "__main__":
    if 'meds_input' not in st.session_state: st.session_state.meds_input = ""
    main()
