import re
from core.catalog import SCHEMA
from core.dictionary import SINONIMOS_COLUMNAS, MAPEO_VISUAL
from core.normalizer import limpiar_texto
from core.errors import CoreError

class QueryGenerator:
    def __init__(self):
        self.schema = SCHEMA
        self.sinonimos = SINONIMOS_COLUMNAS

    def _get_target_source(self, texto):
        meds = ["medicamento", "farmaco", "fármaco", "pastilla", "insulina", "metformina", "tratamiento"]
        return "Medicamentos" if any(w in texto for w in meds) else "Validaciones"

    def _extract_operation(self, texto):
        if any(w in texto for w in ["media", "promedio", "average"]): return "media"
        if any(w in texto for w in ["%", "porcentaje", "proporcion"]): return "porcentaje"
        if any(w in texto for w in ["maximo", "max", "mas alto"]): return "max"
        if any(w in texto for w in ["minimo", "min", "mas bajo"]): return "min"
        return "conteo"

    def _parse_output_type(self, texto, has_grouping=False):
        if "histograma" in texto: return "histogram"
        if any(w in texto for w in ["pie", "sectores", "tarta", "quesito"]): return "pie"
        if any(w in texto for w in ["grafico", "gráfico", "barras", "visualizar"]): return "bar"
        if any(w in texto for w in ["tabla", "lista", "ranking", "top"]): return "table"
        return "bar" if has_grouping else "kpi"

    def _extract_variable(self, texto):
        # Ordenamos sinónimos por longitud (de mayor a menor) para evitar falsos positivos
        for palabra in sorted(self.sinonimos.keys(), key=len, reverse=True):
            if palabra in texto:
                return self.sinonimos[palabra]
        return "ID_REGISTRO"

    def _extract_group_by(self, texto):
        # Captura "por centro", "por sexo", pero también "segun centro" o "distribucion de centro"
        match = re.search(r"(?:por|segun|distribucion\s+de)\s+([a-zA-Záéíóú]+)", texto)
        if match:
            palabra = match.group(1)
            if palabra in self.sinonimos:
                return self.sinonimos[palabra]
        return None

    def _extract_limit(self, texto):
        match = re.search(r"top\s*(\d+)", texto)
        return int(match.group(1)) if match else None

    def _extract_filters(self, texto, source):
        extracted = []
        
        # 1. Normalización de operadores verbales a símbolos
        texto = re.sub(r"menor\s+que|menor\s+de|debajo\s+de", "<", texto)
        texto = re.sub(r"mayor\s+que|mayor\s+de|encima\s+de", ">", texto)
        texto = re.sub(r"igual\s+a", "=", texto)

        # 2. Búsqueda de filtros numéricos (Columna + Op + Valor)
        # Usamos los sinónimos para identificar qué columna se está filtrando
        for palabra, col_real in self.sinonimos.items():
            pattern = rf"{palabra}\s*(<|>|=|<=|>=)\s*(\d+(?:\.\d+)?)"
            match = re.search(pattern, texto)
            if match:
                op = match.group(1)
                val = match.group(2)
                extracted.append({
                    "col": col_real,
                    "op": "==" if op == "=" else op,
                    "val": float(val)
                })

        # 3. Búsqueda de filtros categóricos (ej: "centro cambados")
        # Esto requiere que sepamos qué columnas son categóricas (ej: CENTRO)
        centros = ["cambados", "pontevedra", "vigo", "salnes"] # Esto debería venir de un catálogo
        for c in centros:
            if c in texto:
                extracted.append({"col": "CENTRO", "op": "==", "val": c.upper()})

        return extracted

    def parse_query(self, pregunta_usuario):
        texto = limpiar_texto(pregunta_usuario.lower())

        source = self._get_target_source(texto)
        operation = self._extract_operation(texto)
        variable = self._extract_variable(texto)
        group_by = self._extract_group_by(texto)
        limit = self._extract_limit(texto)
        filters = self._extract_filters(texto, source)
        
        # Lógica de TOP N: Si hay top, la variable es el objeto y agrupamos por ella
        if limit and variable != "ID_REGISTRO":
            group_by = variable
            operation = "conteo"

        # Determinar tipo de salida
        chart_type = self._parse_output_type(texto, has_grouping=(group_by is not None))

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
                "limit": limit or (10 if limit else None) 
            }
        }
