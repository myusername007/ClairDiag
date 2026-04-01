# ── NSE — Natural Symptom Extractor (étape 1) ───────────────────────────────
# Entrée : texte libre OU liste de symptômes bruts
# Sortie : liste de symptômes canoniques connus du système
#
# Responsabilité unique : normaliser l'entrée vers les clés de SYMPTOM_DIAGNOSES.
# Ne calcule aucun score.

from app.data.symptoms import ALIASES, SYMPTOM_DIAGNOSES


def run(symptoms_raw: list[str]) -> list[str]:
    """
    Normalise et dédoublonne une liste de symptômes saisis par l'utilisateur.
    Applique les alias, met en minuscules, supprime les entrées vides.
    Retourne les symptômes canoniques présents dans SYMPTOM_DIAGNOSES.
    """
    result: set[str] = set()
    for raw in symptoms_raw:
        token = raw.lower().strip()
        if not token:
            continue
        # Résolution d'alias exact
        canonical = ALIASES.get(token, token)
        # Accepte uniquement les symptômes connus du dictionnaire
        if canonical in SYMPTOM_DIAGNOSES:
            result.add(canonical)
    return sorted(result)


def _is_negated(text: str, term: str) -> bool:
    """
    Vérifie si un terme est précédé d'une négation dans le texte.
    Patterns : "pas de X", "pas d'X", "sans X", "aucune X", "ni X", "no X"
    """
    import re
    neg_patterns = [
        r"pas\s+de\s+" + re.escape(term),
        r"pas\s+d['']\s*" + re.escape(term),
        r"sans\s+" + re.escape(term),
        r"aucune?\s+" + re.escape(term),
        r"ni\s+" + re.escape(term),
        r"no\s+" + re.escape(term),
        r"absence\s+de\s+" + re.escape(term),
    ]
    for pattern in neg_patterns:
        if re.search(pattern, text):
            return True
    return False


def parse_text(text: str) -> list[str]:
    """
    Détecte les symptômes connus dans un texte libre.
    Priorité aux alias longs (évite les correspondances partielles).
    Ignore les symptômes précédés d'une négation ("pas de fièvre", etc.).
    """
    text_lower = text.lower()
    detected: set[str] = set()

    # Alias (longs en premier)
    for alias in sorted(ALIASES, key=len, reverse=True):
        if alias in text_lower:
            canonical = ALIASES[alias]
            if not _is_negated(text_lower, alias):
                detected.add(canonical)

    # Symptômes canoniques directs
    for symptom in SYMPTOM_DIAGNOSES:
        if symptom in text_lower:
            if not _is_negated(text_lower, symptom):
                detected.add(symptom)

    return sorted(detected)