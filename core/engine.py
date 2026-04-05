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

            try:
                if val is None or val == "":
                    continue

                val_n = limpiar_texto(val) if isinstance(val, str) else val

                if op == "==":
                    if isinstance(val, (int, float)):
                        mask &= (pd.to_numeric(df[col], errors='coerce') == val)
                    else:
                        mask &= (df[col].astype(str).apply(limpiar_texto) == val_n)

                elif op == ">":
                    mask &= (pd.to_numeric(df[col], errors='coerce') > float(val))

                elif op == "<":
                    mask &= (pd.to_numeric(df[col], errors='coerce') < float(val))

                elif op in ["contiene", "contains"]:
                    mask &= (df[col].astype(str).apply(limpiar_texto).str.contains(str(val_n), na=False))

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
            if metrica == "conteo":
                resultado = len(df_filtrado)

            elif metrica == "unico":
                resultado = df_filtrado[var].nunique() if var in df_filtrado.columns else 0

            elif metrica == "promedio":
                if var not in df_filtrado.columns:
                    raise CoreError("engine.py", f"Variable no encontrada: {var}", var)
                col_num = pd.to_numeric(df_filtrado[var], errors='coerce')
                resultado = col_num.mean() if not col_num.isnull().all() else 0

            else:
                resultado = len(df_filtrado)

            frase = f"El resultado del análisis es: {resultado}"
            return resultado, frase, df_filtrado

        except Exception as e:
            raise CoreError("engine.py", "Error en ejecución de métrica", str(e))

    def generar_grafico(self, df_final, query_json):
        if df_final is None or df_final.empty:
            return None

        try:
            col = df_final.columns[0]
            fig = px.histogram(df_final, x=col)
            return fig
        except:
            return None
