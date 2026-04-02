import pandas as pd
import traceback

from core.orchestrator import Orchestrator
from core.normalizer import Normalizer
from core.capa_2 import Capa2Controller
from core.execution_engine import ExecutionEngine
from core.fallback_engine import FallbackEngine


# -----------------------------
# MOCK DATA
# -----------------------------
df_dict = {
    "main": pd.DataFrame({
        "edad": [20, 30, 40, 70],
        "paciente": ["a", "b", "c", "d"]
    })
}


# -----------------------------
# MOCK COMPONENTS SIMPLES
# -----------------------------
class DummySemantic:
    def process(self, x):
        return x

class DummyMatcher:
    def match(self, x):
        return x


# -----------------------------
# DEPENDENCIAS
# -----------------------------
normalizer = Normalizer()

semantic_layer = DummySemantic()
matcher = DummyMatcher()

capa2 = Capa2Controller(
    llm=lambda x: '{"operation": "count"}'
)

executor = ExecutionEngine()
fallback = FallbackEngine()


# -----------------------------
# ORCHESTRATOR
# -----------------------------
orchestrator = Orchestrator(
    normalizer,
    semantic_layer,
    matcher,
    capa2,
    executor,
    fallback
)


# -----------------------------
# TEST QUERY
# -----------------------------
query = "cuenta pacientes"


# -----------------------------
# EJECUCIÓN CON DEBUG
# -----------------------------
try:
    print("\n🧪 EJECUTANDO TEST...\n")

    result = orchestrator.run(query, df_dict)

    print("\n✅ RESULTADO FINAL:")
    print(result)

except Exception as e:

    print("\n❌ ERROR DETECTADO:")
    print(str(e))

    print("\n📍 TRACE COMPLETO (dónde falla):")
    traceback.print_exc()
