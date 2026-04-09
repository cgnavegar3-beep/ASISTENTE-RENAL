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

    def _extract_all_filters(self, texto, source):
        filters = []
        t_clean = " " + texto.lower() + " "

        # 1. EQUIVALENCIAS CLÍNICAS (TEXTO)
        # Aquí NO usamos float(), son strings puros.
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

        for palabra, valor_filtro in equivalencias.items():
            if palabra in t_clean:
                filters.append({"col": "FG_CG", "op": "==", "val": valor_filtro})
                # Eliminamos la palabra para que no cause conflictos en el paso 4
                t_clean = t_clean.replace(palabra, " ")

        # 2. FILTROS NUMÉRICOS (Aquí sí usamos float)
        for palabra, col_real in self.sinonimos.items():
            # Buscamos patron: palabra + operador + numero
            pattern = rf"{palabra}\s*(<|>|<=|>=|=)\s*(\d+(?:\.\d+)?)"
            matches = re.finditer(pattern, t_clean)
            for m in matches:
                op = m.group(1) if m.group(1) != "=" else "=="
                try:
                    # Solo convertimos a float lo que realmente es un número
                    valor_num = float(m.group(2))
                    filters.append({"col": col_real, "op": op, "val": valor_num})
                    t_clean = t_clean.replace(m.group(0), " ")
                except ValueError:
                    continue

        # 3. FILTRO DE CENTRO
        centro_match = re.search(r"centro\s+([a-zA-Z0-9áéíóú]+)", t_clean)
        if centro_match:
            val_centro = centro_match.group(1).strip().upper()
            filters.append({"col": "CENTRO", "op": "contiene", "val": val_centro})
            t_clean = t_clean.replace(centro_match.group(0), " ")

        # 4. FILTRO DE MEDICAMENTO
        if source == "Medicamentos" and not any(w in t_clean for w in ["top", "ranking", "mas frecuentes"]):
            stopwords = ["cuantos", "pacientes", "toman", "tienen", "del", "en", "el", "la", "centro", "media", "edad", "sexo", "que", "hay", "con", "riesgo", "dosis"]
            palabras = t_clean.split()
            for p in palabras:
                if len(p) > 3 and p not in stopwords and p not in self.sinonimos and p not in equivalencias:
                    if not any(f["val"] == p.upper() for f in filters):
                        filters.append({"col": "MEDICAMENTO", "op": "contiene", "val": p.upper()})
        
        return filters

    def parse_query(self, pregunta_usuario):
        texto = limpiar_texto(pregunta_usuario.lower())
        source = self._get_target_source(texto)
        
        # IMPORTANTE: Si es una pregunta de riesgo, la operación debe ser CONTEO
        # Las medias solo se aplican a columnas numéricas (EDAD, FG_CG numérico si existe)
        operation = self._extract_operation(texto)
        
        # Si la pregunta es sobre riesgos (texto), forzamos CONTEO para evitar el error de float
        terminos_riesgo = ["precaucion", "ajuste", "toxicidad", "contraindicado", "leve", "moderado", "grave", "critico"]
        if any(w in texto for w in terminos_riesgo):
            operation = "conteo"

        filters = self._extract_all_filters(texto, source)
        
        limit_match = re.search(r"(?:top|ranking)\s*(\d+)", texto)
        limit_val = int(limit_match.group(1)) if limit_match else None
        
        variable = "ID_REGISTRO"
        group_by = None
        
        if source == "Medicamentos":
            variable = "MEDICAMENTO"
            if limit_val or "medicamento" in texto:
                group_by = "MEDICAMENTO"
                operation = "conteo"
        
        elif operation == "media":
            if "edad" in texto: variable = "EDAD"
            elif any(w in texto for w in ["fg", "filtrado", "glomerular"]): variable = "FG_CG"

        return {
            "metadata": {"source": source, "intent": "kpi" if not group_by else "visual"},
            "request": {
                "metric": operation,
                "target_col": variable,
                "filters": filters,
                "group_by": group_by,
                "limit": limit_val if limit_val else (10 if group_by else None)
            }
        }
