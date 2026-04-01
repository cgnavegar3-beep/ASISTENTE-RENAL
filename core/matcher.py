import re
import schema_resolver as sr
import semantic_layer as sl
from typing import Dict, Any, List, Optional

# Grupos de colisiones clínicas detectadas (Ambigüedad Crítica)
CLINICAL_MODELS = {
    "FG": ["FG_CG", "FG_MDRD", "FG_CKD"],
    "AFEC": ["Nº_TOT_AFEC_CG", "Nº_TOT_AFEC_MDRD", "Nº_TOT_AFEC_CKD"],
    "PRECAU": ["Nº_PRECAU_CG", "Nº_PRECAU_MDRD", "Nº_PRECAU_CKD"],
    "AJUSTE": ["Nº_AJUSTE_DOS_CG", "Nº_AJUSTE_DOS_MDRD", "Nº_AJUSTE_DOS_CKD"],
    "TOXIC": ["Nº_TOXICID_CG", "Nº_TOXICID_MDRD", "Nº_TOXICID_CKD"],
    "CONTRA": ["Nº_CONTRAIND_CG", "Nº_CONTRAIND_MDRD", "Nº_CONTRAIND_CKD"],
    "RIESGO": ["RIESGO_CG", "RIESGO_MDRD", "RIESGO_CKD"],
    "NIVEL": ["NIVEL_ADE_CG", "NIVEL_ADE_MDRD", "NIVEL_ADE_CKD"],
    "CAT": ["CAT_RIESGO_CG", "CAT_RIESGO_MDRD", "CAT_RIESGO_CKD"]
}


def _tokenize(text: str) -> List[str]:
    """Normaliza texto a tokens clínicos seguros."""
    return re.findall(r"[A-Z0-9Ñ]+", text.upper())


def score_candidate(user_input: str, candidate: str) -> float:
    """Calcula nivel de confianza entre input y columna del schema."""

    u = user_input.upper().strip()
    c = candidate.upper().strip()

    # 1. Match exacto
    if u == c:
        return 1.0

    # 2. Match semántico (IA)
    semantic_resolved = sl.resolve_column_name(u)
    if semantic_resolved == c:
        return 0.85

    # 3. Token overlap fuerte (subset)
    u_tokens = set(_tokenize(u))
    c_tokens = set(_tokenize(c))

    if u_tokens and u_tokens.issubset(c_tokens):
        return 0.7

    # 4. Intersección parcial
    intersection = u_tokens & c_tokens

    if len(intersection) >= 2:
        return 0.5

    # 5. Intersección débil
    if len(intersection) == 1:
        return 0.2

    return 0.0


def detect_ambiguity(column_name: str, dataset: str) -> Optional[List[str]]:
    """Detecta ambigüedad entre modelos clínicos (CG / MDRD / CKD)."""

    norm_col = sr.normalize_column_name(column_name)

    # Si ya especifica modelo → no ambiguo
    if any(m in norm_col for m in ["_CG", "_MDRD", "_CKD"]):
        return None

    for key, candidates in CLINICAL_MODELS.items():

        if norm_col == key or norm_col in key:

            valid_candidates = [
                c for c in candidates
                if c in sr.SCHEMA.get(dataset, [])
            ]

            if len(valid_candidates) > 1:
                return valid_candidates

    return None


def match_column(raw_column: str, dataset: str) -> Dict[str, Any]:
    """Resuelve una columna con scoring + ambigüedad clínica."""

    resolved = sl.resolve_column_name(raw_column)
    norm_resolved = sr.normalize_column_name(resolved)

    valid_columns = sr.SCHEMA.get(dataset, [])

    # 1. Ambigüedad clínica
    ambiguous_candidates = detect_ambiguity(norm_resolved, dataset)

    if ambiguous_candidates:
        return {
            "column": raw_column,
            "ambiguous": True,
            "candidates": ambiguous_candidates,
            "confidence": 0.0,
            "reason": "Ambigüedad entre modelos CG / MDRD / CKD"
        }

    # 2. Match exacto schema
    if norm_resolved in valid_columns:
        return {
            "column": norm_resolved,
            "ambiguous": False,
            "confidence": 1.0
        }

    # 3. Mejor candidato por scoring
    best_col = None
    max_score = 0.0

    for col in valid_columns:
        score = score_candidate(raw_column, col)

        if score > max_score:
            max_score = score
            best_col = col

    if best_col and max_score >= 0.5:
        return {
            "column": best_col,
            "ambiguous": False,
            "confidence": max_score
        }

    # 4. Fallback seguro
    return {
        "column": raw_column,
        "ambiguous": False,
        "confidence": 0.1,
        "error": "No se encontró coincidencia clara"
    }


def match_query(query: Dict[str, Any]) -> Dict[str, Any]:
    """Procesa query completa normalizando columnas."""

    dataset = query.get("dataset", "validaciones")
    matched_query = query.copy()

    # -------------------------
    # FILTROS
    # -------------------------
    if "filters" in matched_query:
        new_filters = []

        for f in matched_query["filters"]:
            match_res = match_column(f.get("column", ""), dataset)

            new_f = f.copy()
            new_f["column"] = match_res["column"]
            new_f["confidence"] = match_res["confidence"]

            if match_res.get("ambiguous"):
                new_f["ambiguous"] = True
                new_f["candidates"] = match_res["candidates"]

            new_filters.append(new_f)

        matched_query["filters"] = new_filters

    # -------------------------
    # SELECT / GROUPBY
    # -------------------------
    for field in ["select", "groupby"]:
        if field in matched_query:
            matched_query[field] = [
                match_column(c, dataset)["column"]
                for c in matched_query[field]
            ]

    # -------------------------
    # ORDER BY
    # -------------------------
    if "order_by" in matched_query and isinstance(matched_query["order_by"], dict):
        col = matched_query["order_by"].get("column", "")
        matched_query["order_by"]["column"] = match_column(col, dataset)["column"]

    return matched_query
