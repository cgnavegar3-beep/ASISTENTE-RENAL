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
        
        control_words = ["grafico", "gráfico", "sectores", "barras", "distribucion", "top", "ranking", "reparto", "por", "histograma"]
        
        # 1. Filtros Numéricos
        for palabra, col_real in self.sinonimos.items():
            pattern = rf"{palabra}\s*(<|>|<=|>=|=)\s*(\d+(?:\.\d+)?)"
            matches = re.finditer(pattern, t_clean)
            for m in matches:
                op = m.group(1) if m.group(1) != "=" else "=="
                filters.append({"col": col_real, "op": op, "val": float(m.group(2))})
                t_clean = t_clean.replace(m.group(0), " ")

        # 2. FILTROS CATEGÓRICOS (Sincronizados con mapeo clínico)
        mapeo_categorias = {
            "hombre": ("SEXO", "HOMBRE"), "hombres": ("SEXO", "HOMBRE"),
            "mujer": ("SEXO", "MUJER"), "mujeres": ("SEXO", "MUJER"),
            "residencia": ("RESIDENCIA", "SI"), "no residencia": ("RESIDENCIA", "NO"),
            "leve": ("RIESGO_CG", "LEVE"), "precaucion": ("RIESGO_CG", "LEVE"),
            "moderado": ("RIESGO_CG", "MODERADO"), "ajuste": ("RIESGO_CG", "MODERADO"),
            "grave": ("RIESGO_CG", "GRAVE"), "toxicidad": ("RIESGO_CG", "GRAVE"),
            "critico": ("RIESGO_CG", "CRITICO"), "crítico": ("RIESGO_CG", "CRITICO"), "contraindicado": ("RIESGO_CG", "CRITICO")
        }
        
        for palabra, (col, valor) in mapeo_categorias.items():
            if re.search(rf"\b{palabra}\b", t_clean):
                filters.append({"col": col, "op": "==", "val": valor})
                t_clean = t_clean.replace(palabra, " ")

        # 3. Filtro de CENTRO
        centro_match = re.search(r"centro\s+([a-zA-Z0-9áéíóú]+)", t_clean)
        if centro_match:
            val_centro = centro_match.group(1).strip().upper()
            filters.append({"col": "CENTRO", "op": "contiene", "val": val_centro})
            t_clean = t_clean.replace(centro_match.group(0), " ")

        # 4. Filtro de MEDICAMENTO (Refuerzo de Stopwords)
        if source == "Medicamentos" and not any(w in t_clean for w in ["top", "ranking", "distribucion"]):
            stopwords = ["cuantos", "pacientes", "toman", "tienen", "del", "en", "el", "la", "centro", "media", "edad", "sexo", "que", "hay", "con", "medicamentos", "medicamento", "riesgo", "necesitan", "precisan", "requieren", "estan", "están"]
            palabras = t_clean.split()
            for p in palabras:
                p_clean = p.strip(",.() ")
                if len(p_clean) > 3 and p_clean not in stopwords and p_clean not in control_words and p_clean not in self.sinonimos:
                    if not any(f["col"] == "RIESGO_CG" for f in filters): # Si no es riesgo, es medicamento
                        filters.append({"col": "MEDICAMENTO", "op": "contiene", "val": p_clean.upper()})
        
        return filters

    def _extract_group_by(self, texto):
        # Prioridad a Riesgo
        if "riesgo" in texto: return "RIESGO_CG"
        
        match = re.search(r"(?:por|segun|distribucion\s+de|reparto\s+de|histograma\s+de)\s+([a-zA-Záéíóú]+)", texto)
        if match:
            palabra = match.group(1)
            if palabra in self.sinonimos: return self.sinonimos[palabra]
            if "medicamento" in palabra: return "MEDICAMENTO"

        for palabra in ["edad", "sexo", "centro", "residencia", "medicamento", "fg", "filtrado"]:
            if palabra in texto:
                if "fg" in palabra or "filtrado" in palabra: return "FG_CG"
                if "medicamento" in palabra: return "MEDICAMENTO"
                return self.sinonimos.get(palabra, palabra.upper())
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
            if limit_val or group_by:
                if not group_by: group_by = "MEDICAMENTO"
                operation = "conteo"
        
        elif operation == "media":
            if "edad" in texto: variable = "EDAD"
            elif any(w in texto for w in ["fg", "filtrado"]): variable = "FG_CG"

        chart_type = "kpi"
        if group_by or limit_val:
            chart_type = "bar"
            if any(w in texto for w in ["sectores", "quesito", "pie", "proporcion", "reparto"]) or group_by in ["SEXO", "RESIDENCIA", "RIESGO_CG"]:
                chart_type = "pie"

        # --- ETIQUETAS CLÍNICAS: SINCRONIZACIÓN TOTAL CON ENGINE ---
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
