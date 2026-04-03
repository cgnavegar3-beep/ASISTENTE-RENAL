class IntentParser:

    def parse(self, text: str):
        text_lower = text.lower()

        intent = "unknown"

        # reglas simples iniciales (stub funcional)
        if "cuantos" in text_lower or "número" in text_lower:
            intent = "count"

        if "paciente" in text_lower:
            intent = "patient_query"

        if "medicamento" in text_lower:
            intent = "drug_query"

        return {
            "raw": text,
            "intent": intent
        }
