import unicodedata
from typing import List, Dict, Any

# =========================================================
# 1. NORMALIZACIÓN ROBUSTA
# =========================================================
def normalize_column_name(column: str) -> str:
    """
    Normalización robusta:
    - Unicode NFC (acentos, caracteres compuestos)
    - strip
    - espacios → _
    - MAYÚSCULAS
    """
    if not isinstance(column, str):
        column = str(column)

    column = unicodedata.normalize("NFC", column)
    return column.strip().replace(" ", "_").upper()


def normalize_operator(operator: str) -> str:
    """Normaliza operadores a formato canónico."""
    op = str(operator).strip().upper()
    return OPERATOR_MAP.get(op, op)


# =========================================================
# 2. SCHEMA (SOURCE OF TRUTH)
# =========================================================
_RAW_SCHEMA: Dict[str, List[str]] = {
    "validaciones": [
        "FECHA", "CENTRO", "RESIDENCIA", "ID_REGISTRO", "EDAD", "SEXO", "PESO", "CREATININA",
        "Nº_TOTAL_MEDS_PAC", "FG_CG", "Nº_TOT_AFEC_CG", "Nº_PRECAU_CG", "Nº_AJUSTE_DOS_CG",
        "Nº_TOXICID_CG", "Nº_CONTRAIND_CG", "FG_MDRD", "Nº_TOT_AFEC_MDRD", "Nº_PRECAU_MDRD",
        "Nº_AJUSTE_DOS_MDRD", "Nº_TOXICID_MDRD", "Nº_CONTRAIND_MDRD", "FG_CKD",
        "Nº_TOT_AFEC_CKD", "Nº_PRECAU_CKD", "Nº_AJUSTE_DOS_CKD", "Nº_TOXICID_CKD",
        "Nº_CONTRAIND_CKD", "DISCREPANCIA", "ACEPTACION_MAP", "ACEPTACION_NUM"
    ],
    "medicamentos": [
        "FECHA", "CENTRO", "RESIDENCIA", "ID_REGISTRO", "EDAD", "SEXO", "PESO", "CREATININA",
        "Nº_TOTAL_MEDS_PAC", "FG_CG", "Nº_TOT_AFEC_CG", "Nº_PRECAU_CG", "Nº_AJUSTE_DOS_CG",
        "Nº_TOXICID_CG", "Nº_CONTRAIND_CG", "FG_MDRD", "Nº_TOT_AFEC_MDRD", "Nº_PRECAU_MDRD",
        "Nº_AJUSTE_DOS_MDRD", "Nº_TOXICID_MDRD", "Nº_CONTRAIND_MDRD", "FG_CKD",
        "Nº_TOT_AFEC_CKD", "Nº_PRECAU_CKD", "Nº_AJUSTE_DOS_CKD", "Nº_TOXICID_CKD",
        "Nº_CONTRAIND_CKD", "MEDICAMENTO", "GRUPO_TERAPEUTICO",
        "CAT_RIESGO_CG", "RIESGO_CG", "NIVEL_ADE_CG",
        "CAT_RIESGO_MDRD", "RIESGO_MDRD", "NIVEL_ADE_MDRD",
        "CAT_RIESGO_CKD", "RIESGO_CKD", "NIVEL_ADE_CKD",
        "ACEPTACION_MEDICO", "ADECUACION_FINAL"
    ]
}

# SCHEMA NORMALIZADO (SINGLE SOURCE OF TRUTH)
SCHEMA: Dict[str, List[str]] = {
    ds: [normalize_column_name(c) for c in cols]
    for ds, cols in _RAW_SCHEMA.items()
}


# =========================================================
# 3. OPERADORES
# =========================================================
OPERATORS: Dict[str, List[str]] = {
    "numeric": ["==", "!=", ">", "<", ">=", "<=", "BETWEEN", "IN", "NOT_IN", "IS_NULL", "NOT_NULL"],
    "categorical": ["==", "!=", "IN", "NOT_IN"],
    "string_extended": ["==", "!=", "IN", "CONTAINS", "STARTS_WITH", "ENDS_WITH"]
}

OPERATOR_MAP: Dict[str, str] = {
    "=": "==",
    "EQUALS": "==",
    "MAYOR QUE": ">",
    "MENOR QUE": "<",
    "BETWEEN": "BETWEEN",
    "IN": "IN",
    "NOT IN": "NOT_IN",
    "IS NULL": "IS_NULL",
    "NOT NULL": "NOT_NULL"
}


# =========================================================
# 4. COLUMN TYPES (derivados pero controlados)
# =========================================================
_RAW_COLUMN_TYPES: Dict[str, List[str]] = {
    "numeric": [
        "EDAD", "PESO", "CREATININA", "FG_CG", "FG_MDRD", "FG_CKD", "Nº_TOTAL_MEDS_PAC",
        "Nº_TOT_AFEC_CG", "Nº_PRECAU_CG", "Nº_AJUSTE_DOS_CG", "Nº_TOXICID_CG", "Nº_CONTRAIND_CG",
        "Nº_TOT_AFEC_MDRD", "Nº_PRECAU_MDRD", "Nº_AJUSTE_DOS_MDRD", "Nº_TOXICID_MDRD", "Nº_CONTRAIND_MDRD",
        "Nº_TOT_AFEC_CKD", "Nº_PRECAU_CKD", "Nº_AJUSTE_DOS_CKD", "Nº_TOXICID_CKD", "Nº_CONTRAIND_CKD",
        "ACEPTACION_NUM"
    ],
    "categorical": [
        "FECHA", "CENTRO", "RESIDENCIA", "ID_REGISTRO", "SEXO", "GRUPO_TERAPEUTICO",
        "CAT_RIESGO_CG", "RIESGO_CG", "NIVEL_ADE_CG", "CAT_RIESGO_MDRD", "RIESGO_MDRD",
        "NIVEL_ADE_MDRD", "CAT_RIESGO_CKD", "RIESGO_CKD", "NIVEL_ADE_CKD",
        "ACEPTACION_MEDICO", "ADECUACION_FINAL", "ACEPTACION_MAP", "DISCREPANCIA"
    ],
    "string_extended": [
        "MEDICAMENTO"
    ]
}

COLUMN_TYPES: Dict[str, List[str]] = {
    t: [normalize_column_name(c) for c in cols]
    for t, cols in _RAW_COLUMN_TYPES.items()
}


# =========================================================
# 5. GROUPBY (DERIVADO DEL SCHEMA → SIN DRIFT)
# =========================================================
GROUPBY_ALLOWED: List[str] = [
    normalize_column_name(c)
    for c in ["CENTRO", "SEXO", "MEDICAMENTO", "GRUPO_TERAPEUTICO"]
]


SORT_ALLOWED: List[str] = ["ASC", "DESC"]


# =========================================================
# 6. VALIDACIONES BASE
# =========================================================
def validate_dataset(name: str) -> str:
    name = str(name).strip()
    if name not in SCHEMA:
        raise ValueError(f"Dataset no válido: {name}. Permitidos: {list(SCHEMA.keys())}")
    return name


def resolve_column(dataset: str, column: str) -> str:
    dataset = validate_dataset(dataset)
    col = normalize_column_name(column)

    if col not in SCHEMA[dataset]:
        raise ValueError(f"Columna '{col}' no existe en '{dataset}'")

    return col


def validate_column(dataset: str, column: str) -> str:
    return resolve_column(dataset, column)


def validate_operator(column: str, operator: str) -> str:
    col = normalize_column_name(column)
    op = normalize_operator(operator)

    col_type = None
    for t, cols in COLUMN_TYPES.items():
        if col in cols:
            col_type = t
            break

    if col_type is None:
        col_type = "categorical"

    if op not in OPERATORS[col_type]:
        raise ValueError(f"Operador '{op}' no válido para '{col}' (tipo {col_type})")

    return op


def validate_groupby(column: str) -> str:
    col = normalize_column_name(column)

    if col not in GROUPBY_ALLOWED:
        raise ValueError(f"No permitido GROUP BY en '{col}'")

    return col


def validate_top_n(n: Any) -> int:
    try:
        n = int(n)
        if n <= 0:
            raise ValueError
        return n
    except Exception:
        raise ValueError("top_n debe ser entero positivo")


def validate_sort(direction: str) -> str:
    d = str(direction).strip().upper()
    if d not in SORT_ALLOWED:
        raise ValueError(f"Orden inválido: {d}. Usar {SORT_ALLOWED}")
    return d
