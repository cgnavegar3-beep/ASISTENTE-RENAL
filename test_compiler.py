# test_compiler.py
import pandas as pd
from core.orchestrator import ClinicoOrchestrator

# 1. Creamos un DataFrame de prueba (Simulando Google Sheets)
data_prueba = {
    "ID_REGISTRO": [1, 2, 3, 4],
    "SEXO": ["MUJER", "HOMBRE", "MUJER", "MUJER"],
    "EDAD": [85, 40, 75, 90],
    "MEDICAMENTO": ["METFORMINA", "ASPIRINA", "METFORMINA", "INSULINA"],
    "CENTRO": ["A", "B", "A", "C"],
    "FG_CG": [45, 90, 55, 30]
}
df_test = pd.DataFrame(data_prueba)

# 2. Inicializamos el orquestador
orc = ClinicoOrchestrator()

def probar(pregunta):
    print(f"\n--- 🤖 PREGUNTA: '{pregunta}' ---")
    
    # Ejecutamos el flujo completo
    query_json, respuesta, df_res = orc.procesar_pregunta(pregunta, df_test)
    
    if query_json:
        print(f"✅ JSON GENERADO:\n{query_json}")
        print(f"💬 RESPUESTA IA: {respuesta}")
        print(f"📊 REGISTROS ENCONTRADOS: {len(df_res) if df_res is not None else 0}")
    else:
        print(f"❌ ERROR: {respuesta}")

# 3. LANZAMOS TESTS DE ESTRÉS
if __name__ == "__main__":
    # Test 1: Filtro simple
    probar("¿Cuántas mujeres hay?")
    
    # Test 2: Filtro doble (Edad y Medicamento)
    probar("Pacientes mayores de 80 con metformina")
    
    # Test 3: Filtro clínico complejo
    probar("Mujeres con fg menor de 60 en el Centro A")
    
    # Test 4: Caso de error (Columna inexistente)
    probar("¿Cuántos pacientes tienen diabetes?")
