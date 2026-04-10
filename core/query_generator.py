import re
from core.catalog import SCHEMA
from core.dictionary import SINONIMOS_COLUMNAS
from core.normalizer import limpiar_texto

class QueryGenerator:
    def __init__(self):
        self.schema = SCHEMA
        self.sinonimos = SINONIMOS_COLUMNAS

    def _get_target_source(self, texto):
        med_keywords = ["medicamento", "farmaco", "fármaco", "toman", "tienen", "toma", "tiene", "prescrito", "enalapril", "metformina"]
        terminos_clinicos = ["precaucion", "ajuste", "toxicidad", "contraindicado", "contraindicados", "leve", "moderado", "grave", "critico"]
        if any(w in texto for w in med_keywords) or any(w in texto for w in terminos_clinicos):
            return "Medicamentos"
        return "Validaciones"

    def _extract_operation(self, texto):
        if any(w in texto for w in ["media", "promedio", "avg"]): return "media"
        if any(w in texto for w in ["%", "porcentaje", "proporcion"]): return "porcentaje"
        return "conteo"

    # --- NUEVA FUNCIÓN PARA TRADUCIR TEXTO A SÍMBOLOS ---
    def _normalizar_operadores_texto(self, texto):
        # Traduce "mayor que 60" a "> 60", etc.
        texto = re.sub(r"\b(mayor|superior|mas\s+de|encima\s+de)\s*(que|a)?", ">", texto)
        texto = re.sub(r"\b(menor|inferior|menos\s+de|debajo\s+de)\s*(que|a)?", "<", texto)
        texto = re.sub(r"\b(igual)\s*(a)?", "=", texto)
        return texto

    def _extract_all_filters(self, texto, source):
        filters = []
        # Normalizamos palabras de comparación antes de extraer
        texto_norm = self._normalizar_operadores_texto(texto)
        t_clean = " " + texto_norm.lower() + " "

        # 1. MAPEO DE RIESGOS (Columna riesgo_CG)
        equivalencias = {
            "precaucion": "LEVE", "ajuste de dosis": "MODERADO", "ajuste": "MODERADO",
            "toxicidad": "GRAVE", "contraindicado": "CRITICO", "contraindicados": "CRITICO",
            "leve": "LEVE", "moderado": "MODERADO", "grave": "GRAVE", "critico": "CRITICO"
        }

        for palabra, valor_filtro in equivalencias.items():
            if palabra in t_clean:
                filters.append({"col": "riesgo_CG", "op": "==", "val": str(valor_filtro)})
                t_clean = t_clean.replace(palabra, " ")

        # 2. FILTROS NUMÉRICOS (Ahora detecta > y < generados por la normalización)
        for palabra, col_real in self.sinonimos.items():
            pattern = rf"{palabra}\s*(<|>|<=|>=|=)\s*(\d+(?:\.\d+)?)"
            matches = re.finditer(pattern, t_clean)
            for m in matches:
                op = m.group(1) if m.group(1) != "=" else "=="
                try:
                    filters.append({"col": col_real, "op": op, "val": float(m.group(2))})
                    t_clean = t_clean.replace(m.group(0), " ")
                except: continue

        # 3. FILTRO DE CENTRO Y MEDICAMENTO
        centro_match = re.search(r"centro\s+([a-zA-Z0-9áéíóú]+)", t_clean)
        if centro_match:
            filters.append({"col": "CENTRO", "op": "contiene", "val": centro_match.group(1).strip().upper()})

        if source == "Medicamentos":
            stopwords = ["cuantos", "pacientes", "toman", "tienen", "del", "en", "el", "la", "centro", "media", "edad", "sexo", "que", "hay", "con", "riesgo"]
            for p in t_clean.split():
                if len(p) > 3 and p not in stopwords and p not in self.sinonimos and p not in equivalencias:
                    if not any(f["val"] == p.upper() for f in filters):
                        filters.append({"col": "MEDICAMENTO", "op": "contiene", "val": p.upper()})
        
        return filters

    def parse_query(self, pregunta_usuario):
        texto = limpiar_texto(pregunta_usuario.lower())
        source = self._get_target_source(texto)
        filters = self._extract_all_filters(texto, source)
        
        # LÓGICA DE GRÁFICOS
        group_by = None
        chart_type = "kpi"
        if any(w in texto for w in ["grafico", "gráfico", "histograma", "sectores", "quesito", "distribucion", "por"]):
            chart_type = "bar"
            if any(w in texto for w in ["sectores", "quesito", "pie"]): chart_type = "pie"
            if "histograma" in texto: chart_type = "histogram"
            
            if "centro" in texto: group_by = "CENTRO"
            elif "sexo" in texto: group_by = "SEXO"
            elif "riesgo" in texto or "nivel" in texto: group_by = "riesgo_CG"
            else: group_by = "riesgo_CG"

        # PROTECCIÓN CONTRA ERROR FLOAT
        es_riesgo = any(f["col"] == "riesgo_CG" for f in filters) or group_by == "riesgo_CG"
        
        if es_riesgo:
            operation = "conteo"
            target = "MEDICAMENTO"
        else:
            operation = self._extract_operation(texto)
            target = "MEDICAMENTO" if source == "Medicamentos" else "ID_REGISTRO"
            if operation == "media":
                if "edad" in texto: target = "EDAD"
                elif "fg" in texto: target = "FG_CG"

        return {
            "metadata": {"source": source, "intent": "visual" if group_by else "kpi"},
            "request": {
                "metric": operation,
                "target_col": target,
                "filters": filters,
                "group_by": group_by,
                "chart_type": chart_type,
                "limit": 10 if group_by else None
            }
        }
