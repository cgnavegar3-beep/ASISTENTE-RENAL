def _extract_operation(self, texto):
        if any(w in texto for w in ["media", "promedio", "avg"]): return "media"
        # Quitamos % de aquí para que no se clasifique como KPI numérico simple
        if any(w in texto for w in ["porcentaje", "proporcion"]): return "porcentaje"
        return "conteo"

    def parse_query(self, pregunta_usuario):
        texto_base = limpiar_texto(pregunta_usuario.lower())
        texto = self._normalizar_operadores(texto_base)
        
        source = self._get_target_source(texto)
        operation = self._extract_operation(texto)
        group_by = self._extract_group_by(texto)
        filters = self._extract_all_filters(texto, source)
        
        # --- NUEVA LÓGICA PARA % ---
        # Si detecta el símbolo %, forzamos que agrupe por algo para poder sacar sectores
        es_peticion_porcentaje = "%" in texto or operation == "porcentaje"
        
        if es_peticion_porcentaje and not group_by:
            # Si pide % pero no detectamos grupo, intentamos deducirlo
            if source == "Medicamentos": group_by = "MEDICAMENTO"
            else: group_by = "RIESGO_CG"

        chart_type = "kpi"
        if group_by or es_peticion_porcentaje:
            chart_type = "bar" # Por defecto
            if es_peticion_porcentaje or any(w in texto for w in ["sectores", "pie", "reparto"]):
                chart_type = "pie"
        
        # Si es sectores, la intención DEBE ser visual para que el motor devuelva una tabla
        intent = "visual" if chart_type != "kpi" else "kpi"
        
        # ... (resto de variables igual que antes)

        return {
            "metadata": {"source": source, "intent": intent},
            "request": {
                "metric": "conteo" if es_peticion_porcentaje else operation,
                "target_col": "MEDICAMENTO" if source == "Medicamentos" else "ID_REGISTRO",
                "filters": filters,
                "group_by": group_by,
                "chart_type": chart_type,
                "limit": 10 if es_peticion_porcentaje else None
            }
        }
