# ── ERL — Exam Re-evaluation Loop (Sprint 3, étape 5) ───────────────────────
# Entrée : probs (dict), exam_results (dict test→valeur)
# Sortie : probs recalculées
#
# Logique :
#   Pour chaque résultat d'examen :
#     - "high" / "positive" / "present" / "infiltrat" / "élevé"
#       → boost selon diagnostic_value du TEST_CATALOG
#     - "low" / "negative" / "absent" / "normal"
#       → pénalité inverse (réduit la probabilité)
#     - "normal" → pénalité légère
#
# Source des poids : TEST_CATALOG["diagnostic_value"] — source unique.
# Ne crée pas de nouveaux diagnostics — ajuste uniquement ceux déjà présents.

from app.data.tests import TEST_CATALOG

_MAX_PROB: float = 0.90
_BOOST_MULTIPLIER: float = 0.40    # diagnostic_value × multiplier = boost
_PENALTY_MULTIPLIER: float = 0.20  # diagnostic_value × multiplier = pénalité

# Valeurs considérées comme positives / négatives
_POSITIVE_VALUES: set[str] = {
    "high", "positive", "present", "élevé", "positif",
    "infiltrat", "anormal", "pathologique", "elevated",
    "augmenté", "augmentée", "présent", "présente",
}
_NEGATIVE_VALUES: set[str] = {
    "low", "negative", "absent", "normal", "négatif",
    "négatif", "normal", "bas", "basse", "absent",
    "absente", "dans les normes",
}


def run(
    probs: dict[str, float],
    exam_results: dict[str, str],
) -> tuple[dict[str, float], list[str]]:
    """
    Recalcule les probabilités selon les résultats d'examens.

    Retourne (probs_updated, changes_log).
    changes_log : liste de messages explicatifs pour debug/UI.
    """
    if not probs or not exam_results:
        return probs, []

    result = dict(probs)
    changes_log: list[str] = []

    for test_name, raw_value in exam_results.items():
        value = raw_value.strip().lower()

        # Chercher le test dans le catalogue (insensible à la casse)
        catalog_key = _find_test(test_name)
        if catalog_key is None:
            changes_log.append(f"⚠ Test inconnu ignoré : {test_name}")
            continue

        diagnostic_values: dict[str, float] = TEST_CATALOG[catalog_key].get("diagnostic_value", {})
        if not diagnostic_values:
            continue

        is_positive = value in _POSITIVE_VALUES
        is_negative = value in _NEGATIVE_VALUES

        if not is_positive and not is_negative:
            changes_log.append(f"⚠ Valeur non reconnue pour {test_name} : '{raw_value}' — ignorée")
            continue

        for diag, diag_value in diagnostic_values.items():
            if diag not in result:
                continue  # Ne crée pas de nouveaux diagnostics

            if is_positive:
                delta = diag_value * _BOOST_MULTIPLIER
                result[diag] = min(_MAX_PROB, result[diag] + delta)
                changes_log.append(
                    f"✓ {test_name} = {raw_value} → {diag} +{delta:.3f} "
                    f"(valeur diagnostique: {diag_value:.2f})"
                )
            else:  # negative / normal
                delta = diag_value * _PENALTY_MULTIPLIER
                result[diag] = max(0.0, result[diag] - delta)
                changes_log.append(
                    f"✗ {test_name} = {raw_value} → {diag} -{delta:.3f} "
                    f"(valeur diagnostique: {diag_value:.2f})"
                )

    return result, changes_log


def _find_test(name: str) -> str | None:
    """Recherche insensible à la casse dans TEST_CATALOG."""
    name_lower = name.strip().lower()
    for key in TEST_CATALOG:
        if key.lower() == name_lower:
            return key
    # Recherche partielle
    for key in TEST_CATALOG:
        if name_lower in key.lower() or key.lower() in name_lower:
            return key
    return None