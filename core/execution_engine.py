import pandas as pd
from typing import Dict, Any, Optional


def apply_filters(df: pd.DataFrame, filtros: list) -> pd.DataFrame:
    """Aplica filtros de igualdad sobre el DataFrame."""
    df_filtered = df.copy()
    for f in filtros:
        columna = f.get("columna")
        valor = f.get("valor")

        if columna not in df_filtered.columns:
            raise ValueError(f"La columna '{columna}' no existe en el dataset.")

        df_filtered = df_filtered[df_filtered[columna] == valor]

    return df_filtered


def apply_groupby(df: pd.DataFrame, groupby_cols: list) -> Any:
    """Prepara el objeto groupby si existen columnas especificadas."""
    for col in groupby_cols:
        if col not in df.columns:
            raise ValueError(f"La columna de agrupación '{col}' no existe en el dataset.")
    return df.groupby(groupby_cols)


def apply_operation(df_or_groupby: Any, operacion: str, variable: Optional[str] = None) -> pd.DataFrame:
    """Ejecuta la operación aritmética o de conteo solicitada."""
    is_groupby = hasattr(df_or_groupby, "obj")

    if operacion == "count":
        result = df_or_groupby.size() if is_groupby else len(df_or_groupby)
        return result.reset_index(name="resultado") if is_groupby else pd.DataFrame({"resultado": [result]})

    elif operacion == "mean":
        if not variable:
            raise ValueError("La operación 'mean' requiere una 'variable' especificada.")

        target_df = df_or_groupby.obj if is_groupby else df_or_groupby

        if variable not in target_df.columns:
            raise ValueError(f"La columna '{variable}' no existe para calcular la media.")

        result = df_or_groupby[variable].mean()
        return result.reset_index(name="resultado") if is_groupby else pd.DataFrame({"resultado": [result]})

    else:
        raise ValueError(f"Operación '{operacion}' no soportada.")


def execute_plan(plan: Dict[str, Any], df_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Orquestador principal para la ejecución del plan sobre los datasets."""
    dataset_name = plan.get("dataset")

    if dataset_name not in df_dict:
        raise ValueError(f"El dataset '{dataset_name}' no existe en df_dict.")

    df = df_dict[dataset_name].copy()

    # 1. Filtros
    df = apply_filters(df, plan.get("filtros", []))

    # 2. Agrupación y Operación
    groupby_cols = plan.get("groupby", [])

    if groupby_cols:
        grouped = apply_groupby(df, groupby_cols)
        result_df = apply_operation(grouped, plan.get("operacion"), plan.get("variable"))
    else:
        result_df = apply_operation(df, plan.get("operacion"), plan.get("variable"))

    # 3. Top N
    top_n = plan.get("top_n")
    if top_n is not None:
        result_df = result_df.head(top_n)

    return result_df
