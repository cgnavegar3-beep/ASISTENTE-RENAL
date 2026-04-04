import streamlit as st
import traceback
# --- ADICIÓN DE ERROR ---
from core.errors import CoreError

class ClinicoOrchestrator:
    def __init__(self):
        # Importación diferida para evitar ciclos
        from core.query_generator import QueryGenerator
        from core.validator import validar_query
        from core.engine import ExecutionEngine
        
        self.generator = QueryGenerator()
        self.validar_func = validar_query # Referencia a la función de validación
        self.engine = ExecutionEngine()

    def procesar_pregunta(self, pregunta, df):
        """Punto de entrada principal con gestión de errores modular."""
        if df is None or df.empty:
            return None, "⚠️ **Error de Datos:** La base de datos no está cargada o está vacía.", None
            
        # Ejecución del flujo capturando errores específicos del Core
        try:
            return self._ejecutar_flujo(pregunta, df)
        
        except CoreError as e:
            # --- CAPTURA DE ERROR ESTRUCTURADO ---
            mensaje_clinico = (
                f"{str(e)}\n\n"
                f"👉 **Archivo a modificar:** `{e.modulo}`\n"
                f"💡 **Sugerencia:** Envíame el código original de `{e.modulo}` para aplicar el parche mínimo."
            )
            return None, mensaje_clinico, None

        except Exception as e:
            # --- CAPTURA DE ERROR IMPREVISTO (CRASH) ---
            error_stack = traceback.format_exc()
            mensaje_inesperado = (
                f"🚨 **Error Crítico Inesperado**\n\n"
                f"**Detalle:** `{str(e)}`\n"
                f"--- \n"
                f"Verifica la conexión con los módulos o el estado del DataFrame."
            )
            # Log para consola del desarrollador
            print(f"--- CRITICAL DEBUG ---\n{error_stack}")
            return None, mensaje_inesperado, None

    def _ejecutar_flujo(self, pregunta, df):
        """Privado: Ejecuta la cadena de responsabilidad."""
        
        # 1. GENERACIÓN: NL -> JSON (Puede lanzar CoreError en query_generator.py)
        query_json = self.generator.generar_json(pregunta)
        
        # 2. VALIDACIÓN: (Puede lanzar CoreError en validator.py)
        self.validar_func(query_json)
        
        # 3. FILTRADO: (Puede lanzar CoreError en engine.py)
        df_filtrado = self.engine.aplicar_filtros(df, query_json.get("bloque_a", []))
        
        # 4. ANÁLISIS MÉTRICO: (Puede lanzar CoreError en engine.py)
        resultado_num, frase_ia, df_final = self.engine.ejecutar_analisis(df_filtrado, query_json)
        
        return query_json, frase_ia, df_final
