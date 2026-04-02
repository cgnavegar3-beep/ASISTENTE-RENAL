class FallbackEngine:

    def execute(self, plan: dict, df_dict: dict):

        operation = plan.get("operation")

        if not operation:
            operation = "count"

        df = df_dict[list(df_dict.keys())[0]]

        try:
            if operation == "count":
                return {"result": len(df)}

            if operation == "sum":
                return {"result": df[plan["target"]].sum()}

            if operation == "avg":
                return {"result": df[plan["target"]].mean()}

            if operation == "max":
                return {"result": df[plan["target"]].max()}

            if operation == "min":
                return {"result": df[plan["target"]].min()}

            return {"result": len(df)}

        except Exception:
            return {"result": "fallback_error"}
