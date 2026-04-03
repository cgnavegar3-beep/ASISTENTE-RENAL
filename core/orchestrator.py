# core/orchestrator.py
import streamlit as st
from core.query_generator import QueryGenerator
from core.validator import QueryValidator
from core.engine import ExecutionEngine

class ClinicoOrchestrator:
    def __init__(self):
        # Inicializamos los tres pilares del CORE
        self.generator = QueryGenerator()
        self.validator = QueryValidator()
        self.engine = ExecutionEngine()

    def procesar_pregunta(self, pregunta, df):
        """
        Punto de entrada principal. 
        Llama a la función interna cacheada para ahorrar tiempo y recursos.
        """
        # Validamos que el DataFrame no sea None antes de procesar
        if df is None or df.empty:
            return None, "Error: No hay datos cargados para analizar.", None
            
        return self._ejecutar_logica_con_cache(pregunta, df)

    @st.cache_data(show_spinner="Analizando base de datos...")
    def _ejecutar_logica_con_cache(_self, pregunta, df):
        """
        Esta función está protegida por la caché de Streamlit.
        El prefijo '_self' con guion bajo le dice a Streamlit que no intente 
        cachear la instancia de la clase, solo los resultados.
        """
        try:
            # 1. GENERACIÓN: Traducir lenguaje natural a JSON técnico
            query_json = _self.generator.generar_json(pregunta)
            
            # 2. VALIDACIÓN: Revisar que la consulta tenga sentido y sea segura
            es_valido, mensaje_error = _self.validator.validar_solicitud(query_json)
            
            if not es_valido:
                return query_json, mensaje_error, None

            # 3. FILTRADO: Aplicar los filtros del Bloque A sobre el DataFrame
            df_filtrado = _self.engine.aplicar_filtros(df, query_json["bloque_a"])
            
            # 4. EJECUCIÓN: Calcular el Bloque B y generar la frase humana
            resultado_num, frase_ia, df_final = _self.engine.ejecutar_analisis(df_filtrado, query_json)
            
            return query_json, frase_ia, df_final

        except Exception as e:
            error_msg = f"❌ Error crítico en el procesamiento: {str(e)}"
            return None, error_msg, None
