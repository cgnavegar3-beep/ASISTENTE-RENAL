# core/orchestrator.py
import streamlit as st
import traceback

class ClinicoOrchestrator:
    def __init__(self):
        # Importación diferida para evitar ciclos de importación
        from core.query_generator import QueryGenerator
        from core.validator import QueryValidator
        from core.engine import ExecutionEngine
        
        self.generator = QueryGenerator()
        self.validator = QueryValidator()
        self.engine = ExecutionEngine()

    def procesar_pregunta(self, pregunta, df):
        """Punto de entrada con gestión de errores por etapas."""
        if df is None or df.empty:
            return None, "⚠️ **Error de Datos:** La base de datos no está cargada o está vacía.", None
            
        return self._ejecutar_logica_con_cache(pregunta, df)

    @st.cache_data(show_spinner="Anclando el motor de búsqueda...")
    def _ejecutar_logica_con_cache(_self, pregunta, df):
        # El rastreador de etapa nos dirá exactamente dónde falló el código
        etapa_actual = "Inicialización"
        
        try:
            # 1. TRADUCCIÓN A JSON
            etapa_actual = "Generación de Query (QueryGenerator)"
            query_json = _self.generator.generar_json(pregunta)
            
            # 2. VALIDACIÓN DE REGLAS
            etapa_actual = "Validación Técnica (Validator)"
            es_valido, mensaje_error = _self.validator.validar_solicitud(query_json)
            if not es_valido:
                # Error controlado (por reglas de negocio)
                return query_json, f"📝 **Nota:** {mensaje_error}", None

            # 3. FILTRADO DE DATOS
            etapa_actual = "Filtrado de Registros (Engine -> Bloque A)"
            df_filtrado = _self.engine.aplicar_filtros(df, query_json["bloque_a"])
            
            # 4. CÁLCULOS Y RESPUESTA
            etapa_actual = "Cálculo de Resultados (Engine -> Bloque B)"
            resultado_num, frase_ia, df_final = _self.engine.ejecutar_analisis(df_filtrado, query_json)
            
            return query_json, frase_ia, df_final

        except Exception as e:
            # Captura el error técnico (el 'Crash')
            error_stack = traceback.format_exc()
            
            # Mensaje detallado para el chat
            mensaje_diagnostico = (
                f"🚨 **¡Ups! Algo ha fallado en el motor.**\n\n"
                f"**¿Dónde ocurrió?** En la etapa de: `{etapa_actual}`\n"
                f"**Error técnico:** `{str(e)}` \n\n"
                f"--- \n"
                f"🔧 **Sugerencia:** Revisa que el nombre de las columnas en tu Excel coincida con el Catálogo."
            )
            
            # Esto se imprime en los logs internos de Streamlit para el desarrollador
            print(f"--- DEBUG LOG ---\n{error_stack}\n-----------------")
            
            return None, mensaje_diagnostico, None
