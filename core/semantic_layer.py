import re
import unicodedata
from typing import Dict, List, Tuple

class SemanticResolver:
    def __init__(self):
        # Ordenamos los sinónimos por longitud de clave (descendente)
        # Esto asegura que "ajuste dosis mdrd" se evalúe antes que "ajuste"
        raw_synonyms = self._build_synonyms()
        self.synonyms = dict(sorted(raw_synonyms.items(), key=lambda x: len(x[0]), reverse=True))

    def _normalize_text(self, text: str) -> str:
        """Elimina acentos y limpia caracteres especiales."""
        if not text: return ""
        text = text.lower()
        text = "".join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        return text.strip()

    def _build_synonyms(self) -> Dict[str, str]:
        # He añadido versiones sin acento para mayor robustez
        return {
            "id paciente": "ID_REGISTRO",
            "paciente": "ID_REGISTRO",
            "registro": "ID_REGISTRO",
            
            # MEDICACIÓN
            "numero total de medicamentos": "Nº_TOTAL_MEDS_PAC",
            "total medicamentos": "Nº_TOTAL_MEDS_PAC",
            
            # FG COCKCROFT-GAULT (CG)
            "fg cockcroft gault": "FG_CG",
            "cockcroft gault": "FG_CG",
            "filtrado glomerular": "FG_CG",
            "fg": "FG_CG", # El genérico mapea al principal por defecto
            
            "medicamentos afectados cg": "Nº_TOT_AFEC_CG",
            "afectados cg": "Nº_TOT_AFEC_CG",
            "precaucion cg": "Nº_PRECAU_CG",
            "ajuste dosis cg": "Nº_AJUSTE_DOS_CG",
            "ajustes cg": "Nº_AJUSTE_DOS_CG",
            "toxicidad cg": "Nº_TOXICID_CG",
            "contraindicados cg": "Nº_CONTRAIND_CG",

            # FG MDRD
            "fg mdrd": "FG_MDRD",
            "filtrado mdrd": "FG_MDRD",
            "afectados mdrd": "Nº_TOT_AFEC_MDRD",
            "precaucion mdrd": "Nº_PRECAU_MDRD",
            "ajuste dosis mdrd": "Nº_AJUSTE_DOS_MDRD",
            "toxicidad mdrd": "Nº_TOXICID_MDRD",
            "contraindicados mdrd": "Nº_CONTRAIND_MDRD",

            # FG CKD-EPI
            "fg ckd": "FG_CKD",
            "ckd": "FG_CKD",
            "afectados ckd": "Nº_TOT_AFEC_CKD",
            "precaucion ckd": "Nº_PRECAU_CKD",
            "ajuste dosis ckd": "Nº_AJUSTE_DOS_CKD",
            "toxicidad ckd": "Nº_TOXICID_CKD",
            "contraindicados ckd": "Nº_CONTRAIND_CKD",

            # MÉDICO / ACEPTACIÓN
            "aceptacion medico": "ACEPTACION_MEDICO",
            "propuestas aceptadas": "ACEPTACION_MEDICO",
            "aceptacion": "ACEPTACION_MEDICO"
        }

    def resolve(self, text: str) -> str:
        if not text: return text
        
        t = self._normalize_text(text)

        # 1. Intento de match exacto (Máxima prioridad)
        if t in self.synonyms:
            return self.synonyms[t]

        # 2. Match por palabras clave (Búsqueda de la entidad más larga/específica)
        for synonym_key, column_name in self.synonyms.items():
            # Usamos regex para asegurar que matchee palabras completas (no sub-strings)
            if re.search(rf'\b{re.escape(synonym_key)}\b', t):
                return column_name

        return text

# Instancia global
semantic_resolver = SemanticResolver()

def resolve_column_name(text: str) -> str:
    return semantic_resolver.resolve(text)
