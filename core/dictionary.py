import random

# 🔥 MEJORA: Ordenamos de más largo a más corto para evitar que "fg" 
# rompa a "filtrado glomerular"
SINONIMOS_COLUMNAS = {
    # identidad paciente
    "id registro": "ID_REGISTRO",
    "registro": "ID_REGISTRO",
    "paciente": "ID_REGISTRO",

    # edad
    "edad": "EDAD",
    "años": "EDAD",
    "edad años": "EDAD",

    # sexo
    "sexo": "SEXO",
    "género": "SEXO",
    "genero": "SEXO",
    "mujer": "SEXO",
    "hombre": "SEXO",
    "femenino": "SEXO",
    "masculino": "SEXO",

    # peso
    "peso": "PESO",
    "kilos": "PESO",

    # =========================
    # 🔥 FILTRADO GLOMERULAR
    # =========================
    "filtrado glomerular cg": "FG_CG",
    "filtrado glomerular mdrd": "FG_MDRD",
    "filtrado glomerular ckd": "FG_CKD",
    "filtrado glomerular": "FG_CG",
    "función renal": "FG_CG",
    "funcion renal": "FG_CG",
    "cockcroft": "FG_CG",
    "fg cg": "FG_CG",
    "fg_cg": "FG_CG",
    "fg mdrd": "FG_MDRD",
    "fg ckd": "FG_CKD",
    "fg": "FG_CG", # Al final para que no pise a los anteriores

    # =========================
    # 💊 MEDICACIÓN
    # =========================
    "total medicamentos": "Nº_TOTAL_MEDS_PAC",
    "meds totales": "Nº_TOTAL_MEDS_PAC",
    "numero de medicamentos": "Nº_TOTAL_MEDS_PAC",
    "nº medicamentos": "Nº_TOTAL_MEDS_PAC",
    "medicamentos": "MEDICAMENTO",
    "medicamento": "MEDICAMENTO",
    "fármacos": "MEDICAMENTO",
    "farmacos": "MEDICAMENTO",
    "validaciones": "Nº_TOTAL_MEDS_PAC",

    # =========================
    # CG - afectación
    # =========================
    "afectados cg": "Nº_TOT_AFEC_CG",
    "precaucion cg": "Nº_PRECAU_CG",
    "ajuste cg": "Nº_AJUSTE_DOS_CG",
    "toxicidad cg": "Nº_TOXICID_CG",
    "contraindicados cg": "Nº_CONTRAIND_CG",

    # MDRD
    "afectados mdrd": "Nº_TOT_AFEC_MDRD",
    "precaucion mdrd": "Nº_PRECAU_MDRD",
    "ajuste mdrd": "Nº_AJUSTE_DOS_MDRD",
    "toxicidad mdrd": "Nº_TOXICID_MDRD",
    "contraindicados mdrd": "Nº_CONTRAIND_MDRD",

    # CKD
    "afectados ckd": "Nº_TOT_AFEC_CKD",
    "precaucion ckd": "Nº_PRECAU_CKD",
    "ajuste ckd": "Nº_AJUSTE_DOS_CKD",
    "toxicidad ckd": "Nº_TOXICID_CKD",
    "contraindicados ckd": "Nº_CONTRAIND_CKD",

    # =========================
    # 🧠 RIESGO
    # =========================
    "riesgo cg": "RIESGO_CG",
    "categoria cg": "CAT_RIESGO_CG",
    "nivel cg": "NIVEL_ADE_CG",
    "riesgo mdrd": "RIESGO_MDRD",
    "categoria mdrd": "CAT_RIESGO_MDRD",
    "nivel mdrd": "NIVEL_ADE_MDRD",
    "riesgo ckd": "RIESGO_CKD",
    "categoria ckd": "CAT_RIESGO_CKD",
    "nivel ckd": "NIVEL_ADE_CKD",

    # =========================
    # 👨‍⚕️ ACEPTACIÓN
    # =========================
    "aceptacion medico": "ACEPTACION_MEDICO",
    "aceptación médico": "ACEPTACION_MEDICO",
    "aceptación map": "ACEPTACION_MEDICO",
    "propuestas aceptadas": "ACEPTACION_MEDICO",
    
    # Adición para centros (Para que no dé "12" al filtrar)
    "centro": "CENTRO",
    "residencia": "RESIDENCIA"
}

# 🔥 Crucial para que "pacientes con edad menor a 50" funcione
MAPEO_OPERADORES = {
    "menor de": "<",
    "menor a": "<",
    "menor": "<",
    "mayor de": ">",
    "mayor a": ">",
    "mayor": ">",
    "más de": ">",
    "menos de": "<",
    "igual a": "==",
    "igual": "==",
    "distinto": "!=",
    "diferente": "!=",
    "contiene": "contains",
    "incluye": "contains"
}

# Valores de centros conocidos para el normalizador
VALORES_CATEGORICOS = {
    "cambados": "CAMBADOS",
    "pontevedra": "PONTEVEDRA",
    "salnes": "SALNES",
    "vilagarcía": "VILAGARCÍA"
}

MAPEO_VISUAL = {
    "barras_h": "bar",
    "barras_v": "bar",
    "barras": "bar",
    "sectores": "pie",
    "tarta": "pie",
    "circular": "pie",
    "histograma": "histogram",
    "tabla": "table",
    "listar": "table",
    "lista": "table",
    "kpi": "kpi"
}

RESPUESTAS = {
    "kpi": [
        "El valor obtenido es {valor}.",
        "Hay {valor} registros.",
        "El resultado final es {valor}.",
        "Se ha obtenido un valor de {valor}.",
        "El número total es {valor}."
    ],
    "conteo": [
        "Se han identificado {valor} registros que cumplen los criterios.",
        "Tras aplicar los filtros, aparecen {valor} casos.",
        "El sistema ha encontrado {valor} registros.",
        "Se contabilizan {valor} coincidencias."
    ],
    "ranking": [
        "Top {N}: {lista}.",
        "Ranking: {lista}.",
        "Los principales resultados son: {lista}."
    ],
    "promedio": [
        "La media de {variable} es {valor}.",
        "El promedio de {variable} es {valor}."
    ],
    "agrupacion": [
        "Distribución por {grupo}: {resumen}.",
        "Resumen por {grupo}: {resumen}."
    ],
    "grafico": [
        "Gráfico {tipo_grafico} de {variable}.",
        "Visualización {tipo_grafico} sobre {variable}."
    ],
    "sin_resultados": [
        "No se han encontrado registros.",
        "Sin resultados para los criterios.",
        "No hay coincidencias."
    ]
}

def obtener_respuesta_aleatoria(categoria, **kwargs):
    if categoria not in RESPUESTAS:
        return "Procesamiento finalizado."
    return random.choice(RESPUESTAS[categoria]).format(**kwargs)
