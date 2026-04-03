# core/query_generator.py
import re
import json
from core.catalog import SCHEMA, OPERADORES, FORMATOS_VISUALIZACION
from core.dictionary import SINONIMOS_COLUMNAS, MAPEO_OPERADORES

class QueryGenerator:
    def __init__(self):
        self.schema = SCHEMA
        self.sinonimos = SINONIMOS_COLUMNAS
        self.operadores = MAPEO_OPERADORES

    def _detectar_origen(self, texto):
        """Determina si la consulta es de 'Medicamentos' o 'Validaciones'."""
        keywords_meds = ["medicamento", "fármaco", "metformina", "adecuación", "terapéutico", "riesgo"]
        if any(kw in texto.lower() for kw in keywords_meds):
            return "Medicamentos"
        return "Validaciones"

    def _extraer_filtros(self, texto, origen):
        """Busca patrones de filtros en el texto (Bloque A)."""
        filtros = []
        cols_disponibles = self.schema[origen]["columnas"]
        
        # Ejemplo de lógica de extracción simple por palabras clave
        for palabra, col_tecnica in self.sinonimos.items():
            if palabra in texto.lower() and col_tecnica in cols_disponibles:
                # Buscar números cercanos para operadores
                numeros = re.findall(r'\d+', texto)
                valor = int(numeros[0]) if numeros else ""
                
                # Detectar operador
                op_detectado = "== (IGUAL)" # Default
                for k_op, v_op in self.operadores.items():
                    if k_op in texto.lower():
                        op_detectado = v_op
                
                filtros.append({
                    "id": col_tecnica, # Simplificado para el test
                    "col": col_tecnica,
                    "op": op_detectado,
                    "val": valor
                })
        return filtros

    def generar_json(self, pregunta_usuario):
        """Compila el lenguaje natural a la estructura de 4 bloques."""
        origen = self._detectar_origen(pregunta_usuario)
        
        query_estructurada = {
            "origen": origen,
            "bloque_a": self._extraer_filtros(pregunta_usuario, origen),
            "bloque_b": {
                "variable": "ID_REGISTRO", # Default común
                "operacion": "Conteo Único (Pacientes)",
                "agrupar": "Ninguno"
            },
            "bloque_c": {
                "formato": "KPI" # Default
            },
            "bloque_d": {
                "ranking": "TOP" in pregunta_usuario.upper(),
                "elemento": None,
                "limit": 10
            }
        }

        # Lógica de decisión de visualización (Bloque C)
        if "gráfico" in pregunta_usuario.lower() or "barras" in pregunta_usuario.lower():
            query_estructurada["bloque_c"]["formato"] = "BARRAS H"
        elif "lista" in pregunta_usuario.lower():
            query_estructurada["bloque_c"]["formato"] = "LISTAR"

        return query_estructurada
