import random

SINONIMOS_COLUMNAS = {
    "edad": "EDAD", "años": "EDAD", "sexo": "SEXO", "género": "SEXO",
    "mujer": "SEXO", "hombre": "SEXO", "peso": "PESO", "kilos": "PESO",
    "creatinina": "CREATININA", "pastillas": "Nº_TOTAL_MEDS_PAC",
    "medicamentos": "MEDICAMENTO", "fármacos": "MEDICAMENTO",
    "función renal": "FG_CG", "filtrado": "FG_CG", "fg": "FG_CG",
    "mdrd": "FG_MDRD", "ckd": "FG_CKD", "contraindicados": "Nº_CONTRAIND_CG",
    "ajuste": "Nº_AJUSTE_DOS_CG", "centro": "CENTRO", "residencia": "RESIDENCIA"
}

MAPEO_OPERADORES = {
    "mayor": ">",
    "más de": ">",
    "menor": "<",
    "menos de": "<",
    "igual": "==",
    "distinto": "!=",
    "contiene": "contains",
    "incluye": "contains"
}

RESPUESTAS = {
    "kpi": [
        "El valor obtenido es {valor}.",
        "Hay {valor} registros.",
        "El resultado final es {valor}.",
        "El cálculo devuelve un total de {valor}.",
        "Se ha obtenido un valor de {valor}.",
        "El número total es {valor}."
    ],
    "conteo": [
        "Se han identificado {valor} registros que cumplen los criterios.",
        "Tras aplicar los filtros, aparecen {valor} casos.",
        "El sistema ha encontrado {valor} registros coincidentes.",
        "Se contabilizan {valor} entradas que cumplen las condiciones.",
        "El análisis devuelve {valor} coincidencias.",
        "Hay {valor} registros dentro del grupo solicitado."
    ],
    "ranking": [
        "Los {N} elementos principales son: {lista}.",
        "El ranking queda así: {lista}.",
        "Los más frecuentes son: {lista}.",
        "Top resultados: {lista}.",
        "Los elementos más representativos son: {lista}."
    ],
    "promedio": [
        "La media de {variable} es {valor}.",
        "El promedio de {variable} es {valor}.",
        "Valor medio de {variable}: {valor}."
    ],
    "agrupacion": [
        "Distribución por {grupo}: {resumen}.",
        "Resumen por {grupo}: {resumen}.",
        "Comparación por {grupo}: {resumen}."
    ],
    "grafico": [
        "Gráfico {tipo_grafico} de {variable}.",
        "Visualización {tipo_grafico} sobre {variable}.",
        "Se genera gráfico de {tipo_grafico}."
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
