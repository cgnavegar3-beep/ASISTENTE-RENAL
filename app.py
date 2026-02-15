import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import io

# 1. CONFIGURACIÓN E INYECCIÓN DE INTERFAZ (BLINDAJE VISUAL)
st.set_page_config(page_title="Asistente Renal v3", layout="wide")

def inject_ui_styles():
    st.markdown("""
    <style>
    /* BLINDAJE PESTAÑA ACTIVA: Línea roja inferior */
    div[data-baseweb="tab-list"] button[aria-selected="true"] {
        border-bottom: 3px solid red !important;
        font-weight: bold !important;
        color: black !important;
    }

    /* INDICADOR DE MODELO: Cuadro negro pequeño arriba izq */
    .model-indicator {
        background-color: #000000;
        color: #00FF00;
        padding: 4px 10px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 0.85rem;
        display: inline-block;
        margin-bottom: 15px;
    }

    /* DISPLAY FG GLOW MORADO: El bloque negro solicitado */
    .fg-glow-box {
        background-color: #000000;
        color: #FFFFFF;
        border: 2px solid #9d00ff;
        box-shadow: 0 0 15px #9d00ff;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-top: 10px;
    }
    .fg-val { font-size: 2.2rem; font-weight: bold; color: white; }
    .fg-meth { font-size: 0.8rem; color: #bbbbbb; }

    /* SEPARADOR TIPO HENDIDURA */
    .separator-groove {
        border-top: 1px solid #bbb;
        border-bottom: 1px solid #fff;
        margin: 25px 0;
    }

    /* AVISO DE SEGURIDAD AMARILLO */
    .security-bar {
        background-color: #fff3cd;
        color: #856404;
        padding: 12px;
        border-radius: 6px;
        text-align: center;
        font-size: 0.9rem;
        border: 1px solid #ffeeba;
        margin-top: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. INICIO DE LA APP
inject_ui_styles()

# Indicador de modelo activo
st.markdown('<div class="model-indicator">2.5 Flash</div>', unsafe_allow_html=True)

# Pestañas con línea roja blindada
tab_val, tab_hist = st.tabs(["📋 VALIDACIÓN", "📚 HISTÓRICO"])

with tab_val:
    # --- BLOQUE 0: REGISTRO (CAMPOS SILENCIOSOS) ---
    st.markdown("### Registro de Paciente")
    c_reg1, c_reg2, c_reg3 = st.columns([1.5, 2.5, 1])
    
    with c_reg1:
        centro = st.text_input("Nombre del Centro", placeholder="G/M")
    
    with c_reg2:
        r_col1, r_col2, r_col3 = st.columns(3)
        with r_col1:
            edad = st.number_input("Edad", min_value=0, max_value=120, value=None, placeholder="Ingresar edad")
        with r_col2:
            alfanum = st.text_input("Cuadro Alfanumérico", placeholder="ID-Paciente")
        with r_col3:
            residencia = st.selectbox("¿En Residencia?", ["No", "Sí"])
            
    with c_reg3:
        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        st.text_input("Fecha Actual", value=fecha_actual, disabled=True)

    # ID Dinámico debajo de la fila
    id_gen = f"{centro if centro else 'G/M'}-{edad if edad else '00'}-{alfanum if alfanum else 'GEN'}"
    st.caption(f"ID Registro: {id_gen}")

    st.write("") # Espacio

    # --- BLOQUE 1 Y 2: CALCULADORA Y AJUSTE (SIMETRÍA DUAL) ---
    col_izq, col_der = st.columns(2)

    with col_izq:
        st.markdown("#### 📋 Calculadora")
        st.caption("Método: CKD-EPI / Cockcroft-Gault")
        # Contenedor con margen suave
        with st.container(border=True):
            c_in1, c_in2 = st.columns(2)
            with c_in1:
                calc_edad = st.number_input("Edad (años)", value=65, step=1)
                calc_peso = st.number_input("Peso (kg)", value=70.0, step=1.0)
            with c_in2:
                calc_creat = st.number_input("Creatinina (mg/dL)", value=1.0, step=0.1)
                calc_sexo = st.selectbox("Sexo", ["Hombre", "Mujer"])
            
            # Cálculo automático (ejemplo simplificado)
            fg_calc = round(175 * (calc_creat**-1.154) * (calc_edad**-0.203) * (0.742 if calc_sexo=="Mujer" else 1.0), 1)

    with col_der:
        st.markdown("#### 💊 Ajuste y Captura")
        # Input manual prioritario
        fg_manual = st.text_input("Input Manual del FG (Prioritario)", placeholder="Escriba FG aquí...")
        
        # Lógica de valor final
        valor_final = fg_manual if fg_manual else fg_calc
        metodo = "Manual" if fg_manual else "Fórmula (CKD-EPI)"

        # DISPLAY FG GLOW MORADO
        st.markdown(f"""
        <div class="fg-glow-box">
            <div class="fg-val">{valor_final} mL/min</div>
            <div class="fg-meth">Método: {metodo}</div>
        </div>
        """, unsafe_allow_html=True)

        st.write("") # Espaciador de seguridad
        
        # Zona de carga Multimodal
        c_file, c_paste = st.columns([4, 1])
        with c_file:
            st.file_uploader("Subir archivo (📁)", label_visibility="collapsed")
        with c_paste:
            st.button("📋", help="Pegar Recorte (Ctrl+V)")

    # --- BLOQUE 3: LÍNEA HENDIDURA ---
    st.markdown('<div class="separator-groove"></div>', unsafe_allow_html=True)

    # --- BLOQUE 4: LISTADO DE MEDICAMENTOS ---
    st.markdown("#### 📝 Listado de medicamentos")
    meds_input = st.text_area(
        "Listado", 
        placeholder="Escribe o edita la lista del archivo o captura subidos",
        height=150,
        label_visibility="collapsed"
    )

    # --- BLOQUE 5: BOTONERA DUAL ---
    st.write("")
    btn_val, btn_res = st.columns([0.85, 0.15])
    with btn_val:
        st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True, type="primary")
    with btn_res:
        st.button("🗑️ RESET", use_container_width=True)

    # --- BLOQUE 7: AVISO DE SEGURIDAD PERMANENTE ---
    st.markdown("""
    <div class="security-bar">
        ⚠️ Aviso: Esta herramienta es un apoyo a la revisión farmacoterapéutica. 
        Puede contener errores. Verifique siempre con fuentes oficiales.
    </div>
    """, unsafe_allow_html=True)

with tab_hist:
    st.write("Módulo de historial en desarrollo...")
