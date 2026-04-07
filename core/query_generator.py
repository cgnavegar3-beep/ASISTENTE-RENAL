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
        meds = ["medicamento", "farmaco", "fármaco", "pastilla", "insulina", "metformina", 
                "tratamiento", "toman", "tienen", "prescrito", "toma", "tiene"]
        return "Medicamentos" if any(w in texto for w in meds) else "Validaciones"

    def _extract_operation(self, texto):
        if any(w in texto for w in ["media", "promedio", "average", "avg"]): return "media"
        if any(w in texto for w in ["%", "porcentaje", "proporcion", "ratio"]): return "porcentaje"
        if any(w in texto for w in ["maximo", "max", "mas alto"]): return "max"
        if any(w in texto for w in ["minimo", "min", "mas bajo"]): return "min"
        return "conteo"

    def _parse_output_type(self, texto, has_grouping=False):
        if "histograma" in texto: return "histogram"
        if any(w in texto for w in ["pie", "sectores", "tarta", "quesito"]): return "pie"
        if any(w in texto for w in ["grafico", "gráfico", "barras", "visualizar"]): return "bar"
        if any(w in texto for w in ["tabla", "lista", "ranking", "top"]): return "table"
        return "bar" if has_grouping else "kpi"

    # --- VARIABLE (Reforzada para Medias) ---
    def _extract_variable(self, texto):
        # 1. Si la operación es media, BUSCAMOS primero una variable numérica (Edad, FG...)
        operacion = self._extract_operation(texto)
        if operacion == "media":
            if "edad" in texto: return "EDAD"
            if "fg" in texto or "filtrado" in texto: return "FG_CG"
        
        # 2. Si no, buscamos en los sinónimos generales
        for palabra in sorted(self.sinonimos.keys(), key=len, reverse=True):
            if palabra in texto:
                return self.sinonimos[palabra]
        
        return "ID_REGISTRO"

    # --- FILTROS (Reforzados para cruzar Centro, Sexo y Medicamentos) ---
    def _extract_filters(self, texto, source):
        extracted = []
        texto_orig = texto.lower()

        # Normalizar operadores
        texto_mod = re.sub(r"menor\s+que|menor\s+a|menor\s+de|menor", "<", texto_orig)
        texto_mod = re.sub(r"mayor\s+que|mayor\s+a|mayor\s+de|mayor", ">", texto_mod)

        # A) SEXO
        if "hombre" in texto_orig or "varon" in texto_orig:
            extracted.append({"col": "SEXO", "op": "==", "val": "HOMBRE"})
        if "mujer" in texto_orig:
            extracted.append({"col": "SEXO", "op": "==", "val": "MUJER"})

        # B) CENTROS (Busca el nombre del centro después de la palabra 'centro')
        if "centro" in texto_orig:
            partes = texto_orig.split("centro")
            if len(partes) > 1:
                valor = partes[1].strip().split(" ")[0]
                if len(valor) > 2:
                    extracted.append({"col": "CENTRO", "op": "contiene", "val": valor.upper()})

        # C) MEDICAMENTOS (Si el origen es Medicamentos y no es un TOP)
        if source == "Medicamentos" and "top" not in texto_orig:
            stopwords = ["pacientes", "cuantos", "media", "edad", "centro", "sexo", "toman", "tienen", "el", "la"]
            palabras = texto_orig.split()
            for p in palabras:
                if len(p) > 3 and p not in stopwords and p not in self.sinonimos:
                    extracted.append({"col": "MEDICAMENTO", "op": "contiene", "val": p.upper()})
                    break

        return extracted

    def parse_query(self, pregunta_usuario):
        texto = limpiar_texto(pregunta_usuario.lower())
        source = self._get_target_source(texto)
        operation = self._extract_operation(texto)
        
        # Extraemos filtros primero para ver qué "palabras" quedan
        filters = self._extract_filters(texto, source)
        variable = self._extract_variable(texto)
        
        limit = re.search(r"top\s*(\d+)", texto)
        limit_val = int(limit.group(1)) if limit else None

        # --- LÓGICA DE PORCENTAJE ---
        # Si pide %, la variable suele ser lo que queremos contar (hombres, metformina...)
        if operation == "porcentaje":
            if not filters and variable != "ID_REGISTRO":
                # Si dice "% de hombres", convertimos la variable en filtro para que el motor calcule el ratio
                filters.append({"col": variable, "op": "==", "val": "HOMBRE" if "hombre" in texto else "MUJER"})
                variable = "ID_REGISTRO"

        return {
            "metadata": {"source": source},
            "request": {
                "metric": operation,
                "target_col": variable,
                "filters": filters,
                "chart_type": self._parse_output_type(texto, has_grouping=False),
                "limit": limit_val
            }
        }
