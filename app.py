import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import io
import hashlib
import numpy as np

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

# --- 2. GESTIÓN DE MODELOS (CASCADA: 1.5 PRO -> 1.5 FLASH) ---
MODELS = ["gemini-1.5-pro", "gemini-1.5-flash"]

def get_active_model_name():
    if 'active_model_idx' not in st.session_state:
        st.session_state.active_model_idx = 0
    raw_name = MODELS[st.session_state.active_model_idx]
    # Limpieza: "gemini-1.5-pro" -> "1.5 Pro"
    return raw_name.replace("gemini-", "").replace("-", " ").title()

def run_ia_task(prompt, image=None):
    """Intenta con 1.5 Pro, si falla salta a 1.5 Flash."""
    for i in range(st.session_state.active_model_idx, len(MODELS)):
        try:
            current_model_id = MODELS[i]
            genai.configure(api_key=st.secrets["API_KEY"])
            model = genai.GenerativeModel(current_model_id)
            content = [prompt, image] if image else [prompt]
            response = model.generate_content(content)
            st.session_state.active_model_idx = i 
            return response.text
        except Exception:
            continue
    return "Fallo de conexión o límite de cuota superado"

# --- 3. RECURSOS Y ESTILOS (SIN F-STRINGS PARA EVITAR SYNTAX ERROR) ---
@st.cache_resource
def load_vademecum():
    try:
        doc = fitz.open("vademecum_renal.pdf")
        return "".join([page.get_text() for page in doc])
    except:
        return "Error: No se encontró vademecum_renal.pdf"

def inject_ui_styles():
    model_name = get_active_model_name()
    # String normal para que las llaves { } del CSS no den SyntaxError
    style_html = """
    <style>
        .discreet-v {
            position: fixed; top: 0; left: 0; background-color: #000; color: #0F0;
            padding: 5px 15px; font-family: monospace; font-size: 11px;
            z-index: 999999; border-bottom-right-radius: 10px; border: 1px solid #333;
        }
        .fg-glow-box {
            background-color: #000 !important; color: #fff !important;
            padding: 15px; border-radius: 12px; text-align: center;
            border: 2px solid #6a0dad; box-shadow: 0 0 20px #a020f0; margin: 10px 0;
        }
        .fg-glow-box h1 { font-size: 48px !important; margin: 0; color: #fff !important; }
        
        @keyframes flash-destello {
            0% { opacity: 0; filter: brightness(5); transform: scale(0.98); }
            100% { opacity: 1; filter: brightness(1); transform: scale(1); }
        }
        
        [data-testid="column"] { 
            display: flex; 
            flex-direction: column; 
            justify-content: flex-start !important; 
        }
        
        .result-card { 
            animation: flash-destello 0.7s ease-out; 
            padding: 20px; border-radius: 15px; margin-top: 15px; color: #000; 
        }
        
        .aviso-prof { 
            background-color: #fffde7; padding: 12px; border-radius: 8px; 
            border-left: 5px solid #ffd600; font-size: 13px; margin-top: 20px; 
        }
    </style>
    <div class="discreet-v">""" + model_name + """</div>"""
    
    st.markdown(style_html, unsafe_allow_html=True)

# --- 4. MÓDULO VALIDACIÓN ---
def render_tab_validacion(v_text):
    col_izq, col_der = st.columns([0.4, 0.6], gap="large")
    
    with col_izq:
        st.subheader("📋 Datos Paciente")
        ed = st.number_input("Edad", 18, 110, 75, key="calc_ed")
        ps = st.number_input("Peso (kg)", 35, 180, 70, key="calc_ps")
        cr = st.number_input("Creatinina (mg/dL)", 0.4, 15.0, 1.1, key="calc_cr")
        sx = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True, key="calc_sx")
        f_sex = 0.85 if sx == "Mujer" else 1.0
        fg_auto = round((((140 - ed) * ps) / (72 * cr)) * f_sex, 1)

    with col_der:
        st.subheader(" ") 
        fg_man = st.text_input("Introducir FG Manual (opcional)", placeholder="Cálculo auto: " + str(fg_auto))
        try:
            fg_final = round(float(fg_man.replace(",", ".").strip()), 1) if fg_man else fg_auto
        except:
            fg_final = fg_auto
            
        st.markdown('<div class="fg-glow-box"><h1>' + str(fg_final) + '</h1><p>mL/min (FG Final)</p></div>', unsafe_allow_html=True)
        
        st.write("**Captura de Medicación (Subir o Pegar)**")
        c1, c2 = st.columns([0.7, 0.3])
        img_final = None
        with c1:
            f = st.file_uploader("Archivo", type=['png','jpg','jpeg'], label_visibility="collapsed")
            if f: img_final = Image.open(f).convert("RGB")
        with c2:
            try:
                from streamlit_paste_button import paste_image_button
                p = paste_image_button("📋 Pegar Recorte")
                if p and p.image_data is not None:
                    if isinstance(p.image_data, Image.Image):
                        img_final = p.image_data.convert("RGB")
                    else:  
                        img_final = Image.fromarray(np.uint8(p.image_data)).convert("RGB")
            except: pass

    # Volcado automático tras OCR
    if img_final:
        with st.spinner("Leyendo imagen..."):
            res = run_ia_task("Extrae solo los nombres de fármacos y dosis de esta imagen. Texto limpio.", img_final)
            if "Fallo" not in res:
                st.session_state.meds_input = res
                st.rerun()

    st.write("---")
    meds_text = st.text_area("Listado de medicamentos para validar", 
                            value=st.session_state.get('meds_input', ""),
                            placeholder="Escribe o pega aquí la lista...",
                            height=180)

    if st.button("🚀 VALIDAR AJUSTE RENAL", use_container_width=True):
        if meds_text:
            cache_key = hashlib.md5((str(fg_final) + meds_text).encode()).hexdigest()
            if 'cache_val' not in st.session_state: st.session_state.cache_val = {}
            
            if cache_key in st.session_state.cache_val:
                res = st.session_state.cache_val[cache_key]
            else:
                with st.spinner("Consultando Vademécum..."):
                    prompt = "FG: " + str(fg_final) + ". Vademécum: " + v_text[:7000] + ". Lista: " + meds_text + ". Analiza ajustes (⚠️) o contraindicaciones (⛔) por fármaco."
                    res = run_ia_task(prompt)
                    st.session_state.cache_val[cache_key] = res

            bg = "#ffcdd2" if "⛔" in res else "#ffe0b2" if "⚠️" in res else "#c8e6c9"
            st.markdown('<div class="result-card" style="background-color: ' + bg + ';">' + res + '</div>', unsafe_allow_html=True)

# --- 5. ESTRUCTURA DE PESTAÑAS ---
def main():
    if 'meds_input' not in st.session_state: st.session_state.meds_input = ""
    inject_ui_styles()
    v_text = load_vademecum()
    
    st.title("ASISTENTE RENAL")
    
    # Las 4 pestañas solicitadas
    tab1, tab2, tab3, tab4 = st.tabs(["💊 Validación Renal", "📄 Informe", "📊 Excel (Datos)", "📈 Gráficos"])
    
    with tab1:
        render_tab_validacion(v_text)
    with tab2:
        st.info("Módulo de generación de INFORME clínico.")
    with tab3:
        st.info("Módulo EXCEL: Registro histórico de validaciones.")
    with tab4:
        st.info("Módulo de GRÁFICOS: Evolución del FG y alertas.")

    st.markdown('<div class="aviso-prof">⚠️ Aviso: Esta herramienta es un apoyo a la revisión farmacoterapéutica. Verifique siempre con fuentes oficiales.</div>', unsafe_allow_html=True)
    
    if st.button("🗑️ Reset de Paciente"):
        for k in ['meds_input', 'cache_val']:
            if k in st.session_state: st.session_state.pop(k)
        st.rerun()

if __name__ == "__main__":
    main()
