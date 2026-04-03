# core/orchestrator.py
import streamlit as st
import traceback  # Para rastrear el error exacto en el código

class ClinicoOrchestrator:
    def __init__(self):
        from core.query_generator import QueryGenerator
        from core.validator import QueryValidator
        from core.engine import ExecutionEngine
        
        self.generator = QueryGenerator()
        self.validator = QueryValidator()
        self.engine = ExecutionEngine()

    def procesar_pregunta(self, pregunta, df):
        if df is None or df.empty:
            return None, "⚠️ Error: La base de datos está vacía o no se ha cargado correctamente.", None
            
        return self._ejecutar_logica_con_cache(pregunta, df)

    @st.cache_data(show_spinner="Analizando datos...")
    def _ejecutar_logica_con_cache(_self, pregunta, df):
        etapa = "Inicio"
        try:
            # 1. GENERACIÓN
            etapa = "Generación de JSON (QueryGenerator)"
            query_json = _self.generator.generar_json(pregunta)
            
            # 2. VALIDACIÓN
            etapa = "Validación de Consulta (Validator)"
            es_valido, mensaje_error = _self.validator.validar_solicitud(query_json)
            if not es_valido:
                return query_json, f"🚫 Validación: {mensaje_error}", None

            # 3. FILTRADO
            etapa = "Filtrado de Datos (Engine - Aplicar Filtros)"
            df_filtrado = _self.engine.aplicar_filtros(df, query_json["bloque_a"])
            
            # 4. EJECUCIÓN
            etapa = "Cálculo Final (Engine - Ejecutar Análisis)"
            resultado_num, frase_ia, df_final = _self.engine.ejecutar_analisis(df_filtrado, query_json)
            
            return query_json, frase_ia, df_final

        except Exception as e:
            # Capturamos el error técnico real
            error_detallado = traceback.format_exc()
            
            # Construimos un mensaje útil para el usuario/desarrollador
            mensaje_fallo = (
                f"❌ **Error detectado en el Motor**\n\n"
                f"**Etapa:** {etapa}\n"
                f"**Fallo:** {str(e)}\n\n"
                f"---\n"
                f"💡 *Consejo: Revisa si la columna o el valor existen en el Excel/Google Sheets.*"
            )
            
            # Imprimimos en la consola de Streamlit para el programador
            print(f"DEBUG ERROR:\n{error_detallado}")
            
            return None, mensaje_fallo, None
