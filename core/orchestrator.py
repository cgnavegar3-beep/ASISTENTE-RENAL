class Orchestrator:

    def __init__(self, normalizer, semantic_layer, matcher,
                 capa2, executor, fallback_engine):

        self.normalizer = normalizer
        self.semantic_layer = semantic_layer
        self.matcher = matcher
        self.capa2 = capa2
        self.executor = executor
        self.fallback = fallback_engine

    def run(self, user_input: str, df_dict: dict):

        plan = None  # importante para fallback

        try:
            # 1. NORMALIZACIÓN
            clean_input = self.normalizer.normalize_text(user_input)

            # 2. SEMANTIC LAYER
            enriched_input = self.semantic_layer.process(clean_input)

            # 3. MATCHER
            matched_input = self.matcher.match(enriched_input)

            # 4. CAPA 2 → PLAN ESTRUCTURADO (IA)
            plan = self.capa2.parse(matched_input)

            # 5. VALIDACIÓN MÍNIMA DEL PLAN
            if not isinstance(plan, dict):
                raise ValueError("Plan inválido: no es dict")

            if "operation" not in plan:
                raise ValueError("Plan inválido: falta 'operation'")

            # 6. EJECUCIÓN PRINCIPAL
            result = self.executor.execute_plan(plan, df_dict)

            return {
                "status": "success",
                "result": result,
                "plan": plan
            }

        except Exception as e:

            # 7. FALLBACK ENGINE (seguro)
            try:
                fallback_result = self.fallback.execute(
                    plan if plan else {},
                    df_dict
                )

                return {
                    "status": "fallback",
                    "result": fallback_result,
                    "error": str(e),
                    "plan": plan
                }

            except Exception as e2:

                return {
                    "status": "failed",
                    "error": str(e2),
                    "plan": plan
                }
