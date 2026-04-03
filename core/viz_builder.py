# core/viz_builder.py

import matplotlib.pyplot as plt


class VizBuilder:
    """
    Convierte DataFrames finales en:
    - tablas
    - gráficos
    - salidas clínicas resumidas
    """

    def build(self, df, output_type: str, config: dict = None):
        config = config or {}

        if output_type == "table":
            return self._table(df)

        if output_type == "bar":
            return self._bar(df, config)

        if output_type == "line":
            return self._line(df, config)

        if output_type == "pie":
            return self._pie(df, config)

        if output_type == "clinical_summary":
            return self._clinical_summary(df)

        raise ValueError(f"Output type no soportado: {output_type}")

    # --------------------------
    # TABLA
    # --------------------------
    def _table(self, df):
        return {
            "type": "table",
            "data": df.to_dict(orient="records")
        }

    # --------------------------
    # BAR CHART
    # --------------------------
    def _bar(self, df, config):
        x = config.get("x")
        y = config.get("y")

        plt.figure()
        plt.bar(df[x], df[y])
        plt.xlabel(x)
        plt.ylabel(y)
        plt.title(config.get("title", "Bar chart"))

        return {"type": "plot", "figure": plt.gcf()}

    # --------------------------
    # LINE CHART
    # --------------------------
    def _line(self, df, config):
        x = config.get("x")
        y = config.get("y")

        plt.figure()
        plt.plot(df[x], df[y])
        plt.xlabel(x)
        plt.ylabel(y)
        plt.title(config.get("title", "Line chart"))

        return {"type": "plot", "figure": plt.gcf()}

    # --------------------------
    # PIE CHART
    # --------------------------
    def _pie(self, df, config):
        labels = config.get("labels")
        values = config.get("values")

        plt.figure()
        plt.pie(df[values], labels=df[labels], autopct="%1.1f%%")
        plt.title(config.get("title", "Pie chart"))

        return {"type": "plot", "figure": plt.gcf()}

    # --------------------------
    # RESUMEN CLÍNICO
    # --------------------------
    def _clinical_summary(self, df):
        return {
            "type": "clinical_summary",
            "n_rows": len(df),
            "columns": list(df.columns),
            "preview": df.head(5).to_dict(orient="records")
        }
