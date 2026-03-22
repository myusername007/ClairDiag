from app.models.schemas import AnalyzeResponse, Comparison, Diagnosis, Tests, Cost

# Liens : symptôme → diagnostics avec poids
SYMPTOM_DIAGNOSES: dict[str, dict[str, float]] = {
    "fièvre":                {"Grippe": 0.8, "Rhinopharyngite": 0.7, "Bronchite": 0.4, "Pneumonie": 0.3, "Angine": 0.5},
    "toux":                  {"Bronchite": 0.8, "Rhinopharyngite": 0.6, "Grippe": 0.5, "Pneumonie": 0.4, "Allergie": 0.3},
    "rhinorrhée":            {"Rhinopharyngite": 0.9, "Grippe": 0.6, "Allergie": 0.5},
    "céphalées":             {"Grippe": 0.7, "Rhinopharyngite": 0.5, "Hypertension": 0.4},
    "mal de gorge":          {"Rhinopharyngite": 0.8, "Angine": 0.9, "Grippe": 0.5},
    "essoufflement":         {"Pneumonie": 0.8, "Bronchite": 0.6, "Asthme": 0.7, "Angor": 0.4},
    "douleur thoracique":    {"Pneumonie": 0.6, "Bronchite": 0.4, "Angor": 0.8},
    "fatigue":               {"Grippe": 0.6, "Rhinopharyngite": 0.5, "Anémie": 0.5, "Angine": 0.4, "Pneumonie": 0.4},
    "perte d'appétit":       {"Grippe": 0.4, "Gastrite": 0.6, "Anémie": 0.4},
    "nausées":               {"Gastrite": 0.8, "Grippe": 0.3},
    "éternuements":          {"Allergie": 0.8, "Rhinopharyngite": 0.4},
    "irritation de la gorge":{"Allergie": 0.7},
}

# Liens : diagnostic → analyses
DIAGNOSIS_TESTS: dict[str, dict[str, list[str]]] = {
    "Grippe":          {"required": ["NFS", "CRP"],                              "optional": ["PCR grippe"]},
    "Rhinopharyngite": {"required": ["NFS"],                                     "optional": ["Prélèvement pharyngé"]},
    "Bronchite":       {"required": ["NFS", "CRP", "Radiographie pulmonaire"],   "optional": ["Scanner thoracique"]},
    "Pneumonie":       {"required": ["NFS", "CRP", "Radiographie pulmonaire"],   "optional": ["Scanner thoracique", "Culture des expectorations"]},
    "Angine":          {"required": ["NFS", "Prélèvement pharyngé"],             "optional": ["ASLO"]},
    "Asthme":          {"required": ["Spirométrie", "NFS"],                      "optional": ["Tests allergologiques"]},
    "Hypertension":    {"required": ["ECG", "NFS"],                              "optional": ["Échocardiographie"]},
    "Gastrite":        {"required": ["NFS", "Test Helicobacter pylori"],         "optional": ["Fibroscopie gastrique"]},
    "Anémie":          {"required": ["NFS", "Ferritine"],                        "optional": ["Vitamine B12"]},
    "Allergie":        {"required": ["NFS", "IgE totales"],                      "optional": ["Tests allergologiques"]},
    "Angor":           {"required": ["ECG", "Troponine", "CRP"],                 "optional": ["Échocardiographie", "Holter ECG"]},
}

# Prix de référence (€, marché moyen France / UE — à titre indicatif)
TEST_COSTS: dict[str, int] = {
    "NFS":                         45,
    "CRP":                         65,
    "PCR grippe":                  65,
    "Prélèvement pharyngé":        45,
    "Radiographie pulmonaire":     90,
    "Scanner thoracique":         180,
    "Culture des expectorations":  55,
    "ASLO":                        35,
    "Spirométrie":                 75,
    "Tests allergologiques":      110,
    "ECG":                         60,
    "Échocardiographie":          130,
    "Test Helicobacter pylori":    50,
    "Fibroscopie gastrique":      220,
    "Ferritine":                   40,
    "Vitamine B12":                40,
    "IgE totales":                 55,
    "Troponine":                   45,
    "Holter ECG":                 110,
}

# Explication de chaque analyse (langue simple)
TEST_EXPLANATIONS: dict[str, str] = {
    "NFS":                         "évalue l'inflammation et l'état général du système immunitaire",
    "CRP":                         "marqueur d'inflammation aiguë — mesure la sévérité de l'infection",
    "PCR grippe":                  "confirme ou exclut précisément le virus de la grippe",
    "Prélèvement pharyngé":        "identifie une infection bactérienne de la gorge",
    "Radiographie pulmonaire":     "visualise l'état des poumons et des bronches",
    "Scanner thoracique":          "imagerie détaillée des poumons en cas de complications suspectées",
    "Culture des expectorations":  "identifie l'agent pathogène et sa sensibilité aux antibiotiques",
    "ASLO":                        "détecte une infection streptococcique récente",
    "Spirométrie":                 "évalue la fonction respiratoire en cas d'asthme suspecté",
    "Tests allergologiques":       "identifie les allergènes responsables",
    "ECG":                         "évalue le fonctionnement du cœur",
    "Échocardiographie":           "imagerie détaillée du muscle cardiaque",
    "Test Helicobacter pylori":    "détecte la bactérie principale responsable de la gastrite",
    "Fibroscopie gastrique":       "examen visuel de la muqueuse gastrique",
    "Ferritine":                   "mesure les réserves en fer de l'organisme",
    "Vitamine B12":                "contrôle le taux de vitamine B12, dont le déficit cause une anémie",
    "IgE totales":                 "mesure le niveau global d'anticorps allergiques",
    "Troponine":                   "marqueur de lésion du muscle cardiaque",
    "Holter ECG":                  "monitoring cardiaque sur 24 heures",
}



# ── Facteur de variabilité des prix (min/max réaliste) ──────────────────────
# Chaque analyse a une fourchette basée sur les tarifs publics/privés en France
TEST_COSTS_MIN: dict[str, int] = {
    "NFS": 35, "CRP": 50, "PCR grippe": 55, "Prélèvement pharyngé": 35,
    "Radiographie pulmonaire": 70, "Scanner thoracique": 150,
    "Culture des expectorations": 45, "ASLO": 28, "Spirométrie": 60,
    "Tests allergologiques": 90, "ECG": 45, "Échocardiographie": 110,
    "Test Helicobacter pylori": 40, "Fibroscopie gastrique": 180,
    "Ferritine": 32, "Vitamine B12": 32, "IgE totales": 45,
    "Troponine": 35, "Holter ECG": 90,
}
TEST_COSTS_MAX: dict[str, int] = {
    "NFS": 65, "CRP": 85, "PCR grippe": 80, "Prélèvement pharyngé": 60,
    "Radiographie pulmonaire": 120, "Scanner thoracique": 220,
    "Culture des expectorations": 70, "ASLO": 50, "Spirométrie": 100,
    "Tests allergologiques": 140, "ECG": 80, "Échocardiographie": 160,
    "Test Helicobacter pylori": 65, "Fibroscopie gastrique": 270,
    "Ferritine": 55, "Vitamine B12": 55, "IgE totales": 70,
    "Troponine": 60, "Holter ECG": 135,
}


def _cost_range(tests: set[str], costs_min: dict, costs_max: dict) -> tuple[int, int]:
    lo = sum(costs_min.get(t, TEST_COSTS.get(t, 0)) for t in tests)
    hi = sum(costs_max.get(t, TEST_COSTS.get(t, 0)) for t in tests)
    return lo, hi


def _fmt_range(lo: int, hi: int) -> str:
    return f"~{lo}€ – {hi}€"

# Scénarios prêts pour la démo
DEMO_SCENARIOS: dict[str, list[str]] = {
    "Rhume":      ["rhinorrhée", "mal de gorge", "fatigue"],
    "Grippe":     ["fièvre", "toux", "céphalées", "fatigue"],
    "Bronchite":  ["toux", "essoufflement", "douleur thoracique"],
    "Angine":     ["mal de gorge", "fièvre", "fatigue"],
    "Pneumonie":  ["fièvre", "toux", "essoufflement", "douleur thoracique"],
    "Allergie":   ["rhinorrhée", "éternuements", "irritation de la gorge"],
}

# ── Alias de saisie libre ────────────────────────────────────────────────────
ALIASES: dict[str, str] = {
    "température":            "fièvre",
    "température élevée":    "fièvre",
    "de la fièvre":          "fièvre",
    "j'ai de la fièvre":     "fièvre",
    "toux sèche":            "toux",
    "toux grasse":           "toux",
    "je tousse":             "toux",
    "nez qui coule":         "rhinorrhée",
    "écoulement nasal":      "rhinorrhée",
    "nez bouché":            "rhinorrhée",
    "maux de tête":          "céphalées",
    "mal à la tête":         "céphalées",
    "migraine":              "céphalées",
    "gorge":                 "mal de gorge",
    "douleur en avalant":    "mal de gorge",
    "déglutition douloureuse": "mal de gorge",
    "essoufflé":             "essoufflement",
    "souffle court":         "essoufflement",
    "manque de souffle":     "essoufflement",
    "douleur au thorax":     "douleur thoracique",
    "douleur à la poitrine": "douleur thoracique",
    "mal à la poitrine":     "douleur thoracique",
    "fatigué":               "fatigue",
    "épuisement":            "fatigue",
    "asthénie":              "fatigue",
    "pas d'appétit":         "perte d'appétit",
    "anorexie":              "perte d'appétit",
    "nausée":                "nausées",
    "envie de vomir":        "nausées",
    "éternuement":           "éternuements",
    "gorge qui gratte":      "irritation de la gorge",
    "irritation gorge":      "irritation de la gorge",
}


def parse_symptoms(text: str) -> list[str]:
    """Détecte les symptômes connus dans un texte libre (aliases + noms directs)."""
    text_lower = text.lower()
    detected: set[str] = set()
    for alias in sorted(ALIASES, key=len, reverse=True):
        if alias in text_lower:
            detected.add(ALIASES[alias])
    for symptom in SYMPTOM_DIAGNOSES:
        if symptom in text_lower:
            detected.add(symptom)
    return sorted(detected)


# ── Couche 1 : spécificité des symptômes ────────────────────────────────────
# Un symptôme pointant vers moins de diagnostics porte plus d'information.
_MAX_DIAG_COUNT = max(len(w) for w in SYMPTOM_DIAGNOSES.values())


def _specificity(n: int) -> float:
    return 1.0 + 0.5 * max(0.0, 1.0 - n / _MAX_DIAG_COUNT)


# Score maximal possible par diagnostic (avec facteur de spécificité)
DIAGNOSIS_MAX_SCORES: dict[str, float] = {}
for _sym, _weights in SYMPTOM_DIAGNOSES.items():
    _f = _specificity(len(_weights))
    for _diag, _w in _weights.items():
        DIAGNOSIS_MAX_SCORES[_diag] = DIAGNOSIS_MAX_SCORES.get(_diag, 0) + _w * _f

# Dénominateur minimum — évite les probabilités gonflées pour les diagnostics peu documentés
_MIN_DENOM = 2.0

# Seuil d'inclusion d'un diagnostic dans la réponse
PROBABILITY_THRESHOLD = 0.15


# ── Couche 2 : bonus de combinaisons ────────────────────────────────────────
# Certaines combinaisons de symptômes sont plus diagnostiques que leur somme.
# Le bonus s'applique uniquement si le diagnostic est déjà détecté.
COMBO_BONUSES: list[tuple[frozenset[str], dict[str, float]]] = [
    (frozenset({"fièvre", "toux", "essoufflement"}),            {"Pneumonie": 0.25}),
    (frozenset({"toux", "essoufflement"}),                      {"Bronchite": 0.15, "Asthme": 0.15}),
    (frozenset({"rhinorrhée", "éternuements", "irritation de la gorge"}), {"Allergie": 0.35}),
    (frozenset({"mal de gorge", "fièvre"}),                     {"Angine": 0.20}),
    (frozenset({"douleur thoracique", "essoufflement"}),        {"Angor": 0.25, "Pneumonie": 0.15}),
    (frozenset({"fièvre", "céphalées", "fatigue"}),             {"Grippe": 0.20}),
    (frozenset({"nausées", "perte d'appétit"}),                 {"Gastrite": 0.20}),
    (frozenset({"fatigue", "perte d'appétit"}),                 {"Anémie": 0.15}),
]


# ── Couche 3 : symptômes d'exclusion ────────────────────────────────────────
# Certains symptômes réduisent la probabilité de diagnostics incompatibles.
SYMPTOM_EXCLUSIONS: dict[str, dict[str, float]] = {
    "éternuements":          {"Pneumonie": 0.15, "Bronchite": 0.10, "Angor": 0.20},
    "irritation de la gorge":{"Grippe": 0.15, "Bronchite": 0.15, "Pneumonie": 0.20},
    "nausées":               {"Asthme": 0.15, "Allergie": 0.10},
    "rhinorrhée":            {"Angor": 0.20, "Gastrite": 0.15},
    "douleur thoracique":    {"Gastrite": 0.15, "Allergie": 0.15},
}

# Article grammatical par diagnostic (pour les phrases en français)
_DIAG_ARTICLE: dict[str, str] = {
    "Grippe": "une", "Rhinopharyngite": "une", "Bronchite": "une",
    "Pneumonie": "une", "Angine": "une", "Asthme": "un",
    "Hypertension": "une", "Gastrite": "une", "Anémie": "une",
    "Allergie": "une", "Angor": "un",
}


# Diagnostics nécessitant une attention urgente
_URGENT_DIAGNOSES = {"Pneumonie", "Angor"}

def _urgency_level(diagnoses: list) -> str:
    if not diagnoses:
        return "faible"
    top = diagnoses[0]
    if top.name in _URGENT_DIAGNOSES and top.probability >= 0.40:
        return "élevé"
    if top.probability >= 0.55:
        return "modéré"
    return "faible"


# ── Niveau de confiance ──────────────────────────────────────────────────────
def _confidence_level(diagnoses: list, symptom_count: int) -> str:
    if not diagnoses:
        return "faible"
    top = diagnoses[0].probability
    if top >= 0.65 and symptom_count >= 3:
        return "élevé"
    elif top >= 0.45 or symptom_count >= 2:
        return "modéré"
    return "faible"


# ── Explication ──────────────────────────────────────────────────────────────
def _build_explanation(symptoms: list[str], diagnoses: list[Diagnosis], required_tests: list[str]) -> str:
    if not diagnoses:
        return "Les symptômes fournis ne permettent pas d'établir un diagnostic. Veuillez consulter un médecin."

    top = diagnoses[0]
    pct = int(top.probability * 100)
    art = _DIAG_ARTICLE.get(top.name, "une")

    if pct >= 65:
        start = f"Les symptômes correspondent le plus probablement à {art} {top.name}."
    elif pct >= 40:
        start = f"Le diagnostic le plus probable est {art} {top.name}."
    else:
        start = f"{art.capitalize()} {top.name} est possible, mais les symptômes restent insuffisants pour confirmer."

    if len(diagnoses) > 1:
        art2 = _DIAG_ARTICLE.get(diagnoses[1].name, "une")
        alt = f" {art2.capitalize()} {diagnoses[1].name} ne peut pas être totalement exclue."
    else:
        alt = ""

    first_two = [t for t in required_tests[:2] if t in TEST_EXPLANATIONS]
    tests_hint = ""
    if first_two:
        joined = " et ".join(f"{t} ({TEST_EXPLANATIONS[t]})" for t in first_two)
        tests_hint = f" Pour une première évaluation, les analyses suivantes sont suffisantes : {joined}."

    return start + alt + tests_hint


# ── Fonction principale ──────────────────────────────────────────────────────
def analyze(symptoms: list[str]) -> AnalyzeResponse:
    symptom_set = {s.lower().strip() for s in symptoms}

    empty_comparison = Comparison(
        standard_tests=[], standard_cost=0,
        optimized_tests=[], optimized_cost=0,
        savings=0, savings_multiplier="—",
    )

    # Couche 1 — score de base avec facteur de spécificité
    raw: dict[str, float] = {}
    for sym in symptom_set:
        weights = SYMPTOM_DIAGNOSES.get(sym, {})
        factor = _specificity(len(weights)) if weights else 1.0
        for diag, weight in weights.items():
            raw[diag] = raw.get(diag, 0) + weight * factor

    if not raw:
        return AnalyzeResponse(
            diagnoses=[],
            tests=Tests(required=[], optional=[]),
            cost=Cost(required=0, optional=0, savings=0),
            explanation="Les symptômes indiqués ne permettent pas d'identifier un diagnostic. Veuillez consulter un médecin.",
            comparison=empty_comparison,
            urgency_level="faible",
        )

    # Normalisation : quelle fraction des indices possibles avons-nous recueillis ?
    probs: dict[str, float] = {
        name: min(score / max(DIAGNOSIS_MAX_SCORES[name], _MIN_DENOM), 1.0)
        for name, score in raw.items()
    }

    # Couche 2 — bonus de combinaisons (renforce uniquement les diagnostics déjà détectés)
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

    # Plafond final : probabilité ≤ 75 % — plus honnête pour une démo
    _MAX_PROB = 0.75
    probs = {name: min(prob, _MAX_PROB) for name, prob in probs.items()}

    # Symptômes clés par diagnostic (ceux qui ont contribué au score)
    key_symptoms_map: dict[str, list[str]] = {name: [] for name in probs}
    for sym in symptom_set:
        for diag in SYMPTOM_DIAGNOSES.get(sym, {}):
            if diag in key_symptoms_map and sym not in key_symptoms_map[diag]:
                key_symptoms_map[diag].append(sym)

    # Filtrage, tri, top 3
    diagnoses = sorted(
        [
            Diagnosis(name=name, probability=round(prob, 2), key_symptoms=key_symptoms_map.get(name, []))
            for name, prob in probs.items()
            if prob >= PROBABILITY_THRESHOLD
        ],
        key=lambda d: d.probability,
        reverse=True,
    )[:3]

    # Garantir des probabilités distinctes (évite les ex-aequo à l'affichage)
    deduped: list[Diagnosis] = []
    for d in diagnoses:
        if deduped and d.probability >= deduped[-1].probability:
            prob = round(deduped[-1].probability - 0.04, 2)
        elif deduped and (deduped[-1].probability - d.probability) < 0.04:
            prob = round(deduped[-1].probability - 0.04, 2)
        else:
            prob = d.probability
        deduped.append(Diagnosis(name=d.name, probability=max(prob, 0.10), key_symptoms=d.key_symptoms))
    diagnoses = deduped

    # Collecte des analyses pour les 3 premiers diagnostics
    # Bilan de base (toujours en recommandé si présent)
    BASE_REQUIRED = {"NFS", "CRP"}

    all_tests: set[str] = set()
    for diag in diagnoses:
        tests = DIAGNOSIS_TESTS.get(diag.name, {})
        all_tests.update(tests.get("required", []))
        all_tests.update(tests.get("optional", []))

    # recommandées = uniquement le bilan de base parmi les analyses indiquées
    # optionnelles = tout le reste
    required_set = all_tests & BASE_REQUIRED
    optional_set = all_tests - BASE_REQUIRED

    standard_set   = all_tests
    standard_cost  = sum(TEST_COSTS.get(t, 0) for t in standard_set)
    optimized_cost = sum(TEST_COSTS.get(t, 0) for t in required_set)
    optional_cost  = sum(TEST_COSTS.get(t, 0) for t in optional_set)
    required_list  = sorted(required_set)
    optional_list  = sorted(optional_set)

    return AnalyzeResponse(
        diagnoses=diagnoses,
        tests=Tests(required=required_list, optional=optional_list),
        cost=Cost(required=optimized_cost, optional=optional_cost, savings=optional_cost),
        explanation=_build_explanation(list(symptom_set), diagnoses, required_list),
        comparison=Comparison(
            standard_tests=sorted(standard_set),
            standard_cost=standard_cost,
            optimized_tests=required_list,
            optimized_cost=optimized_cost,
            savings=standard_cost - optimized_cost,
            savings_multiplier=(
                f"~{round(standard_cost / optimized_cost, 1)}x moins cher"
                if optimized_cost > 0 else "—"
            ),
            standard_range=_fmt_range(*_cost_range(standard_set, TEST_COSTS_MIN, TEST_COSTS_MAX)),
            optimized_range=_fmt_range(*_cost_range(required_set, TEST_COSTS_MIN, TEST_COSTS_MAX)),
            savings_range=_fmt_range(
                *(_cost_range(standard_set, TEST_COSTS_MIN, TEST_COSTS_MAX)[0] - _cost_range(required_set, TEST_COSTS_MIN, TEST_COSTS_MAX)[1],
                  _cost_range(standard_set, TEST_COSTS_MIN, TEST_COSTS_MAX)[1] - _cost_range(required_set, TEST_COSTS_MIN, TEST_COSTS_MAX)[0])
            ) if required_set else "—",
            cost_note="Exemple basé sur un cas clinique courant — prix indicatifs (marché France / UE)",
        ),
        confidence_level=_confidence_level(diagnoses, len(symptom_set)),
        urgency_level=_urgency_level(diagnoses),
    )