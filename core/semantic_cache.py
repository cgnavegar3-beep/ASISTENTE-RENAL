import hashlib
from typing import Optional, Dict, Any

# =========================================================
# SEMANTIC CACHE MODULE
# Reduce coste de tokens y latencia
# =========================================================


class SemanticCache:

    def __init__(self):
        # Cache en memoria (RAM)
        self.cache: Dict[str, Any] = {}

    # ---------------------------------------------------------
    # KEY GENERATION (SIN IA → IMPORTANTE PARA NO GASTAR TOKENS)
    # ---------------------------------------------------------
    def _make_key(self, text: str, context: Optional[Dict] = None) -> str:
        """
        Genera clave estable para cache.
        """
        normalized = text.lower().strip()

        if context:
            normalized += str(sorted(context.items()))

        return hashlib.md5(normalized.encode()).hexdigest()

    # ---------------------------------------------------------
    # GET
    # ---------------------------------------------------------
    def get(self, text: str, context: Optional[Dict] = None):
        key = self._make_key(text, context)
        return self.cache.get(key)

    # ---------------------------------------------------------
    # SET
    # ---------------------------------------------------------
    def set(self, text: str, value: Any, context: Optional[Dict] = None):
        key = self._make_key(text, context)
        self.cache[key] = value
