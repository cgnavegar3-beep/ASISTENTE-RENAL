# ==========================================
# VERSIÓN CORREGIDA - CLINICO ORCHESTRATOR
# CONTROL DE INDENTACIÓN Y FILTROS VACÍOS
# ==========================================
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

        # Limpieza de seguridad: Ignorar filtros que tengan valores vacíos o nulos
        # Esto evita que 'CENTRO: ""' haga que la búsqueda devuelva 0 resultados.
        filtros_originales = req.get("filters", [])
        filtros_validos = [
            f for f in filtros_originales 
            if f.get("val") not in [None, "", "null", []]
        ]

        return {
            "origen": meta.get("source"),
            "bloque_a": filtros_validos,
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
            # 1. Generar AST desde el lenguaje natural
            ast_raw = self.parser.parse_query(pregunta)
            
            # 2. Aplicar políticas clínicas (seguridad/privacidad)
            ast_policed = apply_clinical_policies(ast_raw)

            # 3. Transformar al esquema que entiende el motor (Engine)
            query_json = self._ast_to_engine_schema(ast_policed)

            # 4. Ejecutar filtrado de datos
            df_filtrado = self.engine.aplicar_filtros(df, query_json["bloque_a"])

            # 5. Ejecutar cálculos estadísticos/métricas
            res_num, frase, df_final = self.engine.ejecutar_analisis(
                df_filtrado,
                query_json
            )

            # 6. Generar visualización
            figura = self.engine.generar_grafico(df_final, query_json)

            return query_json, frase, figura

        except CoreError as e:
            return None, f"❌ Error en {e.modulo}: {e.mensaje}", None

        except Exception:
            print(traceback.format_exc())
            return None, "🚨 Error Crítico en el sistema", None
