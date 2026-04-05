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
        req = ast.get("request", {})
        meta = ast.get("metadata", {})

        filtros_originales = req.get("filters", [])
        filtros_validos = [
            f for f in filtros_originales
            if f.get("val") not in [None, "", "null", []]
        ]

        limit = req.get("limit") or None

        return {
            "origen": meta.get("source"),
            "bloque_a": filtros_validos,
            "bloque_b": {
                "variable": req.get("target_col"),
                "operacion": req.get("metric"),
                "agrupar": req.get("group_by") or None
            },
            "bloque_c": {
                "tipo": req.get("chart_type")
            },
            "bloque_d": {
                "limit": limit
            }
        }

    def procesar_pregunta(self, pregunta, df):
        if df is None or getattr(df, "empty", True):
            return None, "⚠️ Error: DataFrame no disponible.", None

        try:
            # 1. PARSEO NLP
            ast_raw = self.parser.parse_query(pregunta)

            # 2. POLÍTICAS CLÍNICAS
            ast_policed = apply_clinical_policies(ast_raw)

            # 3. NORMALIZACIÓN A ESQUEMA ENGINE
            query_json = self._ast_to_engine_schema(ast_policed)

            # 4. FILTRO INICIAL
            df_filtrado = self.engine.aplicar_filtros(
                df,
                query_json["bloque_a"]
            )

            # 5. EJECUCIÓN ANALÍTICA
            res_num, frase, df_final = self.engine.ejecutar_analisis(
                df_filtrado,
                query_json
            )

            # 6. GRAFICO (SAFE)
            figura = None
            if df_final is not None and not df_final.empty:
                figura = self.engine.generar_grafico(df_final, query_json)

            # 7. RETURN CONSISTENTE
            return query_json, frase, figura

        except CoreError as e:
            return None, f"❌ Error en {e.modulo}: {e.mensaje}", None

        except Exception as e:
            print(traceback.format_exc())
            return None, f"🚨 Error crítico en el sistema: {str(e)}", None
