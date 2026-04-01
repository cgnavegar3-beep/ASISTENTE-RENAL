import hashlib
from typing import Optional, Dict, Callable, Any

# =========================================================
# SEMANTIC CACHE MODULE
# Reduce coste de tokens y latencia
# =========================================================

# Cache en memoria (RAM)
CACHE: Dict[str, Any] = {}


# ---------------------------------------------------------
# KEY GENERATION (SIN IA → IMPORTANTE PARA NO GASTAR TOKENS)
# ---------------------------------------------------------
def _make_key(text: str, context: Optional[Dict] = None) -> str:
    """
    Genera una clave estable para cache.
    ⚠️ NO usa IA ni semantic_layer (evita gasto de tokens).
    """

    normalized = text.lower().strip()

    # Contexto reducido y estable (evita colisiones pero sin ruido)
    if context:
        try:
            ctx_items = sorted(
                (k, str(v)) for k, v in context.items()
            )
            ctx_str = str(ctx_items)
        except Exception:
            ctx_str = str(context)
    else:
        ctx_str = ""

    raw = f"{normalized}|{ctx_str}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


# ---------------------------------------------------------
# GET CACHE
# ---------------------------------------------------------
def get_cached(text: str, context: Optional[Dict] = None) -> Optional[Any]:
    """Recupera valor cacheado si existe."""
    key = _make_key(text, context)
    return CACHE.get(key)


# ---------------------------------------------------------
# SET CACHE
# ---------------------------------------------------------
def set_cache(text: str, value: Any, context: Optional[Dict] = None) -> None:
    """Guarda resultado en cache."""
    if value is None:
        return

    key = _make_key(text, context)
    CACHE[key] = value


# ---------------------------------------------------------
# WRAPPER PRINCIPAL (PROXY CACHE)
# ---------------------------------------------------------
def resolve_with_cache(
    text: str,
    resolver_fn: Callable[[str], Any],
    context: Optional[Dict] = None
) -> Any:
    """
    1. Busca en cache
    2. Si existe → devuelve directo (0 tokens)
    3. Si no existe → ejecuta IA/orchestrator
    4. Guarda resultado
    """

    cached = get_cached(text, context)
    if cached is not None:
        return cached

    result = resolver_fn(text)
    set_cache(text, result, context)

    return result


# ---------------------------------------------------------
# UTILIDADES
# ---------------------------------------------------------
def clear_cache() -> None:
    """Limpia cache completo."""
    CACHE.clear()


def cache_size() -> int:
    """Número de entradas en cache."""
    return len(CACHE)


def get_cache_stats() -> Dict[str, Any]:
    """Estadísticas básicas del cache."""
    return {
        "entries": len(CACHE),
        "memory_object_id": id(CACHE)
    }
