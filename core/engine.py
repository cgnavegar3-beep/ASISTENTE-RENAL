import pandas as pd
import numpy as np
import plotly.express as px

class ExecutionEngine:
    def __init__(self):
        """Motor de ejecución blindado para procesamiento clínico."""
        pass

    def ejecutar_analisis(self, df_filtrado, request):
        if df_filtrado is None or df_filtrado.empty:
            return "No se encontraron registros con esos criterios."

        df_proc = df_filtrado.copy()
        
        metric = request.get("metric", "conteo")
        variable = request.get("target_col", "ID_REGISTRO")
        group_by = request.get("group_by")
        limit = request.get("limit")
        label_map = request.get("label_map")

        # --- 1. NORMALIZACIÓN DE VARIABLES ---
        columnas_a_revisar = [variable]
        if group_by: columnas_a_revisar.append(group_by)
        
        for col in columnas_a_revisar:
            if col in df_proc.columns:
                if any(x in col.upper() for x in ["FG", "EDAD", "FILTRADO", "CREATININA"]):
                    df_proc[col] = pd.to_numeric(df_proc[col], errors='coerce')
                
                # REPARACIÓN: Blindaje del mapeo de etiquetas (Evolución de etiquetas largas)
                if col == "RIESGO_CG" and label_map:
                    df_proc[col] = df_proc[col].astype(str).str.strip().str.upper()
                    l_map_clean = {str(k).upper(): v for k, v in label_map.items()}
                    df_proc[col] = df_proc[col].replace(l_map_clean)

        # --- 2. CASO: HISTOGRAMAS CLÍNICOS ---
        if group_by in ["EDAD", "FG_CG"]:
            temp_df = df_proc.dropna(subset=[group_by]).copy()
            if group_by == "EDAD":
                bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 150]
                labels = ["0-10", "10-20", "20-30", "30-40", "40-50", "50-60", "60-70", "70-80", "80-90", "90-100", ">100"]
                temp_df["RANGO"] = pd.cut(temp_df["EDAD"], bins=bins, labels=labels, right=False)
            elif group_by == "FG_CG":
                bins = [0, 15, 30, 45, 60, 300]
                labels = ["0-15 (Fallo)", "15-30 (G4)", "30-45 (G3b)", "45-60 (G3a)", ">60 (Normal)"]
                temp_df["RANGO"] = pd.cut(temp_df["FG_CG"], bins=bins, labels=labels, right=False)

            resultado = temp_df.groupby("RANGO", observed=True).size().reset_index(name='CONTEO')
            resultado = resultado.rename(columns={"RANGO": group_by})
            return resultado

        # --- 3. CASO: AGRUPACIÓN / TOP N ---
        if group_by:
            resultado = df_proc.groupby(group_by).size().reset_index(name='CONTEO')
            if group_by == "RIESGO_CG" and label_map:
                # Orden basado en el flujo clínico definido en label_map
                orden_clinico = [v for v in label_map.values() if v in resultado[group_by].values]
                resultado[group_by] = pd.Categorical(resultado[group_by], categories=orden_clinico, ordered=True)
                resultado = resultado.sort_values(by=group_by)
            else:
                resultado = resultado.sort_values(by='CONTEO', ascending=False)
            
            if limit:
                resultado = resultado.head(int(limit))
            return resultado

        # --- 4. CASO: KPIs ---
        if metric == "media":
            series_num = pd.to_numeric(df_proc[variable], errors='coerce')
            val_media = series_num.mean()
            return round(val_media, 2) if not np.isnan(val_media) else 0
        elif metric == "porcentaje":
            return f"Conteo: {len(df_proc)} pacientes"
        else:
            return int(df_proc[variable].nunique()) if variable in df_proc.columns else int(len(df_proc))

    def generar_grafico(self, df_final, query_json):
        if not isinstance(df_final, pd.DataFrame) or df_final.empty:
            return None

        bloque_request = query_json.get("request", {})
        tipo_grafico = query_json.get("bloque_c", {}).get("tipo") or bloque_request.get("chart_type", "bar")
        group_by = bloque_request.get("group_by")
        label_map = bloque_request.get("label_map")
        
        if not group_by: return None

        try:
            title = "Análisis de Riesgo Clínico" if group_by == "RIESGO_CG" else f"Distribución por {group_by}"

            if tipo_grafico == "pie":
                return px.pie(df_final, values='CONTEO', names=group_by, title=title,
                              color_discrete_sequence=px.colors.qualitative.Safe)

            elif tipo_grafico == "bar":
                color_map = None
                if group_by == "RIESGO_CG" and label_map:
                    # Mapeo de colores vinculado a las nuevas etiquetas largas
                    color_map = {
                        label_map.get("LEVE", ""): "#00CC96",      # Verde
                        label_map.get("MODERADO", ""): "#FFA15A",  # Naranja
                        label_map.get("GRAVE", ""): "#EF553B",     # Rojo
                        label_map.get("CRITICO", ""): "#B6E880"    # Lima
                    }

                fig = px.bar(df_final, x=group_by, y='CONTEO', title=title,
                             labels={group_by: "Nivel de Riesgo", 'CONTEO': 'Nº de Pacientes'},
                             template="plotly_white",
                             color=group_by if color_map else None,
                             color_discrete_map=color_map)
                
                if group_by == "RIESGO_CG" or group_by in ["EDAD", "FG_CG"]:
                    fig.update_xaxes(categoryorder='array', categoryarray=df_final[group_by].tolist())
                
                return fig
            return None
        except Exception:
            return None

    def aplicar_filtros(self, df, filtros):
        if not filtros: return df
        df_f = df.copy()
        mask = pd.Series([True] * len(df_f), index=df_f.index)
        for f in filtros:
            col, op, val = f.get("col"), f.get("op"), f.get("val")
            if col not in df_f.columns: continue
            if any(x in col.upper() for x in ["FG", "EDAD", "FILTRADO"]):
                df_f[col] = pd.to_numeric(df_f[col], errors='coerce')
                val_num = float(val)
                if op == ">": mask &= df_f[col] > val_num
                elif op == "<": mask &= df_f[col] < val_num
                elif op == ">=": mask &= df_f[col] >= val_num
                elif op == "<=": mask &= df_f[col] <= val_num
                elif op == "==": mask &= df_f[col] == val_num
            else:
                series = df_f[col].astype(str).str.upper().str.strip()
                val_str = str(val).upper().strip()
                if op == "contiene": mask &= series.str.contains(val_str, na=False, regex=False)
                elif op == "==": mask &= series == val_str
        return df_f[mask]
