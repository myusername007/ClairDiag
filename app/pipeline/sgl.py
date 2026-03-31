# ── SGL — Safety & Guard Layer (étape 10) ───────────────────────────────────
# Entrée : diagnostics finaux, symptômes, nombre de symptômes, confidence actuel
# Sortie : confidence_level ajusté + liste de warnings
#
# Responsabilité finale :
#   - incohérence → baisser confidence
#   - données insuffisantes → plafonner confidence
#   - contradictions → ajouter warning
#   - Ne modifie jamais les diagnostics ni les tests — uniquement la confiance.

# Nombre minimum de symptômes pour maintenir une confiance élevée
_MIN_SYMPTOMS_HIGH_CONFIDENCE: int = 3
_MIN_SYMPTOMS_MODERATE_CONFIDENCE: int = 1

# Paires de diagnostics incompatibles (ne devraient pas coexister au top)
_INCOMPATIBLE_PAIRS: list[tuple[str, str]] = [
    ("Allergie",  "Pneumonie"),
    ("Gastrite",  "Angor"),
    ("Allergie",  "Angor"),
    ("Gastrite",  "Grippe"),
]


def run(
    diagnoses_names: list[str],
    probs: dict[str, float],
    symptom_count: int,
    confidence_level: str,
) -> tuple[str, list[str]]:
    """
    Vérifie la cohérence globale et ajuste le niveau de confiance.
    Retourne (confidence_level_final, warnings).
    """
    warnings: list[str] = []
    level = confidence_level

    # ── 1. Données insuffisantes ──────────────────────────────────────────────
    if symptom_count < _MIN_SYMPTOMS_MODERATE_CONFIDENCE:
        warnings.append("Données insuffisantes : moins d'1 symptôme reconnu.")
        level = "faible"
    elif symptom_count < _MIN_SYMPTOMS_HIGH_CONFIDENCE and level == "élevé":
        warnings.append("Confiance abaissée : moins de 3 symptômes fournis.")
        level = "modéré"

    # ── 2. Aucun diagnostic détecté ───────────────────────────────────────────
    if not diagnoses_names:
        warnings.append("Aucun diagnostic identifiable — veuillez consulter un médecin.")
        return "faible", warnings

    # ── 3. Détection de contradictions entre top diagnostics ─────────────────
    top_set = set(diagnoses_names[:2])  # on vérifie les 2 premiers
    for diag_a, diag_b in _INCOMPATIBLE_PAIRS:
        if diag_a in top_set and diag_b in top_set:
            warnings.append(
                f"Incohérence détectée : {diag_a} et {diag_b} sont peu compatibles. "
                "Consultation médicale recommandée."
            )
            if level == "élevé":
                level = "modéré"
            elif level == "modéré":
                level = "faible"

    # ── 4. Probabilités trop proches (ambiguïté) ──────────────────────────────
    if len(probs) >= 2:
        sorted_probs = sorted(probs.values(), reverse=True)
        if abs(sorted_probs[0] - sorted_probs[1]) < 0.05:
            warnings.append(
                "Plusieurs diagnostics ont des probabilités très proches. "
                "Tests complémentaires nécessaires pour distinguer."
            )
            if level == "élevé":
                level = "modéré"

    # ── 5. Plafonnement : confidence élevé nécessite ≥ 3 symptômes ───────────
    if level == "élevé" and symptom_count < _MIN_SYMPTOMS_HIGH_CONFIDENCE:
        level = "modéré"

    return level, warnings