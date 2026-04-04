import traceback

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
        MAPPING PURO:
        Traduce AST → esquema del ExecutionEngine.
        NO aplica lógica de negocio ni defaults.
        """

        req = ast.get("request", {})
        meta = ast.get("metadata", {})

        return {
            "origen": meta.get("source"),
            "bloque_a": req.get("filters", []),

            "bloque_b": {
                "variable": req.get("target_col"),
                "operacion": req.get("metric"),
                "agrupar": req.get("group_by") or "Ninguno"
            },

            "bloque_c": {
                "tipo": req.get("chart_type")
            },

            "bloque_d": {
                "limit": req.get("limit")
            }
        }

    def procesar_pregunta(self, pregunta, df):
        if df is None or df.empty:
            return None, "⚠️ Error: DataFrame no disponible.", None

        try:
            # 1. PARSE: lenguaje natural → AST
            ast_raw = self.parser.parse_query(pregunta)

            # 2. POLICY: aplicar defaults y reglas de negocio
            ast_policed = apply_clinical_policies(ast_raw)

            # 3. COMPILATION: AST → Engine schema
            query_json = self._ast_to_engine_schema(ast_policed)

            # 4. EXECUTION
            df_filtrado = self.engine.aplicar_filtros(df, query_json["bloque_a"])

            res_num, frase, df_final = self.engine.ejecutar_analisis(
                df_filtrado,
                query_json
            )

            figura = self.engine.generar_grafico(df_final, query_json)

            return query_json, frase, figura

        except CoreError as e:
            return None, f"❌ Error en {e.modulo}: {e.mensaje}", None

        except Exception:
            print(f"DEBUG:\n{traceback.format_exc()}")
            return None, "🚨 Error Crítico en el sistema", None
