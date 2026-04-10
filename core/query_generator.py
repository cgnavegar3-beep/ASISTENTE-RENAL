import re
from core.catalog import SCHEMA
from core.dictionary import SINONIMOS_COLUMNAS
from core.normalizer import limpiar_texto

class QueryGenerator:
    def __init__(self):
        self.schema = SCHEMA
        self.sinonimos = SINONIMOS_COLUMNAS

    def _get_target_source(self, texto):
        if any(w in texto for w in ["medicamento", "farmaco", "fármaco", "alopurinol", "toman", "riesgo", "toxicidad"]):
            return "Medicamentos"
        return "Validaciones"

    def _extract_operation(self, texto):
        if any(w in texto for w in ["media", "promedio", "avg"]): return "media"
        if any(w in texto for w in ["%", "porcentaje", "proporcion"]): return "porcentaje"
        return "conteo"

    def _extract_all_filters(self, texto, source):
        filters = []
        # Trabajamos sobre el texto original en minúsculas para no romper regex
        t_clean = " " + texto.lower() + " "

        # 1. TRADUCCIÓN DE OPERADORES (Directo en el flujo)
        # Buscamos "mayor que 80" o "> 80" indistintamente
        for palabra, col_real in self.sinonimos.items():
            # Regex que soporta símbolos (> , <) y palabras (mayor, menor)
            pattern = rf"{palabra}\s*(?:mayor|superior|más|mas|>)\s*(?:que|a)?\s*(\d+(?:\.\d+)?)"
            for m in re.finditer(pattern, t_clean):
                filters.append({"col": col_real, "op": ">", "val": float(m.group(1))})
            
            pattern_inf = rf"{palabra}\s*(?:menor|inferior|menos|<)\s*(?:que|a)?\s*(\d+(?:\.\d+)?)"
            for m in re.finditer(pattern_inf, t_clean):
                filters.append({"col": col_real, "op": "<", "val": float(m.group(1))})

            # Filtro igual estándar (= o símbolo)
            pattern_eq = rf"{palabra}\s*(?:=|==|es de)\s*(\d+(?:\.\d+)?)"
            for m in re.finditer(pattern_eq, t_clean):
                filters.append({"col": col_real, "op": "==", "val": float(m.group(1))})

        # 2. SEXO (Detección simple sin romper nada)
        if "hombre" in t_clean: filters.append({"col": "sexo", "op": "==", "val": "HOMBRE"})
        if "mujer" in t_clean: filters.append({"col": "sexo", "op": "==", "val": "MUJER"})

        # 3. RIESGOS (Mapeo directo a la columna que pide el sistema)
        riesgos = {"leve": "LEVE", "moderado": "MODERADO", "grave": "GRAVE", "critico": "CRITICO", "crítico": "CRITICO"}
        for k, v in riesgos.items():
            if k in t_clean:
                filters.append({"col": "RIESGO_CG", "op": "==", "val": v})

        # 4. CENTRO
        centro_match = re.search(r"centro\s+([a-zA-Z0-9]+)", t_clean)
        if centro_match:
            filters.append({"col": "centro", "op": "contiene", "val": centro_match.group(1).upper()})

        # 5. MEDICAMENTOS (Si no ha pillado nada antes, es un medicamento)
        if source == "Medicamentos":
            ignorar = ["cuantos", "pacientes", "toman", "hay", "grafico", "por", "centro", "sexo", "riesgo"]
            for p in t_clean.split():
                if len(p) > 3 and p not in ignorar and p not in riesgos:
                    if not any(f["val"] == p.upper() for f in filters):
                        filters.append({"col": "MEDICAMENTO", "op": "contiene", "val": p.upper()})

        return filters

    def parse_query(self, pregunta_usuario):
        texto = limpiar_texto(pregunta_usuario.lower())
        source = self._get_target_source(texto)
        filters = self._extract_all_filters(texto, source)
        operation = self._extract_operation(texto)
        
        # --- LÓGICA DE GRÁFICOS RESTAURADA ---
        group_by = None
        chart_type = "kpi"
        if "grafico" in texto or "gráfico" in texto or "distribucion" in texto:
            chart_type = "bar"
            if "centro" in texto: group_by = "centro"
            elif "sexo" in texto: group_by = "sex
                
