from copy import deepcopy

DEFAULT_TARGET_COL = "ID_REGISTRO"
DEFAULT_SOURCE = "Validaciones"
DEFAULT_METRIC = "conteo"
DEFAULT_DIMENSION = "SEXO"
DEFAULT_CHART_TYPE = "bar"
DEFAULT_LIMIT = 10


def apply_clinical_policies(ast):
    ast = deepcopy(ast)

    request = ast.get("request", {})
    metadata = ast.get("metadata", {})

    if not request.get("metric"):
        request["metric"] = DEFAULT_METRIC

    if not request.get("target_col"):
        request["target_col"] = DEFAULT_TARGET_COL

    if not request.get("group_by"):
        request["group_by"] = None

    if not request.get("chart_type"):
        request["chart_type"] = DEFAULT_CHART_TYPE

    if not metadata.get("source"):
        metadata["source"] = DEFAULT_SOURCE

    if not request.get("limit"):
        request["limit"] = DEFAULT_LIMIT

    ast["request"] = request
    ast["metadata"] = metadata

    return ast
