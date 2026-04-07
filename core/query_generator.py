import re
from core.catalog import SCHEMA
from core.dictionary import SINONIMOS_COLUMNAS, MAPEO_VISUAL
from core.normalizer import limpiar_texto
from core.errors import CoreError

class QueryGenerator:
    def __init__(self):
        self.schema = SCHEMA
        self.sinonimos = SINONIMOS_COLUMNAS

    # -----------------------------
    # 1) ORIGEN (Ampliado con "toman" / "tienen")
    # -----------------------------
    def _get_target_source(self, texto):
        # Añadidas palabras de acción para detectar medicamentos
        meds = ["medicamento", "farmaco", "fármaco", "pastilla", "insulina", "metformina", 
                "tratamiento", "toman", "tienen", "prescrito", "toma", "tiene"]
        return "Medicamentos" if any(w in texto for w in meds) else "Validaciones"

    # -----------------------------
    # 2) OPERACIÓN (Media y Porcentaje)
    # -----------------------------
    def _extract_operation(self, texto):
        if any(w in texto for w in ["media", "promedio", "average"]): return "media"
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

    # -----------------------------
    # VARIABLE (Mejorada para no colisionar con filtros)
    # -----------------------------
    def _extract_variable(self, texto):
        # Priorizamos variables numéricas si hay una operación de media
        for palabra in sorted(self.sinonimos.keys(), key=len, reverse=True):
            if palabra in texto:
                return self.sinonimos[palabra]
        
        if any(w in texto for w in ["medicamento", "farmaco", "toman", "tienen"]):
            return "MEDICAMENTO"
        
        return "ID_REGISTRO"

    def _extract_group_by(self, texto):
        match = re.search(r"(?:por|segun|por\s+el|por\s+la|distribucion\s+de)\s+([a-zA-Záéíóú]+)", texto)
        if match:
            palabra = match.group(1)
            if palabra in self.sinonimos:
                return self.sinonimos[palabra]
        return None

    def _extract_limit(self, texto):
        match = re.search(r"top\s*(\d+)", texto)
        return int(match.group(1)) if match else None

    # -----------------------------
    # FILTROS (Reforzado para "toman x" y filtros cruzados)
    # -----------------------------
    def _extract_filters(self, texto, source):
        extracted = []
        texto_original = texto.lower()

        # Normalizar operadores
        texto = re.sub(r"menor\s+que|menor\s+a|menor\s+de|debajo\s+de|menor", "<", texto_original)
        texto = re.sub(r"mayor\s+que|mayor\s+a|mayor\s+de|encima\s+de|mayor", ">", texto)
        texto = re.sub(r"igual\s+a|igual", "=", texto)

        # 1) Filtros Numéricos
        sinonimos_ordenados = sorted(self.sinonimos.items(), key=lambda x: len(x[0]), reverse=True)
        for palabra, col_real in sinonimos_ordenados:
            pattern = rf"{palabra}\s*(<|>|=|<=|>=)\s*(\d+(?:\.\d+)?)"
            match = re.search(pattern, texto)
            if match:
                extracted.append({"col": col_real, "op": "==", "val": float(match.group(2))})
                texto = texto.replace(match.group(0), "")

        # 2) Filtro de SEXO (Hombre/Mujer)
        if "hombre" in texto_original or "varon" in texto_original:
            extracted.append({"col": "SEXO", "op": "==", "val": "HOMBRE"})
        if "mujer" in texto_original:
            extracted.append({"col": "SEXO", "op": "==", "val": "MUJER"})

        # 3) Filtro de MEDICAMENTOS (Soporta "toman X" o "tienen X")
        if source == "Medicamentos":
            palabras = texto_original.split()
            # Stopwords ampliadas para que "toman" o "tienen" no se filtren como medicamento
            stopwords = ["pacientes", "cuantos", "numero", "media", "edad", "medicamento", 
                         "medicamentos", "con", "del", "un", "el", "hay", "tienen", "toman", "toma", "tiene"]
            
            for p in palabras:
                # Si la palabra no es instrucción y es larga, es el nombre del fármaco
                if len(p) > 3 and p not in stopwords and p not in self.sinonimos:
                    extracted.append({"col": "MEDICAMENTO", "op": "contiene", "val": p.upper()})
                    break

        # 4) Centros y Residencias
        for cat in ["centro", "residencia"]:
            if cat in texto_original:
                partes = texto_original.split(cat)
                if len(partes) > 1:
                    valor = partes[1].strip().split(" ")[0]
                    if valor and len(valor) > 2:
                        extracted.append({"col": cat.upper(), "op": "contiene", "val": valor.upper()})

        return extracted

    # -----------------------------
    # PARSER PRINCIPAL (Lógica de % y Media Cruzada)
    # -----------------------------
    def parse_query(self, pregunta_usuario):
        texto = limpiar_texto(pregunta_usuario.lower())

        source = self._get_target_source(texto)
        operation = self._extract_operation(texto)
        variable = self._extract_variable(texto)
        group_by = self._extract_group_by(texto)
        limit = self._extract_limit(texto)
        filters = self._extract_filters(texto, source)

        # FIX para Media con Filtros: Asegurar que si pides "edad media de hombres", 
        # la variable sea EDAD y el filtro SEXO.
        if operation == "media" and variable == "ID_REGISTRO":
             # Intentar rescatar variable numérica si falló el detector
             if "edad" in texto: variable = "EDAD"
             if "fg" in texto: variable = "FG_CG"

        # FIX para Porcentajes: Si pide %, la variable suele ser el conteo de pacientes (ID_REGISTRO)
        # pero el motor necesita saber qué estamos filtrando para sacar el ratio.
        if operation == "porcentaje":
            if not variable or variable == "ID_REGISTRO":
                if "hombre" in texto or "mujer" in texto: variable = "SEXO"
                if source == "Medicamentos": variable = "MEDICAMENTO"

        # Lógica de TOP
        if limit and variable != "ID_REGISTRO":
            group_by = variable
            operation = "conteo"

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
