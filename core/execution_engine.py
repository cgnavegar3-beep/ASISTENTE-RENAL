# core/execution_engine.py

import pandas as pd


class ExecutionEngine:
    """
    Ejecuta el query_plan generado por QueryBuilder
    sobre un DataFrame pandas.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def execute(self, query_plan: dict) -> pd.DataFrame:
        df = self.df.copy()

        # ---------------------------
        # 1. FILTROS
        # ---------------------------
        df = self._apply_filters(df, query_plan.get("filters", []))

        # ---------------------------
        # 2. GROUP BY + AGGREGATION
        # ---------------------------
        agg = query_plan.get("aggregation")

        if agg:
            df = self._apply_aggregation(df, query_plan, agg)

        # ---------------------------
        # 3. TOP N
        # ---------------------------
        if query_plan.get("operation") == "top":
            limit = query_plan.get("limit", 10)
            df = df.head(limit)

        return df

    # -------------------------------------------------
    # FILTROS
    # -------------------------------------------------

    def _apply_filters(self, df, filters):
        for f in filters:
            field = f["field"]
            op = f["operator"]
            value = f["value"]

            if op == ">":
                df = df[df[field] > value]
            elif op == "<":
                df = df[df[field] < value]
            elif op == ">=":
                df = df[df[field] >= value]
            elif op == "<=":
                df = df[df[field] <= value]
            elif op == "=":
                df = df[df[field] == value]

        return df

    # -------------------------------------------------
    # AGREGACIONES
    # -------------------------------------------------

    def _apply_aggregation(self, df, query_plan, agg):
        agg_type = agg.get("type")
        field = agg.get("field")

        group_by = query_plan.get("group_by")

        # ---------------------------
        # COUNT
        # ---------------------------
        if agg_type == "count":
            if group_by:
                return df.groupby(group_by).size().reset_index(name="count")
            return pd.DataFrame({"count": [len(df)]})

        # ---------------------------
        # MEAN
        # ---------------------------
        if agg_type == "mean":
            if group_by:
                return df.groupby(group_by)[field].mean().reset_index()
            return pd.DataFrame({f"mean_{field}": [df[field].mean()]})

        # ---------------------------
        # SUM
        # ---------------------------
        if agg_type == "sum":
            if group_by:
                return df.groupby(group_by)[field].sum().reset_index()
            return pd.DataFrame({f"sum_{field}": [df[field].sum()]})

        # ---------------------------
        # PERCENT
        # ---------------------------
        if agg_type == "percent":
            condition = agg.get("condition")

            if not condition:
                return pd.DataFrame({"percent": [0]})

            mask = self._build_condition(df, condition)
            percent = (mask.sum() / len(df)) * 100

            return pd.DataFrame({"percent": [percent]})

        return df

    # -------------------------------------------------
    # CONDICIONES
    # -------------------------------------------------

    def _build_condition(self, df, condition):
        field = condition["field"]
        op = condition["operator"]
        value = condition["value"]

        if op == ">":
            return df[field] > value
        elif op == "<":
            return df[field] < value
        elif op == ">=":
            return df[field] >= value
        elif op == "<=":
            return df[field] <= value
        elif op == "=":
            return df[field] == value

        return pd.Series([False] * len(df))
