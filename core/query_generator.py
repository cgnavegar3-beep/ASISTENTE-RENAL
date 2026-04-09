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

    def _normalizar_operadores(self, texto):
        mapeo = {
            r"\bmenor\s+que\b": "<", r"\bmenor\s+a\b": "<", r"\binferior\s+a\b": "<",
            r"\bmayor\s+que\b": ">", r"\bmayor\s+a\b": ">", r"\bsuperior\s+a\b": ">",
            r"\bigual\s+a\b": "=", r"\bigual\b": "="
        }
        for patron, simbolo in mapeo.items():
            texto = re.sub(patron, simbolo, texto)
        return texto

    def _extract_all_filters(self, texto, source):
        filters = []
        t_clean = " " + texto.lower() + " "
        
        # 1. LÓGICA DE EQUIVALENCIAS (Tu petición específica)
        # Mapeamos la palabra del usuario al valor que debe buscar en FG_CG
        equivalencias = {
            "precaucion": "LEVE",
            "ajuste de dosis": "MODERADO",
            "ajuste": "MODERADO",
            "toxicidad": "GRAVE",
            "contraindicado": "CRITICO",
            "contraindicados": "CRITICO",
            "leve": "LEVE",
            "moderado": "MODERADO",
            "grave": "GRAVE",
            "critico": "CRITICO",
            "crítico": "CRITICO"
        }

        # Verificamos si en la frase aparece alguna de estas palabras
        for palabra, valor_filtro in equivalencias.items():
            if palabra in t_clean:
                # IMPORTANTE: Filtramos en la columna FG_CG como pediste
                filters.append({"col": "FG_CG", "op": "==", "val": valor_filtro})

        # 2. Filtros Numéricos (Edad, etc.)
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

        # 4. Filtro de MEDICAMENTO (Evitar que "toxicidad" o "ajuste" se confundan con nombres)
        if source == "Medicamentos":
            stopwords = ["cuantos", "pacientes", "toman", "tienen", "centro", "edad", "riesgo", "hay", "con", "medicamento"]
            palabras = t_clean.split()
            for p in palabras:
                if len(p) > 3 and p not in stopwords and p not in equivalencias and p not in self.sinonimos:
                    if not any(f["val"] == p.upper() for f in filters):
                        filters.append({"col": "MEDICAMENTO", "op": "contiene", "val": p.upper()})
        
        return filters

    def parse_query(self, pregunta_usuario):
        texto = self._normalizar_operadores(limpiar_texto(pregunta_usuario.lower()))
        source = self._get_target_source(texto)
        
        # Si la pregunta incluye términos de riesgo, forzar fuente Medicamentos
        terminos_riesgo = ["riesgo", "leve", "moderado", "grave", "critico", "precaucion", "ajuste", "toxicidad", "contraindicado"]
        if any(w in texto for w in terminos_riesgo):
            source = "Medicamentos"

        filters = self._extract_all_filters(texto, source)
        
        # Para que el conteo funcione, target_col debe ser una columna que SIEMPRE tenga datos.
        # Al filtrar por FG_CG == "LEVE", contaremos cuántas filas (medicamentos) cumplen eso.
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
