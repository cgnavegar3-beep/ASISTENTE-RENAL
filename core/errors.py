class CoreError(Exception):
    def __init__(self, modulo, mensaje, detalle=None):
        self.modulo = modulo
        self.mensaje = mensaje
        self.detalle = detalle
        super().__init__(self.mensaje)

    def __str__(self):
        det = f" ({self.detalle})" if self.detalle else ""
        return f"❌ Error en {self.modulo}: {self.mensaje}{det}"

    def obtener_sugerencia(self):
        msj = self.mensaje.lower()
        if "grafico" in msj or "gráfico" in msj:
            return "💡 Sugerencia: Revisa la lógica de renderizado en engine.py."
        if "json" in msj or "formato" in msj:
            return "💡 Sugerencia: Verifica la estructura en validator.py o el prompt en query_generator.py."
        if "columna" in msj or "catálogo" in msj:
            return "💡 Sugerencia: Revisa catalog.py para asegurar que la columna existe."
        return "💡 Sugerencia: Revisa los logs internos del módulo afectado."
