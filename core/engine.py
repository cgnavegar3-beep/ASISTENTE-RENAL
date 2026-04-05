import pandas as pd
import numpy as np
import plotly.express as px
from core.dictionary import obtener_respuesta_aleatoria
from core.normalizer import limpiar_texto
from core.errors import CoreError


class ExecutionEngine:
    def __init__(self):
        pass

    # -----------------------------
    # FILTROS
    # -----------------------------
    def aplicar_filtros(self, df, filtros_json):
        if df is None or df.empty:
            return df

        mask = pd.Series(True, index=df.index)

        for f in filtros_json:
            col, op, val = f.get("col"), f.get("op"), f.get("val")

            if col not in df.columns:
                raise CoreError("engine.py", f"Columna no encontrada: {col}", col)

            if val is None or val == "":
                continue

            val_n = limpiar_texto(val) if isinstance(val, str) else val

            try:
                series = df[col]

                if op == "==":
                    if isinstance(val, (int, float)):
                        mask &= (pd.to_numeric(series, errors="coerce") == val)
                    else:
                        mask &= (series.astype(str).apply(limpiar_texto) == val_n)

                elif op == "!=":
                    if isinstance(val, (int, float)):
                        mask &= (pd.to_numeric(series, errors="coerce") != val)
                    else:
                        mask &= (series.astype(str).apply(limpiar_texto) != val_n)

                elif op == ">":
                    mask &= (pd.to_numeric(series, errors="coerce") > float(val))

                elif op == "<":
                    mask &= (pd.to_numeric(series, errors="coerce") < float(val))

                elif op == ">=":
                    mask &= (pd.to_numeric(series, errors="coerce") >= float(val))

                elif op == "<=":
                    mask &= (pd.to_numeric(series, errors="coerce") <= float(val))

                elif op in ["contiene", "contains"]:
                    mask &= (
                        series.astype(str)
                        .apply(limpiar_texto)
                        .str.contains(str(val_n), na=False)
                    )

                else:
                    raise CoreError("engine.py", f"Operador no soportado: {op}", op)

            except Exception as e:
                raise CoreError("engine.py", f"Error en filtro: {col} {op} {val}", str(e))

        return df[mask]

    # -----------------------------
    # KPI + ANALÍTICA
    # -----------------------------
    def ejecutar_analisis(self, df_filtrado, query_json):
        if df_filtrado is None or df_filtrado.empty:
            return 0, obtener_respuesta_aleatoria("sin_resultados"), df_filtrado

        config_b = query_json.get("bloque_b", {})
        var = config_b.get("variable") or "ID_REGISTRO"
        metrica = config_b.get("operacion") or "conteo"
        group_by = config_b.get("agrupar")

        limit = query_json.get("bloque_d", {}).get("limit")

        try:
            # ---------------- KPI SIMPLE ----------------
            if group_by is None:

                series = df_filtrado[var] if var in df_filtrado.columns else None

                if metrica == "conteo":
                    resultado = len(df_filtrado)

                elif metrica in ["media"]:
                    col_num = pd.to_numeric(series, errors="coerce")
                    resultado = col_num.mean() if series is not None else 0

                elif metrica == "suma":
                    col_num = pd.to_numeric(series, errors="coerce")
                    resultado = col_num.sum() if series is not None else 0

                elif metrica == "max":
                    col_num = pd.to_numeric(series, errors="coerce")
                    resultado = col_num.max()

                elif metrica == "min":
                    col_num = pd.to_numeric(series, errors="coerce")
                    resultado = col_num.min()

                elif metrica == "porcentaje":
                    # FIX REAL: porcentaje necesita condición (ya filtrado)
                    total_global = len(df_filtrado)
                    resultado = 100 if total_global > 0 else 0

                else:
                    resultado = len(df_filtrado)

                frase = f"Resultado: {resultado}"
                return resultado, frase, df_filtrado

            # ---------------- AGRUPADO ----------------
            if group_by not in df_filtrado.columns:
                raise CoreError("engine.py", f"Group by no válido: {group_by}", group_by)

            data = df_filtrado.groupby(group_by).size().reset_index(name="count")
            data = data.sort_values("count", ascending=False)

            if limit:
                data = data.head(limit)

            frase = "Resultado agrupado generado"
            return data, frase, data

        except Exception as e:
            raise CoreError(
                "engine.py",
                "Error en ejecución de métrica",
                str(e)
            )

    # -----------------------------
    # GRÁFICOS
    # -----------------------------
    def generar_grafico(self, df_final, query_json):
        if df_final is None or df_final.empty:
            return None

        try:
            config_b = query_json.get("bloque_b", {})
            config_c = query_json.get("bloque_c", {})

            var = config_b.get("variable")
            chart_type = config_c.get("tipo", "kpi")

            # ---------------- HISTOGRAMA ----------------
            if chart_type == "histogram":
                numeric_cols = df_final.select_dtypes(include=np.number).columns
                col = var if var in df_final.columns else (numeric_cols[0] if len(numeric_cols) else None)
                return px.histogram(df_final, x=col) if col else None

            # ---------------- PIE ----------------
            if chart_type == "pie":
                if var and var in df_final.columns:
                    data = df_final[var].value_counts().reset_index()
                    data.columns = [var, "count"]
                    return px.pie(data, names=var, values="count")
                return None

            # ---------------- BAR ----------------
            if chart_type == "bar":
                if "count" in df_final.columns:
                    return px.bar(df_final, x=df_final.columns[0], y="count")
                return None

            # ---------------- TABLE ----------------
            if chart_type == "table":
                return None

            # fallback
            return None

        except Exception:
            return None
