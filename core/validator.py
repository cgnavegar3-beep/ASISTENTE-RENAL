# core/validator.py
from core.catalog import SCHEMA

def validar_query(query_json):
    origen = query_json["origen"]
    if origen not in SCHEMA:
        return False, f"Origen {origen} no válido."
    
    cols_reales = SCHEMA[origen]["columnas"]
    for filtro in query_json["bloque_a"]:
        if filtro["col"] not in cols_reales:
            return False, f"La columna {filtro['col']} no existe en {origen}."
            
    return True, "OK"
