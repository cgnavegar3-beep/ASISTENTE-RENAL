import re

class NLParser:
    """
    Traductor lenguaje natural → Query Plan (JSON estructurado)
    Sin IA. Solo reglas deterministas.
    """

    def __init__(self):
        # vocabulario clínico básico (ampliable)
        self.columns = {
            "edad": ["edad", "años", "mayores", "menores"],
            "fg": ["fg", "filtrado", "renal"],
            "creatinina": ["creatinina"],
            "centro": ["centro", "hospital"],
            "medicamento": ["medicamento", "fármaco", "farmaco"],
            "sexo": ["sexo", "hombre", "mujer"]
        }

    # -----------------------------
    # ENTRY POINT
    # -----------------------------
    def parse(self, text: str) -> dict:
        text = text.lower()

        plan = {
            "action": None,
            "filters": []
        }

        # 1. DETECTAR ACCIÓN
        if any(x in text for x in ["histograma", "distribución", "distribucion"]):
            plan["action"] = "plot"
            plan["type"] = "histogram"

        elif "tabla" in text or "lista" in text:
            plan["action"] = "table"

        elif "cuántos" in text or "cuantos" in text or "count" in text:
            plan["action"] = "count"

        elif "top" in text:
            plan["action"] = "groupby"
            plan["sort"] = "desc"
            plan["limit"] = self._extract_number(text) or 10

        elif "por" in text:
            plan["action"] = "groupby"

        else:
            plan["action"] = "filter"

        # 2. FILTROS
        plan["filters"] = self._extract_filters(text)

        # 3. GROUPBY
        gb = self._detect_groupby(text)
        if gb:
            plan["groupby"] = gb

        return plan

    # -----------------------------
    # FILTROS
    # -----------------------------
    def _extract_filters(self, text: str):
        filters = []

        # edad >
        match = re.search(r"mayores de (\d+)", text)
        if match:
            filters.append({"column": "edad", "op": ">", "value": int(match.group(1))})

        match = re.search(r"menores de (\d+)", text)
        if match:
            filters.append({"column": "edad", "op": "<", "value": int(match.group(1))})

        # fg bajo
        if "fg bajo" in text:
            filters.append({"column": "fg", "op": "<", "value": 60})

        # centro
        match = re.search(r"en ([a-záéíóúñ ]+)", text)
        if match:
            val = match.group(1).strip()
            filters.append({"column": "centro", "op": "=", "value": val})

        return filters

    # -----------------------------
    # GROUPBY
    # -----------------------------
    def _detect_groupby(self, text: str):
        for col, keywords in self.columns.items():
            if "por " + col in text or any(k in text for k in keywords):
                if "por " in text:
                    # ejemplo: "por centro"
                    for word in text.split():
                        if word in self.columns:
                            return word
        return None

    # -----------------------------
    # EXTRACT NUMBER
    # -----------------------------
    def _extract_number(self, text):
        match = re.search(r"top (\d+)", text)
        if match:
            return int(match.group(1))
        return None
