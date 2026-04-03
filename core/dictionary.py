# core/dictionary.py
import random

# Mapeo de términos a columnas (Sin cambios)
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
    "mayor": "> (MAYOR QUE)", "más de": "> (MAYOR QUE)",
    "menor": "< (MENOR QUE)", "menos de": "< (MENOR QUE)",
    "igual": "== (IGUAL)", "distinto": "!= (DISTINTO DE)",
    "contiene": "contiene", "incluye": "contiene"
}

# Banco de respuestas estructurado
RESPUESTAS = {
    "kpi": [
        "El valor obtenido es {valor}.", "Hay {valor} registros.",
        "El resultado final es {valor}.", "El cálculo devuelve un total de {valor}.",
        "Se ha obtenido un valor de {valor}.", "El recuento global asciende a {valor}.",
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
        "Los {N} más destacados son: {lista}.",
        "Los {N} más frecuentes en este grupo son: {lista}.",
        "El ranking queda así: {lista}.",
        "Los {N} primeros puestos corresponden a: {lista}.",
        "Los elementos más representativos son: {lista}."
    ],
    "promedio": [
        "El valor medio de {variable} es {valor}.",
        "La media de {variable} se sitúa en {valor}.",
        "El promedio calculado para {variable} es {valor}.",
        "En este grupo, {variable} presenta un valor medio de {valor}.",
        "El valor central de {variable} es {valor}.",
        "La media obtenida para {variable} asciende a {valor}."
    ],
    "agrupacion": [
        "Distribucion por {grupo}: {resumen}.",
        "La distribución por {grupo} es la siguiente: {resumen}.",
        "El análisis por {grupo} muestra: {resumen}.",
        "Así queda la segmentación por {grupo}: {resumen}.",
        "Resumen por {grupo}: {resumen}.",
        "La comparación entre grupos ({grupo}) ofrece este resultado: {resumen}."
    ],
    "grafico": [
        "Se ha generado un gráfico de tipo {tipo_grafico} sobre {variable}.",
        "Se ha creado un gráfico de {tipo_grafico} para visualizar {variable}.",
        "El gráfico representa la distribución de {variable}.",
        "Se muestra un {tipo_grafico} que resume {variable}.",
        "El gráfico permite observar cómo se comporta {variable}.",
        "Visualización generada: {tipo_grafico} sobre {variable}."
    ],
    "sin_resultados": [
        "No se han encontrado registros con los criterios aplicados.",
        "No hay datos que coincidan con los filtros seleccionados.",
        "El análisis no devuelve resultados para estos criterios.",
        "No se han identificado registros compatibles con la búsqueda.",
        "La consulta no ha producido coincidencias.",
        "No existen casos que cumplan las condiciones indicadas."
    ]
}

def obtener_respuesta_aleatoria(categoria, **kwargs):
    """Selecciona una frase aleatoria y la formatea con los datos obtenidos."""
    if categoria not in RESPUESTAS:
        return "Procesamiento finalizado."
    frase = random.choice(RESPUESTAS[categoria])
    return frase.format(**kwargs)
