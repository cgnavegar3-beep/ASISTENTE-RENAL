import traceback
import pandas as pd

from core.errors import CoreError
from core.policy_defaults import apply_clinical_policies
from core.query_generator import QueryGenerator
from core.engine import ExecutionEngine


class ClinicoOrchestrator:
    def __init__(self):
        self.parser = QueryGenerator()
        self.engine = ExecutionEngine()

    def _ast_to_engine_schema(self, ast):
        """
        Normaliza el AST generado por el parser al esquema que espera el Engine.
        Blindado para asegurar que los gráficos se activen correctamente.
        """
        req = ast.get("request", {})
        meta = ast.get("metadata", {})

        # 1. Limpieza de filtros (bloque_a)
        filtros_originales = req.get("filters", [])
        filtros_validos = [
            f for f in filtros_originales
            if f.get("val") not in [None, "", "null", [], "NULL"]
        ]

        # 2. Lógica de visualización (bloque_c)
        chart_type = req.get("chart_type", "kpi")
        group_by = req.get("group_by")

        # Si hay agrupación pero el tipo es kpi, forzamos gráfico de barras
        if group_by and chart_type == "kpi":
            chart_type = "bar"

        # 3. Construcción del esquema final
        return {
            "origen": meta.get("source", "Validaciones"),
            "bloque_a": filtros_validos,
            "bloque_b": {
                "variable": req.get("target_col") or "ID_REGISTRO",
                "operacion": req.get("metric") or "conteo",
                "agrupar": group_by if group_by != "NULL" else None
            },
            "bloque_c": {
                "tipo": chart_type
            },
            "bloque_d": {
                "limit": req.get("limit") or 10
            },
            # Fusionamos bloques en el request para que el engine lo lea directo
            "request": {
                "metric": req.get("metric") or "conteo",
                "target_col": req.get("target_col") or "ID_REGISTRO",
                "group_by": group_by if group_by != "NULL" else None,
                "limit": req.get("limit") or 10
            }
        }

    def procesar_pregunta(self, pregunta, df):
        """
        Flujo principal de procesamiento. Blindado contra DataFrames vacíos.
        """
        if df is None or (isinstance(df, pd.DataFrame) and df.empty):
            return None, "⚠️ Error: DataFrame no disponible o vacío.", None

        try:
            # 1. PARSEO NLP
            ast_raw = self.parser.parse_query(pregunta)

            # 2. POLÍTICAS CLÍNICAS
            ast_policed = apply_clinical_policies(ast_raw)

            # 3. NORMALIZACIÓN
            query_json = self._ast_to_engine_schema(ast_policed)

            # 4. FILTRADO (Bloque A)
            df_filtrado = self.engine.aplicar_filtros(
                df.copy(), # Usamos copia para no alterar el original
                query_json["bloque_a"]
            )

            # 5. EJECUCIÓN ANALÍTICA (FIX: Recibimos un solo objeto resultado)
            # Esto evita el error "cannot unpack non-iterable int object"
            resultado_analisis = self.engine.ejecutar_analisis(
                df_filtrado,
                query_json["request"]
            )

            # 6. GESTIÓN DE RESULTADOS (Diferenciar entre número y tabla)
            figura = None
            df_final = None
            
            if isinstance(resultado_analisis, pd.DataFrame):
                # Caso Top N / Ranking
                df_final = resultado_analisis
                frase = f"Resultados por {query_json['bloque_b']['agrupar']}:"
                # Generación de gráfico si se solicita
                if query_json["bloque_c"]["tipo"] != "kpi":
                    figura = self.engine.generar_grafico(df_final, query_json)
            else:
                # Caso Conteo / Media / Porcentaje (Escalar)
                frase = f"Resultado: {resultado_analisis}"
                df_final = None

            # 7. RETORNO CONSISTENTE
            return query_json, frase, figura

        except CoreError as e:
            return None, f"❌ Error en {e.modulo}: {e.mensaje}", None

        except Exception as e:
            print(f"--- DETALLE DEL ERROR ---")
            print(traceback.format_exc())
            return None, f"🚨 Error crítico en el sistema: {str(e)}", None
