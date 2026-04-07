import pandas as pd
import numpy as np
import plotly.express as px  # Librería estándar para los gráficos

class ExecutionEngine:
    def __init__(self):
        """
        Motor de ejecución blindado para procesamiento clínico.
        """
        pass

    def ejecutar_analisis(self, df_filtrado, request):
        """
        Recibe el DataFrame filtrado y el diccionario de petición.
        Soporta: Conteos, Medias, Porcentajes y Agrupaciones (Top N).
        """
        # Extraer parámetros de los bloques del request
        # Nota: El orquestador mete 'metric' y 'target_col' dentro de 'request'
        metric = request.get("metric", "conteo")
        variable = request.get("target_col", "ID_REGISTRO")
        group_by = request.get("group_by")
        limit = request.get("limit")

        if df_filtrado is None or df_filtrado.empty:
            return "No se encontraron registros con esos criterios."

        # --- 1. NORMALIZACIÓN DE VARIABLES NUMÉRICAS (EDAD, FG) ---
        columnas_a_revisar = [variable]
        if group_by: columnas_a_revisar.append(group_by)
        
        for col in columnas_a_revisar:
            if col in df_filtrado.columns:
                # Blindaje para Filtrado Glomerular y Edad
                if any(x in col.upper() for x in ["FG", "EDAD", "FILTRADO", "CREATININA"]):
                    df_filtrado[col] = pd.to_numeric(df_filtrado[col], errors='coerce')

        # --- 2. CASO: AGRUPACIÓN / TOP N (Gráficos y Listados) ---
        if group_by:
            # Agrupamos por la dimensión (Centro, Medicamento, Sexo...)
            resultado = df_filtrado.groupby(group_by).size().reset_index(name='CONTEO')
            
            # Orden descendente para que el Top sea real
            resultado = resultado.sort_values(by='CONTEO', ascending=False)
            
            # Aplicar límite del bloque_d
            if limit:
                resultado = resultado.head(int(limit))
            
            return resultado # Retorna DataFrame

        # --- 3. CASO: OPERACIONES ESCALARES (KPIs) ---
        if metric == "media":
            series_num = pd.to_numeric(df_filtrado[variable], errors='coerce')
            val_media = series_num.mean()
            return round(val_media, 2) if not np.isnan(val_media) else 0
        
        elif metric == "porcentaje":
            # El porcentaje se devuelve como string formateado
            conteo = len(df_filtrado)
            # Nota: Para un % real sobre total, se requiere el DF original en el contexto
            return f"Conteo: {conteo} pacientes"
            
        else:
            # Conteo por defecto
            if variable in df_filtrado.columns:
                return int(df_filtrado[variable].nunique())
            return int(len(df_filtrado))

    def generar_grafico(self, df_final, query_json):
        """
        Genera la figura visual para el Orquestador.
        """
        if not isinstance(df_final, pd.DataFrame) or df_final.empty:
            return None

        tipo_grafico = query_json.get("bloque_c", {}).get("tipo", "bar")
        group_by = query_json.get("bloque_b", {}).get("agrupar")
        
        if not group_by:
            return None

        try:
            if tipo_grafico == "bar":
                fig = px.bar(
                    df_final, 
                    x=group_by, 
                    y='CONTEO',
                    title=f"Distribución por {group_by}",
                    labels={group_by: group_by, 'CONTEO': 'Nº de Pacientes'},
                    template="plotly_white",
                    color_discrete_sequence=['#00CC96']
                )
                return fig
            
            elif tipo_grafico == "pie":
                fig = px.pie(
                    df_final, 
                    values='CONTEO', 
                    names=group_by,
                    title=f"Proporción por {group_by}"
                )
                return fig
            
            return None
        except Exception:
            return None

    def aplicar_filtros(self, df, filtros):
        """
        Aplica filtros secuenciales (Bloque A).
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

            # Filtros numéricos (FG, Edad)
            if any(x in col.upper() for x in ["FG", "EDAD", "FILTRADO"]):
                df[col] = pd.to_numeric(df[col], errors='coerce')
                val_num = float(val)
                if op == ">": mask &= df[col] > val_num
                elif op == "<": mask &= df[col] < val_num
                elif op == ">=": mask &= df[col] >= val_num
                elif op == "<=": mask &= df[col] <= val_num
                elif op == "==": mask &= df[col] == val_num
            
            # Filtros de texto
            else:
                series = df[col].astype(str).str.upper().str.strip()
                val_str = str(val).upper().strip()
                if op == "contiene":
                    mask &= series.str.contains(val_str, na=False, regex=False)
                elif op == "==":
                    mask &= series == val_str
        
        return df[mask]
