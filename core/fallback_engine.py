from typing import Dict, Any, List
import pandas as pd


# =========================================================
# FALLBACK ENGINE PRINCIPAL
# =========================================================
class FallbackEngine:

    def __init__(self):
        pass

    # -------------------------
    # ENTRY POINT
    # -------------------------
    def safe_execute(self, plan: Dict[str, Any], df: pd.DataFrame) -> pd.DataFrame:
        """
        Ejecuta el plan de forma segura.
        Si algo falla → aplica fallback controlado.
        """

        try:
            return self._execute(plan, df)

        except Exception as e:
            print(f"[FALLBACK ACTIVADO] {str(e)}")
            return self._safe_fallback(df)

    # -------------------------
    # EJECUCIÓN NORMAL
    # -------------------------
    def _execute(self, plan: Dict[str, Any], df: pd.DataFrame) -> pd.DataFrame:

        # 1. filtros
        df_filtered = self._apply_filters(df, plan.get("filters", []))

        # 2. groupby
        groupby = plan.get("groupby", [])

        if groupby:
            df_grouped = df_filtered.groupby(groupby)
        else:
            df_grouped = df_filtered

        # 3. operación (CORREGIDO: operacion)
        op = plan.get("operacion", "count")

        if op == "count":
            result = df_grouped.size().reset_index(name="count")

        elif op == "mean":
            var = plan.get("variable")
            if var not in df_filtered.columns:
                return df_filtered.head(10)

            result = df_grouped[var].mean().reset_index()

        elif op == "sum":
            var = plan.get("variable")
            if var not in df_filtered.columns:
                return df_filtered.head(10)

            result = df_grouped[var].sum().reset_index()

        elif op == "nunique":
            var = plan.get("variable")
            if var not in df_filtered.columns:
                return df_filtered.head(10)

            result = df_grouped[var].nunique().reset_index(name="nunique")

        else:
            # fallback seguro si operación no soportada
            result = df_grouped.size().reset_index(name="count")

        # 4. order_by
        order_by = plan.get("order_by")
        if order_by:
            col = order_by.get("column")
            asc = order_by.get("direction", "DESC") == "ASC"

            if col in result.columns:
                result = result.sort_values(by=col, ascending=asc)

        # 5. top_n
        top_n = plan.get("top_n")
        if top_n:
            result = result.head(top_n)

        return result

    # =========================================================
    # FILTROS SEGURIDAD
    # =========================================================
    def _apply_filters(self, df: pd.DataFrame, filters: List[Dict]) -> pd.DataFrame:

        if not filters:
            return df

        for f in filters:
            col = f.get("column")
            op = f.get("operator")
            val = f.get("value")

            if col not in df.columns:
                continue

            if op == "==":
                df = df[df[col] == val]

            elif op == "!=":
                df = df[df[col] != val]

            elif op == ">":
                df = df[df[col] > val]

            elif op == "<":
                df = df[df[col] < val]

            elif op == ">=":
                df = df[df[col] >= val]

            elif op == "<=":
                df = df[df[col] <= val]

            elif op == "IN":
                if isinstance(val, list):
                    df = df[df[col].isin(val)]

            elif op == "NOT_IN":
                if isinstance(val, list):
                    df = df[~df[col].isin(val)]

            elif op == "IS_NULL":
                df = df[df[col].isna()]

            elif op == "NOT_NULL":
                df = df[df[col].notna()]

            elif op == "BETWEEN":
                if isinstance(val, list) and len(val) == 2:
                    df = df[df[col].between(val[0], val[1])]

        return df

    # =========================================================
    # FALLBACK SEGURO
    # =========================================================
    def _safe_fallback(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Siempre devuelve algo válido aunque todo falle.
        """

        return df.head(10).copy()
