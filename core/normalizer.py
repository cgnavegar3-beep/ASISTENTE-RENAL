import unicodedata
import re

def limpiar_texto(t):
    """
    Normalización clínica avanzada:
    - limpia texto
    - conserva operadores (< > = <= >= !=)
    - normaliza lenguaje clínico tipo 'mas de', 'menos de'
    """

    if t is None:
        return ""

    # 1. string + strip
    texto = str(t).strip()

    # 2. quitar acentos
    texto = "".join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

    # 3. minúsculas
    texto = texto.lower()

    # 4. normalización de lenguaje clínico → operadores
    reemplazos = {
        "mayor o igual que": ">=",
        "menor o igual que": "<=",
        "mayor que": ">",
        "mas de": ">",
        "menos de": "<",
        "igual a": "=",
        "igual que": "=",
        "distinto de": "!=",
        "no igual": "!="
    }

    for k, v in reemplazos.items():
        texto = texto.replace(k, v)

    # 5. asegurar separación correcta de operadores (FG<60 → FG < 60)
    texto = re.sub(r'([a-zA-Z0-9])\s*(>=|<=|!=|=|>|<)\s*([a-zA-Z0-9])',
                   r'\1 \2 \3', texto)

    # 6. limpiar caracteres raros PERO conservar operadores
    texto = re.sub(r"[^\w\s<>=!.\-]", " ", texto)

    # 7. colapsar espacios
    texto = re.sub(r'\s+', ' ', texto).strip()

    return texto
