import json
import re

class Capa2Controller:

    def __init__(self, llm):
        self.llm = llm

    def build_prompt(self, user_input: str):
        return f"""
Eres un traductor de consultas a un JSON estructurado.

Devuelve SOLO JSON válido con esta estructura:

{{
  "operation": "count | sum | avg | groupby | filter | max | min",
  "target": "columna",
  "group_by": "columna opcional",
  "filters": []
}}

Reglas:
- NO expliques nada
- NO texto adicional
- SOLO JSON

Usuario: {user_input}
"""

    def parse(self, user_input: str):
        response = self.llm(self.build_prompt(user_input))

        try:
            data = json.loads(response)
        except:
            raise ValueError("Capa2: JSON inválido")

        # validación mínima
        if "operation" not in data:
            raise ValueError("Capa2: falta operation")

        return data
