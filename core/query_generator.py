import re
from core.catalog import SCHEMA
from core.dictionary import SINONIMOS_COLUMNAS
from core.normalizer import limpiar_texto
from core.errors import CoreError


class QueryGenerator:
    def __init__(self):
        self.schema = SCHEMA
        self.sinonimos = SINONIMOS_COLUMNAS

    # -----------------------------
    # 1. ORIGEN DE DATOS
    # -----------------------------
    def _get_target_source(self, texto):
        keywords_meds = ["medicamento", "farmaco", "pastilla", "metformina", "insulina"]
        if any(kw in texto for kw in keywords_meds):
            return "Medicamentos"
        return "Validaciones"

    # -----------------------------
    # 2. OPERACIÓN REAL (KPI CORE)
    # -----------------------------
    def _extract_operation(self, texto):
        if "media" in texto:
            return "media"
        if "porcentaje" in texto or "%" in texto:
            return "porcentaje"
        if "cuantos" in texto or "cuántos" in texto or "numero" in texto or "número" in texto:
            return "conteo"
        if "suma" in texto:
            return "suma"
        if "max" in texto or "máximo" in texto:
            return "max"
        if "min" in texto or "mínimo" in texto:
            return "min"
        return "conteo"

    # -----------------------------
    # 3. SALIDA VISUAL (SOLO RENDER)
    # -----------------------------
    def _parse_output_type(self, texto):
        if any(w in texto for w in ["histograma", "distribucion", "distribución"]):
            return "histogram"

        if any(w in texto for w in ["torta", "sectores", "pie", "circular"]):
            return "pie"

        if any(w in texto for w in ["barras", "bar", "visualiza", "grafico", "gráfico"]):
            return "bar"

        if any(w in texto for w in ["tabla", "listado", "lista"]):
            return "table"

        return "kpi"

    # -----------------------------
    # 4. FILTROS
    # -----------------------------
    def _extract_filters(self, texto, source):
        if source not in self.schema:
            raise CoreError("query_generator.py", "Origen no válido", source)

        extracted = []

        patrones = re.findall(
            r'([A-Z0-9Ñ_º]+)\s*(>=|<=|!=|=|>|<)\s*([\w\.]+)',
            texto.upper()
        )

        for col, op, val in patrones:
            extracted.append({
                "col": col,
                "op": op,
                "val": val
            })

        for palabra, col_tecnica in self.sinonimos.items():
            if palabra in texto and not any(f["col"] == col_tecnica for f in extracted):
                numeros = re.findall(r'\d+', texto)
                valor = int(numeros[0]) if numeros else None
                extracted.append({
                    "col": col_tecnica,
                    "op": "==",
                    "val": valor
                })

        return extracted

    # -----------------------------
    # 5. VARIABLE PRINCIPAL
    # -----------------------------
    def _extract_variable(self, texto):
        for palabra, col_tecnica in self.sinonimos.items():
            if palabra in texto:
                return col_tecnica
        return "ID_REGISTRO"

    # -----------------------------
    # 6. INTENCIÓN IMPLÍCITA
    # -----------------------------
    def _extract_intent(self, operation, output_type):
        if output_type in ["pie", "bar", "histogram", "table"]:
            return "visual"
        if operation == "conteo":
            return "kpi"
        return "kpi"

    # -----------------------------
    # 7. PARSER PRINCIPAL
    # -----------------------------
    def parse_query(self, pregunta_usuario):
        try:
            texto = limpiar_texto(pregunta_usuario)

            source = self._get_target_source(texto)
            operation = self._extract_operation(texto)
            chart_type = self._parse_output_type(texto)
            variable = self._extract_variable(texto)
            filters = self._extract_filters(texto, source)
            intent = self._extract_intent(operation, chart_type)

            return {
                "metadata": {
                    "source": source,
                    "intent": intent
                },
                "request": {
                    "metric": operation,
                    "target_col": variable,
                    "filters": filters,
                    "group_by": variable if chart_type in ["bar", "pie"] else None,
                    "chart_type": chart_type
                }
            }

        except CoreError:
            raise

        except Exception as e:
            raise CoreError(
                "query_generator.py",
                "Error interpretando la consulta clínica",
                str(e)
            )
