from typing import Dict, Any
import pandas as pd

from normalizer import normalize_plan, normalize_dataset
from capa_2 import build_prompt, validate_json_output, sanitize_plan
from execution_engine import execute_plan


# =========================================================
# ORCHESTRATOR PRINCIPAL
# =========================================================
def run_query(
    user_question: str,
    df_dict: Dict[str, pd.DataFrame],
    llm_call_fn,
    context: Dict[str, Any]
) -> pd.DataFrame:
    """
    Flujo completo:
    USER → IA → PLAN JSON → VALIDACIÓN → EJECUCIÓN → RESULTADO
    """

    # -------------------------
    # 1. GENERAR PROMPT
    # -------------------------
    prompt = build_prompt(user_question, context)

    # -------------------------
    # 2. LLAMADA A IA (EXTERNA)
    # -------------------------
    raw_output = llm_call_fn(prompt)

    # -------------------------
    # 3. VALIDAR JSON
    # -------------------------
    plan = validate_json_output(raw_output)

    # -------------------------
    # 4. SANITIZAR PLAN
    # -------------------------
    plan = sanitize_plan(plan)

    # -------------------------
    # 5. NORMALIZAR PLAN
    # -------------------------
    plan = normalize_plan(plan)

    # -------------------------
    # 6. VALIDAR DATASETS
    # -------------------------
    dataset_name = plan.get("dataset")

    if dataset_name not in df_dict:
        raise ValueError(f"Dataset '{dataset_name}' no existe")

    # -------------------------
    # 7. NORMALIZAR DATASET
    # -------------------------
    df_dict[dataset_name] = normalize_dataset(df_dict[dataset_name])

    # -------------------------
    # 8. EJECUTAR QUERY
    # -------------------------
    result = execute_plan(plan, df_dict)

    return result
