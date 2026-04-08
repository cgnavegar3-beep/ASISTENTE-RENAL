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
        Soporta: Conteos, Medias, Porcentajes y Agrupaciones (Top N / Histogramas).
        """
        metric = request.get("metric", "conteo")
        variable = request.get("target_col", "ID_REGISTRO")
        group_by = request.get("group_by")
        limit = request.get("limit")

        if df_filtrado is None or df_filtrado.empty:
            return "No se encontraron registros con esos criterios."

        # --- 1. NORMALIZACIÓN DE VARIABLES NUMÉRICAS ---
        columnas_a_revisar = [variable]
        if group_by: columnas_a_revisar.append(group_by)
        
        for col in columnas_a_revisar:
            if col in df_filtrado.columns:
                if any(x in col.upper() for x in ["FG", "EDAD", "FILTRADO", "CREATININA"]):
                    df_filtrado[col] = pd.to_numeric(df_filtrado[col], errors='coerce')

        # --- 2. CASO: HISTOGRAMAS CLÍNICOS (EDAD / FG) ---
        if group_by in ["EDAD", "FG_CG"]:
            temp_df = df_filtrado.dropna(subset=[group_by]).copy()
            
            if group_by == "EDAD":
                bins = [0, 20, 40, 60, 80, 150]
                labels = ["0-20", "20-40", "40-60", "60-80", ">80"]
                temp_df["RANGO"] = pd.cut(temp_df["EDAD"], bins=bins, labels=labels, right=False)
            
            elif group_by == "FG_CG":
                bins = [0, 15, 30, 45, 60, 300]
                labels = ["0-15 (Fallo)", "15-30 (G4)", "30-45 (G3b)", "45-60 (G3a)", ">60 (Normal)"]
                temp_df["RANGO"] = pd.cut(temp_df["FG_CG"], bins=bins, labels=labels, right=False)

            resultado = temp_df.groupby("RANGO", observed=True).size().reset_index(name='CONTEO')
            resultado = resultado.rename(columns={"RANGO": group_by})
            return resultado

        # --- 3. CASO: AGRUPACIÓN / TOP N CATEGÓRICO ---
        if group_by:
            resultado = df_filtrado.groupby(group_by).size().reset_index(name='CONTEO')
            resultado = resultado.sort_values(by='CONTEO', ascending=False)
            if limit:
                resultado = resultado.head(int(limit))
            return resultado

        # --- 4. CASO: OPERACIONES ESCALARES (KPIs) ---
        if metric == "media":
            series_num = pd.to_numeric(df_filtrado[variable], errors='coerce')
            val_media = series_num.mean()
            return round(val_media, 2) if not np.isnan(val_media) else 0
        
        elif metric == "porcentaje":
            conteo = len(df_filtrado)
            return f"Conteo: {conteo} pacientes"
            
        else:
            if variable in df_filtrado.columns:
                return int(df_filtrado[variable].nunique())
            return int(len(df_filtrado))

    def generar_grafico(self, df_final, query_json):
        """
        Genera la figura visual para el Orquestador con ordenamiento lógico.
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
                # Si es un histograma clínico, respetamos el orden de los rangos (no por conteo)
                if group_by in ["EDAD", "FG_CG"]:
                    fig.update_xaxes(categoryorder='array', categoryarray=df_final[group_by].tolist())
                
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
