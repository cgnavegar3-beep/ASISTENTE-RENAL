import pandas as pd
import numpy as np
import plotly.express as px
from core.dictionary import obtener_respuesta_aleatoria, VALORES_CATEGORICOS
from core.normalizer import limpiar_texto
from core.errors import CoreError

class ExecutionEngine:
    def __init__(self):
        self.column_fix = {
            "fg": "FG_CG",
            "fg_cg": "FG_CG",
            "fg_mdrd": "FG_MDRD",
            "fg_ckd": "FG_CKD",
            "filtrado glomerular": "FG_CG",
            "medicamento": "MEDICAMENTO",
            "paciente": "ID_REGISTRO",
            "edad": "EDAD",
            "sexo": "SEXO",
            "centro": "CENTRO"
        }

    def resolve_column(self, col, df):
        if col is None or df is None:
            return None
        
        if col in df.columns:
            return col
            
        col_norm = limpiar_texto(str(col))

        if col_norm in self.column_fix:
            mapped = self.column_fix[col_norm]
            if mapped in df.columns:
                return mapped

        for c in df.columns:
            if limpiar_texto(c) == col_norm:
                return c
        return None

    def aplicar_filtros(self, df, filtros_json):
        if df is None or df.empty or not filtros_json:
            return df

        mask = pd.Series(True, index=df.index)

        for f in filtros_json:
            col_raw = f.get("col")
            col = self.resolve_column(col_raw, df)
            op = f.get("op")
            val = f.get("val")

            if col is None:
                return df.iloc[0:0]

            val_str = str(val).lower()
            if col == "CENTRO" and val_str in VALORES_CATEGORICOS:
                val = VALORES_CATEGORICOS[val_str]

            val_n = limpiar_texto(val) if isinstance(val, str) else val
            series = df[col]

            try:
                # ---------------- NUMÉRICO ----------------
                if op in [">", "<", ">=", "<="]:
                    s = pd.to_numeric(series, errors="coerce")
                    v = float(val)
                    if op == ">": mask &= s > v
                    elif op == "<": mask &= s < v
                    elif op == ">=": mask &= s >= v
                    elif op == "<=": mask &= s <= v

                # ---------------- IGUALDAD ----------------
                elif op == "==":
                    if isinstance(val, (int, float)):
                        mask &= pd.to_numeric(series, errors="coerce") == val
                    else:
                        mask &= series.astype(str).str.upper().str.strip() == str(val).upper().strip()

                # 🔥 ---------------- CONTAINS (FIX CLAVE) ----------------
                elif op in ["contains", "contiene"]:
                    serie_limpia = series.astype(str).apply(limpiar_texto)
                    val_clean = str(val_n)

                    # 🔥 FIX SEXO
                    if col == "SEXO":
                        if "hombre" in val_clean:
                            mask &= serie_limpia.isin(["hombre", "h", "varon"])
                        elif "mujer" in val_clean:
                            mask &= serie_limpia.isin(["mujer", "m"])
                        else:
                            mask &= serie_limpia.str.contains(val_clean, na=False)

                    # 🔥 FIX MEDICAMENTOS
                    elif col == "MEDICAMENTO":
                        mask &= serie_limpia.str.contains(val_clean, na=False)

                    # 🔥 RESTO COLUMNAS
                    else:
                        mask &= serie_limpia.str.contains(val_clean, na=False)

            except Exception:
                continue

        return df[mask]

    def ejecutar_analisis(self, df_filtrado, query_json):
        if df_filtrado is None or df_filtrado.empty:
            return 0, "No se encontraron registros con esos criterios.", pd.DataFrame()

        req = query_json.get("request", {})
        metrica = req.get("metric", "conteo")
        var = self.resolve_column(req.get("target_col"), df_filtrado)
        group_by = self.resolve_column(req.get("group_by"), df_filtrado)
        limit = req.get("limit")

        try:
            # ---------------- AGRUPACIÓN ----------------
            if group_by:
                res = df_filtrado.groupby(group_by).size().reset_index(name="count")
                res = res.sort_values("count", ascending=False)
                
                if limit:
                    res = res.head(int(limit))
                
                return res, f"Resultados por {group_by}", res

            # ---------------- KPI ----------------
            if metrica == "conteo":
                resultado = len(df_filtrado)
            else:
                s = pd.to_numeric(df_filtrado[var], errors="coerce").dropna()
                if metrica == "media": resultado = round(s.mean(), 2)
                elif metrica == "max": resultado = s.max()
                elif metrica == "min": resultado = s.min()
                else: resultado = len(df_filtrado)

            return resultado, f"{resultado}", df_filtrado

        except Exception as e:
            return 0, f"Error en cálculo: {str(e)}", df_filtrado

    def generar_grafico(self, df_final, query_json):
        if not isinstance(df_final, pd.DataFrame) or df_final.empty:
            return None

        req = query_json.get("request", {})
        chart_type = req.get("chart_type", "kpi")
        group_by = req.get("group_by")
        target_col = req.get("target_col")

        try:
            if chart_type == "histogram":
                return px.histogram(df_final, x=target_col, title=f"Distribución de {target_col}")

            if chart_type == "pie":
                if "count" in df_final.columns:
                    return px.pie(df_final, names=df_final.columns[0], values="count")
                return px.pie(df_final, names=target_col)

            if chart_type == "bar":
                if "count" in df_final.columns:
                    return px.bar(df_final, x=df_final.columns[0], y="count", text="count")
                
            return None
        except:
            return None
