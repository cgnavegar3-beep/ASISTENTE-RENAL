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

    # --- EXTRACCIÓN DE FILTROS REFORZADA ---
    def _extract_all_filters(self, texto, source):
        filters = []
        t_clean = " " + texto.lower() + " "

        # 1. EQUIVALENCIAS CLÍNICAS (TEXTO PURO - riesgo_CG)
        # Aquí definimos que el valor es un STRING, nunca pasará por float()
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
                # IMPORTANTE: Columna riesgo_CG según tu indicación
                filters.append({"col": "riesgo_CG", "op": "==", "val": str(valor_filtro)})
                t_clean = t_clean.replace(palabra, " ")

        # 2. FILTROS NUMÉRICOS (Edad, FG, etc.)
        for palabra, col_real in self.sinonimos.items():
            pattern = rf"{palabra}\s*(<|>|<=|>=|=)\s*(\d+(?:\.\d+)?)"
            matches = re.finditer(pattern, t_clean)
            for m in matches:
                op = m.group(1) if m.group(1) != "=" else "=="
                try:
                    # Solo convertimos a float lo que es detectado por este regex numérico
                    valor_num = float(m.group(2))
                    filters.append({"col": col_real, "op": op, "val": valor_num})
                    t_clean = t_clean.replace(m.group(0), " ")
                except ValueError:
                    continue

        # 3. Filtro de CENTRO
        centro_match = re.search(r"centro\s+([a-zA-Z0-9áéíóú]+)", t_clean)
        if centro_match:
            val_centro = centro_match.group(1).strip().upper()
            filters.append({"col": "CENTRO", "op": "contiene", "val": val_centro})
            t_clean = t_clean.replace(centro_match.group(0), " ")

        # 4. Filtro de MEDICAMENTO
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
        
        # Si la pregunta es sobre riesgos, la operación DEBE ser conteo
        terminos_riesgo = ["precaucion", "ajuste", "toxicidad", "contraindicado", "leve", "moderado", "grave", "critico"]
        
        operation = self._extract_operation(texto)
        if any(w in texto for w in terminos_riesgo):
            operation = "conteo"

        filters = self._extract_all_filters(texto, source)
        
        limit_match = re.search(r"(?:top|ranking)\s*(\d+)", texto)
        limit_val = int(limit_match.group(1)) if limit_match else None
        
        # Variable de conteo
        variable = "ID_REGISTRO"
        group_by = None
        
        if source == "Medicamentos":
            variable = "MEDICAMENTO"
            if limit_val or "medicamento" in texto:
                group_by = "MEDICAMENTO"
                operation = "conteo"
        
        elif operation == "media":
            if "edad" in texto: variable = "EDAD"
            elif any(w in texto for w in ["fg", "filtrado", "glomerular"]): 
                # Si pide media de FG, usamos la columna numérica, no la de texto
                variable = "FG_CG" 

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
