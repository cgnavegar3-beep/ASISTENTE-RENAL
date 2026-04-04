import pandas as pd
import numpy as np
import plotly.express as px
from core.dictionary import obtener_respuesta_aleatoria
from core.normalizer import limpiar_texto
# --- ADICIÓN DE ERROR ---
from core.errors import CoreError

class ExecutionEngine:
    def __init__(self):
        pass

    def aplicar_filtros(self, df, filtros_json):
        """Aplica los filtros del Bloque A con validación estricta."""
        if df is None or df.empty:
            # No lanzamos error aquí, simplemente devolvemos vacío para que el análisis lo gestione
            return df
            
        mask = pd.Series(True, index=df.index)
        
        for f in filtros_json:
            col = f.get("col")
            op = f.get("op")
            val = f.get("val")
            
            if col not in df.columns:
                # Lanzamos CoreError porque el validador falló o el DF no es el esperado
                raise CoreError("engine.py", f"Columna no encontrada en el dataset activo", col)

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
                # Si el casteo a float falla o hay datos corruptos, informamos
                raise CoreError(
                    modulo="engine.py",
                    mensaje=f"Error de tipos al aplicar filtro en '{col}'",
                    detalle=f"Operación: {op}, Valor: {val}. Error: {str(e)}"
                )
                
        return df[mask]

    def ejecutar_analisis(self, df_filtrado, query_json):
        """Calcula el resultado (Bloque B) con gestión de estados vacíos."""
        config_b = query_json.get("bloque_b", {})
        var = config_b.get("variable", "ID_REGISTRO")
        op = config_b.get("operacion", "Conteo Único (Pacientes)")
        
        if df_filtrado is None or df_filtrado.empty:
            # Caso de negocio: no hay datos. No es un error de sistema, es un resultado.
            return 0, obtener_respuesta_aleatoria("sin_resultados"), df_filtrado

        try:
            if "Total" in op or "Conteo" in op:
                resultado = len(df_filtrado)
                cat = "conteo"
            elif "Único" in op:
                if var not in df_filtrado.columns:
                    raise CoreError("engine.py", "Variable de conteo único no disponible", var)
                resultado = df_filtrado[var].nunique()
                cat = "kpi"
            elif "Promedio" in op:
                col_num = pd.to_numeric(df_filtrado[var], errors='coerce')
                if col_num.isnull().all():
                     raise CoreError("engine.py", "Imposible calcular promedio: la columna no es numérica", var)
                resultado = round(col_num.mean(), 2)
                cat = "promedio"
            else:
                resultado = len(df_filtrado)
                cat = "kpi"
        except CoreError as ce:
            raise ce
        except Exception as e:
            raise CoreError("engine.py", "Fallo inesperado en cálculo métrico", str(e))

        res_humana = obtener_respuesta_aleatoria(
            cat, valor=resultado, variable=var,
            N=query_json.get("bloque_d", {}).get("limit", 10)
        )
        return resultado, res_humana, df_filtrado

    def generar_grafico(self, df_res, query_json):
        """Genera objetos Plotly con validación de renderizado."""
        if df_res is None or df_res.empty:
            return None

        formato = limpiar_texto(query_json.get("bloque_c", {}).get("formato", ""))
        config_b = query_json.get("bloque_b", {})
        eje_x = config_b.get("agrupar", "SEXO")
        
        if eje_x == "Ninguno":
            eje_x = "SEXO" 

        if eje_x not in df_res.columns:
            raise CoreError("engine.py", "Columna de agrupación no encontrada para gráfico", eje_x)

        try:
            # 1. SECTORES
            if any(w in formato for w in ["torta", "pie", "sectores", "circular"]):
                fig = px.pie(df_res, names=eje_x, title=f"Proporción por {eje_x}")
            
            # 2. BARRAS H
            elif "horizontal" in formato:
                df_counts = df_res[eje_x].value_counts().reset_index()
                fig = px.bar(df_counts, x='count', y=eje_x, orientation='h', 
                             title=f"Distribución Horizontal por {eje_x}")
            
            # 3. BARRAS V (Default)
            elif "barras" in formato or formato == "" or "vertical" in formato:
                df_counts = df_res[eje_x].value_counts().reset_index()
                fig = px.bar(df_counts, x=eje_x, y='count', title=f"Distribución por {eje_x}")
            
            else:
                # Si llega aquí algo que el generador aprobó pero el engine no sabe hacer:
                raise CoreError("engine.py", "Formato de gráfico reconocido pero no implementado", formato)

            fig.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=40, b=20))
            return fig
            
        except CoreError as ce:
            raise ce
        except Exception as e:
            raise CoreError("engine.py", "Error crítico en motor Plotly", str(e))
