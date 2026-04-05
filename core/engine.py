import pandas as pd
import numpy as np
import plotly.express as px
from core.dictionary import obtener_respuesta_aleatoria
from core.normalizer import limpiar_texto
from core.errors import CoreError


class ExecutionEngine:
    def __init__(self):
        pass

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

    def ejecutar_analisis(self, df_filtrado, query_json):
        if df_filtrado is None or df_filtrado.empty:
            return 0, obtener_respuesta_aleatoria("sin_resultados"), df_filtrado

        config_b = query_json.get("bloque_b", {})
        var = config_b.get("variable") or "ID_REGISTRO"
        metrica = config_b.get("operacion") or "conteo"

        try:
            series = df_filtrado[var] if var in df_filtrado.columns else None

            if metrica == "conteo":
                resultado = len(df_filtrado)

            elif metrica in ["unico", "conteo_unico"]:
                resultado = series.nunique() if series is not None else 0

            elif metrica in ["promedio", "media"]:
                if series is None:
                    raise CoreError("engine.py", f"Variable no encontrada: {var}", var)

                col_num = pd.to_numeric(series, errors="coerce")
                resultado = col_num.mean() if not col_num.isnull().all() else 0

            elif metrica == "suma":
                if series is None:
                    raise CoreError("engine.py", f"Variable no encontrada: {var}", var)

                col_num = pd.to_numeric(series, errors="coerce")
                resultado = col_num.sum() if not col_num.isnull().all() else 0

            elif metrica == "porcentaje":
                total = len(df_filtrado)
                if total == 0:
                    resultado = 0
                else:
                    resultado = (len(df_filtrado) / total) * 100

            elif metrica == "max":
                if series is None:
                    raise CoreError("engine.py", f"Variable no encontrada: {var}", var)
                col_num = pd.to_numeric(series, errors="coerce")
                resultado = col_num.max()

            elif metrica == "min":
                if series is None:
                    raise CoreError("engine.py", f"Variable no encontrada: {var}", var)
                col_num = pd.to_numeric(series, errors="coerce")
                resultado = col_num.min()

            else:
                resultado = len(df_filtrado)

            frase = f"El resultado del análisis es: {resultado}"
            return resultado, frase, df_filtrado

        except Exception as e:
            raise CoreError(
                "engine.py",
                "Error en ejecución de métrica",
                str(e)
            )

    def generar_grafico(self, df_final, query_json):
        if df_final is None or df_final.empty:
            return None

        try:
            config_b = query_json.get("bloque_b", {})
            config_c = query_json.get("bloque_c", {})

            var = config_b.get("variable")
            chart_type = config_c.get("tipo", "kpi")

            if chart_type == "histogram":
                if var and var in df_final.columns:
                    return px.histogram(df_final, x=var)
                numeric_cols = df_final.select_dtypes(include=np.number).columns
                col = numeric_cols[0] if len(numeric_cols) > 0 else None
                return px.histogram(df_final, x=col) if col else None

            if chart_type == "pie":
                if var and var in df_final.columns:
                    data = df_final[var].value_counts().reset_index()
                    data.columns = [var, "count"]
                    return px.pie(data, names=var, values="count")
                return None

            if chart_type == "bar":
                if var and var in df_final.columns:
                    data = df_final[var].value_counts().reset_index()
                    data.columns = [var, "count"]
                    return px.bar(data, x=var, y="count")
                return None

            if chart_type == "table":
                return None

            # fallback seguro
            numeric_cols = df_final.select_dtypes(include=np.number).columns
            col = numeric_cols[0] if len(numeric_cols) > 0 else None
            return px.histogram(df_final, x=col) if col else None

        except Exception:
            return None
