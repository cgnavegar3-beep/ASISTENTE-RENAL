# =========================================================
# SCHEMA DEFINITIONS
# Contrato único de salida del sistema
# =========================================================

from typing import Dict, Any


# ---------------------------------------------------------
# OUTPUT PRINCIPAL (MATCHER / ORCHESTRATOR RESULT)
# ---------------------------------------------------------
OUTPUT_SCHEMA: Dict[str, Any] = {
    "intent": "string",              # intención detectada (ej: CALC_FG)
    "confidence": "float",          # 0.0 - 1.0

    "entities": "list[str]",        # conceptos detectados (FG, MDRD, etc.)

    "columns_needed": "list[str]",  # columnas reales del dataset

    "filters": "list[str]",         # filtros tipo pandas/sql lógico

    "groupby": "list[str]",         # agrupaciones si existen

    "sort": "string",               # campo de ordenación

    "top_n": "int|null",            # limitación de resultados

    "operation": "string",          # tipo operación (filter, agg, calc)

    "dataset": "string|null",       # dataset objetivo si aplica

    "format": "string"             # output final (table, json, summary)
}


# ---------------------------------------------------------
# INTENTOS CLÍNICOS SOPORTADOS (CONTROL ANTI-ALUCINACIÓN)
# ---------------------------------------------------------
ALLOWED_INTENTS = {
    "CALC_FG",
    "QUERY_PANDAS",
    "MEDICATION_QUERY",
    "DATA_QUALITY",
    "AGGREGATION",
    "UNKNOWN_INTENT"
}


# ---------------------------------------------------------
# OPERACIONES PERMITIDAS
# ---------------------------------------------------------
ALLOWED_OPERATIONS = {
    "filter",
    "aggregate",
    "groupby",
    "calculate",
    "sort",
    "select"
}


# ---------------------------------------------------------
# FORMATOS DE SALIDA PERMITIDOS
# ---------------------------------------------------------
ALLOWED_FORMATS = {
    "table",
    "json",
    "summary"
}
