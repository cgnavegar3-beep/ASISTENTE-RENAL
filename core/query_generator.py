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

        # --- MEJORA: MAPEO SEMÁNTICO Y CATEGÓRICO ---
        
        # 1. Traducciones y Riesgos (Prioridad CAT_RIESGO_CG por defecto)
        col_riesgo = "CAT_RIESGO_CG"
        if "mdrd" in t_clean: col_riesgo = "CAT_RIESGO_MDRD"
        elif "ckd" in t_clean: col_riesgo = "CAT_RIESGO_CKD"

        mapeo_riesgo = {
            "precaucion": "LEVE", "monitorizacion": "LEVE", "leve": "LEVE",
            "ajuste": "MODERADO", "moderado": "MODERADO",
            "toxicidad": "GRAVE", "grave": "GRAVE",
            "contraindicado": "CRITICO", "critico": "CRITICO", "crítico": "CRITICO"
        }

        for palabra, valor in mapeo_riesgo.items():
            if palabra in t_clean:
                filters.append({"col": col_riesgo, "op": "==", "val": valor})
                t_clean = t_clean.replace(palabra, " ")

        # 2. Sexo (Hombres/Mujeres)
        if re.search(r"\b(hombre|hombres|masculino)\b", t_clean):
            filters.append({"col": "sexo", "op": "==", "val": "HOMBRE"})
        elif re.search(r"\b(mujer|mujeres|femenino)\b", t_clean):
            filters.append({"col": "sexo", "op": "==", "val": "MUJER"})

        # 3. Filtros de Centro y Residencia
        centro_match = re.search(r"centro\s+([a-zA-Z0-9áéíóú]+)", t_clean)
        if centro_match:
            filters.append({"col": "centro", "op": "contiene", "val": centro_match.group(1).strip().upper()})
            t_clean = t_clean.replace(centro_match.group(0), " ")

        residencia_match = re.search(r"residencia\s+([a-zA-Z0-9áéíóú]+)", t_clean)
        if residencia_match:
            filters.append({"col": "residencia", "op": "contiene", "val": residencia_match.group(1).strip().upper()})
            t_clean = t_clean.replace(residencia_match.group(0), " ")

        # 4. Filtros Numéricos
        for palabra, col_real in self.sinonimos.items():
            pattern = rf"{palabra}\s*(<|>|<=|>=|=)\s*(\d+(?:\.\d+)?)"
            matches = re.finditer(pattern, t_clean)
            for m in matches:
                op = m.group(1) if m.group(1) != "=" else "=="
                try:
                    filters.append({"col": col_real, "op": op, "val": float(m.group(2))})
                    t_clean = t_clean.replace(m.group(0), " ")
                except: continue

        # 5. Mapeo Genérico de Columnas Categóricas (Medicamentos/Grupos)
        if source == "Medicamentos":
            stopwords = ["cuantos", "pacientes", "toman", "tienen", "del", "en", "el", "la", "centro", "media", "edad", "sexo", "que", "hay", "con", "riesgo", "grafico", "histograma", "numero", "porcentaje"]
            palabras = t_clean.split()
            for p in palabras:
                if len(p) > 3 and p not in stopwords and p not in mapeo_riesgo:
                    # Si no es un filtro previo, lo buscamos como Medicamento o Grupo
                    if not any(f["val"] == p.upper() for f in filters):
                        col_target = "MEDICAMENTO"
                        if "grupo" in t_clean: col_target = "GRUPO_TERAPEUTICO"
                        filters.append({"col": col_target, "op": "contiene", "val": p.upper()})
        
        return filters

    def parse_query(self, pregunta_usuario):
        texto = limpiar_texto(pregunta_usuario.lower())
        source = self._get_target_source(texto)
        filters = self._extract_all_filters(texto, source)
        operation = self._extract_operation(texto)
        
        # LÓGICA DE GRÁFICOS
        group_by = None
        chart_type = "kpi"
        if any(w in texto for w in ["grafico", "gráfico", "histograma", "sectores", "quesito", "distribucion", "reparto"]):
            chart_type = "bar"
            if any(w in texto for w in ["sectores", "quesito", "pie"]): chart_type = "pie"
            elif "histograma" in texto: chart_type = "histogram"
            
            if "centro" in texto: group_by = "centro"
            elif "sexo" in texto: group_by = "sexo"
            elif "riesgo" in texto: group_by = "CAT_RIESGO_CG"
            elif "medicamento" in texto: group_by = "MEDICAMENTO"
            else: group_by = "CAT_RIESGO_CG"

        # DEFINICIÓN DE TARGET Y BLINDAJE
        # Cualquier columna categórica o riesgo fuerza el target a ID_REGISTRO o MEDICAMENTO para contar
        categorias = ["centro", "residencia", "sexo", "MEDICAMENTO", "CAT_RIESGO_CG", "CAT_RIESGO_MDRD", "CAT_RIESGO_CKD", "GRUPO_TERAPEUTICO"]
        es_categorica = any(f["col"] in categorias for f in filters) or group_by in categorias
        
        if es_categorica or operation == "conteo" or operation == "porcentaje":
            target = "MEDICAMENTO" if source == "Medicamentos" else "ID_REGISTRO"
        else:
            target = "ID_REGISTRO"
            if operation == "media":
                if "edad" in texto: target = "EDAD"
                elif "fg" in texto: target = "FG_CG"

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
