import random

# =========================================================
# RESPONSE TEMPLATES ENGINE
# Respuestas naturales + aleatoriedad controlada
# =========================================================


TEMPLATES = {
    # -------------------------
    # KPI (valor único)
    # -------------------------
    "kpi": [
        "El valor obtenido es {valor}.",
        "Hay {valor} registros.",
        "El resultado final es {valor}.",
        "El cálculo devuelve un total de {valor}.",
        "Se ha obtenido un valor de {valor}.",
        "El recuento global asciende a {valor}.",
        "El número total es {valor}."
    ],

    # -------------------------
    # CONTEO
    # -------------------------
    "count": [
        "Se han identificado {valor} registros que cumplen los criterios.",
        "Tras aplicar los filtros, aparecen {valor} casos.",
        "El sistema ha encontrado {valor} registros coincidentes.",
        "Se contabilizan {valor} entradas que cumplen las condiciones.",
        "El análisis devuelve {valor} coincidencias.",
        "Hay {valor} registros dentro del grupo solicitado."
    ],

    # -------------------------
    # TOP N / LISTADO
    # -------------------------
    "topn": [
        "Los {N} más destacados son: {lista}.",
        "Los {N} más frecuentes en este grupo son: {lista}.",
        "El ranking queda así: {lista}.",
        "Los {N} primeros puestos corresponden a: {lista}.",
        "Los elementos más representativos son: {lista}."
    ],

    # -------------------------
    # PROMEDIO
    # -------------------------
    "mean": [
        "La media de {variable} se sitúa en {valor}.",
        "El promedio calculado para {variable} es {valor}.",
        "En este grupo, {variable} presenta un valor medio de {valor}.",
        "El valor central de {variable} es {valor}.",
        "La media obtenida para {variable} asciende a {valor}."
    ],

    # -------------------------
    # AGRUPACIÓN
    # -------------------------
    "group": [
        "La distribución por {grupo} es la siguiente: {resumen}.",
        "El análisis por {grupo} muestra: {resumen}.",
        "Así queda la segmentación por {grupo}: {resumen}.",
        "Resumen por {grupo}: {resumen}.",
        "La comparación entre grupos ({grupo}) ofrece este resultado: {resumen}."
    ],

    # -------------------------
    # GRÁFICOS
    # -------------------------
    "chart": [
        "Se ha creado un gráfico de {tipo_grafico} para visualizar {variable}.",
        "El gráfico representa la distribución de {variable}.",
        "Se muestra un {tipo_grafico} que resume {variable}.",
        "El gráfico permite observar cómo se comporta {variable}.",
        "Visualización generada: {tipo_grafico} sobre {variable}."
    ],

    # -------------------------
    # SIN RESULTADOS
    # -------------------------
    "empty": [
        "No se han encontrado registros con los criterios aplicados.",
        "No hay datos que coincidan con los filtros seleccionados.",
        "El análisis no devuelve resultados para estos criterios.",
        "No se han identificado registros compatibles con la búsqueda.",
        "La consulta no ha producido coincidencias.",
        "No existen casos que cumplan las condiciones indicadas."
    ]
}


# =========================================================
# GENERADOR PRINCIPAL
# =========================================================

def render(template_type: str, **kwargs) -> str:
    """
    Devuelve una frase aleatoria del tipo solicitado
    con variables reemplazadas.
    """

    if template_type not in TEMPLATES:
        return "Tipo de respuesta no soportado."

    template = random.choice(TEMPLATES[template_type])

    try:
        return template.format(**kwargs)
    except KeyError as e:
        return f"Error en plantilla: falta {e}"


# =========================================================
# WRAPPERS OPCIONALES (más limpio para orchestrator)
# =========================================================

def kpi(valor):
    return render("kpi", valor=valor)


def count(valor):
    return render("count", valor=valor)


def topn(N, lista):
    return render("topn", N=N, lista=lista)


def mean(variable, valor):
    return render("mean", variable=variable, valor=valor)


def group(grupo, resumen):
    return render("group", grupo=grupo, resumen=resumen)


def chart(tipo_grafico, variable):
    return render("chart", tipo_grafico=tipo_grafico, variable=variable)


def empty():
    return render("empty")
