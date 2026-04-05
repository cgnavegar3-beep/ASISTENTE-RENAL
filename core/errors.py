class CoreError(Exception):
    def __init__(self, modulo, mensaje, detalle=None):
        self.modulo = modulo
        self.mensaje = mensaje
        self.detalle = detalle
        super().__init__(mensaje)

    def __str__(self):
        if self.detalle:
            return f"❌ Error en {self.modulo}: {self.mensaje} ({self.detalle})"
        return f"❌ Error en {self.modulo}: {self.mensaje}"

    def obtener_sugerencia(self):
        msj = self.mensaje.lower()

        if "grafico" in msj or "gráfico" in msj:
            return "Revisar engine.py (renderizado de gráficos)"

        if "json" in msj or "formato" in msj:
            return "Revisar query_generator.py o validator.py"

        if "columna" in msj:
            return "Revisar catalog.py (schema)"

        return "Revisar logs del módulo afectado"
