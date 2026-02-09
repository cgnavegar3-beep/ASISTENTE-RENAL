import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF

# --- 1. CONFIGURACIÓN Y ESTILO BLINDADO ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

st.markdown("""
    <style>
    .discreet-counter {
        position: fixed; top: 10px; left: 10px; background: #000; color: #0f0;
        padding: 5px 12px; border-radius: 4px; font-family: monospace; font-size: 11px; z-index: 1000;
        border: 1px solid #333;
    }
    .fg-glow {
        padding: 20px; border-radius: 15px; border: 2px solid #a020f0;
        box-shadow: 0 0 20px #a020f0; background: #000; text-align: center; color: #fff;
    }
    .resumen-unico { padding: 25px; border-radius: 15px; margin-top: 20px; border: 1px solid; }
    .verde-suave { background: #e8f5e9; border-color: #a5d6a7; color: #1b5e20; }
    .naranja-suave { background: #fff3e0; border-color: #ffcc80; color: #e65100; }
    .rojo-suave { background: #ffeef0; border-color: #ffcdd2; color: #b71c1c; }
    
    .div-llamativa { height: 4px; background: linear-gradient(90deg, transparent, #a020f0, #ff4b4b, #a020f0, transparent); margin: 30px 0; }
    .card-individual { padding: 15px; border-radius: 10px; margin-bottom: 12px; border-left: 8px solid; background: #fff; color: #333; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)

# --- 2. CONTADOR DISCRETO VERSIÓN 2.5 ---
st.markdown('<div class="discreet-counter">INTENTOS: 50 DÍA | 2 MIN | TOKENS: OK</div>', unsafe_allow_html=True)

# --- 3. CARGA DE VADEMÉCUM ---
@st.cache_resource
def load_pdf_data():
    try:
        doc = fitz.open("vademecum_renal.pdf")
        return "".join([p.get_text() for p in doc])
    except: return ""

pdf_text = load_pdf_data()

# --- 4. INTERFAZ DUAL ---
col_izq, col_der = st.columns([1, 1], gap="large")

with col_izq:
    st.subheader("📋 Calculadora Dinámica")
    edad = st.number_input("Edad", 18, 110, 70)
    peso = st.number_input("Peso (kg)", 35, 200, 75)
    crea = st.number_input("Creatinina (mg/dL)", 0.4, 15.0, 1.2)
    sexo = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
    fg_calc = round((((140 - edad) * peso) / (72 * crea)) * (0.85 if sexo == "Mujer" else 1.0), 1)

with col_der:
    st.subheader("⚡ Filtrado Glomerular")
    fg_manual = st.number_input("FG directo:", 0.0, 200.0, 0.0)
    fg_f = fg_manual if fg_manual > 0 else fg_calc
    st.markdown(f"""<div class="fg-glow"><h1>{fg_f} ml/min</h1><small>Método: {"Manual" if fg_manual > 0 else "Cockcroft-Gault"}</small></div>""", unsafe_allow_html=True)
    
    st.write("### 📷 Captura / Recorte")
    img_up = st.file_uploader("Sube o pega imagen", type=['png', 'jpg', 'jpeg'])

st.write("### Listado de medicamentos")
med_input = st.text_area("escribe o pega tu lista de medicamentos y aqui se reproducira la lista...", height=150)

# --- 5. LÓGICA DE AUTOMATIZACIÓN POR TABLA ---
if st.button("🚀 VALIDAR SEGURIDAD RENAL", use_container_width=True):
    if not med_input and not img_up:
        st.error("Sin datos.")
    elif "API_KEY" not in st.secrets:
        st.error("fallo de conexión o superado el número de intentos")
    else:
        with st.spinner("Buscando en tabla de Vademécum..."):
            try:
                genai.configure(api_key=st.secrets["API_KEY"])
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # PROMPT DE BÚSQUEDA MATRICIAL
                prompt = f"""
                Eres el ASISTENTE RENAL. Tu tarea es extraer la dosis exacta de la tabla del PDF.
                FG actual: {fg_f} ml/min.
                Vademécum: {pdf_text[:9000]}
                Medicamentos a buscar: {med_input}

                PROCESO DE BÚSQUEDA:
                1. Localiza el fármaco en la columna 'Fármaco'.
                2. Selecciona la columna de dosis según el FG:
                   - Si FG es 100-50: Usa columna 'Dosis 100-50 mL/min'.
                   - Si FG es 50-10: Usa columna '50-10 mL/min'.
                   - Si FG es <10: Usa columna '<10 mL/min'.
                3. Si el fármaco NO está en el PDF, búscalo en fuentes oficiales (EMA/FDA) y da el ajuste para FG {fg_f}.
                4. PROHIBIDO decir que el PDF es insuficiente.
                
                FORMATO:
                ESTADO_MAX: [VERDE/NARANJA/ROJO]
                GLOBAL: [Resumen corto]
                DETALLE:
                [Fármaco]|[COLOR]|[Dosis recomendada extraída de la tabla o fuente oficial]|[Breve explicación]
                """
                
                res = model.generate_content([prompt, Image.open(img_up)] if img_up else prompt).text
                
                # Estilo
                color_bg = "verde-suave"
                if "ROJO" in res.upper(): color_bg = "rojo-soft"
                elif "NARANJA" in res.upper(): color_bg = "naranja-suave"
                
                # Cuadro Resumen
                st.markdown(f"""
                    <div class="resumen-unico {color_bg}">
                        <h3 style="margin:0;">🔲 Lista de medicamentos afectados</h3>
                        <div>{res.split('DETALLE:')[0].replace('ESTADO_MAX:', '').strip()}</div>
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown('<div class="div-llamativa"></div>', unsafe_allow_html=True)
                
                # Cuadros Individuales
                if "DETALLE:" in res:
                    for line in res.split("DETALLE:")[1].strip().split("\n"):
                        if "|" in line:
                            n, c, d, e = line.split("|")
                            sc = "#2e7d32" if "VERDE" in c.upper() else "#ef6c00" if "NARANJA" in c.upper() else "#c62828"
                            st.markdown(f"""
                                <div class="card-individual" style="border-color:{sc};">
                                    <strong style="color:{sc};">{n.upper()}</strong><br>
                                    <b>Dosis para FG {fg_f}:</b> {d}<br>
                                    <small>{e}</small>
                                </div>
                            """, unsafe_allow_html=True)
                            
            except:
                st.error("fallo de conexión o superado el número de intentos")

st.info("⚠️ Aviso: ¡¡¡¡ACUERDATEEEE    PILARRRR   esto solo es Apoyo profesional. Los resultados deben ser verificados.LO CONSEGUIREMOS")
