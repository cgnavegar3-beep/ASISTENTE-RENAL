# core/orchestrator.py

from core.semantic_cache import SemanticCache
from core.normalizer import Normalizer
from core.synonym_resolver import SynonymResolver
from core.intent_parser import IntentParser
from core.clinical_semantic_mapper import ClinicalSemanticMapper
from core.query_builder import QueryBuilder
from core.execution_engine import ExecutionEngine
from core.viz_builder import VizBuilder


class Orchestrator:

    def __init__(self, df):
        self.df = df

        self.cache = SemanticCache()

        self.normalizer = Normalizer()
        self.synonyms = SynonymResolver()
        self.intent = IntentParser()
        self.mapper = ClinicalSemanticMapper()
        self.query_builder = QueryBuilder()
        self.executor = ExecutionEngine(df)
        self.viz = VizBuilder()

    # -------------------------------------------------
    # ENTRY POINT
    # -------------------------------------------------
    def run(self, query: str, context: dict = None):

        # -------------------------------------------------
        # 1. CACHE CHECK
        # -------------------------------------------------
        cached = self.cache.get(query, context)
        if cached:
            cached["meta"]["cache"] = True
            return cached

        trace = {
            "query_original": query,
            "steps": {}
        }

        # -------------------------------------------------
        # 2. NORMALIZATION
        # -------------------------------------------------
        query_norm = self.normalizer.normalize(query)
        trace["steps"]["normalizer"] = query_norm

        # -------------------------------------------------
        # 3. SYNONYM RESOLUTION
        # -------------------------------------------------
        query_syn = self.synonyms.resolve(query_norm)
        trace["steps"]["synonym_resolver"] = query_syn

        # -------------------------------------------------
        # 4. INTENT PARSING
        # -------------------------------------------------
        intent = self.intent.parse(query_syn)
        trace["steps"]["intent"] = intent

        # -------------------------------------------------
        # 5. CLINICAL SEMANTIC MAPPER
        # -------------------------------------------------
        mapped = self.mapper.map(intent, context)
        trace["steps"]["clinical_mapper"] = mapped

        # -------------------------------------------------
        # 6. QUERY BUILDER
        # -------------------------------------------------
        query_plan = self.query_builder.build(mapped)
        trace["steps"]["query_plan"] = query_plan

        # -------------------------------------------------
        # 7. EXECUTION
        # -------------------------------------------------
        result_df = self.executor.execute(query_plan)

        # -------------------------------------------------
        # 8. VISUALIZATION
        # -------------------------------------------------
        viz = self.viz.build(result_df, query_plan)

        # -------------------------------------------------
        # 9. RESPONSE FINAL
        # -------------------------------------------------
        response = {
            "data": result_df,
            "visualization": viz,
            "meta": {
                "cache": False
            },
            "trace": trace
        }

        # -------------------------------------------------
        # 10. CACHE STORE
        # -------------------------------------------------
        self.cache.set(query, response, context)

        return response


# -------------------------------------------------
# WRAPPER PARA TEST (IMPORTANTE)
# -------------------------------------------------
def run_query(query, df, context=None):
    orchestrator = Orchestrator(df)
    response = orchestrator.run(query, context)

    # salida simplificada para consola
    if response.get("visualization"):
        return response["visualization"]

    return response["data"]
