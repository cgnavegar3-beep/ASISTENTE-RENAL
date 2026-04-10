import re
from core.catalog import SCHEMA
from core.dictionary import SINONIMOS_COLUMNAS
from core.normalizer import limpiar_texto

class QueryGenerator:
    def __init__(self):
        self.schema = SCHEMA
        self.sinonimos = SINONIMOS_COLUMNAS

    def _get_target_source(self, texto):
        # Simplificamos la detección de fuente
        if any(w in texto for w in ["medicamento", "farmaco", "fármaco", "alopurinol", "toman", "riesgo"]):
            return "Medicamentos"
        return "Validaciones"

    def _extract_operation(self, texto):
        if any(w in texto for w in ["media", "promedio", "avg"]): return "media"
        if any(w in texto for w in ["%", "porcentaje", "proporcion"]): return "porcentaje"
        return "conteo"

    def _extract_all_filters(self, texto, source):
        filters = []
        t_clean = " " + texto.lower() + " "

        # 1. FILTROS NUMÉRICOS CON SOPORTE PARA "MAYOR/MENOR"
        for palabra, col_real in self.sinonimos.items():
            # Caso Mayor: busca "edad mayor 80", "edad > 80", "edad mas de 80"
            patron_mayor = rf"{palabra}\s*(?:mayor|superior|mas|más|>)\s*(?:que|a)?\s*(\d+(?:\.\d+)?)"
            for m in re.finditer(patron_mayor, t_clean):
                filters.append({"col": col_real, "op": ">", "val": float(m.group(1))})
            
            # Caso Menor: busca "edad menor 40", "edad < 40", "edad menos de 40"
            patron_menor = rf"{palabra}\s*(?:menor|inferior|menos|<)\s*(?:que|a)?\s*(\d+(?:\.\d+)?)"
            for m in re.finditer(patron_menor, t_clean):
                filters.append({"col": col_real, "op": "<", "val": float(m.group(1))})

            # Caso Igual
            patron_igual = rf"{palabra}\s*(?:=|==|es de)\s*(\d+(?:\.\d+)?)"
            for m in re.finditer(patron_igual, t_clean):
                filters.append({"col": col_real, "op": "==", "val": float(m.group(1))})

        # 2. SEXO
        if "hombre" in t_clean or "varon" in t_clean: 
            filters.append({"col": "sexo", "op": "==", "val": "HOMBRE"})
        elif "mujer" in t_clean: 
            filters.append({"col": "sexo", "op": "==", "val": "MUJER"})

        # 3. RIESGOS (Mapeo a columna RIESGO_CG)
        riesgos_map = {"leve": "LEVE", "moderado": "MODERADO", "grave": "GRAVE", "critico": "CRITICO"}
        for k, v in riesgos_map.items():
            if k in t_clean:
                filters.append({"col": "RIESGO_CG", "op": "==", "val": v})

        # 4. CENTRO
        centro_match = re.search(r"centro\s+([a-zA-Z0-9]+)", t_clean)
        if centro_match:
            filters.append({"col": "centro", "op": "contiene", "val": centro_match.group(1).upper()})

        # 5. MEDICAMENTOS (Detección por descarte)
        if source == "Medicamentos":
            ignorar = ["cuantos", "pacientes", "toman", "hay", "grafico", "por", "sexo", "riesgo"]
            for p in t_clean.split():
                if len(p) > 3 and p not in ignorar and p not in riesgos_map:
                    if not any(f["val"] == p.upper() for f in filters):
                        filters.append({"col": "MEDICAMENTO", "op": "contiene", "val": p.upper()})

        return filters

    def parse_query(self, pregunta_usuario):
        texto = limpiar_texto(pregunta_usuario.lower())
        source = self._get_target_source(texto)
        filters = self._extract_all_filters(texto, source)
        operation = self._extract_operation(texto)
        
        # --- LÓGICA DE GRÁFICOS ---
        group_by = None
        chart_type = "kpi"
        if any(w in texto for w in ["grafico", "gráfico", "distribucion"]):
            chart_type = "bar"
            # Mapeo manual para evitar que use palabras raras del usuario como columna
            if "centro" in texto: group_by = "centro"
            elif "sexo" in texto: group_by = "sexo"
            elif "edad" in texto: group_by = "EDAD"
            else: group_by = "centro"

        # --- BLINDAJE DE TARGET ---
        # El target col debe ser texto (ID o MEDICAMENTO) para que el motor cuente registros
        target = "MEDICAMENTO" if source == "Medicamentos" else "ID_REGISTRO"
        
        # Solo cambiamos a columna numérica si se pide explícitamente una MEDIA
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
