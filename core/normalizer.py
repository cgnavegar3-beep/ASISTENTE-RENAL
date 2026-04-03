# core/normalizer.py
import unicodedata
import re

def limpiar_texto(t):
    """
    Normalización total: 
    1. Convierte a String.
    2. Elimina espacios extra.
    3. Pasa a minúsculas.
    4. Elimina acentos/diacríticos.
    5. Elimina caracteres especiales no deseados.
    """
    if t is None: return ""
    
    # 1. Convertir a string y quitar espacios extremos
    texto = str(t).strip()
    
    # 2. Eliminar acentos
    texto = "".join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    
    # 3. Minúsculas y eliminar espacios dobles internos
    texto = texto.lower()
    texto = re.sub(r'\s+', ' ', texto)
    
    # 4. Limpieza de caracteres no alfanuméricos (opcional, manteniendo espacios)
    # texto = re.sub(r'[^\w\s]', '', texto) 
    
    return texto
