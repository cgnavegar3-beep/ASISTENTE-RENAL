import re
from core.catalog import SCHEMA
from core.dictionary import SINONIMOS_COLUMNAS, MAPEO_VISUAL
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
    # OPERACIÓN
    # -----------------------------
    def _extract_operation(self, texto):
        if any(w in texto for w in ["media", "promedio"]):
            return "media"

        if "%" in texto or "porcentaje" in texto:
            return "porcentaje"

        if any(w in texto for w in ["cuantos", "cuántos", "numero", "número", "total"]):
            return "conteo"

        if "suma" in texto:
            return "suma"

        if "max" in texto:
            return "max"

        if "min" in texto:
            return "min"

        return "conteo"

    # -----------------------------
    # OUTPUT
    # -----------------------------
    def _parse_output_type(self, texto):
        if any(w in texto for w in ["histograma", "distribucion", "distribución"]):
            return "histogram"

        if any(w in texto for w in ["tarta", "sectores", "pie", "circular"]):
            return "pie"

        if any(w in texto for w in ["barras", "grafico", "gráfico"]):
            return "bar"

        if any(w in texto for w in ["tabla", "lista", "listado"]):
            return "table"

        return "kpi"

    # -----------------------------
    # VARIABLE
    # -----------------------------
    def _extract_variable(self, texto):
        for palabra, col in self.sinonimos.items():
            if palabra in texto:
                return col
        return "ID_REGISTRO"

    # -----------------------------
    # GROUP BY
    # -----------------------------
    def _extract_group_by(self, texto):
        if "por " in texto:
            partes = texto.split("por ")
            if len(partes) > 1:
                posible = partes[1].strip().split(" ")[0]
                for palabra, col in self.sinonimos.items():
                    if palabra == posible:
                        return col
        return None

    # -----------------------------
    # LIMIT (TOP N)
    # -----------------------------
    def _extract_limit(self, texto):
        match = re.search(r"(top\s*\d+|primeros\s*\d+)", texto)
        if match:
            nums = re.findall(r"\d+", match.group())
            return int(nums[0]) if nums else None
        return None

    # -----------------------------
    # FILTROS (🔥 FIX DEFINITIVO)
    # -----------------------------
    def _extract_filters(self, texto, source):
        if source not in self.schema:
            raise CoreError("query_generator.py", "Origen no válido", source)

        extracted = []
        texto_proc = texto

        # 🔥 1. sustituir sinónimos por columnas reales
        for palabra, col_tecnica in self.sinonimos.items():
            if palabra in texto_proc:
                texto_proc = texto_proc.replace(palabra, col_tecnica.lower())

        # 🔥 2. detectar operadores tipo "< 60"
        patrones = re.findall(
            r'([a-zA-Z0-9_]+)\s*(>=|<=|!=|==|=|>|<)\s*([\d\.]+)',
            texto_proc
        )

        for col, op, val in patrones:
            extracted.append({
                "col": col.upper(),
                "op": "==" if op == "=" else op,
                "val": float(val)
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
            raw_output = self._parse_output_type(texto)
            chart_type = MAPEO_VISUAL.get(raw_output, raw_output)

            variable = self._extract_variable(texto)
            group_by = self._extract_group_by(texto)
            filters = self._extract_filters(texto, source)
            limit = self._extract_limit(texto)
            intent = self._extract_intent(operation, chart_type)

            # 🔥 FIX CLAVE: si hay TOP → forzar agrupación por variable
            if limit and not group_by:
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
