import re
from core.catalog import SCHEMA
from core.dictionary import SINONIMOS_COLUMNAS, MAPEO_OPERADORES
from core.normalizer import limpiar_texto
# --- ADICIÓN DE ERROR ---
from core.errors import CoreError 

class QueryGenerator:
    def __init__(self):
        self.schema = SCHEMA
        self.sinonimos = SINONIMOS_COLUMNAS
        self.operadores = MAPEO_OPERADORES

    def _detectar_origen(self, texto):
        t = limpiar_texto(texto)
        keywords_meds = ["medicamento", "farmaco", "pastilla", "metformina", "insulina"]
        if any(kw in t for kw in keywords_meds):
            return "Medicamentos"
        return "Validaciones"

    def _detectar_formato_grafico(self, texto):
        """Analiza si el usuario quiere un gráfico y de qué tipo."""
        t = limpiar_texto(texto)
        
        # Lógica de detección mejorada con lanzamiento de CoreError
        if any(w in t for w in ["grafico", "dibuja", "muestra", "visualiza", "barras", "torta", "histograma"]):
            # CASO DE ERROR: El sistema detecta que el usuario pide un gráfico no soportado
            if "histograma" in t:
                raise CoreError(
                    modulo="query_generator.py",
                    mensaje="Tipo de gráfico solicitado no está implementado aún",
                    detalle="histograma"
                )
            
            if "horizontal" in t:
                return "Barras Horizontales"
            elif any(w in t for w in ["torta", "sectores", "pie", "circular"]):
                return "Sectores"
            else:
                return "Barras Verticales"
        
        return "KPI"

    def _extraer_filtros(self, texto, origen):
        filtros = []
        texto_n = limpiar_texto(texto)
        
        # Validar si el origen existe en el esquema antes de proceder
        if origen not in self.schema:
            raise CoreError(
                modulo="query_generator.py",
                mensaje="Origen de datos no identificado en el esquema",
                detalle=origen
            )
            
        cols_disponibles = self.schema[origen]["columnas"]
        
        # ... (resto de tu lógica de extracción de filtros se mantiene igual) ...
        for palabra, col_tecnica in self.sinonimos.items():
            palabra_n = limpiar_texto(palabra)
            if palabra_n in texto_n:
                numeros = re.findall(r'\d+', texto_n)
                valor = int(numeros[0]) if numeros else ""
                if not valor:
                    palabras_pregunta = texto_n.split()
                    if palabra_n in palabras_pregunta:
                        idx = palabras_pregunta.index(palabra_n)
                        if idx + 1 < len(palabras_pregunta):
                            valor = palabras_pregunta[idx + 1].upper()

                op_detectado = "== (IGUAL)"
                for k_op, v_op in self.operadores.items():
                    if limpiar_texto(k_op) in texto_n:
                        op_detectado = v_op
                
                filtros.append({"col": col_tecnica, "op": op_detectado, "val": valor})
        return filtros

    def generar_json(self, pregunta_usuario):
        # Envolvemos la generación en un bloque para capturar fallos inesperados
        try:
            origen = self._detectar_origen(pregunta_usuario)
            formato = self._detectar_formato_grafico(pregunta_usuario)
            
            agrupar_por = "SEXO" 
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
        except CoreError as e:
            # Re-lanzamos el error de negocio para que Orchestrator lo capture
            raise e
        except Exception as e:
            # Capturamos cualquier otro fallo y lo envolvemos en CoreError
            raise CoreError(
                modulo="query_generator.py",
                mensaje="Fallo crítico durante la generación del JSON clínico",
                detalle=str(e)
            )
