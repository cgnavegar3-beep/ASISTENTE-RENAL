import traceback
from core.errors import CoreError
from core.policy_defaults import apply_clinical_policies

class ClinicoOrchestrator:
    def __init__(self):
        from core.query_generator import QueryGenerator
        from core.engine import ExecutionEngine
        
        self.parser = QueryGenerator()
        self.engine = ExecutionEngine()

    def _ast_to_engine_schema(self, ast):
        """
        MAPPING PURO: Traduce la estructura del AST al esquema de bloques.
        No decide valores, solo transfiere datos.
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
                "limit": 10  # Parámetro técnico de paginación/render
            }
        }

    def procesar_pregunta(self, pregunta, df):
        if df is None or df.empty:
            return None, "⚠️ Error: DataFrame no disponible.", None
            
        try:
            # 1. Interpretación (AST Crudo)
            ast_raw = self.parser.parse_query(pregunta)
            
            # 2. Aplicación de Políticas (Inyección de Defaults)
            ast_policed = apply_clinical_policies(ast_raw)
            
            # 3. Compilación Estructural (AST -> JSON Engine)
            query_json = self._ast_to_engine_schema(ast_policed)
            
            # 4. Ejecución determinista
            df_filtrado = self.engine.aplicar_filtros(df, query_json["bloque_a"])
            res_num, frase, df_final = self.engine.ejecutar_analisis(df_filtrado, query_json)
            figura = self.engine.generar_grafico(df_final, query_json)
            
            return query_json, frase, figura

        except CoreError as e:
            return None, f"❌ Error en {e.modulo}: {e.mensaje}", None
        except Exception as e:
            print(f"DEBUG: {traceback.format_exc()}")
            return None, f"🚨 Error Crítico: {str(e)}", None
