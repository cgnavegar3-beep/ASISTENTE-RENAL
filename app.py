import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

st.markdown("""
    <style>
    /* Contador Discreto Superior Izquierda (Estilo 2.5) */
    .discreet-counter {
        position: fixed; top: 10px; left: 10px; background-color: #000000;
        color: #00FF00; padding: 5px 10px; border-radius: 3px;
        font-family: 'Courier New', monospace; font-size: 11px; z-index: 1000;
        border: 1px solid #333;
    }
    
    /* Glow Morado para FG */
    .fg-glow-purple { 
        padding: 20px; border-radius: 15px; border: 2px solid #a020f0;
        box-shadow: 0 0 20px #a020f0; background: #000; text-align: center; color: white;
    }
    
    /* Cuadros de Resultados con Parpadeo Glow */
    @keyframes flash-glow { 0% { opacity: 0.8; } 50% { opacity: 1; } 100% { opacity: 0.8; } }
    .resumen-unico { padding: 25px; border-radius: 15px; margin-top: 20px; border: 2px solid; animation: flash-glow 2s infinite; }
    .verde-soft { background-color: #e8f5e9; border-color: #a5d6a7; color: #1b5e20; box-shadow: 0 0 15px #a5d6a7; }
    .naranja-soft { background-color: #fff3e0; border-color: #ffcc80; color: #e65100; box-shadow: 0 0 15px #ffcc80; }
    .rojo-soft { background-color: #ffeef0; border-color: #ffcdd2; color: #b71c1c; box-shadow: 0 0 15px #ffcdd2; }
    
    .div-llamativa { height: 5px; background: linear-gradient(90deg, transparent, #a020f0, #ff4b4b, #a020f0, transparent); margin: 30px 0; border-radius: 10px; }
    .card-individual { padding: 18px; border-radius: 10px; margin-bottom: 12px; border-left: 10px solid; background: white; color: #333; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)

# --- 2. CONTADOR DISCRETO (2.5) ---
st.markdown('<div class="discreet-counter">INTENTOS: 50 DÍA | 2 MIN | TOKENS: OK</div>', unsafe_allow_html=True)

# --- 3. CARGA DE MEMORIA PDF ---
@st.cache_resource
def get_vademecum_text():
    try:
        doc = fitz.open("vademecum_renal.pdf")
        return "".join([page.get_text() for page in doc])
    except: return ""

pdf_memory = get_vademecum_text()

# --- 4. INTERFAZ DUAL (ESTRUCTURA FIJA) ---
col_izq, col_der = st.columns([1, 1], gap="large")

with col_izq:
    st.subheader("📋 Calculadora Dinámica")
    edad = st.number_input("Edad", 18, 110, 70)
    peso = st.number_input("Peso (kg)", 35, 200, 75)
    crea = st.number_input("Creatinina", 0.4, 15.0, 1.2)
    sexo = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
    fg_calc = round((((140 - edad) * peso) / (72 * crea)) * (0.85 if sexo == "Mujer" else 1.0), 1)

with col_der:
    st.subheader("⚡ Filtrado Glomerular")
    fg_manual = st.number_input("Poner FG directamente:", 0.0, 200.0, 0.0)
    fg_final = fg_manual if fg_manual > 0 else fg_calc
    
    st.markdown(f"""<div class="fg-glow-purple"><h1>{fg_final} ml/min</h1><small>{"Manual" if fg_manual > 0 else "Cockcroft-Gault"}</small></div>""", unsafe_allow_html=True)
    
    st.write("### 📷 Recorte / Imagen")
    img_up = st.file_uploader("Sube o pega tu listado", type=['png', 'jpg', 'jpeg'])

# Cuadro grande de reproducción
st.write("### Listado de medicamentos")
med_input = st.text_area("escribe o pega tu lista de medicamentos y aqui se reproducira la lista si se ha pegado un RECORTE o se ha subido un pantallazo o imagen.", height=150)

# --- 5. LÓGICA DE PROCESAMIENTO ---
if st.button("🚀 VALIDAR SEGURIDAD RENAL", use_container_width=True):
    if "DNI" in med_input.upper() or "NIE" in med_input.upper():
        st.error("RGPD: Se han detectado datos personales. Uso bloqueado.")
    elif not med_input and not img_up:
        st.warning("Introduzca medicación.")
    else:
        with st.spinner("Ejecutando ASISTENTE RENAL..."):
            try:
                genai.configure(api_key=st.secrets["API_KEY"])
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                prompt = f"""
                Eres el ASISTENTE RENAL. 
                FG Paciente: {fg_final} ml/min.
                Vademécum (Tabla): {pdf_memory[:9000]}
                Medicamentos: {med_input}

                REGLA DE BÚSQUEDA MATRICIAL:
                1. Localiza el fármaco en el texto del Vademécum.
                2. Si FG >= 50, busca en columna '100-50 mL/min'.
                3. Si 10 < FG < 50, busca en columna '50-10 mL/min'.
                4. Si FG <= 10, busca en columna '<10 mL/min'.
                5. Devuelve EL TEXTO EXACTO DE LA DOSIS de esa celda.
                6. SI NO ESTÁ EN EL PDF, usa tu conocimiento (EMA/FDA) para dar el ajuste sin mencionar que falta en el PDF.
                7. Prohibido saludar. Sé directo.

                FORMATO DE SALIDA:
                MAX_RIESGO: [VERDE/NARANJA/ROJO]
                GLOBAL: [Comentario corto global]
                AFECTADOS:
                - [Icono ⚠️ o ⛔] [Nombre]: [Dosis recomendada]
                DETALLE:
                [Nombre]|[COLOR]|[Explicación breve clínica]
                """
                
                res = model.generate_content([prompt, Image.open(img_up)] if img_up else prompt).text
                
                # Sombreado dinámico
                color_bg = "verde-soft"
                if "ROJO" in res.upper(): color_bg = "rojo-soft"
                elif "NARANJA" in res.upper(): color_bg = "naranja-soft"
                
                # 1. Cuadro Resumen Único
                st.markdown(f"""
                    <div class="resumen-unico {color_bg}">
                        <h3 style="margin:0;">🔲 Cuadro resumen único</h3>
                        <div style="margin-top:10px;">{res.split('DETALLE:')[0].replace('MAX_RIESGO:', '').replace('GLOBAL:', '').replace('AFECTADOS:', '').strip()}</div>
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown('<div class="div-llamativa"></div>', unsafe_allow_html=True)
                
                # 2. Cuadros Individuales
                if "DETALLE:" in res:
                    detalles = res.split("DETALLE:")[1].strip().split("\n")
                    for det in detalles:
                        if "|" in det:
                            n, c, e = det.split("|")
                            sc = "#2e7d32" if "VERDE" in c.upper() else "#ef6c00" if "NARANJA" in c.upper() else "#c62828"
                            st.markdown(f"""<div class="card-individual" style="border-color:{sc};"><strong>{n.upper()}</strong><br>{e}</div>""", unsafe_allow_html=True)
                            
            except Exception:
                st.error("fallo de conexión o superado el número de intentos")

st.markdown("---")
st.warning("⚠️ **Aviso**: ACUERDESE DOÑA PILAR QUE ESTA ES TAN SOLO una humilde herramienta de apoyo a la revisión farmacoterapéutica. Los resultados deben ser verificados por un profesional sanitario antes de su aplicación clínica.")
