# --- 1. CONFIGURACIÓN DE COLUMNAS (ALINEACIÓN CON EXCEL) ---
# Columnas automáticas del paciente (A hasta AA)
COLUMNAS_PACIENTE = [
    "FECHA", "CENTRO", "RESIDENCIA", "ID_REGISTRO", "EDAD", "SEXO", "PESO", "CREATININA", 
    "Nº_TOTAL_MEDS_PAC", "FG_CG", "Nº_TOT_AFEC_CG", "Nº_PRECAU_CG", "Nº_AJUSTE_DOS_CG", 
    "Nº_TOXICID_CG", "Nº_CONTRAIND_CG", "FG_MDRD", "Nº_TOT_AFEC_MDRD", "Nº_PRECAU_MDRD", 
    "Nº_AJUSTE_DOS_MDRD", "Nº_TOXICID_MDRD", "Nº_CONTRAIND_MDRD", "FG_CKD", "Nº_TOT_AFEC_CKD", 
    "Nº_PRECAU_CKD", "Nº_AJUSTE_DOS_CKD", "Nº_TOXICID_CKD", "Nº_CONTRAIND_CKD"
]

# Columnas automáticas del fármaco (AB hasta AL)
COLUMNAS_FARMACO_IA = [
    "MEDICAMENTO", "GRUPO_TERAPEUTICO", "CAT_RIESGO_CG", "RIESGO_CG", "NIVEL_ADE_CG",
    "CAT_RIESGO_MDRD", "RIESGO_MDRD", "NIVEL_ADE_MDRD",
    "CAT_RIESGO_CKD", "RIESGO_CKD", "NIVEL_ADE_CKD"
]

# --- 2. FUNCIONES DE PERSISTENCIA ---
def ejecutar_grabado_renal(sheet_val, sheet_meds, datos_paciente, df_farmacos_riesgo):
    """
    Graba los datos respetando las columnas manuales del usuario.
    Validaciones: Escribe A-AA (27 col). AB y AC quedan para el usuario.
    Medicamentos: Escribe A-AA (Paciente) + AB-AL (Fármaco). AM y AN para el usuario.
    """
    try:
        # Preparar fila para VALIDACIONES
        fila_val = [datos_paciente.get(col, "") for col in COLUMNAS_PACIENTE]
        sheet_val.append_row(fila_val)
        
        # Preparar filas para MEDICAMENTOS
        if df_farmacos_riesgo is not None and not df_farmacos_riesgo.empty:
            filas_m = []
            for _, row in df_farmacos_riesgo.iterrows():
                # Parte Paciente (A-AA) + Parte Fármaco IA (AB-AL)
                nueva_fila_m = [datos_paciente.get(col, "") for col in COLUMNAS_PACIENTE] + \
                               [row.get(col, "") for col in COLUMNAS_FARMACO_IA]
                filas_m.append(nueva_fila_m)
            
            if filas_m:
                sheet_meds.append_rows(filas_m)
        
        return True
    except Exception as e:
        st.error(f"Error en grabado: {e}")
        return False
