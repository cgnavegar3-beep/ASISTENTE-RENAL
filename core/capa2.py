from typing import Dict, Any, Optional
import re

# =========================================================
# CAPA 2 - COLUMN MAPPER INTELIGENTE
# Traduce lenguaje natural → intención sobre datos
# =========================================================


# ---------------------------------------------------------
# DICCIONARIO DE COLUMNAS (CRÍTICO)
# AQUÍ CONTROLAS TODO (ANTI-ALUCINACIÓN)
# ---------------------------------------------------------
COLUMN_MAP = {
    "fg": "NIVEL_ADE_MDRD",
    "funcion renal": "NIVEL_ADE_MDRD",
    "filtrado glomerular": "NIVEL_ADE_MDRD",
    "ckd": "NIVEL_ADE_CKD",
    "clearance": "NIVEL_ADE_CG",
    "creatinina": "CREATININA"
}


# ---------------------------------------------------------
# NORMALIZACIÓN SIMPLE
# ---------------------------------------------------------
def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


# ---------------------------------------------------------
# MATCH COLUMN DIRECTO (SIN IA)
# ---------------------------------------------------------
def _match_column(text: str) -> Optional[str]:
    for key, col in COLUMN_MAP.items():
        if key in text:
            return col
    return None


# ---------------------------------------------------------
# DETECCIÓN SIMPLE DE INTENCIÓN
# ---------------------------------------------------------
def _detect_operation(text: str) -> str:
    if any(x in text for x in ["media", "promedio", "suma", "total"]):
        return "aggregate"
    if any(x in text for x in ["mayor", "menor", "<", ">", "bajo", "alto"]):
        return "filter"
    return "select"


# ---------------------------------------------------------
# EXTRACCIÓN DE FILTROS BÁSICOS
# ---------------------------------------------------------
def _extract_filters(text: str) -> list:
    filters = []

    match = re.search(r"(>|<|>=|<=)\s*(\d+)", text)
    if match:
        filters.append(f"{match.group(1)} {match.group(2)}")

    if "bajo" in text:
        filters.append("< threshold")
    if "alto" in text:
        filters.append("> threshold")

    return filters


# ---------------------------------------------------------
# FUNCIÓN PRINCIPAL CAPA 2
# ---------------------------------------------------------
def parse(user_input: str, context: Optional[Dict] = None) -> Dict[str, Any]:

    text = _normalize(user_input)

    column = _match_column(text)
    operation = _detect_operation(text)
    filters = _extract_filters(text)

    # -------------------------
    # CASO SIN MATCH
    # -------------------------
    if column is None:
        return {
            "intent": "UNKNOWN_INTENT",
            "column": "",
            "operation": "",
            "filters": [],
            "value_target": None,
            "confidence": 0.0
        }

    # -------------------------
    # CASO OK
    # -------------------------
    return {
        "intent": operation,
        "column": column,
        "operation": operation,
        "filters": filters,
        "value_target": None,
        "confidence": 0.85
    }


# ---------------------------------------------------------
# WRAPPER COMPATIBLE (por si usas orchestrator)
# ---------------------------------------------------------
def resolve(user_input: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    return parse(user_input, context)
