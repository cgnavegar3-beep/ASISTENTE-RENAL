import pandas as pd
import numpy as np

class ExecutionEngine:
    def __init__(self):
        """
        El motor se encarga de filtrar y procesar los cálculos sobre los DataFrames.
        """
        pass

    def ejecutar_analisis(self, df_filtrado, request):
        """
        PUNTO CLAVE: Recibe el DataFrame (ya filtrado por aplicar_filtros) 
        y el diccionario 'request' del JSON.
        """
        # Extraer parámetros del bloque_b y bloque_d del JSON
        metric = request.get("metric", "conteo")
        variable = request.get("target_col", "ID_REGISTRO")
        group_by = request.get("group_by")
        limit = request.get("limit")

        if df_filtrado is None or df_filtrado.empty:
            return "No se encontraron registros con esos criterios."

        # --- NORMALIZACIÓN DE DATOS CLÍNICOS (FG, EDAD, CREATININA) ---
        # Aseguramos que si la variable es numérica, Pandas la trate como tal
        cols_a_revisar = [variable]
        if group_by: cols_a_revisar.append(group_by)
        
        for col in cols_a_revisar:
            if col in df_filtrado.columns:
                # Si la columna contiene siglas de Filtrado Glomerular o Edad, forzamos numérico
                if any(x in col.upper() for x in ["FG", "EDAD", "CREATININA", "FILTRADO"]):
                    df_filtrado[col] = pd.to_numeric(df_filtrado[col], errors='coerce')

        # --- 1. LÓGICA DE AGRUPACIÓN (TOP N / RANKINGS) ---
        if group_by:
            # Agrupamos por la columna (ej. MEDICAMENTO), contamos registros
            resultado = df_filtrado.groupby(group_by).size().reset_index(name='CONTEO')
            
            # Ordenamos de mayor a menor frecuencia (Descendente)
            resultado = resultado.sort_values(by='CONTEO', ascending=False)
            
            # Aplicamos el límite (Top 5, Top 10, etc.)
            if limit:
                resultado = resultado.head(int(limit))
            
            # Devolvemos el DataFrame completo para que el orquestador lo pinte como tabla
            return resultado

        # --- 2. LÓGICA DE OPERACIONES ESTADÍSTICAS ---
        if metric == "media":
            # Calculamos la media ignorando valores no numéricos (NaN)
            val_col = pd.to_numeric(df_filtrado[variable], errors='coerce')
            val_media = val_col.mean()
            return round(val_media, 2) if not np.isnan(val_media) else 0
        
        elif metric == "porcentaje":
            # El porcentaje se suele calcular sobre el conteo de filas
            # Nota: El orquestador debería manejar el total de la población si es necesario
            conteo_actual = len(df_filtrado)
            return f"{conteo_actual} registros (Porcentaje requiere total de población)"
            
        else:
            # Operación por defecto: CONTEO
            # Si la variable es ID_REGISTRO o similar, contamos valores únicos
            if variable in df_filtrado.columns:
                return int(df_filtrado[variable].nunique())
            return int(len(df_filtrado))

    def aplicar_filtros(self, df, filtros):
        """
        Aplica los filtros del bloque_a. 
        Blindado para Filtrado Glomerular (FG) y búsquedas parciales de texto.
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

            # --- CASO NUMÉRICO (FG, EDAD, etc.) ---
            if any(x in col.upper() for x in ["FG", "EDAD", "FILTRADO", "CREATININA"]):
                # Convertimos la columna y el valor a número para comparar
                series_num = pd.to_numeric(df[col], errors='coerce')
                try:
                    val_num = float(val)
                    if op == ">": mask &= series_num > val_num
                    elif op == "<": mask &= series_num < val_num
                    elif op == ">=": mask &= series_num >= val_num
                    elif os == "<=": mask &= series_num <= val_num
                    elif op == "==": mask &= series_num == val_num
                except:
                    continue
            
            # --- CASO TEXTO (MEDICAMENTO, CENTRO, SEXO) ---
            else:
                series_txt = df[col].astype(str).str.upper().str.strip()
                val_txt = str(val).upper().strip()
                
                if op == "contiene":
                    # Búsqueda parcial (ej. 'ENALAPRIL' dentro de 'ENALAPRIL 5MG')
                    mask &= series_txt.str.contains(val_txt, na=False, regex=False)
                elif op == "==":
                    mask &= series_txt == val_txt
        
        return df[mask]
