nl_parser.py
   ↓
normalizer.py
   ↓
synonym_resolver.py  (+ column_synonyms.py)
   ↓
intent_parser.py
   ↓
clinical_semantic_mapper.py
   ↓
query_builder.py
   ↓
execution_engine.py
   ↓
viz_builder.py
   ↓
response_templates.py
📦 🔍 QUÉ HACE CADA ARCHIVO (CLARO Y SIN RUIDO)
🟢 1. ENTRADA Y LIMPIEZA
nl_parser.py

👉 punto de entrada

recibe texto del usuario
lo pasa al pipeline
normalizer.py

👉 limpia texto

minúsculas
acentos
espacios
synonym_resolver.py

👉 traduce lenguaje → columnas reales

usa:

column_synonyms.py

👉 diccionario (TU clave real)

Ej:

"filtrado glomerular" → FG_CG
"riesgo" → NIVEL_ADE_CG
🟡 2. INTERPRETACIÓN (SIN IA)
intent_parser.py

👉 detecta:

count / mean / sum / %
filtros básicos
group by
tipo de output
clinical_semantic_mapper.py

👉 convierte conceptos clínicos → valores reales

Ej:

"riesgo alto" → NIVEL_ADE_CG >= 3

⚠️ importante: aquí NO se decide nada clínico, solo equivalencias

🔵 3. COMPILACIÓN (EL CORE REAL)
query_builder.py 🔥

👉 convierte todo → DSL final

{
  "filters": [],
  "aggregation": {},
  "group_by": ...
}

👉 ESTE es tu “compilador”

🔴 4. EJECUCIÓN
execution_engine.py

👉 ejecuta en pandas:

filtros
groupby
agregaciones
top N
viz_builder.py

👉 convierte resultado → gráfico

bar
histogram
ranking
response_templates.py

👉 convierte resultado → lenguaje humano

tabla
lista
texto tipo “hay X pacientes…”
🟣 5. SOPORTE (NO TOCAR DE MOMENTO)
semantic_cache.py

👉 cachea consultas (bien 👍)

session_cache.py

👉 contexto sesión (opcional)

schema_definitions.py

👉 define columnas válidas

schema_resolver.py

👉 valida columnas

validation_engine.py

👉 evita queries inválidas

⚪ 6. NO CRÍTICOS (PUEDEN QUEDARSE)
matcher.py

👉 matching (puede quedar)

semantic_layer.py

👉 capa semántica (ligera, no IA)

fallback_engine.py

👉 por si algo falla

capa2.py

👉 si es tu antigua capa IA → ahora NO se usa
(no hace falta tocar aún)

🧠 RESUMEN CLAVE (MUY IMPORTANTE)

Tu sistema ahora es:

Lenguaje natural
   ↓
Normalización + sinónimos
   ↓
Intento estructurado
   ↓
Mapeo clínico simple
   ↓
🔥 QUERY BUILDER (DSL)
   ↓
Pandas real
   ↓
Visualización / respuesta
🔒 ESTADO ACTUAL
✔ NO necesitas eliminar nada
✔ NO necesitas añadir nada
✔ YA tienes todo
🚀 SIGUIENTE PASO (REAL, NO TEÓRICO)
