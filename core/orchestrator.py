from typing import Dict, Any
import pandas as pd

from normalizer import normalize_plan, normalize_dataset
from capa_2 import build_prompt, validate_json_output, sanitize_plan
from execution_engine import execute_plan
from schema_resolver import (
    resolve_natural_column,
    validate_dataset,
    validate_column
)


# =========================================================
# ORCHESTRATOR PRINCIPAL
# =========================================================
def run_query(
    user_question: str,
    df_dict: Dict[str, pd.DataFrame],
    llm_call_fn,
    context: Dict[str, Any]
) -> pd.DataFrame:

    # -------------------------
    # 1. PROMPT IA
    # -------------------------
    prompt = build_prompt(user_question, context)

    # -------------------------
    # 2. IA → JSON
    # -------------------------
    raw_output = llm_call_fn(prompt)
    plan = validate_json_output(raw_output)

    # -------------------------
    # 3. SANITIZAR PLAN
    # -------------------------
    plan = sanitize_plan(plan)

    # -------------------------
    # 4. NORMALIZAR PLAN
    # -------------------------
    plan = normalize_plan(plan)

    # -------------------------
    # 5. VALIDAR DATASET
    # -------------------------
    dataset_name = validate_dataset(plan.get("dataset"))

    if dataset_name not in df_dict:
        raise ValueError(f"Dataset '{dataset_name}' no existe")

    df = normalize_dataset(df_dict[dataset_name])

    # -------------------------
    # 6. 🔥 RESOLVER SINÓNIMOS EN FILTROS
    # -------------------------
    filters = plan.get("filters", [])
    new_filters = []

    for f in filters:
        col = f.get("column")

        # resolver lenguaje natural → columna real
        resolved_col = resolve_natural_column(col)

        # validar columna final
        resolved_col = validate_column(dataset_name, resolved_col)

        f["column"] = resolved_col
        new_filters.append(f)

    plan["filters"] = new_filters

    # -------------------------
    # 7. RESOLVER GROUPBY
    # -------------------------
    groupby = plan.get("groupby", [])
    plan["groupby"] = [
        validate_column(dataset_name, resolve_natural_column(g))
        for g in groupby
    ]

    # -------------------------
    # 8. RESOLVER ORDER_BY
    # -------------------------
    if plan.get("order_by") and plan["order_by"].get("column"):
        col = plan["order_by"]["column"]
        col = resolve_natural_column(col)
        plan["order_by"]["column"] = validate_column(dataset_name, col)

    # -------------------------
    # 9. EJECUCIÓN FINAL
    # -------------------------
    result = execute_plan(plan, {dataset_name: df})

    return result
