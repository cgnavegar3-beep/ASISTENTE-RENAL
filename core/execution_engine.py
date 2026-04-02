import pandas as pd
from typing import Dict, Any, Optional, List


# =========================================================
# FILTER ENGINE (MULTI-OPERATOR SUPPORT)
# =========================================================
def apply_filters(df: pd.DataFrame, filtros: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Aplica filtros avanzados:
    ==, !=, >, <, >=, <=, BETWEEN, IN, NOT_IN, IS_NULL, NOT_NULL
    """

    df_filtered = df.copy()

    for f in filtros:
        col = f.get("column") or f.get("columna")
        op = f.get("operator")
        val = f.get("value")

        if col not in df_filtered.columns:
            raise ValueError(f"La columna '{col}' no existe en el dataset.")

        # =========================
        # OPERADORES
        # =========================
        if op == "==":
            df_filtered = df_filtered[df_filtered[col] == val]

        elif op == "!=":
            df_filtered = df_filtered[df_filtered[col] != val]

        elif op == ">":
            df_filtered = df_filtered[df_filtered[col] > val]

        elif op == "<":
            df_filtered = df_filtered[df_filtered[col] < val]

        elif op == ">=":
            df_filtered = df_filtered[df_filtered[col] >= val]

        elif op == "<=":
            df_filtered = df_filtered[df_filtered[col] <= val]

        elif op == "BETWEEN":
            df_filtered = df_filtered[
                (df_filtered[col] >= val[0]) & (df_filtered[col] <= val[1])
            ]

        elif op == "IN":
            df_filtered = df_filtered[df_filtered[col].isin(val)]

        elif op == "NOT_IN":
            df_filtered = df_filtered[~df_filtered[col].isin(val)]

        elif op == "IS_NULL":
            df_filtered = df_filtered[df_filtered[col].isna()]

        elif op == "NOT_NULL":
            df_filtered = df_filtered[df_filtered[col].notna()]

        else:
            raise ValueError(f"Operador '{op}' no soportado.")

    return df_filtered


# =========================================================
# GROUPBY ENGINE
# =========================================================
def apply_groupby(df: pd.DataFrame, groupby_cols: List[str]) -> Any:
    for col in groupby_cols:
        if col not in df.columns:
            raise ValueError(f"La columna de agrupación '{col}' no existe.")
    return df.groupby(groupby_cols)


# =========================================================
# OPERATION ENGINE (EXPANDIDO)
# =========================================================
def apply_operation(
    df_or_groupby: Any,
    operacion: str,
    variable: Optional[str] = None
) -> pd.DataFrame:

    is_groupby = hasattr(df_or_groupby, "obj")

    # =========================
    # COUNT
    # =========================
    if operacion == "count":
        result = df_or_groupby.size() if is_groupby else len(df_or_groupby)
        return (
            result.reset_index(name="resultado")
            if is_groupby
            else pd.DataFrame({"resultado": [result]})
        )

    # =========================
    # MEAN
    # =========================
    elif operacion == "mean":
        if not variable:
            raise ValueError("mean requiere 'variable'")

        target_df = df_or_groupby.obj if is_groupby else df_or_groupby

        if variable not in target_df.columns:
            raise ValueError(f"'{variable}' no existe")

        result = df_or_groupby[variable].mean()

        return (
            result.reset_index(name="resultado")
            if is_groupby
            else pd.DataFrame({"resultado": [result]})
        )

    # =========================
    # SUM
    # =========================
    elif operacion == "sum":
        if not variable:
            raise ValueError("sum requiere 'variable'")

        result = df_or_groupby[variable].sum()

        return (
            result.reset_index(name="resultado")
            if is_groupby
            else pd.DataFrame({"resultado": [result]})
        )

    # =========================
    # DISTINCT COUNT
    # =========================
    elif operacion == "nunique":
        if not variable:
            raise ValueError("nunique requiere 'variable'")

        result = df_or_groupby[variable].nunique()

        return (
            result.reset_index(name="resultado")
            if is_groupby
            else pd.DataFrame({"resultado": [result]})
        )

    else:
        raise ValueError(f"Operación '{operacion}' no soportada.")


# =========================================================
# SORT ENGINE
# =========================================================
def apply_sort(df: pd.DataFrame, order_by: Dict[str, Any]) -> pd.DataFrame:

    if not order_by:
        return df

    col = order_by.get("column")
    direction = order_by.get("direction", "ASC")

    if not col or col not in df.columns:
        return df

    ascending = direction != "DESC"

    return df.sort_values(by=col, ascending=ascending)


# =========================================================
# TOP N ENGINE (CORREGIDO)
# =========================================================
def apply_top_n(df: pd.DataFrame, top_n: Optional[int]) -> pd.DataFrame:

    if top_n is None:
        return df

    return df.head(int(top_n))


# =========================================================
# MAIN EXECUTION ENGINE
# =========================================================
def execute_plan(plan: Dict[str, Any], df_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Motor principal de ejecución controlada.
    """

    dataset_name = plan.get("dataset")

    if dataset_name not in df_dict:
        raise ValueError(f"Dataset '{dataset_name}' no existe.")

    df = df_dict[dataset_name].copy()

    # -------------------------
    # 1. FILTROS
    # -------------------------
    df = apply_filters(df, plan.get("filters", []))

    # -------------------------
    # 2. GROUPBY + OPERACIÓN
    # -------------------------
    groupby_cols = plan.get("groupby", [])
    operacion = plan.get("operacion")
    variable = plan.get("variable")

    if groupby_cols:
        grouped = apply_groupby(df, groupby_cols)
        result_df = apply_operation(grouped, operacion, variable)
    else:
        result_df = apply_operation(df, operacion, variable)

    # -------------------------
    # 3. SORT
    # -------------------------
    result_df = apply_sort(result_df, plan.get("order_by"))

    # -------------------------
    # 4. TOP N
    # -------------------------
    result_df = apply_top_n(result_df, plan.get("top_n"))

    return result_df
