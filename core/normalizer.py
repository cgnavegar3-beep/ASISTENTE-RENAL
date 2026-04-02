import re
import unicodedata
from typing import Any, Dict, List, Union


# =========================================================
# NORMALIZACIÓN DE TEXTO BASE
# =========================================================
def normalize_text(text: str) -> str:
    """
    Normaliza texto:
    - minúsculas
    - sin acentos
    - espacios limpios
    - trim
    """
    if not isinstance(text, str):
        return text

    text = text.strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"\s+", " ", text)

    return text


# =========================================================
# NORMALIZACIÓN DE COLUMNAS
# =========================================================
def normalize_columns(df):
    df = df.copy()
    df.columns = [normalize_text(col) for col in df.columns]
    return df


# =========================================================
# NORMALIZACIÓN DE VALORES
# =========================================================
def normalize_values(df):
    df = df.copy()

    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].apply(lambda x: normalize_text(x) if isinstance(x, str) else x)

    return df


# =========================================================
# NORMALIZADOR PRINCIPAL
# =========================================================
def normalize_dataset(df):
    """
    Pipeline completo de normalización
    """
    df = normalize_columns(df)
    df = normalize_values(df)
    return df


# =========================================================
# NORMALIZACIÓN DE QUERY DSL (IA -> ENGINE)
# =========================================================
def normalize_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normaliza el JSON generado por la IA:
    - columnas
    - operadores
    - strings
    """

    def norm_filters(filters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []

        for f in filters:
            new_f = dict(f)

            if "column" in new_f:
                new_f["column"] = normalize_text(new_f["column"])

            if "operator" in new_f:
                new_f["operator"] = new_f["operator"].upper()

            out.append(new_f)

        return out

    normalized = dict(plan)

    if "filters" in normalized:
        normalized["filters"] = norm_filters(normalized["filters"])

    if "groupby" in normalized:
        normalized["groupby"] = [normalize_text(c) for c in normalized["groupby"]]

    if "dataset" in normalized:
        normalized["dataset"] = normalize_text(normalized["dataset"])

    if "order_by" in normalized and normalized["order_by"]:
        if "column" in normalized["order_by"]:
            normalized["order_by"]["column"] = normalize_text(
                normalized["order_by"]["column"]
            )

        if "direction" in normalized["order_by"]:
            normalized["order_by"]["direction"] = normalized["order_by"]["direction"].upper()

    return normalized
