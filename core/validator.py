from core.catalog import SCHEMA
# --- ADICIÓN DE ERROR ---
from core.errors import CoreError

def validar_query(query_json):
    """
    Valida la integridad del JSON clínico contra el SCHEMA.
    Lanza CoreError si detecta inconsistencias.
    """
    try:
        # 1. Validar presencia de claves básicas
        if "origen" not in query_json:
            raise CoreError("validator.py", "El JSON no contiene la clave 'origen'")

        origen = query_json["origen"]
        if origen not in SCHEMA:
            raise CoreError(
                modulo="validator.py", 
                mensaje="Origen de datos no definido en el catálogo", 
                detalle=origen
            )
        
        # 2. Validar columnas en Bloque A (Filtros)
        cols_reales = SCHEMA[origen]["columnas"]
        for filtro in query_json.get("bloque_a", []):
            col_solicitada = filtro.get("col")
            if col_solicitada not in cols_reales:
                raise CoreError(
                    modulo="validator.py",
                    mensaje=f"La columna solicitada no existe en el origen {origen}",
                    detalle=col_solicitada
                )
        
        # 3. Validar consistencia del Bloque B (Agrupación)
        agrupar = query_json.get("bloque_b", {}).get("agrupar")
        if agrupar and agrupar != "Ninguno" and agrupar not in cols_reales:
             raise CoreError(
                modulo="validator.py",
                mensaje="La columna de agrupación no es válida para este origen",
                detalle=agrupar
            )

        return True, "OK"

    except CoreError as ce:
        # Re-lanzamos para el Orchestrator
        raise ce
    except Exception as e:
        # Fallo inesperado en la validación
        raise CoreError("validator.py", "Fallo crítico en el motor de validación", str(e))
