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

    # 🔥 REGLA GENERAL DE EXTRACCIÓN DE FILTROS
    def _extract_all_filters(self, texto, source):
        filters = []
        t_clean = " " + texto.lower() + " "

        # 1. Filtros Numéricos (FG < 60, Edad > 50, etc.)
        # Buscamos combinaciones de sinónimos + operador + número
        for palabra, col_real in self.sinonimos.items():
            # Patrón: nombre_columna (espacios opcionales) operador (espacios) número
            pattern = rf"{palabra}\s*(<|>|<=|>=|=)\s*(\d+(?:\.\d+)?)"
            matches = re.finditer(pattern, t_clean)
            for m in matches:
                op = m.group(1) if m.group(1) != "=" else "=="
                filters.append({"col": col_real, "op": op, "val": float(m.group(2))})
                # Borramos del texto para que no interfiera con otras extracciones
                t_clean = t_clean.replace(m.group(0), " ")

        # 2. Filtro de CENTRO (Independiente del orden)
        centro_match = re.search(r"centro\s+([a-zA-Z0-9áéíóú]+)", t_clean)
        if centro_match:
            val_centro = centro_match.group(1).strip().upper()
            filters.append({"col": "CENTRO", "op": "contiene", "val": val_centro})
            t_clean = t_clean.replace(centro_match.group(0), " ")

        # 3. Filtro de SEXO
        if " hombre" in t_clean or " varon" in t_clean:
            filters.append({"col": "SEXO", "op": "==", "val": "HOMBRE"})
        if " mujer" in t_clean:
            filters.append({"col": "SEXO", "op": "==", "val": "MUJER"})

        # 4. Filtro de MEDICAMENTO (Enalapril, Metformina, etc.)
        if source == "Medicamentos":
            stopwords = ["cuantos", "pacientes", "toman", "tienen", "del", "en", "el", "la", "centro", "media", "edad", "sexo", "que", "hay", "con"]
            palabras = t_clean.split()
            for p in palabras:
                # Si la palabra es larga, no es stopword y no es una columna numérica ya procesada
                if len(p) > 3 and p not in stopwords and p not in self.sinonimos:
                    # Evitar duplicar si la palabra se usó para el centro
                    if not any(f["val"] == p.upper() for f in filters):
                        filters.append({"col": "MEDICAMENTO", "op": "contiene", "val": p.upper()})
        
        return filters

    def parse_query(self, pregunta_usuario):
        texto = limpiar_texto(pregunta_usuario.lower())
        
        # 1. Fuente y Operación
        source = self._get_target_source(texto)
        operation = self._extract_operation(texto)
        
        # 2. EXTRAER TODOS LOS FILTROS PRIMERO (Regla de Oro)
        filters = self._extract_all_filters(texto, source)
        
        # 3. Determinar Variable Objetivo
        # Si es media, buscamos qué columna numérica se menciona
        variable = "ID_REGISTRO"
        if operation == "media":
            if "edad" in texto: variable = "EDAD"
            elif "fg" in texto or "filtrado" in texto: variable = "FG_CG"
        
        # 4. Ajuste para Porcentajes
        if operation == "porcentaje" and not filters:
            # Si pide % de hombres sin más filtros
            if "hombre" in texto: filters.append({"col": "SEXO", "op": "==", "val": "HOMBRE"})

        return {
            "metadata": {"source": source},
            "request": {
                "metric": operation,
                "target_col": variable,
                "filters": filters,
                "chart_type": "bar" if "grafico" in texto else "kpi",
                "limit": 10
            }
        }
