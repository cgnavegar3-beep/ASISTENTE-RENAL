from typing import Dict, Any, Optional

from normalizer import normalize_text
from semantic_cache import resolve_with_cache
import semantic_layer as sl
import matcher
import schema_resolver


# =========================================================
# ORCHESTRATOR PRINCIPAL
# Cerebro del sistema (NO IA, solo control)
# =========================================================


def _fallback_strategy(semantic_input: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Estrategia cuando el matcher no entiende el input.
    Evita que el sistema "muera" en UNKNOWN_INTENT.
    """

    # 1. Segundo intento: matcher rule-based
    try:
        rule_result = matcher.match_rules(semantic_input)
        if rule_result and rule_result.get("confidence", 0) > 0:
            return rule_result
    except Exception:
        pass

    # 2. Expansión semántica (sinónimos más amplios)
    try:
        expanded = sl.expand_semantics(semantic_input)
        rule_result = matcher.match_rules(expanded)
        if rule_result and rule_result.get("confidence", 0) > 0:
            return rule_result
    except Exception:
        pass

    # 3. Último recurso estructurado (NO bloquea flujo)
    return {
        "intent": "UNKNOWN_INTENT",
        "confidence": 0.0,
        "entities": [],
        "columns_needed": [],
        "filters": [],
        "operation": "",
        "fallback": {
            "rule_based_attempted": True,
            "semantic_expansion_attempted": True,
            "status": "needs_clarification"
        }
    }


# =========================================================
# ORCHESTRATION CORE
# =========================================================

def orchestrate(user_input: str, context: Optional[Dict] = None) -> Dict[str, Any]:

    # -----------------------------
    # 1. NORMALIZACIÓN
    # -----------------------------
    clean = normalize_text(user_input)

    # -----------------------------
    # 2. SEMÁNTICA (CACHEADA)
    # -----------------------------
    semantic = resolve_with_cache(clean, sl.resolve, context)

    # -----------------------------
    # 3. MATCHER PRINCIPAL (IA o reglas)
    # -----------------------------
    try:
        intent_result = matcher.match_intent(semantic, context)

    except Exception:
        intent_result = {
            "intent": "UNKNOWN_INTENT",
            "confidence": 0.0
        }

    # -----------------------------
    # 4. FALLBACK SI FALLA EL MATCHER
    # -----------------------------
    if intent_result.get("intent") == "UNKNOWN_INTENT" or intent_result.get("confidence", 0) < 0.4:
        intent_result = _fallback_strategy(semantic, context)

    # -----------------------------
    # 5. RESOLVER ESQUEMA (columnas reales)
    # -----------------------------
    try:
        schema = schema_resolver.resolve(intent_result, semantic, context)
    except Exception:
        schema = {
            "columns_needed": [],
            "safe_mode": True
        }

    # -----------------------------
    # 6. OUTPUT FINAL CONTROLADO
    # -----------------------------
    result = {
        "input_raw": user_input,
        "input_clean": clean,
        "semantic": semantic,
        "intent": intent_result,
        "schema": schema
    }

    return result
