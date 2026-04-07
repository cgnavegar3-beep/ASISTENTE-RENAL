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
        if any(w in texto for w in med_keywords):
            return "Medicamentos"
        return "Validaciones"

    def _extract_operation(self, texto):
        if any(w in texto for w in ["media", "promedio", "avg"]): return "media"
        if any(w in texto for w in ["%", "porcentaje", "proporcion"]): return "porcentaje"
        return "conteo"

    # --- EXTRACCIÓN DE FILTROS REFORZADA ---
    def _extract_all_filters(self, texto, source):
        filters = []
        t_clean = " " + texto.lower() + " "

        # 1. Filtros Numéricos (FG < 60, etc.)
        for palabra, col_real in self.sinonimos.items():
            pattern = rf"{palabra}\s*(<|>|<=|>=|=)\s*(\d+(?:\.\d+)?)"
            matches = re.finditer(pattern, t_clean)
            for m in matches:
                op = m.group(1) if m.group(1) != "=" else "=="
                filters.append({"col": col_real, "op": op, "val": float(m.group(2))})
                t_clean = t_clean.replace(m.group(0), " ")

        # 2. Filtro de CENTRO
        centro_match = re.search(r"centro\s+([a-zA-Z0-9áéíóú]+)", t_clean)
        if centro_match:
            val_centro = centro_match.group(1).strip().upper()
            filters.append({"col": "CENTRO", "op": "contiene", "val": val_centro})
            t_clean = t_clean.replace(centro_match.group(0), " ")

        # 3. Filtro de MEDICAMENTO (Específico: ej. 'enalapril')
        # Solo extraemos como filtro si NO es una pregunta de "Top medicamentos"
        if source == "Medicamentos" and not any(w in t_clean for w in ["top", "ranking", "mas frecuentes"]):
            stopwords = ["cuantos", "pacientes", "toman", "tienen", "del", "en", "el", "la", "centro", "media", "edad", "sexo", "que", "hay", "con"]
            palabras = t_clean.split()
            for p in palabras:
                if len(p) > 3 and p not in stopwords and p not in self.sinonimos:
                    if not any(f["val"] == p.upper() for f in filters):
                        filters.append({"col": "MEDICAMENTO", "op": "contiene", "val": p.upper()})
        
        return filters

    # ---------------------------------------------------------
    # PARSER PRINCIPAL CON LÓGICA TOP N
    # ---------------------------------------------------------
    def parse_query(self, pregunta_usuario):
        texto = limpiar_texto(pregunta_usuario.lower())
        
        source = self._get_target_source(texto)
        operation = self._extract_operation(texto)
        filters = self._extract_all_filters(texto, source)
        
        # 1. DETECTAR LÍMITE (TOP N)
        limit_match = re.search(r"(?:top|ranking)\s*(\d+)", texto)
        limit_val = int(limit_match.group(1)) if limit_match else None
        
        # 2. DETERMINAR VARIABLE Y AGRUPACIÓN
        variable = "ID_REGISTRO"
        group_by = None
        
        # Si pide TOP MEDICAMENTOS:
        if limit_val and (source == "Medicamentos" or "medicamento" in texto):
            group_by = "MEDICAMENTO"
            variable = "MEDICAMENTO"
            operation = "conteo" # El top siempre cuenta frecuencias
        
        # Si pide MEDIA:
        elif operation == "media":
            if "edad" in texto: variable = "EDAD"
            elif "fg" in texto: variable = "FG_CG"

        # 3. DETERMINAR TIPO DE GRÁFICO
        # Si hay agrupación o es un Top, forzamos gráfico o tabla
        if limit_val or group_by:
            chart_type = "bar" if any(w in texto for w in ["grafico", "barras", "visualizar"]) else "table"
        else:
            chart_type = "kpi"

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
                "limit": limit_val if limit_val else 10 # Default 10 para listas
            }
        }
