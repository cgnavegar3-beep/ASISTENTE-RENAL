import schema_resolver as sr
from typing import Dict, Any, List, Optional


# =========================================================
# ERROR FORMATTER
# =========================================================
def _error(
    message: str,
    field: str,
    stage: str = "semantic_validation",
    suggestion: str = ""
) -> Dict[str, Any]:
    """Estructura estándar de error tipo compiler."""
    return {
        "error": True,
        "stage": stage,
        "message": message,
        "field": field,
        "suggestion": suggestion
    }


# =========================================================
# 1. DATASET VALIDATION
# =========================================================
def validate_dataset_stage(query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    dataset = query.get("dataset")

    if not dataset:
        return _error(
            "Falta el campo 'dataset'",
            "dataset",
            "structure_validation",
            "Usa 'validaciones' o 'medicamentos'"
        )

    try:
        sr.validate_dataset(dataset)
    except ValueError as e:
        return _error(str(e), "dataset", "schema_validation")

    return None


# =========================================================
# 2. COLUMN VALIDATION
# =========================================================
def validate_columns_stage(query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    dataset = query.get("dataset")
    if not dataset:
        return None

    filters = query.get("filters") or []
    if not isinstance(filters, list):
        return _error("filters debe ser una lista", "filters", "syntax_validation")

    fields_to_check = {
        "select": query.get("select") or [],
        "groupby": query.get("groupby") or [],
        "filters": [
            f.get("column")
            for f in filters
            if isinstance(f, dict) and f.get("column")
        ]
    }

    order_by = query.get("order_by")
    if isinstance(order_by, dict) and order_by.get("column"):
        fields_to_check["order_by"] = [order_by["column"]]

    for field, cols in fields_to_check.items():
        if not isinstance(cols, list):
            continue

        for col in cols:
            try:
                sr.validate_column(dataset, col)
            except ValueError as e:
                return _error(str(e), field, "column_validation")

    return None


# =========================================================
# 3. FILTER VALIDATION (SEMANTIC + TYPE SAFE)
# =========================================================
def validate_filters_stage(query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    filters = query.get("filters") or []

    if not isinstance(filters, list):
        return _error("filters debe ser lista", "filters", "syntax_validation")

    seen = set()

    for idx, f in enumerate(filters):
        if not isinstance(f, dict):
            return _error("Filtro inválido", f"filters[{idx}]", "syntax_validation")

        col = f.get("column")
        op = f.get("operator")
        val = f.get("value")

        if not col or not op:
            return _error(
                f"Filtro incompleto en índice {idx}",
                f"filters[{idx}]",
                "syntax_validation"
            )

        # Normaliza operador + valida compatibilidad
        try:
            norm_op = sr.validate_operator(col, op)
        except ValueError as e:
            return _error(str(e), f"filters[{idx}].operator")

        # BETWEEN
        if norm_op == "BETWEEN":
            if not isinstance(val, list) or len(val) != 2:
                return _error(
                    "BETWEEN requiere [min, max]",
                    f"filters[{idx}].value"
                )
            try:
                if float(val[0]) > float(val[1]):
                    return _error(
                        "mínimo mayor que máximo en BETWEEN",
                        f"filters[{idx}].value"
                    )
            except Exception:
                return _error(
                    "BETWEEN requiere valores numéricos",
                    f"filters[{idx}].value"
                )

        # IN / NOT_IN
        elif norm_op in ["IN", "NOT_IN"]:
            if not isinstance(val, list):
                return _error(
                    f"{norm_op} requiere lista",
                    f"filters[{idx}].value"
                )

        # NULL OPERATORS
        elif norm_op in ["IS_NULL", "NOT_NULL"]:
            if val is not None:
                return _error(
                    f"{norm_op} no debe tener value",
                    f"filters[{idx}].value"
                )

        # DUPLICATE DETECTION (robusta)
        sig = (sr.normalize_column_name(col), norm_op, repr(val))
        if sig in seen:
            return _error(
                "Filtro duplicado detectado",
                f"filters[{idx}]"
            )
        seen.add(sig)

    return None


# =========================================================
# 4. GROUPBY VALIDATION
# =========================================================
def validate_groupby_stage(query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    groupby = query.get("groupby") or []

    if not isinstance(groupby, list):
        return _error("groupby debe ser lista", "groupby")

    for col in groupby:
        try:
            sr.validate_groupby(col)
        except ValueError as e:
            return _error(str(e), "groupby")

    return None


# =========================================================
# 5. GLOBAL CONSISTENCY CHECK
# =========================================================
def validate_consistency_stage(query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    dataset = query.get("dataset")

    # TOP N
    if "top_n" in query:
        try:
            sr.validate_top_n(query["top_n"])
        except ValueError as e:
            return _error(str(e), "top_n")

    # ORDER BY
    order_by = query.get("order_by")
    if isinstance(order_by, dict):
        col = order_by.get("column")
        direction = order_by.get("direction", "ASC")

        if col:
            try:
                sr.validate_column(dataset, col)
            except Exception:
                return _error(
                    "order_by column no válida",
                    "order_by.column"
                )

        try:
            sr.validate_sort(direction)
        except ValueError as e:
            return _error(str(e), "order_by.direction")

    return None


# =========================================================
# 6. MAIN PIPELINE (COMPILER STYLE)
# =========================================================
def validate_query(query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pipeline tipo compiler frontend:
    dataset → columns → filters → groupby → consistency
    """

    pipeline = [
        validate_dataset_stage,
        validate_columns_stage,
        validate_filters_stage,
        validate_groupby_stage,
        validate_consistency_stage
    ]

    for stage in pipeline:
        error = stage(query)
        if error:
            return error

    return {
        "error": False,
        "stage": "complete",
        "message": "Query válida",
        "query_canonical": query
    }
