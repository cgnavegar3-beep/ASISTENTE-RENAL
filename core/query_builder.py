# core/query_builder.py


class QueryBuilder:
    """
    Convierte intención + semántica clínica en un query_plan
    ejecutable por ExecutionEngine.
    """

    def build(self, intent: dict, semantic_map: dict = None) -> dict:

        semantic_map = semantic_map or {}

        query_plan = {
            "operation": intent.get("operation", "filter"),
            "filters": [],
            "aggregation": None,
            "group_by": None,
            "limit": None
        }

        # ---------------------------------------------------
        # 1. RIESGO CLÍNICO (desde semantic mapper)
        # ---------------------------------------------------
        if semantic_map:
            for fg, cfg in semantic_map.items():

                # ejemplo: NIVEL_ADE_CG >= 3
                query_plan["filters"].append({
                    "field": cfg["field"],
                    "operator": ">=",
                    "value": cfg["threshold"]
                })

        # ---------------------------------------------------
        # 2. CONDICIONES EXPLÍCITAS (intent parser)
        # ---------------------------------------------------
        for c in intent.get("comparators", []):
            query_plan["filters"].append({
                "field": None,   # se resuelve en resolver final
                "operator": c["op"],
                "value": c["value"]
            })

        # ---------------------------------------------------
        # 3. OPERACIÓN CLÍNICA
        # ---------------------------------------------------
        op = intent.get("operation")

        if op in ["count", "mean", "sum", "percent"]:
            query_plan["aggregation"] = {
                "type": op,
                "field": None
            }

        # ---------------------------------------------------
        # 4. CONCEPTO CLÍNICO
        # ---------------------------------------------------
        concept = intent.get("concept")

        if concept:
            query_plan["concept"] = concept

        # ---------------------------------------------------
        # 5. DEFAULT SEGURIDAD
        # ---------------------------------------------------
        if not query_plan["filters"] and not query_plan["aggregation"]:
            query_plan["operation"] = "noop"

        return query_plan
