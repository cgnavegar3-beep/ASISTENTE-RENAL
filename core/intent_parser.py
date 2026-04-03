# core/query_builder.py

class QueryBuilder:
    """
    Compilador final:
    convierte intención estructurada → DSL pandas clínico
    """

    def build(self, mapped: dict) -> dict:

        query = {
            "select": ["*"],
            "filters": [],
            "logic": "AND",
            "group_by": None,
            "aggregation": None,
            "order_by": None,
            "limit": None,
            "output": {"type": "table"}
        }

        # -------------------------
        # FILTROS
        # -------------------------
        if "filters" in mapped:
            query["filters"] = mapped["filters"]

        # -------------------------
        # GROUP BY
        # -------------------------
        if "group_by" in mapped:
            query["group_by"] = mapped["group_by"]

        # -------------------------
        # AGGREGATION
        # -------------------------
        if "aggregation" in mapped:
            query["aggregation"] = mapped["aggregation"]

        # -------------------------
        # ORDER BY
        # -------------------------
        if "order_by" in mapped:
            query["order_by"] = mapped["order_by"]

        # -------------------------
        # LIMIT
        # -------------------------
        if "limit" in mapped:
            query["limit"] = mapped["limit"]

        # -------------------------
        # OUTPUT TYPE
        # -------------------------
        if "output" in mapped:
            query["output"] = mapped["output"]

        return query
