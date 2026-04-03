# core/engine.py
import pandas as pd
import numpy as np
import plotly.express as px
from core.dictionary import obtener_respuesta_aleatoria
from core.normalizer import limpiar_texto

class ExecutionEngine:
    def __init__(self):
        pass

    def aplicar_filtros(self, df, filtros_json):
        """Aplica los filtros del Bloque A sobre el DataFrame."""
        if df is None or df.empty:
            return df
            
        mask = pd.Series(True, index=df.index)
        
        for f in filtros_json:
            col = f.get("col")
            op = f.get("op")
            val = f.get("val")
            
            if col not in df.columns:
                continue

            try:
                val_n = limpiar_texto(val)
                df_col_n = df[col].astype(str).apply(limpiar_texto)

                if "==" in op:
                    if isinstance(val, (int, float)):
                        mask &= (pd.to_numeric(df[col], errors='coerce') == val)
                    else:
                        mask &= (df_col_n == val_n)
                elif ">" in op:
                    mask &= (pd.to_numeric(df[col], errors='coerce') > float(val))
                elif "<" in op:
                    mask &= (pd.to_numeric(df[col], errors='coerce') < float(val))
                elif "contiene" in op:
                    mask &= (df_col_n.str.contains(val_n, na=False))

            except Exception as e:
                print(f"⚠️ Error en filtro '{col}': {e}")
                continue
                
        return df[mask]

    def ejecutar_analisis(self, df_filtrado, query_json):
        """Calcula el resultado (Bloque B) y genera la respuesta humana."""
        config_b = query_json.get("bloque_b", {})
        var = config_b.get("variable", "ID_REGISTRO")
        op = config_b.get("operacion", "Conteo Único (Pacientes)")
        
        if df_filtrado is None or df_filtrado.empty:
            return 0, obtener_respuesta_aleatoria("sin_resultados"), df_filtrado

        try:
            if "Total" in op or "Conteo" in op:
                resultado = len(df_filtrado)
                cat = "conteo"
            elif "Único" in op:
                resultado = df_filtrado[var].nunique()
                cat = "kpi"
            elif "Promedio" in op:
                resultado = round(pd.to_numeric(df_filtrado[var], errors='coerce').mean(), 2)
                cat = "promedio"
            else:
                resultado = len(df_filtrado)
                cat = "kpi"
        except:
            return 0, obtener_respuesta_aleatoria("sin_resultados"), df_filtrado

        res_humana = obtener_respuesta_aleatoria(
            cat, valor=resultado, variable=var,
            N=query_json.get("bloque_d", {}).get("limit", 10)
        )
        return resultado, res_humana, df_filtrado

    def generar_grafico(self, df_res, query_json):
        """Genera gráficos de barras (H/V) y sectores (Bloque C)."""
        if df_res is None or df_res.empty:
            return None

        formato = limpiar_texto(query_json.get("bloque_c", {}).get("formato", ""))
        config_b = query_json.get("bloque_b", {})
        eje_x = config_b.get("agrupar", "SEXO") # Por defecto agrupar por sexo si no hay nada
        
        # Si no hay agrupación definida, no podemos hacer barras/sectores útiles
        if eje_x == "Ninguno":
            eje_x = "SEXO" 

        try:
            # 1. GRÁFICO DE SECTORES (Torta / Pie)
            if any(w in formato for w in ["torta", "pie", "sectores", "circular"]):
                fig = px.pie(df_res, names=eje_x, title=f"Proporción por {eje_x}")
            
            # 2. BARRAS HORIZONTALES
            elif "horizontal" in formato:
                # Contamos ocurrencias para el gráfico
                df_counts = df_res[eje_x].value_counts().reset_index()
                fig = px.bar(df_counts, x='count', y=eje_x, orientation='h', 
                             title=f"Distribución Horizontal por {eje_x}",
                             labels={'count': 'Cantidad', eje_x: eje_x})
            
            # 3. BARRAS VERTICALES (Por defecto)
            else:
                df_counts = df_res[eje_x].value_counts().reset_index()
                fig = px.bar(df_counts, x=eje_x, y='count', 
                             title=f"Distribución por {eje_x}",
                             labels={'count': 'Cantidad'})

            fig.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=40, b=20))
            return fig
        except Exception as e:
            print(f"❌ Error al crear gráfico: {e}")
            return None
