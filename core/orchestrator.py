from typing import Dict, Any
import pandas as pd

from core.normalizer import Normalizer
from core.capa_2 import Capa2Controller
from core.execution_engine import ExecutionEngine
from core.fallback_engine import FallbackEngine
from core.session_cache import SessionCache


# =========================================================
# ORCHESTRATOR PRINCIPAL (CEREBRO DEL SISTEMA)
# =========================================================
class Orchestrator:

    def __init__(self):

        self.normalizer = Normalizer()
        self.capa2 = Capa2Controller()
        self.executor = ExecutionEngine()
        self.fallback = FallbackEngine()
        self.cache = SessionCache()

    # =====================================================
    # ENTRY POINT
    # =====================================================
    def run(self, query: str, df: pd.DataFrame, session_id: str = "default") -> pd.DataFrame:

        # 1. CACHE (respuesta previa)
        cached = self.cache.get(session_id, query)
        if cached is not None:
            return cached

        try:

            # 2. NORMALIZAR TEXTO
            clean_query = self.normalizer.normalize(query)

            # 3. IA CONTROLADA → PLAN ESTRUCTURADO
            plan = self.capa2.parse_to_plan(clean_query, df.columns)

            # 4. VALIDACIÓN BÁSICA (anti alucinaciones)
            plan = self._validate_plan(plan, df)

            # 5. EJECUCIÓN SEGURA
            result = self.executor.execute(plan, df)

            # 6. CACHE RESULTADO
            self.cache.set(session_id, query, result)

            return result

        except Exception as e:

            print(f"[ORCHESTRATOR ERROR] {str(e)}")

            # 7. FALLBACK FINAL
            return self.fallback.safe_execute({}, df)

    # =====================================================
    # VALIDACIÓN ANTI-ALUCINACIONES
    # =====================================================
    def _validate_plan(self, plan: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:

        valid_columns = set(df.columns)

        # 1. VALIDAR GROUPBY
        if "groupby" in plan:
            plan["groupby"] = [
                c for c in plan["groupby"]
                if c in valid_columns
            ]

        # 2. VALIDAR FILTROS
        if "filters" in plan:
            clean_filters = []

            for f in plan["filters"]:
                if f.get("column") in valid_columns:
                    clean_filters.append(f)

            plan["filters"] = clean_filters

        # 3. VALIDAR VARIABLE
        if "variable" in plan:
            if plan["variable"] not in valid_columns:
                plan["variable"] = None

        # 4. LIMPIEZA FINAL
        if plan.get("operation") not in ["count", "mean", "sum", "nunique"]:
            plan["operation"] = "count"

        return plan
