 ast_raw = self.parser.parse_query(pregunta)
            ast_policed = apply_clinical_policies(ast_raw)

            query_json = self._ast_to_engine_schema(ast_policed)

            df_filtrado = self.engine.aplicar_filtros(df, query_json["bloque_a"])

            res_num, frase, df_final = self.engine.ejecutar_analisis(
                df_filtrado,
                query_json
            )

            figura = self.engine.generar_grafico(df_final, query_json)

            return query_json, frase, figura

        except CoreError as e:
            return None, f"❌ Error en {e.modulo}: {e.mensaje}", None

        except Exception:
            print(traceback.format_exc())
            return None, "🚨 Error Crítico en el sistema", None
