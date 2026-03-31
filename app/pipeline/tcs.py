# ── TCS — Threshold & Classification System (étape 8) ───────────────────────
# Entrée : dict de probabilités finales (sortie CRE), nombre de symptômes
# Sortie : tcs_level str + confidence_level str
#
# Seuils (ТЗ) :
#   ≥ 0.90 → diagnostic fort  ("fort")
#   0.75–0.89 → besoin de tests ("besoin_tests")
#   < 0.75 → incertain → médecin ("incertain")
#
# confidence_level : évaluation globale de la fiabilité du résultat.


def run(probs: dict[str, float], symptom_count: int) -> tuple[str, str]:
    """
    Retourne (tcs_level, confidence_level).

    tcs_level    : décision principale basée sur la probabilité du top diagnostic.
    confidence_level : fiabilité globale — tient compte du nombre de symptômes.
    """
    if not probs:
        return "incertain", "faible"

    top_prob = max(probs.values())

    # ── TCS level ────────────────────────────────────────────────────────────
    if top_prob >= 0.90:
        tcs_level = "fort"
    elif top_prob >= 0.75:
        tcs_level = "besoin_tests"
    else:
        tcs_level = "incertain"

    # ── Confidence level ─────────────────────────────────────────────────────
    # Tient compte : probabilité top + nombre de symptômes fournis
    if top_prob >= 0.65 and symptom_count >= 3:
        confidence_level = "élevé"
    elif top_prob >= 0.45 or symptom_count >= 2:
        confidence_level = "modéré"
    else:
        confidence_level = "faible"

    return tcs_level, confidence_level