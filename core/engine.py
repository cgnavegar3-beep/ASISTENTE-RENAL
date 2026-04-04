import pandas as pd
import numpy as np
import plotly.express as px
from core.dictionary import obtener_respuesta_aleatoria
from core.normalizer import limpiar_texto
from core.errors import CoreError

class ExecutionEngine:
    def __init__(self):
        # Mantenemos el init ligero
        pass

    def aplicar_filtros(self, df, filtros_json):
        """Aplica filtros. Se asume que 'op' y 'col' ya vienen validados."""
        if df is None or df.empty:
            return df
            
        mask = pd.Series(True, index=df.index)
        
        for f in filtros_json:
            col, op, val = f.get("col"), f.get("op"), f.get("val")
            
            if col not in df.columns:
                raise CoreError("engine.py", f"Columna no encontrada: {col}", col)

            try:
                # Optimización: Normalizamos el valor de comparación una sola vez fuera del apply
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
                elif op == "contiene":
                    mask &= (df[col].astype(str).apply(limpiar_texto).str.contains(str(val_n), na=False))

            except Exception as e:
                raise CoreError("engine.py", f"Error en filtro: {col} {op} {val}", str(e))
                
        return df[mask]

    def ejecutar_analisis(self, df_filtrado, query_json):
        """Calcula métrica final basándose en el estándar del bloque_b."""
        if df_filtrado is None or df_filtrado.empty:
            return 0, obtener_respuesta_aleatoria("sin_resultados"), df_filtrado

        config_b = query_json.get("bloque_b", {})
        var = config_b.get("variable", "ID_REGISTRO")
        # Estándar técnico único: conteo, unico, promedio
        metrica = config_b.get("metrica", "conteo") 

        try:
            if metrica == "conteo":
                resultado = len(df_filtrado)
                tipo_res = "conteo"
            elif metrica == "unico":
                if var not in df_filtrado.columns:
                    raise CoreError("engine.py", f"Variable no encontrada: {var}", var)
                resultado = df_filtrado[var].nunique()
                tipo_res = "kpi"
            elif metrica == "promedio":
                col_num = pd.to_numeric(df_filtrado[var], errors='coerce')
                if col_num.isnull().all():
