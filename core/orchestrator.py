# core/orchestrator.py

import pandas as pd

from core.normalizer import normalize_query
from core.synonym_resolver import SynonymResolver
from core.intent_parser import IntentParser
from core.query_builder import QueryBuilder
from core.execution_engine import ExecutionEngine
from core.viz_builder import VizBuilder


class Orchestrator:
    """
    PIPELINE COMPLETO:
    Lenguaje natural → ejecución pandas → visualización
    """

    def __init__(self, df: pd.DataFrame, synonym_map: dict):
        self.df = df

        # módulos
        self.synonyms = SynonymResolver(synonym_map)
        self.intent = IntentParser()
        self.query_builder = QueryBuilder()
        self.executor = ExecutionEngine(df)
        self.viz = VizBuilder()

    # -----------------------------
    # ENTRY POINT
    # -----------------------------
    def run(self, user_query: str, output_type="table", viz_config=None):

        # 1. NORMALIZAR TEXTO
        query_norm = normalize_query(user_query)

        # 2. RESOLVER SINÓNIMOS (columnas clínicas)
        query_resolved = self.synonyms.resolve(query_norm)

        # 3. DETECTAR INTENCIÓN
        intent = self.intent.parse(query_resolved)

        # 4. CONSTRUIR QUERY PLAN (JSON pandas)
        query_plan = self.query_builder.build(intent)

        # 5. EJECUTAR SOBRE DATAFRAME
        result_df = self.executor.execute(query_plan)

        # 6. GENERAR SALIDA FINAL
        output = self.viz.build(
            result_df,
            output_type=output_type,
            config=viz_config
        )

        return {
            "query": user_query,
            "normalized": query_norm,
            "intent": intent,
            "query_plan": query_plan,
            "result": output
        }
