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
        meds = ["medicamento", "farmaco", "fármaco", "pastilla", "insulina", "metformina", "tratamiento"]
        return "Medicamentos" if any(w in texto for w in meds) else "Validaciones"

    # -----------------------------
    # OPERACIÓN
    # -----------------------------
    def _extract_operation(self, texto):
        if any(w in texto for w in ["media", "promedio", "average"]): return "media"
        if any(w in texto for w in ["%", "porcentaje", "proporcion"]): return "porcentaje"
        if any(w in texto for w in ["maximo", "max", "mas alto"]): return "max"
        if any(w in texto for w in ["minimo", "min", "mas bajo"]): return "min"
        return "conteo"

    # -----------------------------
    # OUTPUT
    # -----------------------------
    def _parse_output_type(self, texto, has_grouping=False):
        if "histograma" in texto: return "histogram"
        if any(w in texto for w in ["pie", "sectores", "tarta", "quesito"]): return "pie"
        if any(w in texto for w in ["grafico", "gráfico", "barras", "visualizar"]): return "bar"
        if any(w in texto for w in ["tabla", "lista", "ranking", "top"]): return "table"
        return "bar" if has_grouping else "kpi"

    # -----------------------------
    # VARIABLE
    # -----------------------------
    def _extract_variable(self, texto):
        for palabra in sorted(self.sinonimos.keys(), key=len, reverse=True):
            if palabra in texto:
                return self.sinonimos[palabra]

        if any(w in texto for w in ["medicamento", "farmaco", "fármaco"]):
            return "MEDICAMENTO"

        return "ID_REGISTRO"

    # -----------------------------
    # GROUP BY
    # -----------------------------
    def _extract_group_by(self, texto):
        match = re.search(r"(?:por|segun|por\s+el|por\s+la|distribucion\s+de)\s+([a-zA-Záéíóú]+)", texto)
        if match:
            palabra = match.group(1)
            if palabra in self.sinonimos:
                return self.sinonimos[palabra]

        if any(w in texto for w in ["grafico", "histograma", "sectores", "barras"]):
            for palabra in ["sexo", "centro", "residencia", "edad"]:
                if palabra in texto:
                    return self.sinonimos.get(palabra)

        return None

    # -----------------------------
    # LIMIT
    # -----------------------------
    def _extract_limit(self, texto):
        match = re.search(r"top\s*(\d+)", texto)
        return int(match.group(1)) if match else None

    # -----------------------------
    # FILTROS (🔥 FIX DEFINITIVO)
    # -----------------------------
    def _extract_filters(self, texto, source):
        extracted = []
        texto_original = texto

        # ---------------- NORMALIZAR OPERADORES ----------------
        texto = re.sub(r"menor\s+que|menor\s+a|menor\s+de|debajo\s+de|menor", "<", texto)
        texto = re.sub(r"mayor\s+que|mayor\s+a|mayor\s+de|encima\s+de|mayor", ">", texto)
        texto = re.sub(r"igual\s+a|igual", "=", texto)

        # ---------------- FILTROS NUMÉRICOS ----------------
        sinonimos_ordenados = sorted(self.sinonimos.items(), key=lambda x: len(x[0]), reverse=True)

        for palabra, col_real in sinonimos_ordenados:
            pattern = rf"{palabra}\s*(<|>|=|<=|>=)\s*(\d+(?:\.\d+)?)"
            match = re.search(pattern, texto)

            if match:
                op = match.group(1)
                val = match.group(2)

                extracted.append({
                    "col": col_real,
                    "op": "==" if op == "=" else op,
                    "val": float(val)
                })

                texto = texto.replace(match.group(0), "")

        # 🔥 EXTRA: detectar "< 60" sin variable explícita
        match_extra = re.search(r"(<|>|<=|>=)\s*(\d+(?:\.\d+)?)", texto)
        if match_extra and not extracted:
            op = match_extra.group(1)
            val = match_extra.group(2)

            if "fg" in texto_original or "filtrado" in texto_original:
                extracted.append({
                    "col": "FG_CG",
                    "op": op,
                    "val": float(val)
                })

        # ---------------- SEXO ----------------
        if "hombre" in texto_original:
            extracted.append({"col": "SEXO", "op": "contiene", "val": "hombre"})
        if "mujer" in texto_original:
            extracted.append({"col": "SEXO", "op": "contiene", "val": "mujer"})

        # ---------------- MEDICAMENTOS ----------------
        if source == "Medicamentos" and "top" not in texto_original:
            palabras = texto_original.split()
            stopwords = ["pacientes", "cuantos", "numero", "media", "edad"]

            for p in palabras:
                if len(p) > 4 and p not in stopwords:
                    extracted.append({
                        "col": "MEDICAMENTO",
                        "op": "contiene",
                        "val": p
                    })
                    break

        # ---------------- CENTRO ----------------
        if "centro" in texto_original:
            partes = texto_original.split("centro")
            if len(partes) > 1:
                valor = partes[1].strip().split(" ")[0]
                if valor:
                    extracted.append({
                        "col": "CENTRO",
                        "op": "contiene",
                        "val": valor
                    })

        # ---------------- RESIDENCIA ----------------
        if "residencia" in texto_original:
            partes = texto_original.split("residencia")
            if len(partes) > 1:
                valor = partes[1].strip().split(" ")[0]
                if valor:
                    extracted.append({
                        "col": "RESIDENCIA",
                        "op": "contiene",
                        "val": valor
                    })

        return extracted

    # -----------------------------
    # PARSER PRINCIPAL
    # -----------------------------
    def parse_query(self, pregunta_usuario):
        texto = limpiar_texto(pregunta_usuario.lower())

        source = self._get_target_source(texto)
        operation = self._extract_operation(texto)
        variable = self._extract_variable(texto)
        group_by = self._extract_group_by(texto)
        limit = self._extract_limit(texto)
        filters = self._extract_filters(texto, source)

        # 🔥 TOP FIX
        if limit and variable != "ID_REGISTRO":
            group_by = variable
            operation = "conteo"

        chart_type = self._parse_output_type(texto, has_grouping=(group_by is not None))

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
                "limit": limit or (10 if limit else None)
            }
        }
