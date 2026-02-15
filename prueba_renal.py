import streamlit as st
from datetime import datetime
from PIL import Image
import time

# --- CONFIGURACIÓN DE PÁGINA (OBLIGATORIO PARA QUE SE VEA BIEN) ---
st.set_page_config(page_title="Asistente Renal", layout="wide")

# --- INYECCIÓN DE ESTILOS (TU NUEVA INTERFAZ) ---
def inject_custom_css():
    st.markdown("""
    <style>
    /* 1. BLINDAJE PESTAÑA ACTIVA: Línea roja inferior y negrita */
    div[data-baseweb="tab-list"] button[aria-selected="true"] {
        border-bottom: 3px solid red !important;
        font-weight: bold !important;
        color: black !important;
    }
    
    /* 2. INDICADOR DE MODELO: Cuadro negro pequeño arriba a la izquierda */
    .model-indicator {
        background-color: #000000;
        color: #00FF00; /* Verde terminal */
        padding: 4px 8px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 0.8rem;
        display: inline-block;
        margin-bottom: 10px;
    }

    /* 3. DISPLAY FG GLOW: La caja negra con borde morado NEÓN */
    .fg-glow-box {
        background-color: #000000;
        color: #FFFFFF;
        border: 2px solid #9d00ff;
        box-shadow: 0 0 15px #9d00ff; /* Glow más intenso */
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 10px;
    }
    .fg-value { font-size: 2rem; font-weight: bold; }
    .fg-label { font-size: 0.8rem; color: #cccccc; }

    /* 4. SEPARADOR TIPO SURCO/HENDIDURA */
    .separator-groove {
        border-top: 1px solid #bbb;
        border-bottom: 1px solid #fff;
        margin: 20px 0;
    }
    
    /* 5. AVISO AMARILLO ABAJO */
    .security-warning {
        background-color: #fff3cd;
        color: #856404;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
        border: 1px solid #ffeeba;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN DUMMY PARA SIMULAR LÓGICA ---
def calculate_gfr_dummy():
    return 45.5 # Valor fijo para demo visual

# --- FUNCIÓN PRINCIPAL DE RENDERIZADO ---
def render_tab_validacion():
    inject_custom_css()
    
    # Inicializar estado mínimo
    if 'reset_counter' not in st.session_state: st.session_state['reset_counter'] = 0

    # 1. INDICADOR DISCRETO DEL MODELO
    st.markdown('<div class="model-indicator">Model: 1.5 Pro</div>', unsafe_allow_html=True)

    # 2. DATOS DEL PACIENTE (Campos Silenciosos)
    st.markdown("### Datos del Paciente")
    
    # Fila de registro
    c1, c2, c3 = st.columns([1, 2, 1])
    
    with c1:
        # Placeholder G/M
        centro = st.text_input("Centro", placeholder="G/M")
    
    with c2:
        cc1, cc2, cc3 = st.columns(3)
        with cc1: st.number_input("Edad", min_value=0, value=None, placeholder="0")
        with cc2: st.text_input("ID Alfanum.", placeholder="ABC")
        with cc3: st.selectbox("Residencia", ["No", "Sí"])
            
    with c3:
        # Fecha bloqueada gris
        st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%Y"), disabled=True)

    # ID Registro pequeño abajo
    st.caption("ID Registro: GM-00-GEN (Auto-generado)")

    st.markdown("---")

    # 3. INTERFAZ DUAL (Calculadora vs Ajuste)
    col_calc, col_adjust = st.columns(2)

    # === IZQUIERDA: CALCULADORA ===
    with col_calc:
        st.info("📋 Calculadora (Simulada)")
        st.write("Aquí van los inputs numéricos de edad, peso, creatinina...")
        # (Aquí irían los inputs reales, simplificado para visualización)

    # === DERECHA: AJUSTE Y CAPTURA ===
    with col_adjust:
        st.warning("💊 Ajuste y Captura")
        
        # Input manual
        st.text_input("Input Manual FG", placeholder="Prioritario")
        
        st.write("") # Espacio
        
        # EL CUADRO MORADO NEÓN (Punto clave visual)
        st.markdown(f"""
        <div class="fg-glow-box">
            <div class="fg-label">Filtrado Glomerular (Fórmula)</div>
            <div class="fg-value">45.5 mL/min</div>
        </div>
        """, unsafe_allow_html=True)

        st.write("") # Espacio
        
        # Zona carga
        c_load1, c_load2 = st.columns([3, 1])
        with c_load1: st.file_uploader("Subir", label_visibility="collapsed")
        with c_load2: st.button("📋", help="Pegar")

    # 4. SURCO DE SEPARACIÓN
    st.markdown('<div class="separator-groove"></div>', unsafe_allow_html=True)

    # 5. LISTADO MEDICAMENTOS
    st.subheader("📝 Listado de medicamentos")
    st.text_area("Lista", height=150, placeholder="Escribe o edita la lista del archivo...", label_visibility="collapsed")

    # 6. BOTONERA DUAL
    b1, b2 = st.columns([0.85, 0.15])
    with b1: st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True, type="primary")
    with b2: st.button("🗑️ RESET", use_container_width=True)

    # 7. AVISO PERMANENTE
    st.markdown('<div class="security-warning">⚠️ Aviso: Herramienta de apoyo. Verifique con fuentes oficiales.</div>', unsafe_allow_html=True)

# --- EJECUCIÓN (ENTRY POINT) ---
if __name__ == "__main__":
    # Creamos las pestañas para simular el entorno real
    tab1, tab2 = st.tabs(["Validación", "Histórico"])
    
    with tab1:
        render_tab_validacion()
    
    with tab2:
        st.write("Pestaña inactiva")
