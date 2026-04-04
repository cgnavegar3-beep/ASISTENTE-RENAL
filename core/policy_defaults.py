"""
CAPA DE POLÍTICA: Define reglas de negocio, fallbacks y convenciones clínicas.
"""

from copy import deepcopy

# Defaults de Identificación
DEFAULT_TARGET_COL = "ID_REGISTRO"
DEFAULT_SOURCE = "Validaciones"

# Defaults de Análisis
DEFAULT_METRIC = "conteo"
DEFAULT_DIMENSION = "SEXO"

# Defaults de Visualización
DEFAULT_CHART_TYPE = "bar"
DEFAULT_LIMIT = 10


def apply_clinical_policies(ast):
    """
    Recibe un AST y le inyecta los valores por defecto 
    según las reglas de negocio vigentes.
    """

    # 🔒 IMPORTANTE: evitar efectos secundarios
    ast = deepcopy(ast)

    request = ast.get("request", {})
    metadata = ast.get("metadata", {})

    # 1. Asegurar métrica y columna objetivo
    if not request.get("metric"):
        request["metric"] = DEFAULT_METRIC

    if not request.get("target_col"):
        request["target_col"] = DEFAULT_TARGET_COL

    # 2. Lógica de Agrupación
    # Si es visual → siempre agrupar por dimensión por defecto
    if metadata.get("intent") == "visual":
        if not request.get("group_by"):
            request["group_by"] = DEFAULT_DIMENSION
    else:
        # Si no es visual → no hay agrupación
        request["group_by"] = None

    # 3. Tipo de gráfico
    if not request.get("chart_type"):
        request["chart_type"] = DEFAULT_CHART_TYPE

    # 4. Origen de datos
    if not metadata.get("source"):
        metadata["source"] = DEFAULT_SOURCE

    # 5. Parámetros técnicos (importante que exista siempre)
    if not request.get("limit"):
        request["limit"] = DEFAULT_LIMIT

    # 🔁 Reasignación final segura
    ast["request"] = request
    ast["metadata"] = metadata

    return ast
