# core/catalog.py

SCHEMA = {
    "Validaciones": {
        "columnas": [
            "FECHA", "CENTRO", "RESIDENCIA", "ID_REGISTRO", "EDAD", "SEXO", "PESO", "CREATININA",
            "Nº_TOTAL_MEDS_PAC", "FG_CG", "Nº_TOT_AFEC_CG", "Nº_PRECAU_CG", "Nº_AJUSTE_DOS_CG",
            "Nº_TOXICID_CG", "Nº_CONTRAIND_CG", "FG_MDRD", "Nº_TOT_AFEC_MDRD", "Nº_PRECAU_MDRD",
            "Nº_AJUSTE_DOS_MDRD", "Nº_TOXICID_MDRD", "Nº_CONTRAIND_MDRD", "FG_CKD",
            "Nº_TOT_AFEC_CKD", "Nº_PRECAU_CKD", "Nº_AJUSTE_DOS_CKD", "Nº_TOXICID_CKD",
            "Nº_CONTRAIND_CKD", "Discrepancia", "ACEPTACION MAP", "aceptacion num"
        ],
        "numericas": [
            "EDAD", "PESO", "CREATININA", "Nº_TOTAL_MEDS_PAC", "FG_CG", "Nº_TOT_AFEC_CG", 
            "Nº_PRECAU_CG", "Nº_AJUSTE_DOS_CG", "Nº_TOXICID_CG", "Nº_CONTRAIND_CG", 
            "FG_MDRD", "FG_CKD", "aceptacion num"
        ]
    },
    "Medicamentos": {
        "columnas": [
            "FECHA", "CENTRO", "RESIDENCIA", "ID_REGISTRO", "EDAD", "SEXO", "PESO", "CREATININA",
            "Nº_TOTAL_MEDS_PAC", "FG_CG", "Nº_TOT_AFEC_CG", "Nº_PRECAU_CG", "Nº_AJUSTE_DOS_CG",
            "Nº_TOXICID_CG", "Nº_CONTRAIND_CG", "FG_MDRD", "Nº_TOT_AFEC_MDRD", "Nº_PRECAU_MDRD",
            "Nº_AJUSTE_DOS_MDRD", "Nº_TOXICID_MDRD", "Nº_CONTRAIND_MDRD", "FG_CKD", 
            "Nº_TOT_AFEC_CKD", "Nº_PRECAU_CKD", "Nº_AJUSTE_DOS_CKD", "Nº_TOXICID_CKD", 
            "Nº_CONTRAIND_CKD", "MEDICAMENTO", "GRUPO_TERAPEUTICO", "CAT_RIESGO_CG", 
            "RIESGO_CG", "NIVEL_ADE_CG", "CAT_RIESGO_MDRD", "RIESGO_MDRD", "NIVEL_ADE_MDRD", 
            "CAT_RIESGO_CKD", "RIESGO_CKD", "NIVEL_ADE_CKD", "ACEPTACION_MEDICO", "ADECUACION_FINAL"
        ],
        "numericas": [
            "EDAD", "PESO", "CREATININA", "Nº_TOTAL_MEDS_PAC", "FG_CG", "Nº_TOT_AFEC_CG", 
            "FG_MDRD", "FG_CKD"
        ]
    }
}

OPERADORES = ["== (IGUAL)", "!= (DISTINTO DE)", "> (MAYOR QUE)", "< (MENOR QUE)", "≥ (MAYOR O IGUAL)", "≤ (MENOR O IGUAL)", "contiene"]

FORMATOS_VISUALIZACION = ["KPI", "LISTAR", "TABLA", "BARRAS H", "BARRAS V", "SECTORES", "HISTOGRAMA"]
