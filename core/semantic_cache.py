# core/semantic_cache.py

import hashlib
import json
import pandas as pd


class SemanticCache:
    """
    Cache semántico del compilador clínico.

    Evita recomputar:
    - intent parsing
    - query plan
    - execution
    """

    def __init__(self):
        # cache en memoria (puedes migrar luego a Redis)
        self._cache = {}

    # -------------------------------------------------
    # PUBLIC API
    # -------------------------------------------------
    def get(self, query: str, context: dict = None):
        key = self._build_key(query, context)

        if key in self._cache:
            return self._cache[key]

        return None

    def set(self, query: str, result: dict, context: dict = None):
        key = self._build_key(query, context)
        self._cache[key] = result

    def clear(self):
        self._cache = {}

    # -------------------------------------------------
    # KEY GENERATION (SEMÁNTICO)
    # -------------------------------------------------
    def _build_key(self, query: str, context: dict):

        normalized_query = self._normalize(query)

        context_str = ""
        if context:
            # solo campos relevantes clínicos
            context_str = json.dumps(
                self._normalize_context(context),
                sort_keys=True
            )

        raw_key = f"{normalized_query}::{context_str}"

        return self._hash(raw_key)

    # -------------------------------------------------
    # NORMALIZACIÓN
    # -------------------------------------------------
    def _normalize(self, text: str) -> str:
        return (
            text.lower()
            .strip()
        )

    def _normalize_context(self, context: dict):
        """
        Reduce ruido del contexto:
        solo variables clínicas relevantes
        """
        allowed_keys = {
            "fg",
            "tipo_filtrado",
            "edad",
            "sexo",
            "centro",
            "nivel_ade"
        }

        return {
            k: context[k]
            for k in context
            if k in allowed_keys
        }

    # -------------------------------------------------
    # HASH
    # -------------------------------------------------
    def _hash(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()
