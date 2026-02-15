import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import datetime

# --- CONFIGURACIÓN E INICIALIZACIÓN ---
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

if 'active_model_name' not in st.session_state:
    st.session_state.active_model_name = "1.5 Pro"
if 'meds_input' not in st.session_state:
    st.session_state.meds_input = ""
if 'cache_result' not in st.session_state:
    st.session_state.cache_result = None
if 'reset_counter' not in st.session_state:
    st.session_state.reset_counter = 0

# --- GESTIÓN DE MODELOS (CASCADA CON FALLBACK Y LIMPIEZA DE NOMBRE) ---
def run_ia_task(prompt, image_bytes=None):
    models_to_try = [
        ("gemini-1.5-pro", "1.5 Pro"),
        ("gemini-2.5-flash", "2.5 Flash")
    ]
    for model_id, tech_name in models_to_try:
        try:
            # Blindaje: Detectar y limpiar nombre dinámicamente
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

# --- INYECCIÓN DE INTERFAZ Y ESTILOS ---
def inject_ui_styles():
    # Limpieza final del nombre para el indicador visual
    display_model = st.session_state.active_model_name.replace("gemini-", "")
    
    st.markdown(f"""
    <style>
        /* INDICADOR INTELIGENTE: Texto verde neón, sin borde, fondo negro */
        .model-indicator {{
            position: fixed; 
            top: 10px; 
            left: 10px; 
            background-color: #000; 
            color: #0F0; /* Verde Neón */
            padding: 5px 12px; 
            font-family: 'Courier New', monospace; 
            font-size: 13px;
            font-weight: bold; 
            z-index: 999999; 
            border: none; /* ELIMINADO EL BORDE POR INSTRUCCIÓN */
            border-radius: 4px;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.5);
        }}

        /* PESTAÑA ACTIVA: Línea Púrpura y Negrita */
        div[role="tablist"] {{ gap: 10px; }}
        div[role="tab"]:not([aria-selected="false"]) {{
            color: #6a0dad !important; 
            font-weight: bold !important; 
            border-bottom: 3px solid #6a0dad !important;
        }}

        /* CUADRO FG GLOW MORADO */
        .fg-glow-box {{
            background-color: #000; 
            color: #fff; 
            border-radius: 12px;
            padding: 15px; 
            text-align: center; 
            border: 2px solid #6a0dad;
            box-shadow: 0 0 20px #a020f0; 
            margin: 5px 0;
        }}

        /* AVISO DE SEGURIDAD FIJO */
        .footer-warning {{
            position: fixed; bottom: 0; left: 0; width: 100%;
            background-color: #FFFACD; color: #333; text-align: center;
            padding: 8px; font-size: 12px; z-index: 1000;
            border-top: 1px solid #e6db55;
        }}
    </style>
    <div class="model-indicator">{display_model}</div>
    """, unsafe_allow_html=True)

# --- ESTRUCTURA PRINCIPAL ---
def main():
    inject_ui_styles()
    st.title("ASISTENTE RENAL")
    
    tabs = st.tabs(["💊 VALIDACIÓN", "📄 INFORME", "📊 EXCEL", "📈 GRÁFICOS"])
    
    with tabs[0]:
        # Bloque de Registro FASE 2
        st.markdown("### Registro")
        col_reg = st.columns([2, 1, 1, 2])
        with col_reg[0]: centro = st.text_input("Centro", value="Hospital Central")
        with col_reg[1]: edad = st.number_input("Edad", 0, 120, 70)
        with col_reg[2]: ref = st.text_input("Ref. Alfanumérica", "A1")
        with col_reg[3]: st.text_input("Fecha", datetime.date.today().strftime("%d/%m/%Y"), disabled=True)
        
        st.caption(f"ID Paciente: {centro}-{edad}-{ref}")
        st.markdown("---")

        # Columnas 50/50 para Calculadora y Ajuste
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📋 Calculadora")
            creatina = st.number_input("Creatinina (mg/dL)", 0.1, 10.0, 1.2)
            sexo = st.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
            # Cálculo interno CKD-EPI simplificado para el ejemplo
            fg_calc = 142 * min(creatina/0.9, 1)**-0.302 * max(creatina/0.9, 1)**-1.200 * 0.9938**edad
            fg_calc = round(fg_calc, 1)

        with c2:
            st.subheader("💊 Ajuste")
            fg_man = st.text_input("FG Manual (Prioritario)")
            fg_val = float(fg_man) if fg_man.isnumeric() else fg_calc
            
            st.markdown(f"""
                <div class="fg-glow-box">
                    <div style="font-size: 24px; font-weight: bold;">{fg_val}</div>
                    <div style="font-size: 12px;">mL/min</div>
                    <div style="font-size: 10px; color: #a020f0;">MÉTODO: {"Manual" if fg_man else "CKD-EPI"}</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📝 Listado de medicamentos")
        meds = st.text_area("Introduzca fármacos:", value=st.session_state.meds_input, height=150)
        st.session_state.meds_input = meds

        # Botonera Dual 85/15
        b1, b2 = st.columns([0.85, 0.15])
        with b1:
            if st.button("🚀 VALIDAR ADECUACIÓN", use_container_width=True):
                # Aquí se llamaría a run_ia_task con el prompt maestro
                pass
        with b2:
            if st.button("🗑️ RESET", use_container_width=True):
                st.session_state.meds_input = ""
                st.rerun()

    st.markdown('<div class="footer-warning">⚠️ Aviso: Esta herramienta es un apoyo a la revisión farmacoterapéutica. Puede contener errores. Verifique con fuentes oficiales.</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()

