# core/execution_engine.py

import pandas as pd


class ExecutionEngine:
    """
    Motor final de ejecución del query_plan.
    - Aplica filtros
    - Resuelve campos faltantes
    - Ejecuta agregaciones
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df

    # -------------------------------------------------
    # ENTRY POINT
    # -------------------------------------------------
    def execute(self, query_plan: dict) -> pd.DataFrame:

        df = self.df.copy()

        # 1. FILTROS
        df = self._apply_filters(df, query_plan.get("filters", []))

        # 2. AGREGACIONES
        agg = query_plan.get("aggregation")
        if agg:
            df = self._apply_aggregation(df, query_plan, agg)

        # 3. LIMIT / OPERATION
        if query_plan.get("operation") == "noop":
            return df

        return df

    # -------------------------------------------------
    # FILTROS
    # -------------------------------------------------
    def _apply_filters(self, df, filters):

        for f in filters:

            field = f.get("field")
            op = f.get("operator")
            value = f.get("value")

            # -------------------------------------------------
            # 🔴 RESOLUCIÓN DE CAMPOS INCOMPLETOS
            # -------------------------------------------------
            if field is None:
                # si no hay campo, no podemos aplicar filtro
                # lo ignoramos de forma segura
                continue

            if field not in df.columns:
                continue

            df = self._apply_single_filter(df, field, op, value)

        return df

    # -------------------------------------------------
    # FILTRO INDIVIDUAL
    # -------------------------------------------------
    def _apply_single_filter(self, df, field, op, value):

        if op == ">":
            return df[df[field] > value]

        if op == "<":
            return df[df[field] < value]

        if op == ">=":
            return df[df[field] >= value]

        if op == "<=":
            return df[df[field] <= value]

        if op == "=":
            return df[df[field] == value]

        return df

    # -------------------------------------------------
    # AGREGACIONES
    # -------------------------------------------------
    def _apply_aggregation(self, df, query_plan, agg):

        agg_type = agg.get("type")
        field = agg.get("field")
        group_by = query_plan.get("group_by")

        # -------------------------
        # COUNT
        # -------------------------
        if agg_type == "count":
            if group_by:
                return df.groupby(group_by).size().reset_index(name="count")
            return pd.DataFrame({"count": [len(df)]})

        # -------------------------
        # MEAN
        # -------------------------
        if agg_type == "mean":
            if group_by and field:
                return df.groupby(group_by)[field].mean().reset_index()
            if field:
                return pd.DataFrame({f"mean_{field}": [df[field].mean()]})
            return pd.DataFrame({"mean": [0]})

        # -------------------------
        # SUM
        # -------------------------
        if agg_type == "sum":
            if group_by and field:
                return df.groupby(group_by)[field].sum().reset_index()
            if field:
                return pd.DataFrame({f"sum_{field}": [df[field].sum()]})
            return pd.DataFrame({"sum": [0]})

        # -------------------------
        # PERCENT
        # -------------------------
        if agg_type == "percent":
            condition = agg.get("condition")

            if not condition:
                return pd.DataFrame({"percent": [0]})

            mask = self._build_condition(df, condition)

            percent = (mask.sum() / len(df)) * 100 if len(df) > 0 else 0

            return pd.DataFrame({"percent": [percent]})

        return df

    # -------------------------------------------------
    # CONDICIONES AUXILIARES
    # -------------------------------------------------
    def _build_condition(self, df, condition):

        field = condition.get("field")
        op = condition.get("operator")
        value = condition.get("value")

        if field not in df.columns:
            return pd.Series([False] * len(df))

        if op == ">":
            return df[field] > value

        if op == "<":
            return df[field] < value

        if op == ">=":
            return df[field] >= value

        if op == "<=":
            return df[field] <= value

        if op == "=":
            return df[field] == value

        return pd.Series([False] * len(df))
