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
        meds = ["medicamento", "farmaco", "fármaco", "pastilla", "insulina", "metformina"]
        return "Medicamentos" if any(w in texto for w in meds) else "Validaciones"

    # -----------------------------
    # OPERACIÓN
    # -----------------------------
    def _extract_operation(self, texto):
        if "media" in texto or "promedio" in texto:
            return "media"
        if "%" in texto or "porcentaje" in texto:
            return "porcentaje"
        if any(w in texto for w in ["cuantos", "cuántos", "numero", "número", "total"]):
            return "conteo"
        return "conteo"

    # -----------------------------
    # OUTPUT
    # -----------------------------
    def _parse_output_type(self, texto):
        if "histograma" in texto:
            return "histogram"
        if any(w in texto for w in ["pie", "sectores", "tarta"]):
            return "pie"
        if any(w in texto for w in ["grafico", "gráfico", "barras"]):
            return "bar"
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
    # GROUP BY (🔥 FIX REAL)
    # -----------------------------
    def _extract_group_by(self, texto):
        match = re.search(r"por\s+(\w+)", texto)
        if match:
            palabra = match.group(1)
            for k, v in self.sinonimos.items():
                if palabra == k:
                    return v
        return None

    # -----------------------------
    # LIMIT
    # -----------------------------
    def _extract_limit(self, texto):
        match = re.search(r"top\s*(\d+)", texto)
        return int(match.group(1)) if match else None

    # -----------------------------
    # FILTROS (🔥 FIX CLAVE TOTAL)
    # -----------------------------
    def _extract_filters(self, texto, source):
        extracted = []

        # 🔥 NORMALIZAR lenguaje clínico manualmente (clave)
        texto = texto.replace("menor de", "<")
        texto = texto.replace("mayor de", ">")

        # 🔥 aplicar sinónimos → columnas reales
        for palabra, col in self.sinonimos.items():
            texto = texto.replace(palabra, col.lower())

        # 🔥 detectar patrones tipo FG_CG < 60
        patrones = re.findall(r'([a-zA-Z0-9_]+)\s*(<|>|<=|>=|=)\s*(\d+)', texto)

        for col, op, val in patrones:
            extracted.append({
                "col": col.upper(),
                "op": "==" if op == "=" else op,
                "val": float(val)
            })

        return extracted

    # -----------------------------
    # PARSER
    # -----------------------------
    def parse_query(self, pregunta_usuario):
        texto = limpiar_texto(pregunta_usuario)

        source = self._get_target_source(texto)
        operation = self._extract_operation(texto)
        chart_type = self._parse_output_type(texto)

        variable = self._extract_variable(texto)
        group_by = self._extract_group_by(texto)
        filters = self._extract_filters(texto, source)
        limit = self._extract_limit(texto)

        # 🔥 FIX TOP
        if limit:
            group_by = variable
            chart_type = "bar"

        # 🔥 FIX GROUP BY
        if group_by and chart_type == "kpi":
            chart_type = "bar"

        return {
            "metadata": {
                "source": source,
                "intent": "visual" if chart_type != "kpi" else "kpi"
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
