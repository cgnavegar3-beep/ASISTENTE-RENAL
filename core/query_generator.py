import re
from core.catalog import SCHEMA
from core.dictionary import SINONIMOS_COLUMNAS, MAPEO_OPERADORES
from core.normalizer import limpiar_texto
from core.errors import CoreError 

class QueryGenerator:
    def __init__(self):
        self.schema = SCHEMA
        self.sinonimos = SINONIMOS_COLUMNAS
        self.operadores = MAPEO_OPERADORES

    def _get_target_source(self, texto_n):
        """Identifica el origen de datos (Entidad principal)."""
        keywords_meds = ["medicamento", "farmaco", "pastilla", "metformina", "insulina"]
        if any(kw in texto_n for kw in keywords_meds):
            return "Medicamentos"
        return "Validaciones"

    def _parse_visual_intent(self, texto_n):
        """Mapea la intención visual a un estándar técnico único."""
        if "histograma" in texto_n:
            raise CoreError("query_generator.py", "Gráfico no soportado", "histograma")
        
        # Diccionario de mapeo técnico directo
        if any(w in texto_n for w in ["torta", "sectores", "pie", "circular"]):
            return "pie"
        if "horizontal" in texto_n:
            return "bar_h"
        if any(w in texto_n for w in ["grafico", "dibuja", "barras", "visualiza"]):
            return "bar"
        
        return "kpi"

    def _extract_filters(self, texto_n, source):
        """Extrae criterios de filtrado usando el catálogo y sinónimos."""
        if source not in self.schema:
            raise CoreError("query_generator.py", "Origen no válido", source)
            
        extracted = []
        # Buscamos coincidencias semánticas
        for palabra, col_tecnica in self.sinonimos.items():
            palabra_n = limpiar_texto(palabra)
            if palabra_n in texto_n:
                # Extracción simple de valor (numérico o palabra siguiente)
                numeros = re.findall(r'\d+', texto_n)
                valor = int(numeros[0]) if numeros else ""
                
                if not valor:
                    palabras = texto_n.split()
                    if palabra_n in palabras:
                        idx = palabras.index(palabra_n)
                        if idx + 1 < len(palabras):
                            valor = palabras[idx + 1].upper()

                # Mapeo de operador técnico (eliminamos etiquetas como "== (IGUAL)")
                op_tecnico = "=="
                for k_op, v_op in self.operadores.items():
                    if limpiar_texto(k_op) in texto_n:
                        # Limpiamos el valor del diccionario de sinónimos para dejar solo el símbolo
                        op_tecnico = v_op.split()[0] 
                
                extracted.append({"col": col_tecnica, "op": op_tecnico, "val": valor})
        return extracted

    def parse_query(self, pregunta_usuario):
        """
        Punto de entrada: Convierte lenguaje natural en Estructura Intermedia.
        Esta estructura es agnóstica a la organización por 'bloques' del engine.
        """
        try:
            texto_n = limpiar_texto(pregunta_usuario)
            source = self._get_target_source(texto_n)
            visual_type = self._parse_visual_intent(texto_n)
            
            # Detectar columna de interés o agrupación
            dimension = "SEXO" # Default
            for palabra, col_tecnica in self.sinonimos.items():
                if limpiar_texto(palabra) in texto_n:
                    dimension = col_tecnica

            # --- ESTRUCTURA INTERMEDIA (AST LIGERO) ---
            return {
                "metadata": {
                    "source": source,
                    "intent": "visual" if visual_type != "kpi" else "metric"
                },
                "request": {
                    "metric": "conteo", # Estándar técnico
                    "target_col": "ID_REGISTRO",
                    "filters": self._extract_filters(texto_n, source),
                    "group_by": dimension if visual_type != "kpi" else None,
                    "chart_type": visual_type
                }
            }

        except CoreError as e:
            raise e
        except Exception as e:
            raise CoreError(
                modulo="query_generator.py",
                mensaje="Error interpretando la consulta clínica",
                detalle=str(e)
            )
