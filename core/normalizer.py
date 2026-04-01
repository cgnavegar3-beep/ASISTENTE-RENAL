import re
import schema_resolver as sr
from typing import Dict, Any, List, Union


def infer_dataset(query_data: Dict[str, Any]) -> str:
    """Infiere dataset basado en columnas usadas."""
    if query_data.get("dataset"):
        return query_data["dataset"]

    med_exclusive = {
        "MEDICAMENTO",
        "GRUPO_TERAPEUTICO",
        "ADECUACION_FINAL",
        "ACEPTACION_MEDICO"
    }

    cols_mentioned = set()

    for f in query_data.get("filters", []):
        if isinstance(f, dict) and f.get("column"):
            cols_mentioned.add(sr.normalize_column_name(f["column"]))

    for col in query_data.get("select", []):
        cols_mentioned.add(sr.normalize_column_name(col))

    if cols_mentioned & med_exclusive:
        return "medicamentos"

    return "validaciones"


def normalize_value(value: Any) -> Any:
    """Convierte strings a tipos adecuados."""
    if not isinstance(value, str):
        return value

    val = value.strip()

    if "," in val:
        return [normalize_value(v.strip()) for v in val.split(",")]

    try:
        if re.match(r"^-?\d+$", val):
            return int(val)
        if re.match(r"^-?\d+\.\d+$", val):
            return float(val)
    except:
        pass

    return val


def map_operator(op: str) -> str:
    """Normaliza operadores."""
    op = op.lower().strip()

    mapping = {
        ">": ">",
        "mayor que": ">",
        "gt": ">",

        "<": "<",
        "menor que": "<",
        "lt": "<",

        ">=": ">=",
        "mayor o igual": ">=",

        "<=": "<=",
        "menor o igual": "<=",

        "=": "==",
        "==": "==",
        "igual a": "==",
        "es": "==",
        "equals": "==",

        "entre": "BETWEEN",
        "range": "BETWEEN",

        "in": "IN",
        "en": "IN",
        "dentro de": "IN",

        "contiene": "CONTAINS",
        "contains": "CONTAINS"
    }

    return mapping.get(op, "==")


def parse_natural_filters(text: str) -> List[Dict[str, Any]]:
    """
    Extrae filtros desde lenguaje natural.
    """

    filters = []

    parts = re.split(r",| y ", text, flags=re.IGNORECASE)

    pattern = r"(.+?)\s+(mayor que|menor que|igual a|entre|contiene|es|in|>|<|>=|<=|==|=)\s+(.+)"

    for part in parts:
        match = re.search(pattern, part.strip(), re.IGNORECASE)

        if match:
            col, op, val = match.groups()

            filters.append({
                "column": sr.normalize_column_name(col.strip()),
                "operator": map_operator(op),
                "value": normalize_value(val.strip())
            })

    return filters


def parse_order_by(order_input: Any) -> Dict[str, str]:
    """Normaliza order_by."""
    if not order_input:
        return {}

    if isinstance(order_input, dict):
        col = sr.normalize_column_name(order_input.get("column", ""))
        direction = order_input.get("direction", "ASC").upper()

        return {
            "column": col,
            "direction": "DESC" if "DESC" in direction else "ASC"
        }

    if isinstance(order_input, str):
        text = order_input.lower()

        direction = "DESC" if "desc" in text else "ASC"

        # buscar columna más robusta
        col_match = re.search(r"ordenar por\s+(.+?)(asc|desc|$)", text)

        if col_match:
            col = sr.normalize_column_name(col_match.group(1).strip())
        else:
            col = ""

        return {"column": col, "direction": direction}

    return {}


def normalize_query(input_data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Pipeline principal."""

    query = {
        "dataset": None,
        "select": [],
        "filters": [],
        "groupby": [],
        "order_by": {},
        "top_n": None
    }

    if isinstance(input_data, str):
        query["filters"] = parse_natural_filters(input_data)

    elif isinstance(input_data, dict):
        query["dataset"] = input_data.get("dataset")

        query["select"] = [
            sr.normalize_column_name(c)
            for c in input_data.get("select", [])
        ]

        query["groupby"] = [
            sr.normalize_column_name(c)
            for c in input_data.get("groupby", [])
        ]

        query["top_n"] = normalize_value(input_data.get("top_n"))

        raw_filters = input_data.get("filters", [])

        if isinstance(raw_filters, list):
            for f in raw_filters:
                if isinstance(f, dict):
                    query["filters"].append({
                        "column": sr.normalize_column_name(f.get("column", "")),
                        "operator": map_operator(f.get("operator", "==")),
                        "value": normalize_value(f.get("value"))
                    })

        query["order_by"] = parse_order_by(input_data.get("order_by"))

    query["dataset"] = infer_dataset(query)

    if query["top_n"] and not isinstance(query["top_n"], int):
        try:
            query["top_n"] = int(query["top_n"])
        except:
            query["top_n"] = None

    return query
