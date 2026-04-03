# core/clinical_semantic_mapper.py


class ClinicalSemanticMapper:
    """
    Convierte lenguaje clínico (riesgo) en estructuras
    para CG, MDRD y CKD simultáneamente.
    """

    def __init__(self):
        # niveles clínicos universales
        self.level_map = {
            "leve": 1,
            "bajo": 1,
            "moderado": 2,
            "medio": 2,
            "alto": 3,
            "grave": 3,
            "crítico": 4,
            "critico": 4
        }

        # mapping por fórmula
        self.schemas = {
            "CG": {
                "nivel": "NIVEL_ADE_CG",
                "riesgo": "RIESGO_CG",
                "categoria": "CAT_RIESGO_CG"
            },
            "MDRD": {
                "nivel": "NIVEL_ADE_MDRD",
                "riesgo": "RIESGO_MDRD",
                "categoria": "CAT_RIESGO_MDRD"
            },
            "CKD": {
                "nivel": "NIVEL_ADE_CKD",
                "riesgo": "RIESGO_CKD",
                "categoria": "CAT_RIESGO_CKD"
            }
        }

    # ---------------------------------------
    # MAIN ENTRY
    # ---------------------------------------
    def map_risk(self, intent: dict):
        """
        Convierte intención clínica en reglas aplicables a todos los FG
        """

        risk_level = intent.get("risk_level")  # leve/moderado/alto/crítico
        numeric_level = self.level_map.get(risk_level)

        if numeric_level is None:
            return {}

        result = {}

        for fg in self.schemas:
            schema = self.schemas[fg]

            result[fg] = {
                "field": schema["nivel"],
                "threshold": numeric_level,
                "rule": f"{schema['nivel']} >= {numeric_level}"
            }

        return result

    # ---------------------------------------
    # CAT RIESGO (acción clínica)
    # ---------------------------------------
    def map_category(self, intent: dict):
        """
        Traduce intención a categoría clínica (CG/MDRD/CKD)
        """

        category = intent.get("category")  # ajuste, precaución, contraindicado

        if not category:
            return {}

        result = {}

        for fg in self.schemas:
            schema = self.schemas[fg]

            result[fg] = {
                "field": schema["categoria"],
                "value": category
            }

        return result
