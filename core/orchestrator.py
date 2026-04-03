# core/orchestrator.py
from core.query_generator import QueryGenerator
from core.validator import validar_query
from core.engine import ExecutionEngine

class ClinicoOrchestrator:
    def __init__(self):
        self.generator = QueryGenerator()
        self.engine = ExecutionEngine()

    def procesar_pregunta(self, pregunta, df_pool):
        # 1. Generar JSON
        query_json = self.generator.generar_json(pregunta)
        
        # 2. Validar
        es_valido, msg = validar_query(query_json)
        if not es_valido:
            return None, msg, None
        
        # 3. Filtrar datos
        df_filtrado = self.engine.aplicar_filtros(df_pool, query_json["bloque_a"])
        
        # 4. Ejecutar análisis y obtener respuesta humana
        resultado, respuesta_humana, df_final = self.engine.ejecutar_analisis(df_filtrado, query_json)
        
        return query_json, respuesta_humana, df_final
