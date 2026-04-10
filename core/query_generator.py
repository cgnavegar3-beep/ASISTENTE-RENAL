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
        terminos_clinicos = ["precaucion", "ajuste", "toxicidad", "contraindicado", "contraindicados", "leve", "moderado", "grave", "critico", "riesgo", "adecuacion"]
        if any(w in texto for w in med_keywords) or any(w in texto for w in terminos_clinicos):
            return "Medicamentos"
        return "Validaciones"

    def _extract_operation(self, texto):
        if any(w in texto for w in ["media", "promedio", "avg"]): return "media"
        if any(w in texto for w in ["%", "porcentaje", "proporcion"]): return "porcentaje"
        return "conteo"

    def _pre_procesar_operadores(self, texto):
        texto = re.sub(r"\b(mayor que|mayor a|superior a|mas de)\b", ">", texto)
        texto = re.sub(r"\b(menor que|menor a|inferior a|menos de)\b", "<", texto)
        texto = re.sub(r"\b(igual a)\b", "=", texto)
        return texto

    def _extract_all_filters(self, texto, source):
        filters = []
        texto_con_simbolos = self._pre_procesar_operadores(texto)
        t_clean = " " + texto_con_simbolos.lower() + " "

        # 1. MAPEO DE RIESGOS (CG por defecto, MDRD/CKD si se mencionan)
        # Priorizamos el nombre de la columna exacta que pediste
        col_riesgo = "RIESGO_CG" 
        if "mdrd" in t_clean: col_riesgo = "RIESGO_MDRD"
        elif "ckd" in t_clean: col_riesgo = "RIESGO_CKD"

        equivalencias = {
            "precaucion": "LEVE", "monitorizacion": "LEVE", "leve": "LEVE",
            "ajuste": "MODERADO", "moderado": "MODERADO",
            "toxicidad": "GRAVE", "grave": "GRAVE",
            "contraindicado": "CRITICO", "critico": "CRITICO", "crítico": "CRITICO"
        }

        for palabra, valor in equivalencias.items():
            if palabra in t_clean:
                filters.append({"col": col_riesgo, "op": "==", "val": valor})
                t_clean = t_clean.replace(palabra, " ")

        # 2. CATEGORÍAS GENERALES (Sexo, Centro, Residencia)
        if re.search(r"\b(hombre|hombres|masculino)\b", t_clean):
            filters.append({"col": "sexo", "op": "==", "val": "HOMBRE"})
        elif re.search(r"\b(mujer|mujeres|femenino)\b", t_clean):
            filters.append({"col": "sexo", "op": "==", "val": "MUJER"})

        # Búsqueda de Centro y Residencia
        for col in ["centro", "residencia"]:
            match = re.search(rf"{col}\s+([a-zA-Z0-9áéíóú]+)", t_clean)
            if match:
                filters.append({"col": col, "op": "contiene", "val": match.group(1).strip().upper()})
                t_clean = t_clean.replace(match.group(0), " ")

        # 3. FILTROS NUMÉRICOS (EDAD, FG...)
        for palabra, col_real in self.sinonimos.items():
            pattern = rf"{palabra}\s*(<|>|<=|>=|=)\s*(\d+(?:\.\d+)?)"
            matches = re.finditer(pattern, t_clean)
            for m in matches:
                op = m.group(1) if m.group(1) != "=" else "=="
                try:
                    filters.append({"col": col_real, "op": op, "val": float(m.group(2))})
                    t_clean = t_clean.replace(m.group(0), " ")
                except: continue

        # 4. MEDICAMENTOS Y GRUPOS TERAPÉUTICOS
        if source == "Medicamentos":
            # Lista de palabras a ignorar para no confundirlas con medicamentos
            ignorar = ["cuantos", "pacientes", "toman", "tienen", "centro", "riesgo", "grafico", "total", "numero"]
            palabras = [p for p in t_clean.split() if len(p) > 3 and p not in ignorar and p not in equivalencias]
            
            for p in palabras:
                col_med = "GRUPO_TERAPEUTICO" if "grupo" in t_clean else "MEDICAMENTO"
                if not any(f["val"] == p.upper() for f in filters):
                    filters.append({"col": col_med, "op": "contiene", "val": p.upper()})
        
        return filters

    def parse_query(self, pregunta_usuario):
        texto = limpiar_texto(pregunta_usuario.lower())
        source = self._get_target_source(texto)
        filters = self._extract_all_filters(texto, source)
        operation = self._extract_operation(texto)
        
        # LÓGICA DE GRÁFICOS
        group_by = None
        chart_type = "kpi"
        if any(w in texto for w in ["grafico", "gráfico", "histograma", "sectores", "quesito", "distribucion"]):
            chart_type = "bar"
            if any(w in texto for w in ["sectores", "quesito", "pie"]): chart_type = "pie"
            elif "histograma" in texto: chart_type = "histogram"
            
            if "centro" in texto: group_by = "centro"
            elif "sexo" in texto: group_by = "sexo"
            elif "riesgo" in texto: group_by = "RIESGO_CG"
            elif "medicamento" in texto: group_by = "MEDICAMENTO"
            else: group_by = "RIESGO_CG"

        # --- EL CAMBIO CLAVE PARA SOLUCIONAR EL CONTEO ---
        # Si la columna es de texto (categórica), el target DEBE ser una columna que siempre tenga datos (ID)
        cols_texto = ["centro", "residencia", "sexo", "MEDICAMENTO", "RIESGO_CG", "RIESGO_MDRD", "RIESGO_CKD", "GRUPO_TERAPEUTICO", "ADECUACION_FINAL"]
        
        es_consulta_texto = any(f["col"] in cols_texto for f in filters) or group_by in cols_texto
        
        if es_consulta_texto or operation == "conteo" or operation == "porcentaje":
            # Si estamos en medicamentos, contamos medicamentos. Si no, IDs de pacientes.
            target = "MEDICAMENTO" if source == "Medicamentos" else "ID_REGISTRO"
        else:
            # Fallback para medias numéricas
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
