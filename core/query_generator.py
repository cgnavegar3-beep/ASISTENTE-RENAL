import re
from core.catalog import SCHEMA
from core.dictionary import SINONIMOS_COLUMNAS
from core.normalizer import limpiar_texto

class QueryGenerator:
    def __init__(self):
        self.schema = SCHEMA
        self.sinonimos = SINONIMOS_COLUMNAS

    def _get_target_source(self, texto):
        # Refuerzo total de verbos y términos de riesgo (Objetivo 2)
        med_keywords = [
            "medicamento", "farmaco", "fármaco", "toman", "tienen", "toma", "tiene", 
            "prescrito", "enalapril", "metformina", "alopurinol", "riesgo", 
            "adecuacion", "ajuste", "toxicidad", "contraindicado", "hay", 
            "necesitan", "precisan", "producen", "requieren", "estan", "están", "dan"
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

    def _analizar_riesgo_maestro(self, texto):
        """
        Objetivo 1 y 3: Centralización de lógica de riesgo.
        Detecta categorías sin destruir tokens del texto original.
        """
        mapeo_riesgo = {
            "LEVE": r"\b(precauci[oó]n|leve)\b",
            "MODERADO": r"\b(ajuste(\s+de\s+dosis)?|moderado)\b",
            "GRAVE": r"\b(toxicidad|riesgo\s+de\s+toxicidad|grave)\b",
            "CRITICO": r"\b(contraindicado[s]?|cr[ií]tico[s]?)\b"
        }
        
        for categoria, patron in mapeo_riesgo.items():
            if re.search(patron, texto, re.IGNORECASE):
                return {"col": "RIESGO_CG", "op": "==", "val": categoria}
        return None

    def _extract_all_filters(self, texto, source):
        filters = []
        t_clean = " " + texto.lower() + " "
        
        control_words = ["grafico", "gráfico", "sectores", "barras", "distribucion", "top", "ranking", "reparto", "por", "histograma"]

        # A. Prioridad: Capa de Riesgo (Objetivo 4: Unificación Semántica)
        filtro_riesgo = self._analizar_riesgo_maestro(t_clean)
        if filtro_riesgo:
            filters.append(filtro_riesgo)

        # 1. Filtros Numéricos (FG < 60, etc.)
        for palabra, col_real in self.sinonimos.items():
            pattern = rf"{palabra}\s*(<|>|<=|>=|=)\s*(\d+(?:\.\d+)?)"
            matches = re.finditer(pattern, t_clean)
            for m in matches:
                op = m.group(1) if m.group(1) != "=" else "=="
                filters.append({"col": col_real, "op": op, "val": float(m.group(2))})
                t_clean = t_clean.replace(m.group(0), " ")

        # 2. FILTROS CATEGÓRICOS (Restantes: Sexo, Residencia, etc.)
        mapeo_restante = {
            "hombre": ("SEXO", "HOMBRE"), "hombres": ("SEXO", "HOMBRE"),
            "mujer": ("SEXO", "MUJER"), "mujeres": ("SEXO", "MUJER"),
            "residencia": ("RESIDENCIA", "SI"), "no residencia": ("RESIDENCIA", "NO"),
            "nula": ("ACEPTACION_MAP", "NULA"), "parcial": ("ACEPTACION_MAP", "PARCIAL"), 
            "total": ("ACEPTACION_MAP", "TOTAL")
        }
        
        for palabra, (col, valor) in mapeo_restante.items():
            if re.search(rf"\b{palabra}\b", t_clean):
                filters.append({"col": col, "op": "==", "val": valor})
                t_clean = t_clean.replace(palabra, " ")

        # 3. Filtro de CENTRO
        centro_match = re.search(r"centro\s+([a-zA-Z0-9áéíóú]+)", t_clean)
        if centro_match:
            val_centro = centro_match.group(1).strip().upper()
            filters.append({"col": "CENTRO", "op": "contiene", "val": val_centro})
            t_clean = t_clean.replace(centro_match.group(0), " ")

        # 4. Filtro de MEDICAMENTO
        if source == "Medicamentos" and not any(w in t_clean for w in ["top", "ranking", "mas frecuentes", "distribucion", "reparto"]):
            stopwords = ["cuantos", "pacientes", "toman", "tienen", "del", "en", "el", "la", "centro", "media", "edad", "sexo", "que", "hay", "con", "medicamentos", "medicamento", "riesgo", "necesitan", "precisan", "requieren", "estan", "producen", "dan"]
            palabras = t_clean.split()
            for p in palabras:
                if len(p) > 3 and p not in stopwords and p not in control_words and p not in self.sinonimos and p not in mapeo_restante:
                    # Evitar que términos de riesgo ya capturados se tomen como nombre de medicamento
                    if not filtro_riesgo or p.upper() not in ["LEVE", "MODERADO", "GRAVE", "CRITICO"]:
                        if not any(f["val"] == p.upper() for f in filters):
                            filters.append({"col": "MEDICAMENTO", "op": "contiene", "val": p.upper()})
        
        return filters

    def _extract_group_by(self, texto):
        match = re.search(r"(?:por|segun|por\s+el|por\s+la|distribucion\s+de|reparto\s+de|histograma\s+de|grafico\s+de)\s+([a-zA-Záéíóú]+)", texto)
        if match:
            palabra = match.group(1)
            if palabra in self.sinonimos: return self.sinonimos[palabra]
            if "medicamento" in palabra: return "MEDICAMENTO"
            if "riesgo" in palabra: return "RIESGO_CG"

        if any(w in texto for w in ["grafico", "gráfico", "visualizar", "barras", "reparto", "distribucion", "histograma", "sectores"]):
            for palabra in ["edad", "sexo", "centro", "residencia", "medicamento", "medicamentos", "riesgo", "fg", "filtrado"]:
                if palabra in texto:
                    if "medicamento" in palabra: return "MEDICAMENTO"
                    if "riesgo" in palabra: return "RIESGO_CG"
                    if "fg" in palabra or "filtrado" in palabra: return "FG_CG"
                    return self.sinonimos.get(palabra) if palabra in self.sinonimos else palabra.upper()
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
        
        if source == "Medicamentos":
            variable = "MEDICAMENTO"
            if limit_val or "medicamento" in texto or "medicamentos" in texto or group_by:
                if not group_by: group_by = "MEDICAMENTO"
                operation = "conteo"
        
        elif operation == "media":
            if "edad" in texto: variable = "EDAD"
            elif any(w in texto for w in ["fg", "filtrado", "glomerular"]): variable = "FG_CG"

        chart_type = "kpi"
        if group_by or limit_val:
            chart_type = "bar"
            if any(w in texto for w in ["sectores", "quesito", "pie", "proporcion", "reparto"]) or group_by in ["SEXO", "RESIDENCIA", "RIESGO_CG", "ADECUACION"]:
                chart_type = "pie"

        # --- ETIQUETAS CLÍNICAS (Objetivo 5: SIEMPRE con equivalencia clínica) ---
        label_map = None
        if group_by == "RIESGO_CG":
            label_map = {
                "LEVE": "LEVE (Precaución)",
                "MODERADO": "MODERADO (Ajuste de dosis)",
                "GRAVE": "GRAVE (Riesgo de toxicidad)",
                "CRITICO": "CRITICO (Contraindicado)"
            }

        return {
            "metadata": {"source": source, "intent": "visual" if chart_type != "kpi" else "kpi"},
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
