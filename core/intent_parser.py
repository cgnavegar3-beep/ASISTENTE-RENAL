# core/intent_parser.py

import re


class IntentParser:
    """
    Convierte lenguaje clínico en una intención estructurada
    lista para convertirse en JSON de pandas.
    """

    def __init__(self):
        pass

    def parse(self, text: str) -> dict:
        text = text.lower()

        intent = {
            "action": None,            # filter | groupby | aggregate | top | select
            "filters": [],
            "group_by": [],
            "aggregation": None,       # count | sum | mean | percent
            "metrics": [],
            "sort": None,
            "limit": None
        }

        # ---------------------------
        # 1. FILTROS (condiciones)
        # ---------------------------
        filter_patterns = [
            r"(fg|filtrado glomerular)\s*(<|>|<=|>=|=)\s*(\d+)",
            r"(edad)\s*(<|>|<=|>=|=)\s*(\d+)",
            r"(creatinina)\s*(<|>|<=|>=|=)\s*(\d+)"
        ]

        for pattern in filter_patterns:
            match = re.search(pattern, text)
            if match:
                field, op, value = match.groups()
                intent["filters"].append({
                    "field": field,
                    "operator": op,
                    "value": float(value)
                })

        # ---------------------------
        # 2. GROUP BY
        # ---------------------------
        if "por centro" in text:
            intent["group_by"].append("centro")

        if "por edad" in text:
            intent["group_by"].append("edad")

        if "por sexo" in text:
            intent["group_by"].append("sexo")

        # ---------------------------
        # 3. AGREGACIONES CLÍNICAS
        # ---------------------------

        # COUNT
        if re.search(r"\b(cuantos|cuántos|numero de|número de)\b", text):
            intent["action"] = "aggregate"
            intent["aggregation"] = {"type": "count"}

        # MEAN / PROMEDIO
        elif re.search(r"\b(media|promedio)\b", text):
            intent["action"] = "aggregate"
            intent["aggregation"] = {
                "type": "mean",
                "field": self._extract_field(text)
            }

        # SUMA
        elif re.search(r"\b(suma|total)\b", text):
            intent["action"] = "aggregate"
            intent["aggregation"] = {
                "type": "sum",
                "field": self._extract_field(text)
            }

        # PORCENTAJE
        elif re.search(r"\b(%|porcentaje|proporción)\b", text):
            intent["action"] = "aggregate"
            intent["aggregation"] = {
                "type": "percent",
                "condition": self._extract_condition(text)
            }

        # ---------------------------
        # 4. TOP N
        # ---------------------------
        top_match = re.search(r"top\s+(\d+)", text)
        if top_match:
            intent["action"] = "top"
            intent["limit"] = int(top_match.group(1))

        # ---------------------------
        # 5. FILTRO SIMPLE O DEFAULT
        # ---------------------------
        if intent["action"] is None:
            if intent["group_by"]:
                intent["action"] = "groupby"
            elif intent["filters"]:
                intent["action"] = "filter"
            else:
                intent["action"] = "select"

        return intent

    # -------------------------------------------------
    # HELPERS
    # -------------------------------------------------

    def _extract_field(self, text: str):
        """
        Extrae campo probable para agregaciones.
        Ej: "media de edad" → edad
        """
        fields = ["edad", "fg", "creatinina"]
        for f in fields:
            if f in text:
                return f
        return None

    def _extract_condition(self, text: str):
        """
        Extrae condición simple para percent.
        Ej: "riesgo alto" → nivel_ade = alto
        """
        if "riesgo alto" in text:
            return {
                "field": "nivel_ade",
                "operator": "=",
                "value": "alto"
            }

        if "fg < 60" in text or "filtrado < 60" in text:
            return {
                "field": "fg",
                "operator": "<",
                "value": 60
            }

        return None
