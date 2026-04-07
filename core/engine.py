import pandas as pd
import numpy as np

class ExecutionEngine:
    def __init__(self):
        # No requiere inicializar con DFs si el orquestador se los pasa en cada llamada
        pass

    def ejecutar_analisis(self, df_filtrado, request):
        """
        Recibe el DF ya filtrado y el diccionario de petición (request).
        """
        # Extraemos variables del request (Bloque B y D)
        metric = request.get("metric", "conteo")
        variable = request.get("target_col", "ID_REGISTRO")
        group_by = request.get("group_by")
        limit = request.get("limit")

        if df_filtrado is None or df_filtrado.empty:
            return "No se encontraron registros con esos criterios."

        # --- NORMALIZACIÓN DE COLUMNAS NUMÉRICAS (FG, EDAD) ---
        # Si la variable es FG (Filtrado Glomerular) o Edad, aseguramos que sea número
        columnas_numericas = [variable]
        if group_by: columnas_numericas.append(group_by)
        
        for col in columnas_numericas:
            if col in df_filtrado.columns and any(x in col.upper() for x in ["FG", "EDAD", "CREATININA"]):
                df_filtrado[col] = pd.to_numeric(df_filtrado[col], errors='coerce')

        # --- 1. CASO DE AGRUPACIÓN (TOP N / RANKINGS) ---
        if group_by:
            # Agrupamos por la columna (ej. MEDICAMENTO), contamos y renombramos
            resultado = df_filtrado.groupby(group_by).size().reset_index(name='CONTEO')
            
            # Ordenamos de mayor a menor frecuencia
            resultado = resultado.sort_values(by='CONTEO', ascending=False)
            
            # Aplicamos el límite del Top N (Bloque D)
            if limit:
                resultado = resultado.head(int(limit))
            
            return resultado # Devuelve el DataFrame para la tabla/gráfico

        # --- 2. CASO DE OPERACIONES ESCALARES ---
        if metric == "media":
            # Calculamos la media de la columna seleccionada
            val_media = pd.to_numeric(df_filtrado[variable], errors='coerce').mean()
            return round(val_media, 2) if not np.isnan(val_media) else 0
        
        elif metric == "porcentaje":
            # Aquí el orquestador debería proveer el total, 
            # pero como fallback usamos el tamaño del DF antes de este filtro si es posible.
            # Por ahora, conteo simple si no hay contexto de total.
            return f"{(len(df_filtrado))} registros" 
            
        else:
            # Conteo por defecto (IDs únicos o filas)
            if variable in df_filtrado.columns:
                return df_filtrado[variable].nunique()
            return len(df_filtrado)

    def aplicar_filtros(self, df, filtros):
        """
        Mantiene el blindaje de filtros para texto y números (FG, Centro, etc.)
        """
        if not filtros:
            return df
            
        mask = pd.Series([True] * len(df), index=df.index)
        
        for f in filtros:
            col = f.get("col")
            op = f.get("op")
            val = f.get("val")

            if col not in df.columns:
                continue

            # Lógica para Filtrado Glomerular y Edad
            if any(x in col.upper() for x in ["FG", "EDAD", "FILTRADO"]):
                df[col] = pd.to_numeric(df[col], errors='coerce')
                val_num = float(val)
                if op == ">": mask &= df[col] > val_num
                elif op == "<": mask &= df[col] < val_num
                elif op == ">=": mask &= df[col] >= val_num
                elif op == "<=": mask &= df[col] <= val_num
                elif op == "==": mask &= df[col] == val_num
            
            # Lógica para Texto (Medicamentos, Centros)
            else:
                series = df[col].astype(str).str.upper().str.strip()
                val_str = str(val).upper().strip()
                
                if op == "contiene":
                    mask &= series.str.contains(val_str, na=False, regex=False)
                elif op == "==":
                    mask &= series == val_str
        
        return df[mask]
