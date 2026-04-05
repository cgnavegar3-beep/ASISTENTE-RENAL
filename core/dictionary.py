import random

SINONIMOS_COLUMNAS = {
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

    # renal
    "creatinina": "CREATININA",
    "función renal": "FG_CG",
    "funcion renal": "FG_CG",
    "filtrado": "FG_CG",
    "fg": "FG_CG",
    "fg cg": "FG_CG",
    "fg_cg": "FG_CG",
    "mdrd": "FG_MDRD",
    "ckd": "FG_CKD",

    # medicación
    "medicamentos": "MEDICAMENTO",
    "medicamento": "MEDICAMENTO",
    "fármacos": "MEDICAMENTO",
    "farmacos": "MEDICAMENTO",
    "pastillas": "Nº_TOTAL_MEDS_PAC",

    # otros clínicos
    "contraindicados": "Nº_CONTRAIND_CG",
    "ajuste": "Nº_AJUSTE_DOS_CG",

    # centros
    "centro": "CENTRO",
    "residencia": "RESIDENCIA"
}

MAPEO_OPERADORES = {
    "mayor": ">",
    "más": ">",
    "más de": ">",
    "menor": "<",
    "menos de": "<",
    "igual": "==",
    "distinto": "!=",
    "diferente": "!=",
    "contiene": "contains",
    "incluye": "contains"
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
