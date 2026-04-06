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
            # Mantenemos 'request' original para que el engine tenga acceso a claves directas
            "request": req 
        }

    def procesar_pregunta(self, pregunta, df):
        """
        Flujo principal de procesamiento. Blindado contra DataFrames vacíos.
        """
        if df is None or (isinstance(df, pd.DataFrame) and df.empty):
            return None, "⚠️ Error: DataFrame no disponible o vacío.", None

        try:
            # 1. PARSEO NLP (Traduce texto a JSON inicial)
            ast_raw = self.parser.parse_query(pregunta)

            # 2. POLÍTICAS CLÍNICAS (Aplica reglas de negocio automáticas)
            ast_policed = apply_clinical_policies(ast_raw)

            # 3. NORMALIZACIÓN (Prepara el JSON para el motor de ejecución)
            query_json = self._ast_to_engine_schema(ast_policed)

            # 4. FILTRADO (Aplica filtros del bloque_a)
            df_filtrado = self.engine.aplicar_filtros(
                df,
                query_json["bloque_a"]
            )

            # 5. EJECUCIÓN ANALÍTICA (Cálculos de métricas o agrupaciones)
            res_num, frase, df_final = self.engine.ejecutar_analisis(
                df_filtrado,
                query_json
            )

            # 6. GENERACIÓN DE GRÁFICO (Solo si hay datos y el tipo no es KPI)
            figura = None
            if df_final is not None and not (isinstance(df_final, pd.DataFrame) and df_final.empty):
                if query_json["bloque_c"]["tipo"] != "kpi":
                    figura = self.engine.generar_grafico(df_final, query_json)

            # 7. RETORNO CONSISTENTE
            return query_json, frase, figura

        except CoreError as e:
            return None, f"❌ Error en {e.modulo}: {e.mensaje}", None

        except Exception as e:
            print(f"--- DETALLE DEL ERROR ---")
            print(traceback.format_exc())
            return None, f"🚨 Error crítico en el sistema: {str(e)}", None
