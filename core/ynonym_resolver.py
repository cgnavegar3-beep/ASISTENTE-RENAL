# core/synonym_resolver.py

class SynonymResolver:
    """
    Convierte términos del lenguaje natural clínico
    a nombres reales de columnas del dataset.
    """

    def __init__(self, synonym_dict: dict):
        """
        synonym_dict ejemplo:
        {
            "riesgo": "nivel_ade",
            "funcion renal": "fg",
            "edad": "edad"
        }
        """
        self.synonym_dict = synonym_dict

    def resolve(self, text: str) -> str:
        """
        Sustituye sinónimos en el texto por columnas reales.
        """
        text_lower = text.lower()

        for synonym, column in self.synonym_dict.items():
            if synonym in text_lower:
                text_lower = text_lower.replace(synonym, column)

        return text_lower

    def resolve_tokens(self, tokens: list) -> list:
        """
        Si ya viene tokenizado.
        """
        resolved = []

        for token in tokens:
            token_lower = token.lower()
            resolved.append(
                self.synonym_dict.get(token_lower, token_lower)
            )

        return resolved
