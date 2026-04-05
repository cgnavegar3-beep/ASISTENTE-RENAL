from core.catalog import SCHEMA
from core.errors import CoreError

def validar_query(query_json):
    try:
        if "origen" not in query_json:
            raise CoreError("validator.py", "Falta clave 'origen'")

        origen = query_json["origen"]

        if origen not in SCHEMA:
            raise CoreError("validator.py", "Origen no válido", origen)

        cols_reales = SCHEMA[origen]["columnas"]

        for filtro in query_json.get("bloque_a", []):
            col = filtro.get("col")
            if col and col not in cols_reales:
                raise CoreError(
                    "validator.py",
                    f"Columna no existe: {col}",
                    col
                )

        agrupar = query_json.get("bloque_b", {}).get("agrupar")

        if agrupar and agrupar != "Ninguno" and agrupar not in cols_reales:
            raise CoreError(
                "validator.py",
                "Columna de agrupación inválida",
                agrupar
            )

        return True, "OK"

    except CoreError:
        raise
    except Exception as e:
        raise CoreError("validator.py", "Error en validación", str(e))
