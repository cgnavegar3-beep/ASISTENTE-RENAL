import re
from core.catalog import SCHEMA
from core.dictionary import SINONIMOS_COLUMNAS, MAPEO_OPERADORES
from core.normalizer import limpiar_texto
from core.errors import CoreError

class QueryGenerator:
    def __init__(self):
        self.schema = SCHEMA
        self.sinonimos = SINONIMOS_COLUMNAS
        self.operadores = {
            "mayor": ">",
            "más de": ">",
            "menor": "<",
            "menos de": "<",
            "igual": "==",
            "distinto": "!=",
            "contiene": "contains",
            "incluye": "contains"
        }

    def _get_target_source(self, texto_n):
        keywords_meds = ["medicamento", "farmaco", "pastilla", "metformina", "insulina"]
        if any(kw in texto_n for kw in keywords_meds):
            return "Medicamentos"
        return "Validaciones"

    def _parse_visual_intent(self, texto_n):
        if "histograma" in texto_n:
            raise CoreError("query_generator.py", "Gráfico no soportado", "histograma")

        if any(w in texto_n for w in ["torta", "sectores", "pie", "circular"]):
            return "pie"
        if "horizontal" in texto_n:
            return "bar_h"
        if any(w in texto_n for w in ["grafico", "dibuja", "barras", "visualiza"]):
            return "bar"

        return "kpi"

    def _extract_filters(self, texto_n, source):
        if source not in self.schema:
            raise CoreError("query_generator.py", "Origen no válido", source)

        extracted = []

        # filtros ya normalizados tipo FG_CG < 60
        patrones = re.findall(r'([a-zA-Z_]+)\s*(>=|<=|!=|=|>|<)\s*([\w\.]+)', texto_n)

        for col, op, val in patrones:
            extracted.append({
                "col": col.upper(),
                "op": op,
                "val": val
            })

        # fallback por sinónimos
        for palabra, col_tecnica in self.sinonimos.items():
            if palabra in texto_n and not any(f["col"] == col_tecnica for f in extracted):
                numeros = re.findall(r'\d+', texto_n)
                valor = int(numeros[0]) if numeros else ""
                extracted.append({
                    "col": col_tecnica,
                    "op": "==",
                    "val": valor
                })

        return extracted

    def parse_query(self, pregunta_usuario):
        try:
            texto_n = limpiar_texto(pregunta_usuario)

            source = self._get_target_source(texto_n)
            visual_type = self._parse_visual_intent(texto_n)

            dimension = None
            for palabra, col_tecnica in self.sinonimos.items():
                if palabra in texto_n:
                    dimension = col_tecnica
                    break

            return {
                "metadata": {
                    "source": source,
                    "intent": "visual" if visual_type != "kpi" else "metric"
                },
                "request": {
                    "metric": "conteo",
                    "target_col": "ID_REGISTRO",
                    "filters": self._extract_filters(texto_n, source),
                    "group_by": dimension,
                    "chart_type": visual_type
                }
            }

        except CoreError as e:
            raise e
        except Exception as e:
            raise CoreError(
                modulo="query_generator.py",
                mensaje="Error interpretando la consulta clínica",
                detalle=str(e)
            )
