# core/engine.py
import pandas as pd
import numpy as np
from core.dictionary import obtener_respuesta_aleatoria
from core.normalizer import limpiar_texto  # Importante para la comparación robusta

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
                # Normalización de valores para comparación de texto
                val_n = limpiar_texto(val)
                df_col_n = df[col].astype(str).apply(limpiar_texto)

                if "==" in op:
                    if isinstance(val, (int, float)):
                        mask &= (pd.to_numeric(df[col], errors='coerce') == val)
                    else:
                        mask &= (df_col_n == val_n)
                
                elif "!=" in op:
                    if isinstance(val, (int, float)):
                        mask &= (pd.to_numeric(df[col], errors='coerce') != val)
                    else:
                        mask &= (df_col_n != val_n)
                
                elif ">" in op:
                    mask &= (pd.to_numeric(df[col], errors='coerce') > float(val))
                
                elif "<" in op:
                    mask &= (pd.to_numeric(df[col], errors='coerce') < float(val))
                
                elif "≥" in op:
                    mask &= (pd.to_numeric(df[col], errors='coerce') >= float(val))
                
                elif "≤" in op:
                    mask &= (pd.to_numeric(df[col], errors='coerce') <= float(val))
                
                elif "contiene" in op:
                    mask &= (df_col_n.str.contains(val_n, na=False))

            except Exception as e:
                print(f"⚠️ Error procesando filtro en columna '{col}': {e}")
                continue
                
        return df[mask]

    def ejecutar_analisis(self, df_filtrado, query_json):
        """
        Calcula el resultado (Bloque B) y genera la respuesta humana 
        usando las frases aleatorias del diccionario.
        """
        config_b = query_json.get("bloque_b", {})
        var = config_b.get("variable", "ID_REGISTRO")
        op = config_b.get("operacion", "Conteo Único (Pacientes)")
        
        # Caso: No hay datos tras filtrar
        if df_filtrado is None or df_filtrado.empty:
            return 0, obtener_respuesta_aleatoria("sin_resultados"), df_filtrado

        resultado = 0
        categoria_res = "kpi"

        try:
            # 1. CONTEO DE REGISTROS (Filas totales)
            if "Total" in op or "Conteo" in op:
                resultado = len(df_filtrado)
                categoria_res = "conteo"
            
            # 2. CONTEO ÚNICO (Pacientes distintos)
            elif "Único" in op:
                resultado = df_filtrado[var].nunique()
                categoria_res = "kpi"
            
            # 3. PROMEDIO
            elif "Promedio" in op:
                resultado = pd.to_numeric(df_filtrado[var], errors='coerce').mean()
                resultado = round(resultado, 2) if not np.isnan(resultado) else 0
                categoria_res = "promedio"
            
            # 4. SUMA (Si fuera necesario en el futuro)
            elif "Suma" in op:
                resultado = pd.to_numeric(df_filtrado[var], errors='coerce').sum()
                categoria_res = "kpi"

        except Exception as e:
            print(f"❌ Error en el cálculo del Bloque B: {e}")
            return 0, obtener_respuesta_aleatoria("sin_resultados"), df_filtrado

        # Generar la frase humana final formateada
        # Pasamos 'valor', 'variable' y 'N' para que las frases del diccionario funcionen
        res_humana = obtener_respuesta_aleatoria(
            categoria_res, 
            valor=resultado,
            variable=var,
            N=query_json.get("bloque_d", {}).get("limit", 10),
            lista="", # Se llenaría en caso de listados
            grupo=config_b.get("agrupar", "Total"),
            resumen="" # Se llenaría en caso de agrupaciones
        )

        return resultado, res_humana, df_filtrado
