import json
from typing import Dict, Any


# =========================================================
# SYSTEM PROMPT CONTROLADO (HÍBRIDO)
# =========================================================
SYSTEM_PROMPT = """
Eres un traductor de lenguaje natural a JSON estructurado.

REGLAS ESTRICTAS:
- NO inventes datos
- NO texto libre
- SOLO JSON válido
- NO reasoning
- NO SQL
- NO pandas

FORMATO OBLIGATORIO:

{
  "dataset": "string",
  "filters": [
    {
      "column": "string",
      "operator": "== | != | > | < | >= | <= | BETWEEN | IN | NOT_IN | IS_NULL | NOT_NULL",
      "value": "any"
    }
  ],
  "groupby": ["string"],
  "operation": "count | mean | sum | nunique",
  "variable": "string or null",
  "order_by": {
    "column": "string",
    "direction": "ASC | DESC"
  },
  "top_n": number or null
}

REGLAS OPERATIVAS:
- BETWEEN solo si hay rango claro
- IN solo si hay lista explícita
- IS_NULL / NOT_NULL solo si se pide explícitamente ausencia de datos
- top_n solo para "top", "mayores", "mejores"
"""


# =========================================================
# PROMPT BUILDER
# =========================================================
def build_prompt(user_question: str, context: Dict[str, Any]) -> str:
    return f"""
{SYSTEM_PROMPT}

CONTEXTO:
datasets disponibles: {list(context.get("datasets", []))}
columnas: {context.get("columns", {})}

PREGUNTA:
{user_question}

RESPONDE SOLO JSON:
""".strip()


# =========================================================
# VALIDACIÓN JSON
# =========================================================
def validate_json_output(output: str) -> Dict[str, Any]:
    try:
        data = json.loads(output)
    except Exception:
        raise ValueError("IA no devolvió JSON válido")

    required = ["dataset", "filters", "groupby", "operation"]

    for k in required:
        if k not in data:
            raise ValueError(f"Falta campo obligatorio: {k}")

    return data


# =========================================================
# SANITIZER (SEGURIDAD + CONTROL OPERADORES)
# =========================================================
ALLOWED_OPERATIONS = {"count", "mean", "sum", "nunique"}

ALLOWED_OPERATORS = {
    "==", "!=", ">", "<", ">=", "<=",
    "BETWEEN", "IN", "NOT_IN",
    "IS_NULL", "NOT_NULL"
}


def sanitize_plan(plan: Dict[str, Any]) -> Dict[str, Any]:

    # -------------------------
    # operation control
    # -------------------------
    if plan.get("operation") not in ALLOWED_OPERATIONS:
        plan["operation"] = "count"

    # -------------------------
    # filters safety
    # -------------------------
    clean_filters = []

    for f in plan.get("filters", []):
        if not isinstance(f, dict):
            continue

        col = f.get("column")
        op = f.get("operator")
        val = f.get("value")

        if not col or not op:
            continue

        if op not in ALLOWED_OPERATORS:
            continue

        clean_filters.append({
            "column": str(col).strip().lower(),
            "operator": op,
            "value": val
        })

    plan["filters"] = clean_filters

    # -------------------------
    # groupby safety
    # -------------------------
    if isinstance(plan.get("groupby"), list):
        plan["groupby"] = [
            str(g).strip().lower()
            for g in plan["groupby"]
            if g
        ]
    else:
        plan["groupby"] = []

    # -------------------------
    # top_n safety
    # -------------------------
    if plan.get("top_n") is not None:
        try:
            plan["top_n"] = min(int(plan["top_n"]), 100)
        except:
            plan["top_n"] = None

    # -------------------------
    # order_by safety
    # -------------------------
    if plan.get("order_by"):
        ob = plan["order_by"]

        if not isinstance(ob, dict):
            plan["order_by"] = None
        else:
            if ob.get("direction") not in ["ASC", "DESC"]:
                ob["direction"] = "DESC"

            if ob.get("column"):
                ob["column"] = str(ob["column"]).strip().lower()

            plan["order_by"] = ob

    return plan


# =========================================================
# NORMALIZACIÓN FINAL
# =========================================================
def normalize_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    plan["dataset"] = str(plan.get("dataset", "")).lower()
    return plan
