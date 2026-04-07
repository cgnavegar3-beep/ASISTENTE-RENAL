import pandas as pd
import numpy as np

class ExecutionEngine:
    def __init__(self, df_validaciones=None, df_medicamentos=None):
        self.dfs = {
            "Validaciones": df_validaciones,
            "Medicamentos": df_medicamentos
        }

    def ejecutar_analisis(self, request):
        # 1. Extraer metadatos del request
        origen = request.get("origen", "Validaciones")
        bloque_a = request.get("bloque_a", []) # Filtros
        bloque_b = request.get("bloque_b", {}) # Operación
        bloque_d = request.get("bloque_d", {}) # Límites
        
        df = self.dfs.get(origen)
        if df is None or df.empty:
            return "No se encontraron registros: Fuente de datos no cargada."

        # 2. APLICAR FILTROS (Bloque A)
        df_filtrado = self.aplicar_filtros(df.copy(), bloque_a)

        if df_filtrado.empty:
            return "No se encontraron registros con esos criterios."

        # 3. IDENTIFICAR MÉTRICA Y VARIABLE (Bloque B)
        metric = bloque_b.get("operacion", "conteo")
        variable = bloque_b.get("variable", "ID_REGISTRO")
        group_by = bloque_b.get("agrupar")
        limit = bloque_d.get("limit")

        # --- LÓGICA DE FILTRADO GLOMERULAR (FG) ---
        # Si la variable es FG, nos aseguramos de que sea numérica
        if "FG" in variable:
            df_filtrado[variable] = pd.to_numeric(df_filtrado[variable], errors='coerce')

        # --- CASO A: SI HAY AGRUPACIÓN (TOP N / RANKINGS) ---
        if group_by:
            # Agrupamos, contamos y ordenamos de mayor a menor
            res = df_filtrado.groupby(group_by).size().reset_index(name='CONTEO')
            res = res.sort_values(by='CONTEO', ascending=False)
            
            if limit:
                res = res.head(int(limit))
            return res # Retorna el DataFrame para la tabla o gráfico

        # --- CASO B: OPERACIONES ESCALARES (MEDIA, %, CONTEO) ---
        if metric == "media":
            # Convertir a numérico por seguridad antes de la media
            val_media = pd.to_numeric(df_filtrado[variable], errors='coerce').mean()
            return round(val_media, 2) if not np.isnan(val_media) else 0
        
        elif metric == "porcentaje":
            # % = (Filtrados / Total de la tabla) * 100
            total_tabla = len(df)
            proporcion = (len(df_filtrado) / total_tabla) * 100
            return f"{round(proporcion, 2)}%"
            
        else:
            # Conteo de pacientes únicos por ID si es posible, si no, filas
            return df_filtrado[variable].nunique() if variable in df_filtrado.columns else len(df_filtrado)

    def aplicar_filtros(self, df, filtros):
        """Aplica los filtros del bloque_a de forma secuencial."""
        mask = pd.Series([True] * len(df), index=df.index)
        
        for f in filtros:
            col = f.get("col")
            op = f.get("op")
            val = f.get("val")

            if col not in df.columns:
                continue

            # Tratamiento especial para Filtrado Glomerular y Edad (Numéricos)
            if any(x in col for x in ["FG", "EDAD", "CREATININA"]):
                df[col] = pd.to_numeric(df[col], errors='coerce')
                if op == ">": mask &= df[col] > float(val)
                elif op == "<": mask &= df[col] < float(val)
                elif op == ">=": mask &= df[col] >= float(val)
                elif op == "<=": mask &= df[col] <= float(val)
                elif op == "==": mask &= df[col] == float(val)
            
            # Tratamiento para Texto (Medicamentos, Centros, Sexo)
            else:
                series = df[col].astype(str).str.upper().str.strip()
                val_str = str(val).upper().strip()
                
                if op == "contiene":
                    mask &= series.str.contains(val_str, na=False, regex=False)
                elif op == "==":
                    mask &= series == val_str
        
        return df[mask]
