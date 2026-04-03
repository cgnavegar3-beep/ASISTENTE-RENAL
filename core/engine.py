# core/engine.py
import pandas as pd
import numpy as np
from core.dictionary import obtener_respuesta_aleatoria

class ExecutionEngine:
    def __init__(self):
        pass

    def aplicar_filtros(self, df, filtros_json):
        """Reclica tu lógica de 'mask' del Bloque A."""
        mask = pd.Series(True, index=df.index)
        for f in filtros_json:
            col = f["col"]
            op = f["op"]
            val = f["val"]
            
            try:
                if "==" in op:
                    mask &= (df[col].astype(str) == str(val))
                elif "!=" in op:
                    mask &= (df[col].astype(str) != str(val))
                elif ">" in op:
                    mask &= (pd.to_numeric(df[col], errors='coerce') > float(val))
                elif "<" in op:
                    mask &= (pd.to_numeric(df[col], errors='coerce') < float(val))
                elif "≥" in op:
                    mask &= (pd.to_numeric(df[col], errors='coerce') >= float(val))
                elif "≤" in op:
                    mask &= (pd.to_numeric(df[col], errors='coerce') <= float(val))
                elif "contiene" in op:
                    mask &= (df[col].astype(str).str.contains(str(val), case=False, na=False))
            except Exception as e:
                print(f"Error filtrando columna {col}: {e}")
                continue
        return df[mask]

    def ejecutar_analisis(self, df_filtrado, query_json):
        """Ejecuta la operación del Bloque B y elige la respuesta del diccionario."""
        config_b = query_json["bloque_b"]
        var = config_b["variable"]
        op = config_b["operacion"]
        
        if df_filtrado.empty:
            return 0, obtener_respuesta_aleatoria("sin_resultados"), None

        # Lógica de cálculo
        if "Total" in op:
            resultado = len(df_filtrado)
            categoria_res = "conteo"
        elif "Único" in op:
            resultado = df_filtrado[var].nunique()
            categoria_res = "kpi"
        elif "Promedio" in op:
            resultado = pd.to_numeric(df_filtrado[var], errors='coerce').mean()
            categoria_res = "promedio"
        else:
            resultado = len(df_filtrado)
            categoria_res = "kpi"

        # Formatear respuesta humana
        res_humana = obtener_respuesta_aleatoria(
            categoria_res, 
            valor=f"{resultado:.2f}" if isinstance(resultado, float) else resultado,
            variable=var
        )

        return resultado, res_humana, df_filtrado
