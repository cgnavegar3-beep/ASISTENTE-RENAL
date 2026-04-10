import re
from core.catalog import SCHEMA
from core.dictionary import SINONIMOS_COLUMNAS
from core.normalizer import limpiar_texto

class QueryGenerator:
    def __init__(self):
        self.schema = SCHEMA
        self.sinonimos = SINONIMOS_COLUMNAS

    def _get_target_source(self, texto):
        med_keywords = ["medicamento", "farmaco", "fármaco", "alopurinol", "toman", "tienen", "prescrito"]
        terminos_clinicos = ["riesgo", "adecuacion", "toxicidad", "ajuste", "contraindicado", "leve", "moderado", "grave", "critico"]
        if any(w in texto for w in med_keywords) or any(w in texto for w in terminos_clinicos):
            return "Medicamentos"
        return "Validaciones"

    def _extract_operation(self, texto):
        if any(w in texto for w in ["media", "promedio", "avg"]): return "media"
        if any(w in texto for w in ["%", "porcentaje", "proporcion"]): return "porcentaje"
        return "conteo"

    def _pre_procesar_operadores(self, texto):
        # Sustitución agresiva de operadores en texto a símbolos
        texto = re.sub(r"\b(mayor que|mayor a|superior a|mas de|mas que)\b", ">", texto)
        texto = re.sub(r"\b(menor que|menor a|inferior a|menos de|menos que)\b", "<", texto)
        texto = re.sub(r"\b(igual a)\b", "=", texto)
        return texto

    def _extract_all_filters(self, texto, source):
        filters = []
        # 1. Pre-procesamos operadores ANTES de cualquier otra limpieza
        texto_norm = self._pre_procesar_operadores(texto)
        t_clean = " " + texto_norm.lower() + " "

        # 2. MAPEO DE RIESGOS (Basado en tu lista CRÍTICA)
        col_riesgo = "RIESGO_CG"
        if "mdrd" in t_clean: col_riesgo = "RIESGO_MDRD"
        elif "ckd" in t_clean: col_riesgo = "RIESGO_CKD"

        equivalencias = {
            "precaucion": "LEVE", "monitorizacion": "LEVE", "leve": "LEVE",
            "ajuste": "MODERADO", "moderado": "MODERADO",
            "toxicidad": "GRAVE", "grave": "GRAVE",
            "contraindicado": "CRITICO", "critico": "CRITICO"
        }

        for palabra, valor in equivalencias.items():
            if palabra in t_clean:
                filters.append({"col": col_riesgo, "op": "==", "val": valor})
                t_clean = t_clean.replace(palabra, " ")

        # 3. SEXO, CENTRO Y RESIDENCIA (Detección de valores)
        if "hombre" in t_clean or "masculino" in t_clean:
            filters.append({"col": "sexo", "op": "==", "val": "HOMBRE"})
        elif "mujer" in t_clean or "femenino" in t_clean:
            filters.append({"col": "sexo", "op": "==", "val": "MUJER"})

        # Detección genérica de Centro y Residencia
        for col in ["centro", "residencia"]:
            match = re.search(rf"{col}\s+([a-zA-Z0-9áéíóú]+)", t_clean)
            if match:
                filters.append({"col": col, "op": "contiene", "val": match.group(1).strip().upper()})
                t_clean = t_clean.replace(match.group(0), " ")

        # 4. FILTROS NUMÉRICOS (EDAD, FG...)
        for palabra, col_real in self.sinonimos.items():
            pattern = rf"{palabra}\s*(<|>|<=|>=|=)\s*(\d+(?:\.\d+)?)"
            matches = re.finditer(pattern, t_clean)
            for m in matches:
                op = m.group(1) if m.group(1) != "=" else "=="
                filters.append({"col": col_real, "op": op, "val": float(m.group(2))})
                t_clean = t_clean.replace(m.group(0), " ")

        # 5. MEDICAMENTOS Y GRUPOS
        if source == "Medicamentos":
            stopwords = ["cuantos", "pacientes", "toman", "hay", "con", "grafico", "por", "sexo", "edad", "centro"]
            palabras = [p for p in t_clean.split() if len(p) > 3 and p not in stopwords and p not in equivalencias]
            for p in palabras:
                col_med = "GRUPO_TERAPEUTICO" if "grupo" in t_clean else "MEDICAMENTO"
                if not any(f["val"] == p.upper() for f in filters):
                    filters.append({"col": col_med, "op": "contiene", "val": p.upper()})
        
        return filters

    def parse_query(self, pregunta_usuario):
        texto = limpiar_texto(pregunta_usuario.lower())
        source = self._get_target_source(texto)
        filters = self._extract_all_filters(pregunta_usuario, source)
        operation = self._extract_operation(texto)
        
        # --- LÓGICA DE GRÁFICOS (Solución al Error Crítico de Columna) ---
        group_by = None
        chart_type = "kpi"
        
        if any(w in texto for w in ["grafico", "gráfico", "distribucion", "reparto"]):
            chart_type = "bar"
            if any(w in texto for w in ["sectores", "quesito", "pie"]): chart_type = "pie"
            
            # Mapeo forzado a nombres de columna reales del SCHEMA
            if "centro" in texto: group_by = "centro"
            elif "sexo" in texto: group_by = "sexo"
            elif "edad" in texto: group_by = "EDAD"
            elif "riesgo" in texto: group_by = "RIESGO_CG"
            elif "medicamento" in texto: group_by = "MEDICAMENTO"
            else: group_by = "centro" # Fallback seguro

        # --- BLINDAJE DE TARGET PARA CONTEO ---
        # Si hay filtros de texto o es un conteo, el target debe ser un ID para evitar errores de tipo
        cols_texto = ["centro", "sexo", "residencia", "MEDICAMENTO", "RIESGO_CG", "RIESGO_MDRD", "RIESGO_CKD"]
        es_categorica = any(f["col"] in cols_texto for f in filters) or group_by in cols_texto
        
        if es_categorica or operation in ["conteo", "porcentaje"]:
            target = "MEDICAMENTO" if source == "Medicamentos" else "ID_REGISTRO"
        else:
            target = "EDAD" if "edad" in texto else ("FG_CG" if "fg" in texto else "ID_REGISTRO")

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
