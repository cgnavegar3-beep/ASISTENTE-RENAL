# core/intent_parser.py

import re


class IntentParser:
    """
    Convierte lenguaje clínico ya normalizado en una estructura de intención.
    NO usa pandas.
    NO usa columnas.
    Solo detecta significado clínico.
    """

    def parse(self, text: str) -> dict:
        text = text.lower()

        intent = {
            "concept": None,        # riesgo, fg, toxicidad, etc.
            "operation": None,      # filter, count, mean, percent
            "risk_level": None,     # leve, moderado, alto, crítico
            "category": None,       # ajuste, precaucion, contraindicado
            "comparators": [],      # >=, <=, = etc.
            "value": None,
            "logic": "and"          # base (luego AND/OR avanzado)
        }

        # ---------------------------
        # 1. CONCEPTO PRINCIPAL
        # ---------------------------
        if "riesgo" in text:
            intent["concept"] = "risk"

        if "toxicidad" in text:
            intent["concept"] = "toxicity"

        if "precauc" in text:
            intent["concept"] = "precaution"

        if "contraind" in text:
            intent["concept"] = "contraindication"

        # ---------------------------
        # 2. NIVEL CLÍNICO
        # ---------------------------
        if "leve" in text:
            intent["risk_level"] = "leve"

        if "moderado" in text:
            intent["risk_level"] = "moderado"

        if "alto" in text:
            intent["risk_level"] = "alto"

        if "grave" in text:
            intent["risk_level"] = "alto"

        if "critico" in text or "crítico" in text:
            intent["risk_level"] = "critico"

        # ---------------------------
        # 3. OPERADORES NUMÉRICOS
        # ---------------------------
        # >= 3, <=2, =1 etc.
        pattern = r"(>=|<=|=|>|<)\s*(\d+)"
        matches = re.findall(pattern, text)

        for op, val in matches:
            intent["comparators"].append({
                "op": op,
                "value": int(val)
            })

        # ---------------------------
        # 4. DETECCIÓN DE OPERACIÓN
        # ---------------------------
        if "cuantos" in text or "numero" in text or "total" in text:
            intent["operation"] = "count"

        if "media" in text or "promedio" in text:
            intent["operation"] = "mean"

        if "%" in text or "porcentaje" in text:
            intent["operation"] = "percent"

        # ---------------------------
        # 5. DEFAULT
        # ---------------------------
        if intent["operation"] is None:
            intent["operation"] = "filter"

        return intent
