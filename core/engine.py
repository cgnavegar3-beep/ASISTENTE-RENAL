import pandas as pd
import numpy as np
import plotly.express as px
from core.dictionary import obtener_respuesta_aleatoria, VALORES_CATEGORICOS
from core.normalizer import limpiar_texto
from core.errors import CoreError

class ExecutionEngine:
    def __init__(self):
        # Mantenemos el fix pero priorizamos el match exacto
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
        
        # 1. SI YA EXISTE, NO TOCAR (Evita FG_CG_CG)
        if col in df.columns:
            return col
            
        col_norm = limpiar_texto(str(col))

        # 2. Match en mapping clínico
        if col_norm in self.column_fix:
            mapped = self.column_fix[col_norm]
            if mapped in df.columns:
                return mapped

        # 3. Match flexible (case insensitive / sin espacios)
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
                # Si no encontramos la columna, el filtro es inválido pero no rompemos, 
                # simplemente devolvemos vacío para no dar el "12" engañoso.
                return df.iloc[0:0] 

            # Normalizar el valor si es un Centro (usando el diccionario)
            val_str = str(val).lower()
            if col == "CENTRO" and val_str in VALORES_CATEGORICOS:
                val = VALORES_CATEGORICOS[val_str]

            val_n = limpiar_texto(val) if isinstance(val, str) else val
            series = df[col]

            try:
                # NUMÉRICO
                if op in [">", "<", ">=", "<="]:
                    s = pd.to_numeric(series, errors="coerce")
                    v = float(val)
                    if op == ">": mask &= s > v
                    elif op == "<": mask &= s < v
                    elif op == ">=": mask &= s >= v
                    elif op == "<=": mask &= s <= v

                # IGUALDAD / CATEGÓRICO
                elif op == "==":
                    if isinstance(val, (int, float)):
                        mask &= pd.to_numeric(series, errors="coerce") == val
                    else:
                        mask &= series.astype(str).str.upper().str.strip() == str(val).upper().strip()

                elif op == "contains":
                    mask &= series.astype(str).apply(limpiar_texto).str.contains(str(val_n), na=False)

            except Exception as e:
                continue # Ignorar filtros mal formados para evitar crash

        return df[mask]

    def ejecutar_analisis(self, df_filtrado, query_json):
        if df_filtrado is None or df_filtrado.empty:
            return 0, "No se encontraron registros con esos criterios.", pd.DataFrame()

        # Extraer parámetros de la petición (Bloques B, C y D)
        req = query_json.get("request", {})
        metrica = req.get("metric", "conteo")
        var = self.resolve_column(req.get("target_col"), df_filtrado)
        group_by = self.resolve_column(req.get("group_by"), df_filtrado)
        limit = req.get("limit")

        try:
            # --- CASO 1: AGRUPACIÓN (Gráficos, Tablas, Rankings) ---
            if group_by:
                # Contamos ocurrencias por grupo
                res = df_filtrado.groupby(group_by).size().reset_index(name="count")
                res = res.sort_values("count", ascending=False)
                
                if limit:
                    res = res.head(int(limit))
                
                return res, f"Resultados por {group_by}", res

            # --- CASO 2: KPI (Un solo número) ---
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
                # Si viene de un group_by ya tiene columna 'count'
                if "count" in df_final.columns:
                    return px.pie(df_final, names=df_final.columns[0], values="count")
                # Si no, agrupamos aquí
                return px.pie(df_final, names=target_col)

            if chart_type == "bar":
                if "count" in df_final.columns:
                    # Usamos la primera columna (la dimensión) y 'count'
                    return px.bar(df_final, x=df_final.columns[0], y="count", text="count")
                
            return None
        except:
            return None
