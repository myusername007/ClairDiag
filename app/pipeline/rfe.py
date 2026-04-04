# ── RFE — Red Flag Engine (étape 3) ─────────────────────────────────────────
# Entrée : liste de symptômes (sortie SCM)
# Sortie : RFEResult {emergency, reason, category}
#
# CRITIQUE : s'exécute AVANT le scoring (BPU).
# Si un red flag est détecté → le pipeline retourne immédiatement EMERGENCY.
# Ne calcule aucun diagnostic — uniquement la détection de danger immédiat.
#
# Catégories :
#   respiratory | cardiac | neurological | digestive | infectious | systemic

# Symptômes déclenchant une alerte d'urgence absolue
# Format : symptôme → (reason, category)
_RED_FLAGS: dict[str, tuple[str, str]] = {
    "cyanose":                    ("Cyanose détectée — appel du 15 (SAMU) immédiat requis.", "respiratory"),
    "syncope":                    ("Syncope — perte de connaissance, appel du 15 immédiat.", "cardiac"),
    "hémoptysie":                 ("Hémoptysie — sang dans les crachats, consultation urgente.", "respiratory"),
    "douleur thoracique intense": ("Douleur thoracique intense — suspicion d'infarctus, appel du 15.", "cardiac"),
    "paralysie":                  ("Paralysie soudaine — suspicion d'AVC, appel du 15 immédiat.", "neurological"),
    "détresse respiratoire":      ("Détresse respiratoire sévère — appel du 15 immédiat.", "respiratory"),
    "perte de connaissance":      ("Perte de connaissance — appel du 15 immédiat.", "neurological"),
    "déficit neurologique":       ("Déficit neurologique brutal — suspicion d'AVC, appel du 15.", "neurological"),
}

# Combinaisons de symptômes déclenchant une alerte
# Format : (frozenset requis, reason, category)
_RED_FLAG_COMBOS: list[tuple[frozenset[str], str, str]] = [
    (
        frozenset({"douleur thoracique intense", "essoufflement"}),
        "Douleur thoracique intense + essoufflement — suspicion d'infarctus, appel du 15.",
        "cardiac",
    ),
    (
        frozenset({"syncope", "douleur thoracique"}),
        "Syncope + douleur thoracique — risque cardiaque majeur, appel du 15.",
        "cardiac",
    ),
    (
        frozenset({"fièvre", "altération état général", "hypotension"}),
        "Syndrome septique probable — fièvre + AEG + hypotension, appel du 15.",
        "infectious",
    ),
]

# Catégories → labels lisibles
CATEGORY_LABELS: dict[str, str] = {
    "respiratory":   "Alerte respiratoire",
    "cardiac":       "Alerte cardiaque",
    "neurological":  "Alerte neurologique",
    "digestive":     "Alerte digestive",
    "infectious":    "Alerte infectieuse",
    "systemic":      "Alerte systémique",
}


class RFEResult:
    __slots__ = ("emergency", "reason", "category")

    def __init__(self, emergency: bool, reason: str = "", category: str = ""):
        self.emergency = emergency
        self.reason = reason
        self.category = category


def run(symptoms: list[str]) -> RFEResult:
    """
    Vérifie la présence de red flags dans la liste de symptômes.
    Retourne RFEResult(emergency=True, reason=..., category=...) si danger immédiat.
    Retourne RFEResult(emergency=False) si tout est normal — le pipeline continue.
    """
    symptom_set = set(symptoms)

    # 1. Red flags isolés
    for flag, (reason, category) in _RED_FLAGS.items():
        if flag in symptom_set:
            return RFEResult(emergency=True, reason=reason, category=category)

    # 2. Combinaisons dangereuses
    for combo, reason, category in _RED_FLAG_COMBOS:
        if combo.issubset(symptom_set):
            return RFEResult(emergency=True, reason=reason, category=category)

    return RFEResult(emergency=False)