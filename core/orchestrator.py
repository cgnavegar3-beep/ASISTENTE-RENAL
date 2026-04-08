import traceback
import pandas as pd

from core.errors import CoreError
from core.policy_defaults import apply_clinical_policies
from core.query_generator import QueryGenerator
from core.engine import ExecutionEngine


class ClinicoOrchestrator:
    def __init__(self):
        self.parser = QueryGenerator()
        self.engine = ExecutionEngine()

    def _ast_to_engine_schema(self, ast):
        """
        Normaliza el AST generado por el parser al esquema que espera el Engine.
        Blindado para asegurar que los gráficos se activen correctamente.
        """
        req = ast.get("request", {})
        meta = ast.get("metadata", {})

        # 1. Limpieza de filtros (bloque_a)
        filtros_originales = req.get("filters", [])
        filtros_validos = [
            f for f in filtros_originales
            if f.get("val") not in [None, "", "null", [], "NULL"]
        ]

        # 2. Lógica de visualización (bloque_c)
        chart_type = req.get("chart_type", "kpi")
        group_by = req.get("group_by")

        # Si hay agrupación pero el tipo es kpi, forzamos gráfico de barras
        if group_by and chart_type == "kpi":
            chart_type = "bar"

        # 3. Construcción del esquema final
        return {
            "origen": meta.get("source", "Validaciones"),
            "bloque_a": filtros_validos,
            "bloque_b": {
                "variable": req.get("target_col") or "ID_REGISTRO",
                "operacion": req.get("metric") or "conteo",
                "agrupar": group_by if group_by != "NULL" else None
            },
            "bloque_c": {
                "tipo": chart_type
            },
            "bloque_d": {
                "limit": req.get("limit") or 10
            },
            # Fusionamos bloques en el request para que el engine lo lea directo
            "request": {
                "metric": req.get("metric") or "conteo",
                "target_col": req.get("target_col") or "ID_REGISTRO",
                "group_by": group_by if group_by != "NULL" else None,
                "limit": req.get("limit") or 10
            }
        }

    def procesar_pregunta(self, pregunta, df_input):
        """
        Flujo principal de procesamiento. 
        Soporta entrada de DataFrame único o Diccionario de DataFrames {"Origen": df}.
        """
        try:
            # 1. PARSEO NLP
            ast_raw = self.parser.parse_query(pregunta)

            # 2. POLÍTICAS CLÍNICAS
            ast_policed = apply_clinical_policies(ast_raw)

            # 3. NORMALIZACIÓN
            query_json = self._ast_to_engine_schema(ast_policed)

            # --- SELECCIÓN DINÁMICA DE DATA (PROPUESTA INCORPORADA) ---
            origen_detectado = query_json.get("origen", "Validaciones")
            
            if isinstance(df_input, dict):
                df_trabajo = df_input.get(origen_detectado)
            else:
                df_trabajo = df_input # Retrocompatibilidad si solo pasas un DF

            if df_trabajo is None or (isinstance(df_trabajo, pd.DataFrame) and df_trabajo.empty):
                return None, f"⚠️ Error: No hay datos disponibles para el origen '{origen_detectado}'.", None
            # ---------------------------------------------------------

            # 4. FILTRADO (Bloque A)
            df_filtrado = self.engine.aplicar_filtros(
                df_trabajo.copy(), 
                query_json["bloque_a"]
            )

            # 5. EJECUCIÓN ANALÍTICA
            resultado_analisis = self.engine.ejecutar_analisis(
                df_filtrado,
                query_json["request"]
            )

            # 6. GESTIÓN DE RESULTADOS
            figura = None
            df_final = None
            
            if isinstance(resultado_analisis, pd.DataFrame):
                df_final = resultado_analisis
                label_grupo = query_json['bloque_b']['agrupar'] or "Categoría"
                frase = f"Resultados por {label_grupo}:"
                if query_json["bloque_c"]["tipo"] != "kpi":
                    figura = self.engine.generar_grafico(df_final, query_json)
            else:
                frase = f"Resultado: {resultado_analisis}"
                df_final = None

            return query_json, frase, figura

        except CoreError as e:
            return None, f"❌ Error en {e.modulo}: {e.mensaje}", None

        except Exception as e:
            print(f"--- DETALLE DEL ERROR ---")
            print(traceback.format_exc())
            return None, f"🚨 Error crítico en el sistema: {str(e)}", None
