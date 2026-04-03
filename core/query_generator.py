# core/query_generator.py
import re
from core.catalog import SCHEMA
from core.dictionary import SINONIMOS_COLUMNAS, MAPEO_OPERADORES
from core.normalizer import limpiar_texto # <-- Importamos tu limpiador

class QueryGenerator:
    def __init__(self):
        self.schema = SCHEMA
        self.sinonimos = SINONIMOS_COLUMNAS
        self.operadores = MAPEO_OPERADORES

    def _detectar_origen(self, texto):
        t = limpiar_texto(texto)
        keywords_meds = ["medicamento", "farmaco", "metformina", "adecuacion", "riesgo"]
        if any(kw in t for kw in keywords_meds):
            return "Medicamentos"
        return "Validaciones"

    def _extraer_filtros(self, texto, origen):
        filtros = []
        texto_n = limpiar_texto(texto) # Limpiamos la pregunta del usuario
        cols_disponibles = self.schema[origen]["columnas"]
        
        # Buscamos cada sinónimo en la pregunta limpia
        for palabra, col_tecnica in self.sinonimos.items():
            palabra_n = limpiar_texto(palabra)
            if palabra_n in texto_n:
                # Extraer valor numérico
                numeros = re.findall(r'\d+', texto_n)
                valor = int(numeros[0]) if numeros else ""
                
                # Si no hay números, quizás el valor es una palabra (ej: "Metformina")
                # Buscamos palabras después del nombre de la columna
                if not valor:
                    palabras_pregunta = texto_n.split()
                    if palabra_n in palabras_pregunta:
                        idx = palabras_pregunta.index(palabra_n)
                        if idx + 1 < len(palabras_pregunta):
                            valor = palabras_pregunta[idx + 1].upper() # Valor en MAYUS para el Excel

                op_detectado = "== (IGUAL)"
                for k_op, v_op in self.operadores.items():
                    if limpiar_texto(k_op) in texto_n:
                        op_detectado = v_op
                
                filtros.append({
                    "col": col_tecnica,
                    "op": op_detectado,
                    "val": valor
                })
        return filtros

    def generar_json(self, pregunta_usuario):
        origen = self._detectar_origen(pregunta_usuario)
        return {
            "origen": origen,
            "bloque_a": self._extraer_filtros(pregunta_usuario, origen),
            "bloque_b": {
                "variable": "ID_REGISTRO",
                "operacion": "Conteo Único (Pacientes)",
                "agrupar": "Ninguno"
            },
            "bloque_c": {"formato": "KPI"},
            "bloque_d": {"ranking": False, "elemento": None, "limit": 10}
        }
