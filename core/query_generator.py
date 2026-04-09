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
        """Traduce palabras clave de comparación a símbolos matemáticos."""
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
        
        # Palabras de control que NUNCA deben ser valores de filtro
        control_words = ["grafico", "gráfico", "sectores", "barras", "distribucion", "top", "ranking", "reparto", "por", "histograma"]

        # 1. Filtros Numéricos (FG < 60, etc.)
        for palabra, col_real in self.sinonimos.items():
            pattern = rf"{palabra}\s*(<|>|<=|>=|=)\s*(\d+(?:\.\d+)?)"
            matches = re.finditer(pattern, t_clean)
            for m in matches:
                op = m.group(1) if m.group(1) != "=" else "=="
                filters.append({"col": col_real, "op": op, "val": float(m.group(2))})
                t_clean = t_clean.replace(m.group(0), " ")

        # 2. MAPEO CLÍNICO AVANZADO (Riesgo_FG y Sinónimos de Ajuste/Toxicidad)
        mapeo_clinico = {
            # Valores directos
            "leve": ("RIESGO_FG", "LEVE"),
            "moderado": ("RIESGO_FG", "MODERADO"),
            "grave": ("RIESGO_FG", "GRAVE"),
            "critico": ("RIESGO_FG", "CRITICO"),
            "critica": ("RIESGO_FG", "CRITICO"),
            # Sinónimos para LEVE
            "precaucion": ("RIESGO_FG", "LEVE"),
            "monitorizacion": ("RIESGO_FG", "LEVE"),
            # Sinónimos para MODERADO
            "ajuste de dosis": ("RIESGO_FG", "MODERADO"),
            "requiere ajuste": ("RIESGO_FG", "MODERADO"),
            "necesita ajuste": ("RIESGO_FG", "MODERADO"),
            "ajuste de intervalo": ("RIESGO_FG", "MODERADO"),
            # Sinónimos para GRAVE
            "toxicidad": ("RIESGO_FG", "GRAVE"),
            # Sinónimos para CRITICO
            "contraindicado": ("RIESGO_FG", "CRITICO"),
            "contraindicacion": ("RIESGO_FG", "CRITICO"),
            # Categorías base
            "hombre": ("SEXO", "HOMBRE"), "hombres": ("SEXO", "HOMBRE"),
            "mujer": ("SEXO", "MUJER"), "mujeres": ("SEXO", "MUJER"),
            "residencia": ("RESIDENCIA", "SI"), "no residencia": ("RESIDENCIA", "NO"),
            "nula": ("ACEPTACION_MAP", "NULA"), "parcial": ("ACEPTACION_MAP", "PARCIAL"),
            "total": ("ACEPTACION_MAP", "TOTAL")
        }
        
        for palabra, (col, valor) in mapeo_clinico.items():
            if palabra in t_clean:
                filters.append({"col": col, "op": "==", "val": valor})
                # No reemplazamos por espacio aquí para permitir que se detecten varios términos clínicos

        # 3. Filtro de CENTRO
        centro_match = re.search(r"centro\s+([a-zA-Z0-9áéíóú]+)", t_clean)
        if centro_match:
            val_centro = centro_match.group(1).strip().upper()
            filters.append({"col": "CENTRO", "op": "contiene", "val": val_centro})
            t_clean = t_clean.replace(centro_match.group(0), " ")

        # 4. Filtro de MEDICAMENTO (Protegido contra términos clínicos y control)
        if source == "Medicamentos" and not any(w in t_clean for w in ["top", "ranking", "mas frecuentes", "distribucion", "reparto"]):
            stopwords = ["cuantos", "pacientes", "toman", "tienen", "del", "en", "el", "la", "centro", "media", "edad", "sexo", "que", "hay", "con", "medicamentos", "medicamento", "riesgo", "ajuste", "dosis", "necesitan", "requieren"]
            palabras = t_clean.split()
            for p in palabras:
                # Evitamos que palabras ya mapeadas en mapeo_clinico entren como medicamento
                if len(p) > 3 and p not in stopwords and p not in control_words and p not in self.sinonimos and not any(p in k for k in mapeo_clinico):
                    if not any(f["val"] == p.upper() for f in filters):
                        filters.append({"col": "MEDICAMENTO", "op": "contiene", "val": p.upper()})
        
        return filters

    def _extract_group_by(self, texto):
        """Detecta sobre qué columna agrupar para gráficos."""
        match = re.search(r"(?:por|segun|por\s+el|por\s+la|distribucion\s+de|reparto\s+de|histograma\s+de|grafico\s+de)\s+([a-zA-Záéíóú]+)", texto)
        if match:
            palabra = match.group(1)
            if palabra in self.sinonimos: return self.sinonimos[palabra]
            if "medicamento" in palabra: return "MEDICAMENTO"
            if "riesgo" in palabra: return "RIESGO_FG"

        if any(w in texto for w in ["grafico", "gráfico", "visualizar", "barras", "reparto", "distribucion", "histograma", "sectores"]):
            for palabra in ["edad", "sexo", "centro", "residencia", "medicamento", "medicamentos", "riesgo", "fg"]:
                if palabra in texto:
                    if "medicamento" in palabra: return "MEDICAMENTO"
                    if "riesgo" in palabra: return "RIESGO_FG"
                    if "fg" in palabra: return "FG_CG"
                    return self.sinonimos.get(palabra) if palabra in self.sinonimos else palabra.upper()
        return None

    def parse_query(self, pregunta_usuario):
        texto_base = limpiar_texto(pregunta_usuario.lower())
        texto = self._normalizar_operadores(texto_base)
        
        source = self._get_target_source(texto)
        # Forzar fuente Medicamentos si hay términos clínicos específicos
        if any(w in texto for w in ["ajuste", "toxicidad", "contraindicado", "precaucion", "riesgo"]):
            source = "Medicamentos"

        operation = self._extract_operation(texto)
        group_by = self._extract_group_by(texto)
        filters = self._extract_all_filters(texto, source)
        
        limit_match = re.search(r"(?:top|ranking)\s*(\d+)", texto)
        limit_val = int(limit_match.group(1)) if limit_match else None
        
        variable = "ID_REGISTRO"
        
        # Blindaje: Si la columna es group_by, no debe estar como filtro de valor
        filters = [f for f in filters if f["col"] != group_by]
        
        if source == "Medicamentos":
            variable = "MEDICAMENTO"
            if limit_val or "medicamento" in texto or group_by:
                if not group_by: group_by = "MEDICAMENTO"
                operation = "conteo"
        
        elif operation == "media":
            if "edad" in texto: variable = "EDAD"
            elif any(w in texto for w in ["fg", "filtrado", "glomerular"]): variable = "FG_CG"

        chart_type = "kpi"
        if group_by or limit_val:
            chart_type = "bar"
            if any(w in texto for w in ["sectores", "quesito", "pie", "proporcion", "reparto"]) or group_by in ["SEXO", "RESIDENCIA", "RIESGO_FG", "ADECUACION"]:
                chart_type = "pie"

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
                "limit": limit_val if limit_val else (10 if group_by else None)
            }
        }
