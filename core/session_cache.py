class SessionCache:

    def __init__(self):
        self._cache = {}

    # -------------------------
    # OBTENER CACHE
    # -------------------------
    def get(self, key):
        return self._cache.get(key)

    # -------------------------
    # GUARDAR CACHE
    # -------------------------
    def set(self, key, value):
        self._cache[key] = value

    # -------------------------
    # LIMPIAR CACHE (opcional)
    # -------------------------
    def clear(self):
        self._cache.clear()

    # -------------------------
    # DEBUG
    # -------------------------
    def show(self):
        return self._cache
