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
            "criticos": ("RIESGO_CG", "CRITICO"), "críticos": ("RIESGO_CG", "CRITICO"),
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

        if source == "Medicamentos" and not any(w in t_clean for w in ["top", "ranking", "mas frecuentes", "distribucion", "reparto"]):
            stopwords = ["cuantos", "pacientes", "toman", "tienen", "del", "en", "el", "la", "centro", "media", "edad", "sexo", "que", "hay", "con", "medicamentos", "medicamento", "riesgo", "necesitan", "precisan", "requieren", "estan", "nivel", "categoria", "tipo", "grafico", "gráfico"]
            palabras = t_clean.split()
            for p in palabras:
                if len(p) > 3 and p not in stopwords and p not in control_words and p not in self.sinonimos and p not in mapeo_categorias:
                    if not any(f["val"] == p.upper() for f in filters):
                        filters.append({"col": "MEDICAMENTO", "op": "contiene", "val": p.upper()})
        
        return filters

    def _extract_group_by(self, texto):
        t_tmp = re.sub(r"\b(nivel|categoria|clase|tipo)\s+de\b", "", texto)
        match = re.search(r"(?:por|segun|por\s+el|por\s+la|distribucion\s+de|reparto\s+de|histograma\s+de|grafico\s+de)\s+([a-zA-Záéíóú]+)", t_tmp)
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
        if source == "Medicamentos": variable = "MEDICAMENTO"

        # --- MEJORA: Prioridad de KPI sobre Gráfico ---
        # Si pregunta "cuantos" y hay un filtro (ej. alopurinol), anulamos el group_by automático
        es_pregunta_conteo = any(w in texto for w in ["cuantos", "cuántos", "numero de", "total"])
        
        if source == "Medicamentos":
            # Si pide conteo total o hay filtros específicos, no agrupamos por medicamento
            if es_pregunta_conteo or (len(filters) > 0 and not limit_val and "distribucion" not in texto):
                group_by = None
                operation = "conteo"
            # Si no es conteo directo, mantenemos el comportamiento de ranking
            elif limit_val or "medicamento" in texto or group_by:
                if not group_by: group_by = "MEDICAMENTO"
                operation = "conteo"

        elif operation == "media":
            if "edad" in texto: variable = "EDAD"
            elif any(w in texto for w in ["fg", "filtrado", "glomerular"]): variable = "FG_CG"

        # --- MEJORA: Relación % = Sectores y gestión de KPI ---
        chart_type = "kpi"
        if group_by or limit_val:
            chart_type = "bar"
            # Si la operación es porcentaje o pide sectores, forzamos PIE
            if operation == "porcentaje" or any(w in texto for w in ["sectores", "quesito", "pie", "proporcion", "reparto"]) or group_by in ["SEXO", "RESIDENCIA", "RIESGO_CG", "ADECUACION"]:
                chart_type = "pie"

        filters = [f for f in filters if f["col"] != group_by]

        label_map = None
        if group_by == "RIESGO_CG":
            label_map = {"LEVE": "LEVE (Precaución)", "MODERADO": "MODERADO (Ajuste de dosis)", "GRAVE": "GRAVE (Riesgo de toxicidad)", "CRITICO": "CRITICO (Contraindicado)"}

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
                "limit": limit_val # Eliminado el predeterminado de 10
            }
        }
