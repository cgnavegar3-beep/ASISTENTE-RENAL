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
    # ORIGEN
    # -----------------------------
    def _get_target_source(self, texto):
        keywords_meds = [
            "medicamento", "farmaco", "fármaco",
            "pastilla", "tratamiento", "insulina", "metformina"
        ]
        return "Medicamentos" if any(kw in texto for kw in keywords_meds) else "Validaciones"

    # -----------------------------
    # MÉTRICA PRINCIPAL
    # -----------------------------
    def _extract_operation(self, texto):
        if any(w in texto for w in ["media", "promedio"]):
            return "media"

        if "%" in texto or "porcentaje" in texto:
            return "porcentaje"

        if any(w in texto for w in ["cuantos", "cuántos", "numero", "número", "total"]):
            return "conteo"

        if any(w in texto for w in ["suma"]):
            return "suma"

        if any(w in texto for w in ["max", "máximo"]):
            return "max"

        if any(w in texto for w in ["min", "mínimo"]):
            return "min"

        return "conteo"

    # -----------------------------
    # OUTPUT VISUAL
    # -----------------------------
    def _parse_output_type(self, texto):
        if any(w in texto for w in ["histograma", "distribución", "distribucion"]):
            return "histogram"

        if any(w in texto for w in ["sectores", "tarta", "pie", "circular"]):
            return "pie"

        if any(w in texto for w in ["barras", "bar", "gráfico", "grafico"]):
            return "bar"

        if any(w in texto for w in ["lista", "listado", "tabla"]):
            return "table"

        return "kpi"

    # -----------------------------
    # TOP N
    # -----------------------------
    def _extract_limit(self, texto):
        match = re.search(r"(top\s*\d+|primeros\s*\d+)", texto)
        if match:
            nums = re.findall(r"\d+", match.group())
            return int(nums[0]) if nums else None
        return None

    # -----------------------------
    # VARIABLE PRINCIPAL
    # -----------------------------
    def _extract_variable(self, texto):
        for palabra, col in self.sinonimos.items():
            if palabra in texto:
                return col
        return "ID_REGISTRO"

    # -----------------------------
    # FILTROS
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
                    "op": "=",
                    "val": valor
                })

        return extracted

    # -----------------------------
    # INTENT
    # -----------------------------
    def _extract_intent(self, operation, output_type):
        if output_type in ["bar", "pie", "histogram", "table"]:
            return "visual"
        return "kpi"

    # -----------------------------
    # PARSER PRINCIPAL
    # -----------------------------
    def parse_query(self, pregunta_usuario):
        try:
            texto = limpiar_texto(pregunta_usuario)

            source = self._get_target_source(texto)
            operation = self._extract_operation(texto)
            chart_type = self._parse_output_type(texto)
            variable = self._extract_variable(texto)
            filters = self._extract_filters(texto, source)
            limit = self._extract_limit(texto)
            intent = self._extract_intent(operation, chart_type)

            group_by = None
            if chart_type in ["bar", "pie"]:
                group_by = variable

            return {
                "metadata": {
                    "source": source,
                    "intent": intent
                },
                "request": {
                    "metric": operation,
                    "target_col": variable,
                    "filters": filters,
                    "group_by": group_by,
                    "chart_type": chart_type,
                    "limit": limit
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
