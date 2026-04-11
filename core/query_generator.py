import re
from core.catalog import SCHEMA
from core.dictionary import SINONIMOS_COLUMNAS
from core.normalizer import limpiar_texto

class QueryGenerator:
    def __init__(self):
        self.schema = SCHEMA
        self.sinonimos = SINONIMOS_COLUMNAS

    def _get_target_source(self, texto):
        med_keywords = [
            "medicamento", "farmaco", "fármaco",
            "toman", "tienen", "toma", "tiene", 
            "prescrito", "enalapril", "metformina",
            "alopurinol", "riesgo", 
            "adecuacion", "ajuste", "toxicidad",
            "contraindicado", "hay", 
            "necesitan", "precisan", "producen",
            "requieren", "estan", "están"
        ]
        if any(w in texto for w in med_keywords):
            return "Medicamentos"
        return "Validaciones"

    def _extract_operation(self, texto):
        if any(w in texto for w in ["media", "promedio", "avg"]):
            return "media"

        # 🔥 CAMBIO: porcentaje sigue siendo conteo (visual lo decide engine)
        if any(w in texto for w in ["%", "porcentaje", "proporcion"]):
            return "conteo"

        return "conteo"

    def _normalizar_operadores(self, texto):
        mapeo = {
            r"\bmenor\s+que\b": "<",
            r"\bmenor\s+a\b": "<",
            r"\binferior\s+a\b": "<",
            r"\bdebajo\s+de\b": "<",
            r"\bmenor\b": "<",
            r"\bmayor\s+que\b": ">",
            r"\bmayor\s+a\b": ">",
            r"\bsuperior\s+a\b": ">",
            r"\bencima\s+de\b": ">",
            r"\bmayor\b": ">",
            r"\bigual\s+a\b": "=",
            r"\bigual\b": "="
        }
        for patron, simbolo in mapeo.items():
            texto = re.sub(patron, simbolo, texto)
        return texto

    def _extract_all_filters(self, texto, source):
        filters = []
        t_clean = " " + texto.lower() + " "

        control_words = [
            "grafico", "gráfico", "sectores", "barras",
            "distribucion", "top", "ranking", "reparto",
            "por", "histograma"
        ]

        for palabra, col_real in self.sinonimos.items():
            pattern = rf"{palabra}\s*(<|>|<=|>=|=)\s*(\d+(?:\.\d+)?)"
            matches = re.finditer(pattern, t_clean)
            for m in matches:
                op = m.group(1) if m.group(1) != "=" else "=="
                filters.append({
                    "col": col_real,
                    "op": op,
                    "val": float(m.group(2))
                })
                t_clean = t_clean.replace(m.group(0), " ")

        mapeo_categorias = {
            "hombre": ("SEXO", "HOMBRE"),
            "hombres": ("SEXO", "HOMBRE"),
            "mujer": ("SEXO", "MUJER"),
            "mujeres": ("SEXO", "MUJER"),
            "residencia": ("RESIDENCIA", "SI"),
            "no residencia": ("RESIDENCIA", "NO"),
            "precaucion": ("RIESGO_CG", "LEVE"),
            "leve": ("RIESGO_CG", "LEVE"),
            "moderado": ("RIESGO_CG", "MODERADO"),
            "grave": ("RIESGO_CG", "GRAVE"),
            "critico": ("RIESGO_CG", "CRITICO")
        }

        for palabra, (col, valor) in mapeo_categorias.items():
            if re.search(rf"\b{palabra}\b", t_clean):
                filters.append({"col": col, "op": "==", "val": valor})
                t_clean = t_clean.replace(palabra, " ")

        centro_match = re.search(r"centro\s+([a-zA-Z0-9áéíóú]+)", t_clean)
        if centro_match:
            val_centro = centro_match.group(1).strip().upper()
            filters.append({
                "col": "CENTRO",
                "op": "contiene",
                "val": val_centro
            })
            t_clean = t_clean.replace(centro_match.group(0), " ")

        if source == "Medicamentos":
            stopwords = [
                "cuantos", "pacientes", "toman", "tienen", "del",
                "en", "el", "la", "centro", "media", "edad",
                "sexo", "medicamentos", "riesgo"
            ]

            palabras = t_clean.split()
            for p in palabras:
                if len(p) > 3 and p not in stopwords:
                    filters.append({
                        "col": "MEDICAMENTO",
                        "op": "contiene",
                        "val": p.upper()
                    })

        return filters

    def _extract_group_by(self, texto):
        t_tmp = re.sub(r"\b(nivel|categoria|clase|tipo)\s+de\b", "", texto)

        match = re.search(
            r"(?:por|segun|por\s+el|por\s+la|distribucion\s+de|reparto\s+de|histograma\s+de|grafico\s+de)\s+([a-zA-Záéíóú]+)",
            t_tmp
        )

        if match:
            palabra = match.group(1)
            if palabra in self.sinonimos:
                return self.sinonimos[palabra]
            if "medicamento" in palabra:
                return "MEDICAMENTO"
            if "riesgo" in palabra:
                return "RIESGO_CG"

        if any(w in texto for w in ["grafico", "gráfico", "barras", "sectores"]):
            for palabra in ["edad", "sexo", "centro", "medicamento", "riesgo"]:
                if palabra in texto:
                    return palabra.upper()

        return None

    def parse_query(self, pregunta_usuario):
        texto_base = limpiar_texto(pregunta_usuario.lower())
        texto = self._normalizar_operadores(texto_base)

        source = self._get_target_source(texto)
        operation = self._extract_operation(texto)
        group_by = self._extract_group_by(texto)
        filters = self._extract_all_filters(texto, source)

        limit_match = re.search(r"(?:top|ranking)\s*(\d+)", texto)
        limit_val = int(limit_match.group(1)) if limit_match else None

        variable = "ID_REGISTRO"

        filters = [f for f in filters if f["col"] != group_by]

        # 🔥 MEDICAMENTOS
        if source == "Medicamentos":
            variable = "MEDICAMENTO"
            if not group_by:
                group_by = "MEDICAMENTO"
            operation = "conteo"

        elif operation == "media":
            if "edad" in texto:
                variable = "EDAD"
            elif "fg" in texto:
                variable = "FG_CG"

        # 🔥 NUEVO: DETECCIÓN DE %
        chart_type = "kpi"

        if group_by or limit_val:
            chart_type = "bar"

        if any(w in texto for w in ["%", "porcentaje", "proporcion", "reparto"]):
            if group_by:
                chart_type = "pie"
            elif "medicamento" in texto:
                group_by = "MEDICAMENTO"
                chart_type = "pie"
            elif "sexo" in texto:
                group_by = "SEXO"
                chart_type = "pie"
            elif "riesgo" in texto:
                group_by = "RIESGO_CG"
                chart_type = "pie"

        label_map = None
        if group_by == "RIESGO_CG":
            label_map = {
                "LEVE": "LEVE (Precaución)",
                "MODERADO": "MODERADO (Ajuste)",
                "GRAVE": "GRAVE (Toxicidad)",
                "CRITICO": "CRITICO (Contraindicado)"
            }

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
                "label_map": label_map,
                "limit": limit_val if limit_val else (10 if group_by else None)
            }
        }
