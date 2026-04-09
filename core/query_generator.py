import re
from core.catalog import SCHEMA
from core.dictionary import SINONIMOS_COLUMNAS
from core.normalizer import limpiar_texto

class QueryGenerator:
    def __init__(self):
        self.schema = SCHEMA
        self.sinonimos = SINONIMOS_COLUMNAS

    def _get_target_source(self, texto):
        med_keywords = ["medicamento", "farmaco", "fármaco", "toman", "tienen", "toma", "tiene", "prescrito", "enalapril", "metformina", "alopurinol"]
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

    # --- EXTRACCIÓN DE FILTROS REFORZADA ---
    def _extract_all_filters(self, texto, source):
        filters = []
        t_clean = " " + texto.lower() + " "
        control_words = ["grafico", "gráfico", "sectores", "barras", "distribucion", "top", "ranking", "reparto", "por"]

        # 1. TRADUCCIÓN CLÍNICA (Mapeo solicitado: término -> valor real en RIESGO_FG)
        mapeo_riesgos = {
            "precaucion": "LEVE",
            "ajuste de dosis": "MODERADO",
            "necesitan ajuste": "MODERADO",
            "requieren ajuste": "MODERADO",
            "toxicidad": "GRAVE",
            "contraindicado": "CRITICO",
            "contraindicacion": "CRITICO",
            "leve": "LEVE",
            "moderado": "MODERADO",
            "grave": "GRAVE",
            "critico": "CRITICO",
            "crítico": "CRITICO"
        }

        for palabra, valor_excel in mapeo_riesgos.items():
            if palabra in t_clean:
                filters.append({"col": "RIESGO_FG", "op": "==", "val": valor_excel})

        # 2. Filtros Numéricos (Edad, FG, etc.)
        for palabra, col_real in self.sinonimos.items():
            pattern = rf"{palabra}\s*(<|>|<=|>=|=)\s*(\d+(?:\.\d+)?)"
            matches = re.finditer(pattern, t_clean)
            for m in matches:
                op = m.group(1) if m.group(1) != "=" else "=="
                filters.append({"col": col_real, "op": op, "val": float(m.group(2))})
                t_clean = t_clean.replace(m.group(0), " ")

        # 3. Filtro de CENTRO
        centro_match = re.search(r"centro\s+([a-zA-Z0-9áéíóú]+)", t_clean)
        if centro_match:
            val_centro = centro_match.group(1).strip().upper()
            filters.append({"col": "CENTRO", "op": "contiene", "val": val_centro})

        # 4. Filtro de MEDICAMENTO (Blindado)
        if source == "Medicamentos":
            stopwords = ["cuantos", "pacientes", "toman", "tienen", "centro", "edad", "riesgo", "hay", "con", "medicamento"]
            palabras = t_clean.split()
            for p in palabras:
                if len(p) > 3 and p not in stopwords and p not in control_words and p not in self.sinonimos and p not in mapeo_riesgos:
                    if not any(f["val"] == p.upper() for f in filters):
                        filters.append({"col": "MEDICAMENTO", "op": "contiene", "val": p.upper()})
        
        return filters

    def parse_query(self, pregunta_usuario):
        texto = self._normalizar_operadores(limpiar_texto(pregunta_usuario.lower()))
        source = self._get_target_source(texto)
        
        # Forzado de fuente si hay términos de riesgo
        if any(w in texto for w in ["riesgo", "precaucion", "ajuste", "toxicidad", "contraindicado", "leve", "moderado", "grave", "critico"]):
            source = "Medicamentos"

        filters = self._extract_all_filters(texto, source)
        
        return {
            "metadata": {"source": source, "intent": "kpi"},
            "request": {
                "metric": "conteo",
                "target_col": "MEDICAMENTO" if source == "Medicamentos" else "ID_REGISTRO",
                "filters": filters,
                "group_by": None,
                "limit": 10
            }
        }
