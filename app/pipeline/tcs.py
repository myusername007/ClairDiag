# ── TCS — Threshold & Classification System (étape 8) ───────────────────────
# Entrée : probs, symptom_count, symptoms, incoherence_score
# Sortie : (tcs_level, confidence_level, confidence_score)
#
# Échelle TCS 4 niveaux :
#   TCS_1 = données suffisantes pour orientation forte
#   TCS_2 = orientation probable mais confirmation nécessaire
#   TCS_3 = insuffisant sans examens complémentaires
#   TCS_4 = haut niveau d'incertitude / sécurité prioritaire
#
# Mapping affichage → "élevé | modéré | faible | critique"
#
# Confidence composite (5 composantes) :
#   1. couverture  : part des symptômes couverts par le top diagnostic
#   2. gap         : écart top1–top2 (cap 0.55 si gap < 0.10)
#   3. qualité     : nombre de symptômes fournis
#   4. red_flag    : pénalité si symptômes urgents présents
#   5. incoherence : pénalité si profil contradictoire

from app.data.symptoms import SYMPTOM_DIAGNOSES

# Plafond si données insuffisantes
_LOW_DATA_CAP: float = 0.55
_LOW_DATA_THRESHOLD: int = 2

_INCOHERENCE_PENALTY_PER_UNIT: float = 0.08

# Mapping TCS → label affiché
TCS_LABELS: dict[str, str] = {
    "TCS_1": "élevé",
    "TCS_2": "modéré",
    "TCS_3": "faible",
    "TCS_4": "critique",
}


def _compute_confidence(
    probs: dict[str, float],
    symptoms: list[str],
    incoherence_score: float,
) -> float:
    """
    Confidence composite recalibrée 0.0–1.0.

    5 composantes :
      1. couverture       — symptômes couverts par le top diagnostic
      2. gap_top1_top2    — séparation entre top1 et top2 (plus large = plus clair)
      3. qualité données  — nombre de symptômes (sature à 4)
      4. red_flag penalty — présence de symptômes urgents dégrade la certitude
      5. incoherence      — pénalité si profil contradictoire

    Règle clé : si gap top1–top2 < 0.10, confidence plafonné à 0.55 (modéré max).
    """
    if not probs:
        return 0.0

    sorted_probs = sorted(probs.values(), reverse=True)
    top_diag = max(probs, key=probs.get)
    n = len(symptoms)
    symptom_set = set(symptoms)

    # Composante 1 — couverture
    diag_symptoms = {sym for sym, diags in SYMPTOM_DIAGNOSES.items() if top_diag in diags}
    couverture = len(symptom_set & diag_symptoms) / len(symptom_set) if symptom_set else 0.0

    # Composante 2 — gap top1 vs top2
    gap = (sorted_probs[0] - sorted_probs[1]) if len(sorted_probs) >= 2 else 1.0
    coherence = min(gap / 0.30, 1.0)

    # Composante 3 — qualité données
    qualite = min(n / 4.0, 1.0)

    # Composante 4 — red flag presence
    _RED_FLAG_SYMS: frozenset[str] = frozenset({
        "syncope", "cyanose", "hémoptysie", "perte de connaissance",
        "détresse respiratoire", "déficit neurologique", "confusion aiguë",
    })
    has_red_flag = bool(symptom_set & _RED_FLAG_SYMS)
    red_flag_penalty = 0.10 if has_red_flag else 0.0

    # Score composite pondéré
    score = 0.35 * couverture + 0.35 * coherence + 0.20 * qualite - red_flag_penalty

    # Pénalité incoherence
    score -= incoherence_score * _INCOHERENCE_PENALTY_PER_UNIT
    score = max(0.0, score)

    # Cap hard si gap trop faible
    if gap < 0.10:
        score = min(score, 0.55)

    # Cap si données insuffisantes
    if n <= 1:
        score = min(score, 0.35)
    elif n <= _LOW_DATA_THRESHOLD:
        score = min(score, _LOW_DATA_CAP)

    return round(score, 3)


def _score_to_level(score: float) -> str:
    if score >= 0.65:
        return "élevé"
    elif score >= 0.40:
        return "modéré"
    return "faible"


def run(
    probs: dict[str, float],
    symptom_count: int,
    symptoms: list[str] | None = None,
    incoherence_score: float = 0.0,
) -> tuple[str, str, float]:
    """
    Retourne (tcs_level, confidence_level, confidence_score).

    tcs_level         : TCS_1 | TCS_2 | TCS_3 | TCS_4
    confidence_level  : élevé | modéré | faible
    confidence_score  : float 0.0–1.0 (composite)
    """
    if not probs:
        return "TCS_4", "faible", 0.0

    top_prob = max(probs.values())
    top_diag = max(probs, key=probs.get)

    # ── Groupes de diagnostics ──────────────────────────────────────────────
    _ALWAYS_NEEDS_TESTS: set[str] = {
        "Insuffisance cardiaque", "Embolie pulmonaire", "Trouble du rythme",
        "RGO", "SII",
    }
    _NEEDS_TESTS_IF_STRONG: set[str] = {
        "Asthme", "Bronchite", "Pneumonie",
    }
    _LIGHT_DIAGNOSES: set[str] = {
        "Gastrite", "Rhinopharyngite", "Allergie",
    }
    _INFECTIEUX: set[str] = {"Grippe", "Angine"}

    _syms_set = set(symptoms or [])
    has_fievre = "fièvre" in _syms_set

    # ── Étape 1 : niveau brut selon top_prob ────────────────────────────────
    if top_prob >= 0.90:
        tcs_level = "TCS_1"
    elif top_prob >= 0.75:
        tcs_level = "TCS_2"
    elif top_prob >= 0.50:
        tcs_level = "TCS_3"
    else:
        tcs_level = "TCS_4"

    # ── Étape 2 : overrides par groupe ──────────────────────────────────────

    # Jamais TCS_1 — confirmation biologique obligatoire
    if tcs_level == "TCS_1" and top_diag in _ALWAYS_NEEDS_TESTS:
        tcs_level = "TCS_2"
    if top_diag in _ALWAYS_NEEDS_TESTS and symptom_count < 2:
        tcs_level = "TCS_4"

    # Pneumonie
    if top_diag == "Pneumonie":
        if symptom_count >= 5 and top_prob >= 0.75:
            tcs_level = "TCS_1"
        elif symptom_count >= 3 and top_prob >= 0.60:
            tcs_level = "TCS_2"
        elif symptom_count >= 2 and top_prob >= 0.75:
            tcs_level = "TCS_2"
        else:
            tcs_level = "TCS_3"

    # Asthme / Bronchite
    if top_diag in _NEEDS_TESTS_IF_STRONG - {"Pneumonie"}:
        if tcs_level == "TCS_1":
            tcs_level = "TCS_2"
        if symptom_count < 2:
            tcs_level = "TCS_3"

    # Diagnostics légers
    if top_diag in _LIGHT_DIAGNOSES and symptom_count <= 3:
        tcs_level = "TCS_3"

    # Infectieux
    if top_diag in _INFECTIEUX:
        if tcs_level == "TCS_1":
            tcs_level = "TCS_2"
        if has_fievre and symptom_count >= 2:
            tcs_level = "TCS_2"
        elif not has_fievre or symptom_count < 2:
            tcs_level = "TCS_3"

    # Threshold Guard final — TCS_1 seulement si profil vraiment solide
    if tcs_level == "TCS_1":
        if symptom_count <= _LOW_DATA_THRESHOLD:
            tcs_level = "TCS_2"
        elif incoherence_score > 0.15:
            tcs_level = "TCS_2"
        else:
            _syms = symptoms or []
            _diag_syms = {sym for sym, diags in SYMPTOM_DIAGNOSES.items() if top_diag in diags}
            _covered = len(set(_syms) & _diag_syms)
            if _covered < 2:
                tcs_level = "TCS_2"

    # TCS_4 si données très insuffisantes (sécurité prioritaire)
    if symptom_count <= 1 and tcs_level not in ("TCS_3", "TCS_4"):
        tcs_level = "TCS_4"

    # Composite confidence
    syms = symptoms or []
    conf_score = _compute_confidence(probs, syms, incoherence_score)
    conf_level = _score_to_level(conf_score)

    return tcs_level, conf_level, conf_score
# Entrée : probs, symptom_count, symptoms, incoherence_score
# Sortie : (tcs_level, confidence_level)
#
# Seuils ТЗ :
#   ≥ 0.90 → fort | 0.75–0.89 → besoin_tests | < 0.75 → incertain
#
# Confidence composite (ТЗ п.5) — trois composantes :
#   1. couverture  : part des symptômes couverts par le top diagnostic
#   2. cohérence   : écart entre top prob et 2e prob (plus grand = plus clair)
#   3. qualité     : nombre de symptômes fournis (proxy qualité données)
#
# Règle ТЗ : si données insuffisantes → confidence plafonné à 0.55

from app.data.symptoms import SYMPTOM_DIAGNOSES

# Plafond si données insuffisantes (ТЗ п.5)
_LOW_DATA_CAP: float = 0.55
_LOW_DATA_THRESHOLD: int = 2      # ≤ N symptômes = données insuffisantes

# Pénalité incoherence par unité de score
_INCOHERENCE_PENALTY_PER_UNIT: float = 0.08


def _compute_confidence(
    probs: dict[str, float],
    symptoms: list[str],
    incoherence_score: float,
) -> float:
    """
    Confidence composite recalibrée 0.0–1.0.

    5 composantes :
      1. couverture       — symptômes couverts par le top diagnostic
      2. gap_top1_top2    — séparation entre top1 et top2 (plus large = plus clair)
      3. qualité données  — nombre de symptômes (sature à 4)
      4. red_flag penalty — présence de symptômes urgents dégrade la certitude
      5. incoherence      — pénalité si profil contradictoire

    Règle clé : si gap top1–top2 < 0.10, confidence plafonné à 0.55 (modéré max).
    """
    if not probs:
        return 0.0

    sorted_probs = sorted(probs.values(), reverse=True)
    top_diag = max(probs, key=probs.get)
    n = len(symptoms)
    symptom_set = set(symptoms)

    # Composante 1 — couverture
    diag_symptoms = {sym for sym, diags in SYMPTOM_DIAGNOSES.items() if top_diag in diags}
    couverture = len(symptom_set & diag_symptoms) / len(symptom_set) if symptom_set else 0.0

    # Composante 2 — gap top1 vs top2
    gap = (sorted_probs[0] - sorted_probs[1]) if len(sorted_probs) >= 2 else 1.0
    coherence = min(gap / 0.30, 1.0)

    # Composante 3 — qualité données
    qualite = min(n / 4.0, 1.0)

    # Composante 4 — red flag presence (urgents réduisent la certitude diagnostic)
    _RED_FLAG_SYMS: frozenset[str] = frozenset({
        "syncope", "cyanose", "hémoptysie", "perte de connaissance",
        "détresse respiratoire", "déficit neurologique", "confusion aiguë",
    })
    has_red_flag = bool(symptom_set & _RED_FLAG_SYMS)
    red_flag_penalty = 0.10 if has_red_flag else 0.0

    # Score composite pondéré
    score = 0.35 * couverture + 0.35 * coherence + 0.20 * qualite - red_flag_penalty

    # Pénalité incoherence
    score -= incoherence_score * _INCOHERENCE_PENALTY_PER_UNIT
    score = max(0.0, score)

    # Cap hard si gap trop faible — deux hypothèses proches = incertitude réelle
    if gap < 0.10:
        score = min(score, 0.55)

    # Cap si données insuffisantes
    if n <= 1:
        score = min(score, 0.35)
    elif n <= _LOW_DATA_THRESHOLD:
        score = min(score, _LOW_DATA_CAP)

    return round(score, 3)


def _score_to_level(score: float) -> str:
    if score >= 0.65:
        return "élevé"
    elif score >= 0.40:
        return "modéré"
    return "faible"


def run(
    probs: dict[str, float],
    symptom_count: int,
    symptoms: list[str] | None = None,
    incoherence_score: float = 0.0,
) -> tuple[str, str, float]:
    """
    Retourne (tcs_level, confidence_level, confidence_score).

    tcs_level         : décision clinique — fort | besoin_tests | incertain
    confidence_level  : élevé | modéré | faible
    confidence_score  : float 0.0–1.0 (composite)
    """
    if not probs:
        return "incertain", "faible", 0.0

    top_prob = max(probs.values())
    top_diag = max(probs, key=probs.get)

    # ── TCS decision logic ──────────────────────────────────────────────────
    # Groupes de diagnostics par comportement TCS :
    #
    # ALWAYS_NEEDS_TESTS : jamais fort (confirmation biologique obligatoire)
    # NEEDS_TESTS_IF_STRONG : besoin_tests si symptom_count >= 2, incertain sinon
    # LIGHT : incertain sauf profil fort (>= 3 symptômes ET top_prob >= 0.75)
    # Pneumonie : fort autorisé si >= 5 symptômes
    # Autres (Angor, Hypertension...) : logique prob pure

    _ALWAYS_NEEDS_TESTS: set[str] = {
        "Insuffisance cardiaque", "Embolie pulmonaire", "Trouble du rythme",
        "RGO", "SII",
    }
    _NEEDS_TESTS_IF_STRONG: set[str] = {
        "Asthme", "Bronchite", "Pneumonie",
    }
    _LIGHT_DIAGNOSES: set[str] = {
        "Gastrite", "Rhinopharyngite", "Allergie",
    }
    # Infectieux : besoin_tests si fièvre présente, incertain si profil très léger
    _INFECTIEUX: set[str] = {"Grippe", "Angine"}

    _syms_set = set(symptoms or [])
    has_fievre = "fièvre" in _syms_set

    # Étape 1 : score brut basé sur top_prob
    if top_prob >= 0.90:
        tcs_level = "fort"
    elif top_prob >= 0.75:
        tcs_level = "besoin_tests"
    else:
        tcs_level = "incertain"

    # Étape 2 : overrides par groupe de diagnostic

    # Jamais fort; et si 1 seul symptôme → incertain même pour ces diagnostics
    if tcs_level == "fort" and top_diag in _ALWAYS_NEEDS_TESTS:
        tcs_level = "besoin_tests"
    if top_diag in _ALWAYS_NEEDS_TESTS and symptom_count < 2:
        tcs_level = "incertain"

    # Pneumonie : fort seulement si profil très complet (>= 5 symptômes)
    if top_diag == "Pneumonie":
        if symptom_count >= 5 and top_prob >= 0.75:
            tcs_level = "fort"
        elif symptom_count >= 3 and top_prob >= 0.60:
            tcs_level = "besoin_tests"
        elif symptom_count >= 2 and top_prob >= 0.75:
            tcs_level = "besoin_tests"
        else:
            tcs_level = "incertain"

    # Asthme / Bronchite : besoin_tests si >= 2 symptômes, incertain sinon
    # (jamais fort — confirmation spirométrie/Rx nécessaire)
    if top_diag in _NEEDS_TESTS_IF_STRONG - {"Pneumonie"}:
        if tcs_level == "fort":
            tcs_level = "besoin_tests"
        if symptom_count < 2:
            tcs_level = "incertain"

    # Diagnostics légers : incertain si <= 3 symptômes (Gastrite, Rhinopharyngite, Allergie)
    if top_diag in _LIGHT_DIAGNOSES and symptom_count <= 3:
        tcs_level = "incertain"

    # Infectieux (Grippe, Angine) :
    # - fièvre présente ET symptom_count >= 2 → besoin_tests (bilan infectieux justifié)
    # - sinon → incertain
    if top_diag in _INFECTIEUX:
        if tcs_level == "fort":
            tcs_level = "besoin_tests"
        if has_fievre and symptom_count >= 2:
            tcs_level = "besoin_tests"
        elif not has_fievre or symptom_count < 2:
            tcs_level = "incertain"

    # Threshold Guard final — fort seulement si profil vraiment solide
    if tcs_level == "fort":
        if symptom_count <= _LOW_DATA_THRESHOLD:
            tcs_level = "besoin_tests"
        elif incoherence_score > 0.15:
            tcs_level = "besoin_tests"
        else:
            _syms = symptoms or []
            _diag_syms = {sym for sym, diags in SYMPTOM_DIAGNOSES.items() if top_diag in diags}
            _covered = len(set(_syms) & _diag_syms)
            if _covered < 2:
                tcs_level = "besoin_tests"

    # Composite confidence
    syms = symptoms or []
    conf_score = _compute_confidence(probs, syms, incoherence_score)
    conf_level = _score_to_level(conf_score)

    return tcs_level, conf_level, conf_score