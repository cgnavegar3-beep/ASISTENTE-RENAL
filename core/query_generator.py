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
            "medicamento", "farmaco", "fármaco", "toman", "tienen", "toma", "tiene", 
            "prescrito", "enalapril", "metformina", "alopurinol", "riesgo", 
            "adecuacion", "ajuste", "toxicidad", "contraindicado", "hay", 
            "necesitan", "precisan", "producen", "requieren", "estan", "están"
        ]
        if any(w in texto for w in med_keywords):
            return "Medicamentos"
        return "Validaciones"

    def _extract_operation(self, texto):
        if any(w in texto for w in ["media", "promedio", "avg"]): return "media"
        if any(w in texto for w in ["%", "porcentaje", "proporcion"]): return "porcentaje"
        return "conteo"

    def _normalizar_operadores(self, texto):
        mapeo = {
            r"\bmenor\s+que\b": "<", r"\bmenor\s+a\b": "<", r"\binferior\s+a\b": "<",
            r"\bdebajo\s+de\b": "<", r"\bmenor\b": "<",
            r"\bmayor\s+que\b": ">", r"\bmayor\s+a\b": ">", r"\bsuperior\s+a\b": ">",
            r"\bencima\s+de\b": ">", r"\bmayor\b": ">",
            r"\bigual\s+a\b": "=", r"\bigual\b": "="
        }
        for patron, simbolo in mapeo.items():
            texto = re.sub(patron, simbolo, texto)
        return texto

    def _extract_all_filters(self, texto, source):
        filters = []
        t_clean = " " + texto.lower() + " "
        control_words = ["grafico", "gráfico", "sectores", "barras", "distribucion", "top", "ranking", "reparto", "por", "histograma", "%", "porcentaje"]

        for palabra, col_real in self.sinonimos.items():
            pattern = rf"{palabra}\s*(<|>|<=|>=|=)\s*(\d+(?:\.\d+)?)"
            matches = re.finditer(pattern, t_clean)
            for m in matches:
                op = m.group(1) if m.group(1) != "=" else "=="
                filters.append({"col": col_real, "op": op, "val": float(m.group(2))})
                t_clean = t_clean.replace(m.group(0), " ")

        mapeo_categorias = {
            "hombre": ("SEXO", "HOMBRE"), "hombres": ("SEXO", "HOMBRE"),
            "mujer": ("SEXO", "MUJER"), "mujeres": ("SEXO", "MUJER"),
            "residencia": ("RESIDENCIA", "SI"), "no residencia": ("RESIDENCIA", "NO"),
            "precaucion": ("RIESGO_CG", "LEVE"), "precaución": ("RIESGO_CG", "LEVE"), "leve": ("RIESGO_CG", "LEVE"),
            "ajuste de dosis": ("RIESGO_CG", "MODERADO"), "ajuste": ("RIESGO_CG", "MODERADO"), "moderado": ("RIESGO_CG", "MODERADO"),
            "toxicidad": ("RIESGO_CG", "GRAVE"), "riesgo de toxicidad": ("RIESGO_CG", "GRAVE"), "grave": ("RIESGO_CG", "GRAVE"),
            "contraindicado": ("RIESGO_CG", "CRITICO"), "contraindicados": ("RIESGO_CG", "CRITICO"),
            "critico": ("RIESGO_CG", "CRITICO"), "crítico": ("RIESGO_CG", "CRITICO"),
            "nula": ("ACEPTACION_MAP", "NULA"), "parcial": ("ACEPTACION_MAP", "PARCIAL"), "total": ("ACEPTACION_MAP", "TOTAL")
        }
        
        for palabra, (col, valor) in mapeo_categorias.items():
            if re.search(rf"\b{palabra}\b", t_clean):
                filters.append({"col": col, "op": "==", "val": valor})
                t_clean = t_clean.replace(palabra, " ")

        centro_match = re.search(r"centro\s+([a-zA-Z0-9áéíóú]+)", t_clean)
        if centro_match:
            val_centro = centro_match.group(1).strip().upper()
            filters.append({"col": "CENTRO", "op": "contiene", "val": val_centro})
            t_clean = t_clean.replace(centro_match.group(0), " ")

        if source == "Medicamentos" and not any(w in t_clean for w in ["top", "ranking", "distribucion"]):
            stopwords = ["cuantos", "pacientes", "toman", "tienen", "del", "en", "el", "la", "centro", "media", "edad", "sexo", "que", "hay", "con", "medicamentos", "medicamento", "riesgo"]
            palabras = t_clean.split()
            for p in palabras:
                if len(p) > 3 and p not in stopwords and p not in control_words and p not in self.sinonimos and p not in mapeo_categorias:
                    if not any(f["val"] == p.upper() for f in filters):
                        filters.append({"col": "MEDICAMENTO", "op": "contiene", "val": p.upper()})
        return filters

    def _extract_group_by(
