class ExecutionEngine:

    def execute_plan(self, plan: dict, df_dict: dict):

        operation = plan.get("operation")

        if not operation:
            raise ValueError("Missing operation")

        df_name = plan.get("source", list(df_dict.keys())[0])
        df = df_dict[df_name]

        if operation == "count":
            return {"result": len(df)}

        if operation == "sum":
            col = plan["target"]
            return {"result": df[col].sum()}

        if operation == "avg":
            col = plan["target"]
            return {"result": df[col].mean()}

        if operation == "max":
            col = plan["target"]
            return {"result": df[col].max()}

        if operation == "min":
            col = plan["target"]
            return {"result": df[col].min()}

        if operation == "groupby":
            col = plan["group_by"]
            return {"result": df.groupby(col).size().to_dict()}

        raise ValueError(f"Unknown operation: {operation}")
