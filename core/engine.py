import pandas as pd
import numpy as np
import plotly.express as px

class ExecutionEngine:
    def __init__(self):
        pass

    def ejecutar_analisis(self, df_filtrado, request):

        if df_filtrado is None or df_filtrado.empty:
            return "No se encontraron registros con esos criterios."

        df_proc = df_filtrado.copy()

        metric = request.get("metric", "conteo")
        variable = request.get("target_col", "ID_REGISTRO")
        group_by = request.get("group_by")
        limit = request.get("limit")
        label_map = request.get("label_map")

        for col in [variable, group_by]:
            if col and col in df_proc.columns:
                if any(x in col.upper() for x in ["FG", "EDAD"]):
                    df_proc[col] = pd.to_numeric(df_proc[col], errors='coerce')

        if group_by in ["EDAD", "FG_CG"]:
            temp_df = df_proc.dropna(subset=[group_by]).copy()

            if group_by == "EDAD":
                bins = [0,10,20,30,40,50,60,70,80,90,100,150]
                labels = ["0-10","10-20","20-30","30-40","40-50",
                          "50-60","60-70","70-80","80-90","90-100",">100"]
                temp_df["RANGO"] = pd.cut(temp_df["EDAD"], bins=bins, labels=labels)

            else:
                bins = [0,15,30,45,60,300]
                labels = ["0-15","15-30","30-45","45-60",">60"]
                temp_df["RANGO"] = pd.cut(temp_df["FG_CG"], bins=bins, labels=labels)

            return temp_df.groupby("RANGO").size().reset_index(name="CONTEO")

        if group_by:
            resultado = df_proc.groupby(group_by).size().reset_index(name="CONTEO")

            if limit:
                resultado = resultado.head(int(limit))

            return resultado

        if metric == "media":
            return round(pd.to_numeric(df_proc[variable], errors='coerce').mean(), 2)

        # 🔥 porcentaje eliminado como KPI (se usa solo visual)
        return int(df_proc[variable].nunique())

    def generar_grafico(self, df_final, query_json):

        if not isinstance(df_final, pd.DataFrame) or df_final.empty:
            return None

        req = query_json.get("request", {})
        chart_type = req.get("chart_type", "bar")
        group_by = req.get("group_by")
        label_map = req.get("label_map")

        if not group_by:
            return None

        title = f"Distribución por {group_by}"

        if chart_type == "pie":
            return px.pie(
                df_final,
                values="CONTEO",
                names=group_by,
                title=title
            )

        return px.bar(
            df_final,
            x=group_by,
            y="CONTEO",
            title=title
        )

    def aplicar_filtros(self, df, filtros):

        if not filtros:
            return df

        df_f = df.copy()
        mask = pd.Series([True] * len(df_f), index=df_f.index)

        for f in filtros:
            col, op, val = f.get("col"), f.get("op"), f.get("val")

            if col not in df_f.columns:
                continue

            if any(x in col.upper() for x in ["FG", "EDAD"]):
                df_f[col] = pd.to_numeric(df_f[col], errors='coerce')
                val = float(val)

                if op == "<":
                    mask &= df_f[col] < val
                elif op == ">":
                    mask &= df_f[col] > val
                elif op == "==":
                    mask &= df_f[col] == val

            else:
                series = df_f[col].astype(str).str.upper()
                if op == "contiene":
                    mask &= series.str.contains(str(val).upper(), na=False)
                elif op == "==":
                    mask &= series == str(val).upper()

        return df_f[mask]
