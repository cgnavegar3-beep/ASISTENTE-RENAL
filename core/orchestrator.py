from typing import Dict
import pandas as pd

from core.normalizer import Normalizer
from core.capa2 import Capa2Controller
from core.execution_engine import ExecutionEngine
from core.fallback_engine import FallbackEngine
from core.session_cache import SessionCache


class Orchestrator:

    def __init__(
        self,
        semantic_layer,
        matcher,
        capa2: Capa2Controller,
        executor: ExecutionEngine,
        fallback: FallbackEngine,
        session_cache: SessionCache = None
    ):
        # -------------------------
        # COMPONENTES DEL PIPELINE
        # -------------------------
        self.normalizer = Normalizer()
        self.semantic_layer = semantic_layer
        self.matcher = matcher
        self.capa2 = capa2
        self.executor = executor
        self.fallback = fallback
        self.cache = session_cache

    def run(self, user_input: str, df_dict: Dict[str, pd.DataFrame]):

        plan = None

        # -------------------------
        # 1. CACHE (si existe)
        # -------------------------
        if self.cache:
            cached_result = self.cache.get(user_input)
            if cached_result:
                return cached_result

        try:
            # -------------------------
            # 2. NORMALIZACIÓN
            # -------------------------
            clean_input = self.normalizer.normalize_text(user_input)

            # -------------------------
            # 3. SEMANTIC LAYER
            # -------------------------
            enriched_input = self.semantic_layer.process(clean_input)

            # -------------------------
            # 4. MATCHER
            # -------------------------
            matched_input = self.matcher.match(enriched_input)

            # -------------------------
            # 5. CAPA 2 (IA → PLAN)
            # -------------------------
            plan = self.capa2.parse(matched_input)

            if not isinstance(plan, dict):
                raise ValueError("Plan inválido: no es dict")

            if "operation" not in plan:
                raise ValueError("Plan inválido: falta 'operation'")

            # -------------------------
            # 6. EJECUCIÓN
            # -------------------------
            result = self.executor.execute_plan(plan, df_dict)

            response = {
                "status": "success",
                "result": result,
                "plan": plan
            }

            # -------------------------
            # 7. CACHE STORE
            # -------------------------
            if self.cache:
                self.cache.set(user_input, response)

            return response

        except Exception as e:

            # -------------------------
            # 8. FALLBACK ENGINE
            # -------------------------
            try:
                fallback_result = self.fallback.execute(
                    plan if plan else {},
                    df_dict
                )

                return {
                    "status": "fallback",
                    "result": fallback_result,
                    "error": str(e),
                    "plan": plan
                }

            except Exception as e2:

                return {
                    "status": "failed",
                    "error": str(e2),
                    "plan": plan
                }
