# core/query_generator.py
import re
from core.catalog import SCHEMA
from core.dictionary import SINONIMOS_COLUMNAS, MAPEO_OPERADORES
from core.normalizer import limpiar_texto

class QueryGenerator:
    def __init__(self):
        self.schema = SCHEMA
        self.sinonimos = SINONIMOS_COLUMNAS
        self.operadores = MAPEO_OPERADORES

    def _detectar_origen(self, texto):
        t = limpiar_texto(texto)
        # Si menciona medicamentos o fármacos, va a esa tabla
        keywords_meds = ["medicamento", "farmaco", "pastilla", "metformina", "insulina"]
        if any(kw in t for kw in keywords_meds):
            return "Medicamentos"
        return "Validaciones"

    def _detectar_formato_grafico(self, texto):
        """Analiza si el usuario quiere un gráfico y de qué tipo."""
        t = limpiar_texto(texto)
        
        if any(w in t for w in ["grafico", "dibuja", "muestra", "visualiza", "barras", "torta"]):
            if "horizontal" in t:
                return "Barras Horizontales"
            elif any(w in t for w in ["torta", "sectores", "pie", "circular"]):
                return "Sectores"
            else:
                return "Barras Verticales"
        return "KPI" # Por defecto devuelve solo el número

    def _extraer_filtros(self, texto, origen):
        filtros = []
        texto_n = limpiar_texto(texto)
        cols_disponibles = self.schema[origen]["columnas"]
        
        for palabra, col_tecnica in self.sinonimos.items():
            palabra_n = limpiar_texto(palabra)
            if palabra_n in texto_n:
                # Buscar números para filtros tipo "mayor que 80"
                numeros = re.findall(r'\d+', texto_n)
                valor = int(numeros[0]) if numeros else ""
                
                # Si no hay número, buscamos el valor de texto (ej: Centro A)
                if not valor:
                    palabras_pregunta = texto_n.split()
                    if palabra_n in palabras_pregunta:
                        idx = palabras_pregunta.index(palabra_n)
                        if idx + 1 < len(palabras_pregunta):
                            valor = palabras_pregunta[idx + 1].upper()

                # Detectar el operador (>, <, ==)
                op_detectado = "== (IGUAL)"
                for k_op, v_op in self.operadores.items():
                    if limpiar_texto(k_op) in texto_n:
                        op_detectado = v_op
                
                filtros.append({"col": col_tecnica, "op": op_detectado, "val": valor})
        return filtros

    def generar_json(self, pregunta_usuario):
        origen = self._detectar_origen(pregunta_usuario)
        formato = self._detectar_formato_grafico(pregunta_usuario)
        
        # Intentamos adivinar por qué columna agrupar si pide un gráfico
        agrupar_por = "SEXO" # Valor seguro por defecto
        for palabra, col_tecnica in self.sinonimos.items():
            if limpiar_texto(palabra) in limpiar_texto(pregunta_usuario):
                agrupar_por = col_tecnica

        return {
            "origen": origen,
            "bloque_a": self._extraer_filtros(pregunta_usuario, origen),
            "bloque_b": {
                "variable": "ID_REGISTRO",
                "operacion": "Conteo Único (Pacientes)",
                "agrupar": agrupar_por if formato != "KPI" else "Ninguno"
            },
            "bloque_c": {"formato": formato},
            "bloque_d": {"ranking": False, "elemento": None, "limit": 10}
        }
