from typing import Dict, Any, Optional
import pandas as pd
import hashlib


# =========================================================
# SESSION CACHE CENTRALIZADO
# =========================================================
class SessionCache:

    def __init__(self):
        # cache de datasets
        self.data_cache: Dict[str, pd.DataFrame] = {}

        # cache de resultados de consultas
        self.query_cache: Dict[str, Any] = {}

    # =========================================================
    # DATASET CACHE
    # =========================================================
    def set_dataset(self, key: str, df: pd.DataFrame):
        self.data_cache[key] = df

    def get_dataset(self, key: str) -> Optional[pd.DataFrame]:
        return self.data_cache.get(key)

    def clear_dataset(self, key: str):
        if key in self.data_cache:
            del self.data_cache[key]

    # =========================================================
    # QUERY CACHE
    # =========================================================
    def _make_key(self, plan: Dict[str, Any]) -> str:
        """
        Convierte el plan en una clave estable
        (NO usa lenguaje natural → evita errores)
        """

        raw = str(sorted(plan.items()))
        return hashlib.md5(raw.encode()).hexdigest()

    def get_query(self, plan: Dict[str, Any]) -> Optional[Any]:
        key = self._make_key(plan)
        return self.query_cache.get(key)

    def set_query(self, plan: Dict[str, Any], result: Any):
        key = self._make_key(plan)
        self.query_cache[key] = result

    def has_query(self, plan: Dict[str, Any]) -> bool:
        key = self._make_key(plan)
        return key in self.query_cache

    # =========================================================
    # CLEAR
    # =========================================================
    def clear_all(self):
        self.data_cache.clear()
        self.query_cache.clear()
