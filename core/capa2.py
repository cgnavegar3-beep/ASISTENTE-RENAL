import json
from typing import Dict, Any, List


# =========================================================
# PROMPT BASE CONTROLADO (NO ALUCINACIONES)
# =========================================================
SYSTEM_PROMPT = """
Eres un generador de consultas estructuradas para un motor clínico.

REGLAS ESTRICTAS:
- NO inventes datos
- NO expliques
- NO respondas en lenguaje natural
- SOLO devuelve JSON válido
- SOLO usa campos permitidos

FORMATO DE SALIDA:
{
  "dataset": "...",
  "filters": [
    {
      "column": "...",
      "operator": "== | != | > | < | >= | <= | BETWEEN | IN | NOT_IN | IS_NULL | NOT_NULL",
      "value": "..."
    }
  ],
  "groupby": [],
  "operacion": "count | mean | sum | nunique",
  "variable": null,
  "order_by": {
    "column": "...",
    "direction": "ASC | DESC"
  },
  "top_n": null
}
"""


# =========================================================
# PARSER DE PREGUNTA SIMPLE → DSL
# =========================================================
def build_prompt(user_question: str, context: Dict[str, Any]) -> str:
    """
    Construye prompt seguro para el modelo IA
    """

    return f"""
{SYSTEM_PROMPT}

CONTEXTO DISPONIBLE:
- datasets: {list(context.get("datasets", []))}
- columnas: {context.get("columns", {})}

PREGUNTA DEL USUARIO:
{user_question}

RESPUESTA (SOLO JSON):
"""


# =========================================================
# VALIDACIÓN BÁSICA DE OUTPUT IA
# =========================================================
def validate_json_output(output: str) -> Dict[str, Any]:
    """
    Garantiza que la IA devuelve JSON válido
    """

    try:
        data = json.loads(output)
    except Exception:
        raise ValueError("La IA no devolvió JSON válido")

    required_keys = ["dataset", "filters", "groupby", "operacion"]

    for k in required_keys:
        if k not in data:
            raise ValueError(f"Falta clave obligatoria: {k}")

    return data


# =========================================================
# POST-PROCESADO DE SEGURIDAD
# =========================================================
def sanitize_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Seguridad final antes de ejecución
    """

    allowed_ops = {"count", "mean", "sum", "nunique"}

    if plan.get("operacion") not in allowed_ops:
        plan["operacion"] = "count"

    if not isinstance(plan.get("filters", []), list):
        plan["filters"] = []

    if not isinstance(plan.get("groupby", []), list):
        plan["groupby"] = []

    return plan
