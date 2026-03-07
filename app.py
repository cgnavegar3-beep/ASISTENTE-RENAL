import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import re
import uuid

# =================================================================
# ASISTENTE RENAL - Versión: v. 07 mar 2026 12:50
# =================================================================
# [PRINCIPIO FUNDAMENTAL: NO MODIFICAR ESTRUCTURA SIN AUTORIZACIÓN]

# 10 PRINCIPIOS FUNDAMENTALES (PE A PA - BLINDADOS)
# 1. RIGOR CLÍNICO ABSOLUTO: Basado en Ficha Técnica AEMPS.
# 2. INTEGRIDAD DE LA ESTRUCTURA: Cajas negras, tabs y registro intactos.
# 3. INTERFAZ DUAL: Calculadora y Glow Morado (Filtrado Glomerular).
# 4. GLOW SYSTEM: Categorización 1-4 con colores hexadecimales específicos.
# 5. REGLA DE CELDAS CUBIERTAS: 12 columnas obligatorias si hay riesgo > 0.
# 6. EXCLUSIÓN DE RIESGO 0: Los fármacos con ✅ en las 3 fórmulas se excluyen del Bloque 2.
# 7. BLOQUE 3 EXCLUSIVO C-G: Ajustes basados únicamente en Cockcroft-Gault.
# 8. VERSIÓN VISIBLE: v. 07 mar 2026 12:50 visible en la interfaz.
# 9. PROHIBICIÓN DE INVENCIÓN: No inferir datos fuera de la evidencia.
# 10. PROTOCOLO DE MODIFICACIÓN: Propuesta -> Aprobación -> Ejecución completa.

st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- ESTILOS CSS (BLINDAJE VISUAL) ---
st.markdown("""
    <style>
    .black-box { background-color: #000000; color: white; padding: 10px; border-radius: 5px; text-align: center; }
    .glow-purple { border: 2px solid #6a0dad; box-shadow: 0 0 10px #6a0dad; padding: 15px; border-radius: 10px; }
    .warning-yellow { background-color: #ffffcc; padding: 10px; border-left: 5px solid #ffeb3b; color: #333; }
    .version-text { font-size: 0.7rem; color: #666; text-align: right; }
    </style>
""", unsafe_allow_html=True)

# --- LÓGICA DE PERSISTENCIA (INGENIERÍA SUPERIOR) ---
def grabar_datos_sheets(id_reg, datos_paciente, tabla_bloque2):
    try:
        # 1. Preparar fila para PESTAÑA VALIDACIONES
        fila_val = pd.DataFrame([{
            "FECHA": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "ID_REGISTRO": id_reg,
            "CENTRO": datos_paciente['centro'],
            "EDAD": datos_paciente['edad'],
            "SEXO": datos_paciente['sexo'],
            "PESO": datos_paciente['peso'],
            "RESIDENCIA": datos_paciente.get('residencia', 'N/A'),
            "CREATININA": datos_paciente['creatinina'],
            "FG_LAB_CKD": datos_paciente['fg_ckd'],
            "FG_LAB_MDRD": datos_paciente['fg_mdrd'],
            "FG_CG_CALCULADO": datos_paciente['fg_cg'],
            "TOTAL_AFECTADOS_CG": datos_paciente['tot_cg'],
            "MEDS_PRECAUCION_CG": datos_paciente['prec_cg'],
            "MEDS_AJUSTE_CG": datos_paciente['ajus_cg'],
            "MEDS_CONTRAINDICADO_CG": datos_paciente['cont_cg'],
            "RIESGO_ADE_MAX": datos_paciente['riesgo_max'],
            "ACEPTACION_GLOBAL": "" # Manual
        }])
        
        # 2. Preparar filas para PESTAÑA MEDICAMENTOS
        filas_meds = []
        for med in tabla_bloque2:
            filas_meds.append({
                "ID_REGISTRO": id_reg,
                "MEDICAMENTO": med['nombre'],
                "GRUPO_TERAPEUTICO": med['atc'],
                "ADECUACION_INICIAL_CG": med['cat_cg'],
                "ADECUACION_INICIAL_CKD": med['cat_ckd'],
                "ADECUACION_INICIAL_MDRD": med['cat_mdrd'],
                "RIESGO_ADE": med['nivel_riesgo'],
                "ACEPTACION_MEDICO": "", "ADECUACION_FINAL": "", "DISCREPANCIA_IA": ""
            })
        df_meds_new = pd.DataFrame(filas_meds)

        # 3. Volcado (Append)
        # Nota: En un entorno real, se concatena con el existente y se hace update
        st.success(f"Registro {id_reg} preparado para sincronización.")
        return fila_val, df_meds_new
    except Exception as e:
        st.error(f"Error en volcado: {e}")
        return None, None

# --- ESTRUCTURA DE LA APP ---
st.markdown('<div class="black-box">ASISTENTE RENAL</div>', unsafe_allow_html=True)
st.markdown(f'<p class="version-text">v. 07 mar 2026 12:50</p>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["VALIDACIÓN", "INFORMES", "DATOS"])

with tab1:
    # FILA ÚNICA REGISTRO
    col_id, col_centro = st.columns([1,1])
    with col_id:
        # ID generado con inicial centro y num aleatorio (ejemplo: H-4321)
        centro_init = st.text_input("Centro (Inicial)", "H", key="c_init")
        id_gen = f"{centro_init}-{str(uuid.uuid4().int)[:5]}"
        st.info(f"ID_REGISTRO: {id_gen}")
    
    # INTERFAZ DUAL
    col_calc, col_glow = st.columns(2)
    with col_calc:
        st.subheader("Calculadora")
        edad = st.number_input("Edad", 18, 110, 65)
        peso = st.number_input("Peso (kg)", 30, 200, 70)
        sexo = st.selectbox("Sexo", ["Varón", "Mujer"])
        creat = st.number_input("Creatinina (mg/dL)", 0.4, 15.0, 1.2)
        
    with col_glow:
        st.markdown('<div class="glow-purple">', unsafe_allow_html=True)
        st.subheader("Filtrado Glomerular")
        # Algoritmo C-G
        fg_cg = ((140 - edad) * peso) / (72 * creat)
        if sexo == "Mujer": fg_cg *= 0.85
        st.metric("Cockcroft-Gault", f"{fg_cg:.1f} mL/min")
        st.markdown('</div>', unsafe_allow_html=True)

    meds_input = st.text_area("Listado de medicamentos", placeholder="Introduzca fármacos separados por comas...")

    if st.button("VALIDAR"):
        st.warning("Ejecutando algoritmo AFR-V10.1...")
        # Aquí se dispararía la llamada a la IA con el PROMPT_AFR_V10
        st.session_state['validado'] = True

    if st.session_state.get('validado'):
        if st.button("📥 GRABAR DATOS EN EXCEL"):
            # Simulación de datos extraídos para el volcado
            datos_p = {
                'centro': centro_init, 'edad': edad, 'sexo': sexo, 'peso': peso, 
                'creatinina': creat, 'fg_cg': fg_cg, 'fg_ckd': 45.0, 'fg_mdrd': 48.0,
                'tot_cg': 2, 'prec_cg': 1, 'ajus_cg': 1, 'cont_cg': 0, 'riesgo_max': 3
            }
            # Datos ficticios de tabla (Bloque 2)
            tabla_b2 = [
                {'nombre': 'Metformina', 'atc': 'A10BA02', 'cat_cg': '⚠️⚠️', 'cat_ckd': '⚠️', 'cat_mdrd': '⚠️', 'nivel_riesgo': 2}
            ]
            f_val, f_med = grabar_datos_sheets(id_gen, datos_p, tabla_b2)
            st.balloons()

with tab2:
    st.subheader("Informes SOIP e Interconsulta")
    col_s, col_o = st.columns(2)
    with col_s: st.text_area("S (Subjetivo)", height=100)
    with col_o: st.text_area("O (Objetivo)", height=100)
    st.text_area("INTERCONSULTA", placeholder="Texto de volcado automático...", height=150)

with tab3:
    st.subheader("Pestaña de Datos y Gestión")
    try:
        df_v = conn.read(worksheet="VALIDACIONES")
        df_m = conn.read(worksheet="MEDICAMENTOS")
        
        st.write("### Editor de Registros (Validaciones)")
        edit_v = st.data_editor(df_v, key="ed_v", num_rows="dynamic")
        
        st.write("### Editor de Intervenciones (Medicamentos)")
        edit_m = st.data_editor(df_m, key="ed_m", num_rows="dynamic")
        
        if st.button("💾 GUARDAR CAMBIOS EN GOOGLE SHEETS"):
            conn.update(worksheet="VALIDACIONES", data=edit_v)
            conn.update(worksheet="MEDICAMENTOS", data=edit_m)
            st.success("Excel actualizado correctamente.")
    except:
        st.info("Conecte su Google Sheet en Secrets para visualizar el histórico.")

st.markdown('<div class="warning-yellow">Aviso: El uso de este asistente no sustituye el juicio clínico.</div>', unsafe_allow_html=True)
