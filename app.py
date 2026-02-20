import streamlit as st

# Configuración de página
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

# --- REGLA: CONTADOR DISCRETO (Sup. Izquierda) ---
st.markdown("""
    <div style="position: fixed; top: 10px; left: 10px; font-size: 12px; color: #888; z-index: 1000;">
        Intentos restantes: 2.5
    </div>
""", unsafe_allow_html=True)

# --- ESTILOS CSS (Protegidos y Nuevos para SOIP) ---
st.markdown("""
    <style>
    /* Estilo General y Título */
    .main-title { font-size: 32px; font-weight: bold; color: #1E1E1E; margin-bottom: 0px; }
    .version-text { font-size: 10px; color: gray; margin-bottom: 20px; }

    /* Bloque SOIP Esculpido (Efecto Cuchara) */
    .soip-container {
        background-color: #f0f2f5;
        padding: 30px;
        border-radius: 35px;
        box-shadow: 10px 10px 20px #d1d9e6, -10px -10px 20px #ffffff;
        margin-top: 20px;
    }
    
    .surco-wrapper {
        display: flex;
        align-items: center;
        background: #f0f2f5;
        border-radius: 50px;
        margin-bottom: 18px;
        padding: 5px 25px;
        /* Efecto Cóncavo Inset */
        box-shadow: inset 6px 6px 12px #b8b9be, 
                    inset -6px -6px 12px #ffffff;
    }

    .letra-indicador {
        font-size: 24px;
        font-weight: 900;
        color: #4a5568;
        margin-right: 20px;
        min-width: 25px;
        text-shadow: 1px 1px 0px #fff;
    }

    /* Reset de Inputs de Streamlit para que parezcan parte del surco */
    .stTextInput input {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #333 !important;
        font-family: sans-serif;
    }

    /* Caja de Aviso Amarilla (Protegida) */
    .warning-box {
        background-color: #fff9c4;
        padding: 15px;
        border-left: 5px solid #fbc02d;
        border-radius: 5px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# --- ESTRUCTURA VISUAL ---
st.markdown('<p class="main-title">ASISTENTE RENAL</p>', unsafe_allow_html=True)
st.markdown('<p class="version-text">v. 2026-02-20 13:05</p>', unsafe_allow_html=True)

# Tabs principales
tab1, tab2, tab3 = st.tabs(["Calculadora / Filtrado", "Registro Paciente", "Informes"])

with tab1:
    st.info("Sección de Interfaz Dual (Calculadora y Filtrado Glomerular con brillo púrpura) - [CONTENIDO PROTEGIDO]")
    # Aquí iría tu código de la Interfaz Dual que no se debe tocar

with tab2:
    st.write("Registro de Paciente - [CONTENIDO PROTEGIDO]")

with tab3:
    st.subheader("Generación de Informe Clínico")
    
    # --- PPIO FUNDAMENTAL: EL RECTÁNGULO ESCULPIDO SOIP ---
    st.markdown("### Nota Evolutiva (SOIP)")
    
    st.markdown('<div class="soip-container">', unsafe_allow_html=True)
    
    # Línea S
    st.markdown('<div class="surco-wrapper"><span class="letra-indicador">S</span>', unsafe_allow_html=True)
    st.text_input("S", key="input_s", label_visibility="collapsed", placeholder="Subjetivo: Síntomas y relato del paciente...")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Línea O
    st.markdown('<div class="surco-wrapper"><span class="letra-indicador">O</span>', unsafe_allow_html=True)
    st.text_input("O", key="input_o", label_visibility="collapsed", placeholder="Objetivo: Signos vitales, laboratorio, examen físico...")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Línea I
    st.markdown('<div class="surco-wrapper"><span class="letra-indicador">I</span>', unsafe_allow_html=True)
    st.text_input("I", key="input_i", label_visibility="collapsed", placeholder="Interpretación: Impresión diagnóstica o análisis...")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Línea P
    st.markdown('<div class="surco-wrapper"><span class="letra-indicador">P</span>', unsafe_allow_html=True)
    st.text_input("P", key="input_p", label_visibility="collapsed", placeholder="Plan: Tratamiento, medicación, próximas citas...")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Aviso amarillo protegido
    st.markdown("""
        <div class="warning-box">
            <strong>PPIO FUNDAMENTAL:</strong> Verifique siempre los niveles de Creatinina antes de confirmar el Plan (P).
        </div>
    """, unsafe_allow_html=True)

# --- REGLA: VERSIÓN EN ESQUINA INFERIOR DERECHA ---
st.markdown("""
    <div style="position: fixed; bottom: 5px; right: 5px; font-size: 9px; color: #bbb;">
        v. 2026-02-20 13:05
    </div>
""", unsafe_allow_html=True)
