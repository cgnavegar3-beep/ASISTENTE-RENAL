import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Validador Renal Pro v2", layout="wide")

# --- ESTILOS CSS AVANZADOS (Glow, Flash y Semáforo) ---
st.markdown("""
    <style>
    @keyframes flash-glow {
        0% { opacity: 0.5; transform: scale(0.98); }
        50% { opacity: 1; transform: scale(1); }
        100% { opacity: 1; transform: scale(1); }
    }
    .report-box {
        padding: 25px;
        border-radius: 15px;
        border: 3px solid;
        margin-top: 20px;
        animation: flash-glow 0.8s ease-out;
    }
    .fg-glow {
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 0 15px #a020f0;
        border: 1px solid #a020f0;
        background-color: #1a1a1a;
        color: white;
    }
    .rojo { background-color: #f8d7da; color: #721c24; border-color: #dc3545; box-shadow: 0 0 20px #ff0000; }
    .naranja { background-color: #fff3cd; color: #856404; border-color: #ffc107; box-shadow: 0 0 20px #ffa500; }
    .verde { background-color: #d4edda; color: #155724; border-color: #28a745; box-shadow: 0 0 20px #28a745; }
    .footer-disclaimer {
        font-size: 0.8em;
        color: #666;
        border-top: 1px solid #eee;
        margin-top: 30px;
        padding-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE CONEXIÓN Y DATOS ---
@st.cache_resource
def inicializar_recursos():
    # 1. Leer PDF (Fuente prioritaria)
    texto_pdf = ""
    try:
        doc = fitz.open("vademecum_renal.pdf")
        for pagina in doc:
            texto_pdf += pagina.get_text()
    except:
        texto_pdf = "Error: Vademécum PDF no encontrado en el servidor."
    
    # 2. Configurar IA
    modelo_ia = None
    if "API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["API_KEY"])
        modelo_ia = genai.GenerativeModel('gemini-2.5-flash')
    
    return modelo_ia, texto_pdf

modelo, contexto_pdf = inicializar_recursos()

# --- INTERFAZ DE USUARIO ---
st.title("🩺 Validador de Seguridad Renal")

if not modelo:
    st.error("⚠️ Configura la API_KEY en los Secrets para continuar.")
    st.stop()

col_izq, col_der = st.columns([1, 1.2], gap="large")

with col_izq:
    st.subheader("1. Parámetros Clínicos")
    
    # Entrada directa de FG (Prioridad)
    fg_manual = st.number_input("Introducir FG directamente (si se conoce)", 0.0, 200.0, 0.0, help="Si dejas 0, se usará el cálculo de abajo.")
    
    with st.expander("Calculadora (Cockcroft-Gault)", expanded=fg_manual == 0):
        edad = st.number_input("Edad", 18, 110, 70)
        peso = st.number_input("Peso (kg)", 30, 200, 75)
        crea = st.number_input("Creatinina (mg/dL)", 0.3, 15.0, 1.2)
        sexo = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
        
        fg_calc = ((140 - edad) * peso) / (72 * crea)
        if sexo == "Mujer": fg_calc *= 0.85
        fg_calc = round(fg_calc, 1)
        st.caption("Fórmula: Cockcroft-Gault")

    # FG Final a usar
    fg_final = fg_manual if fg_manual > 0 else fg_calc
    
    st.markdown(f"""
        <div class="fg-glow">
            <h2 style='margin:0; text-align:center;'>FG: {fg_final} ml/min</h2>
        </div>
    """, unsafe_allow_html=True)

with col_der:
    st.subheader("2. Medicación")
    
    # Subida de imagen / Captura
    archivo_img = st.file_uploader("Sube o pega imagen de la medicación", type=['jpg', 'jpeg', 'png'])
    
    texto_extraido = ""
    if archivo_img:
        with st.spinner("Leyendo imagen..."):
            img = Image.open(archivo_img)
            # IA extrae texto de la imagen directamente
            response_ocr = modelo.generate_content(["Extrae todos los nombres de fármacos y dosis (mg) de esta imagen. Devuelve solo la lista.", img])
            texto_extraido = response_ocr.text

    # Cuadro de texto donde se reproduce lo extraído o se escribe
    lista_farmacos = st.text_area(
        "Listado de medicamentos (Edita o escribe aquí):",
        value=texto_extraido,
        placeholder="Escribe o pega tu lista de medicamentos y aquí se reproducirá...",
        height=200
    )

# --- BOTÓN DE ACCIÓN ---
if st.button("🚀 VALIDAR SEGURIDAD RENAL", use_container_width=True):
    if not lista_farmacos:
        st.warning("Por favor, introduce algún medicamento.")
    else:
        with st.spinner("Analizando contra Vademécum y fuentes oficiales..."):
            # Prompt blindado con las reglas solicitadas
            prompt_final = f"""
            Actúa como experto en Farmacia Renal. 
            PACIENTE: FG de {fg_final} ml/min.
            MEDICAMENTOS: {lista_farmacos}
            
            FUENTE PRIORITARIA: {contexto_pdf[:10000]} (Usa esta tabla de aclaramiento si el fármaco existe aquí).
            
            REGLAS DE RESPUESTA:
            1. Si el fármaco está en el PDF, usa estrictamente esa recomendación. Si no, busca en fuentes oficiales (EMA, FDA).
            2. Empieza con una de estas palabras clave para el color: VERDE, NARANJA o ROJO.
               - ROJO: Si hay algún CONTRAINDICADO.
               - NARANJA: Si hay PRECAUCIÓN o DISMINUIR DOSIS.
               - VERDE: Si todo es seguro.
            3. ESTRUCTURA DEL MENSAJE:
               - LISTA DE AFECTADOS: (Nombre - COMENTARIO CORTO EN MAYÚSCULAS).
               - --- (Línea divisoria)
               - EXPLICACIÓN CLÍNICA: (Breve y técnica).
            """
            
            try:
                respuesta = modelo.generate_content(prompt_final).text
                
                # Lógica del semáforo
                clase, emoji = "verde", "🟢"
                res_upper = respuesta.upper()
                if "ROJO" in res_upper or "CONTRAINDICADO" in res_upper:
                    clase, emoji = "rojo", "🔴"
                elif "NARANJA" in res_upper or "PRECAUCIÓN" in res_upper or "DISMINUIR" in res_upper:
                    clase, emoji = "naranja", "🟠"
                
                if "VERDE" in res_upper and "AFECTADO" not in res_upper:
                    respuesta = "No se ha detectado ningún fármaco o medicamento afectado para este nivel de función renal."

                st.markdown(f"""
                    <div class="report-box {clase}">
                        <h3>{emoji} Informe de Validación</h3>
                        {respuesta.replace('---', '<hr>')}
                    </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Error en el análisis: {e}")

# --- DISCLAIMER PROTECTOR ---
st.markdown("""
    <div class="footer-disclaimer">
        ⚠️ <b>AVISO LEGAL:</b> Esta herramienta es un asistente de apoyo basado en IA y un vademécum predefinido. 
        <b>El profesional sanitario debe verificar obligatoriamente los resultados</b> antes de tomar cualquier decisión clínica. 
        No sustituye el juicio médico.
    </div>
""", unsafe_allow_html=True)
