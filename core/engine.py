import pandas as pd
import numpy as np
import plotly.express as px
from core.dictionary import obtener_respuesta_aleatoria
from core.normalizer import limpiar_texto
from core.errors import CoreError


class ExecutionEngine:
    def __init__(self):
        # 🔥 FIX: mapping clínico robusto (mantiene tu base)
        self.column_fix = {
            "fg": "FG_CG",
            "fg_cg": "FG_CG",
            "fg_mdrd": "FG_MDRD",
            "fg_ckd": "FG_CKD",
            "filtrado glomerular": "FG_CG",

            "medicamento": "MEDICAMENTO",
            "medicamentos": "MEDICAMENTO",

            "paciente": "ID_REGISTRO",
            "id": "ID_REGISTRO",
            "id_registro": "ID_REGISTRO",

            "edad": "EDAD",
            "sexo": "SEXO"
        }

    # -----------------------------
    # NORMALIZADOR DE COLUMNAS
    # -----------------------------
    def resolve_column(self, col, df):
        if col is None:
            return None

        col_norm = limpiar_texto(str(col))

        # 1. match directo
        if col in df.columns:
            return col

        # 2. mapping clínico
        if col_norm in self.column_fix:
            mapped = self.column_fix[col_norm]
            if mapped in df.columns:
                return mapped

        # 3. match flexible
        for c in df.columns:
            if limpiar_texto(c) == col_norm:
                return c

        return None

    # -----------------------------
    # FILTROS
    # -----------------------------
    def aplicar_filtros(self, df, filtros_json):
        if df is None or df.empty:
            return df

        mask = pd.Series(True, index=df.index)

        for f in filtros_json:
            col = self.resolve_column(f.get("col"), df)
            op = f.get("op")
            val = f.get("val")

            if col is None:
                raise CoreError("engine.py", f"Columna no encontrada: {f.get('col')}", col)

            if val is None or val == "":
                continue

            val_n = limpiar_texto(val) if isinstance(val, str) else val
            series = df[col]

            try:
                # NUMÉRICO
                if op in [">", "<", ">=", "<="]:
                    s = pd.to_numeric(series, errors="coerce")
                    v = float(val)

                    if op == ">":
                        mask &= s > v
                    elif op == "<":
                        mask &= s < v
                    elif op == ">=":
                        mask &= s >= v
                    elif op == "<=":
                        mask &= s <= v

                # IGUALDAD
                elif op == "==":
                    if isinstance(val, (int, float)):
                        mask &= pd.to_numeric(series, errors="coerce") == val
                    else:
                        mask &= series.astype(str).apply(limpiar_texto) == val_n

                elif op == "!=":
                    if isinstance(val, (int, float)):
                        mask &= pd.to_numeric(series, errors="coerce") != val
                    else:
                        mask &= series.astype(str).apply(limpiar_texto) != val_n

                # TEXTO
                elif op in ["contiene", "contains"]:
                    mask &= series.astype(str).apply(limpiar_texto).str.contains(str(val_n), na=False)

                else:
                    raise CoreError("engine.py", f"Operador no soportado: {op}", op)

            except Exception as e:
                raise CoreError("engine.py", f"Error en filtro: {col} {op} {val}", str(e))

        return df[mask]

    # -----------------------------
    # ANALÍTICA
    # -----------------------------
    def ejecutar_analisis(self, df_filtrado, query_json):
        if df_filtrado is None or df_filtrado.empty:
            return 0, obtener_respuesta_aleatoria("sin_resultados"), df_filtrado

        config_b = query_json.get("bloque_b", {})
        var = self.resolve_column(config_b.get("variable") or "ID_REGISTRO", df_filtrado)
        metrica = config_b.get("operacion") or "conteo"
        group_by = self.resolve_column(config_b.get("agrupar"), df_filtrado)

        limit = query_json.get("bloque_d", {}).get("limit")

        try:
            # ---------------- KPI ----------------
            if group_by is None:

                if metrica == "conteo":
                    resultado = len(df_filtrado)

                else:
                    if var is None or var not in df_filtrado.columns:
                        return len(df_filtrado), "Variable no encontrada → conteo", df_filtrado

                    s = pd.to_numeric(df_filtrado[var], errors="coerce")

                    if metrica == "media":
                        resultado = s.mean()
                    elif metrica == "suma":
                        resultado = s.sum()
                    elif metrica == "max":
                        resultado = s.max()
                    elif metrica == "min":
                        resultado = s.min()
                    elif metrica == "porcentaje":
                        resultado = 100 if len(df_filtrado) > 0 else 0
                    else:
                        resultado = len(df_filtrado)

                return resultado, f"Resultado: {resultado}", df_filtrado

            # ---------------- GROUP BY ----------------
            if group_by not in df_filtrado.columns:
                raise CoreError("engine.py", f"Group by no válido: {group_by}", group_by)

            data = df_filtrado.groupby(group_by).size().reset_index(name="count")
            data = data.sort_values("count", ascending=False)

            if limit:
                data = data.head(limit)

            return data, "Resultado agrupado generado", data

        except Exception as e:
            raise CoreError("engine.py", "Error en ejecución de métrica", str(e))

    # -----------------------------
    # GRÁFICOS
    # -----------------------------
    def generar_grafico(self, df_final, query_json):
        if df_final is None or df_final.empty:
            return None

        try:
            config_b = query_json.get("bloque_b", {})
            config_c = query_json.get("bloque_c", {})

            var = self.resolve_column(config_b.get("variable"), df_final)
            chart_type = config_c.get("tipo", "kpi")

            # ---------------- HISTOGRAMA ----------------
            if chart_type == "histogram":
                col = var if var in df_final.columns else None
                return px.histogram(df_final, x=col) if col else None

            # ---------------- PIE ----------------
            if chart_type == "pie" and var:
                data = df_final[var].value_counts().reset_index()
                data.columns = [var, "count"]
                return px.pie(data, names=var, values="count")

            # ---------------- BAR ----------------
            if chart_type == "bar" and "count" in df_final.columns:
                return px.bar(df_final, x=df_final.columns[0], y="count")

            return None

        except Exception:
            return None
