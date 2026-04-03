# core/query_builder.py

class QueryBuilder:
    """
    Convierte la intención del intent_parser en un
    plan de ejecución estructurado (JSON pandas).
    """

    def __init__(self):
        pass

    def build(self, intent: dict) -> dict:
        """
        Entrada: intent_parser output
        Salida: query plan ejecutable
        """

        query_plan = {
            "operation": intent.get("action"),
            "filters": intent.get("filters", []),
            "group_by": intent.get("group_by", []),
            "aggregation": None,
            "sort": intent.get("sort"),
            "limit": intent.get("limit"),
            "visualization": None
        }

        # ---------------------------
        # 1. AGREGACIONES
        # ---------------------------
        agg = intent.get("aggregation")

        if agg:
            query_plan["aggregation"] = {
                "type": agg.get("type"),
                "field": agg.get("field"),
                "condition": agg.get("condition")
            }

        # ---------------------------
        # 2. VISUALIZACIÓN AUTOMÁTICA
        # ---------------------------
        query_plan["visualization"] = self._build_visualization(intent)

        return query_plan

    # -------------------------------------------------
    # VISUALIZACIÓN
    # -------------------------------------------------

    def _build_visualization(self, intent: dict) -> dict | None:
        """
        Decide automáticamente tipo de gráfico.
        """

        action = intent.get("action")

        # ---------------------------
        # COUNT / AGGREGATES → BAR
        # ---------------------------
        if action == "aggregate":
            return {
                "type": "bar",
                "x": intent.get("group_by", [None])[0],
                "y": "value"
            }

        # ---------------------------
        # TOP N → BAR HORIZONTAL
        # ---------------------------
        if action == "top":
            return {
                "type": "barh",
                "x": "value",
                "y": "category"
            }

        # ---------------------------
        # GROUPBY → BAR
        # ---------------------------
        if action == "groupby":
            return {
                "type": "bar",
                "x": intent.get("group_by", [None])[0],
                "y": "count"
            }

        # ---------------------------
        # FILTER SIMPLE → TABLE
        # ---------------------------
        if action == "filter":
            return {
                "type": "table"
            }

        # DEFAULT
        return {
            "type": "table"
        }
