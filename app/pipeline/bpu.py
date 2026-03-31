# ── BPU — Bayesian Probability Unit (étape 4) ───────────────────────────────
# Entrée : liste de symptômes canoniques (sortie SCM, après RFE)
# Sortie : dict {diagnostic → probabilité normalisée 0.0–1.0}
#
# Logique identique à l'engine.py original — 3 couches :
#   1. Score de base avec facteur de spécificité
#   2. Bonus de combinaisons (COMBO_BONUSES)
#   3. Pénalités pour symptômes incompatibles (SYMPTOM_EXCLUSIONS)
#
# Plafond : 0.75 (honnêteté démo)
# Seuil d'inclusion : PROBABILITY_THRESHOLD

from app.data.symptoms import (
    SYMPTOM_DIAGNOSES,
    COMBO_BONUSES,
    SYMPTOM_EXCLUSIONS,
)

# ── Constantes ───────────────────────────────────────────────────────────────
_MAX_PROB: float = 0.75
_MIN_DENOM: float = 2.0
PROBABILITY_THRESHOLD: float = 0.15

# Pré-calcul du score maximal possible par diagnostic (spécificité incluse)
_MAX_DIAG_COUNT: int = max(len(w) for w in SYMPTOM_DIAGNOSES.values())


def _specificity(n: int) -> float:
    """Facteur de spécificité : symptôme rare → poids plus élevé."""
    return 1.0 + 0.5 * max(0.0, 1.0 - n / _MAX_DIAG_COUNT)


DIAGNOSIS_MAX_SCORES: dict[str, float] = {}
for _sym, _weights in SYMPTOM_DIAGNOSES.items():
    _f = _specificity(len(_weights))
    for _diag, _w in _weights.items():
        DIAGNOSIS_MAX_SCORES[_diag] = DIAGNOSIS_MAX_SCORES.get(_diag, 0) + _w * _f


def run(symptoms: list[str]) -> dict[str, float]:
    """
    Calcule les probabilités brutes pour chaque diagnostic.
    Retourne un dict {diagnostic → probabilité} pour les diagnostics ≥ PROBABILITY_THRESHOLD.
    """
    symptom_set = {s.lower().strip() for s in symptoms}

    # Couche 1 — score de base avec spécificité
    raw: dict[str, float] = {}
    for sym in symptom_set:
        weights = SYMPTOM_DIAGNOSES.get(sym, {})
        factor = _specificity(len(weights)) if weights else 1.0
        for diag, weight in weights.items():
            raw[diag] = raw.get(diag, 0) + weight * factor

    if not raw:
        return {}

    # Normalisation
    probs: dict[str, float] = {
        name: min(score / max(DIAGNOSIS_MAX_SCORES.get(name, _MIN_DENOM), _MIN_DENOM), 1.0)
        for name, score in raw.items()
    }

    # Couche 2 — bonus de combinaisons (uniquement diagnostics déjà détectés)
    for combo, bonuses in COMBO_BONUSES:
        if combo.issubset(symptom_set):
            for diag, bonus in bonuses.items():
                if diag in probs:
                    probs[diag] = min(1.0, probs[diag] + bonus)

    # Couche 3 — pénalités pour symptômes incompatibles
    for sym in symptom_set:
        for diag, penalty in SYMPTOM_EXCLUSIONS.get(sym, {}).items():
            if diag in probs:
                probs[diag] = max(0.0, probs[diag] - penalty)

    # Plafond
    probs = {name: min(prob, _MAX_PROB) for name, prob in probs.items()}

    # Filtre seuil
    return {name: prob for name, prob in probs.items() if prob >= PROBABILITY_THRESHOLD}