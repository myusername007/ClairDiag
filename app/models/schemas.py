from pydantic import BaseModel
from typing import List, Optional


class AnalyzeRequest(BaseModel):
    symptoms: List[str]
    # TCE — temporal logic (étape 6)
    onset: Optional[str] = None        # "brutal" | "progressif" | None
    duration: Optional[str] = None     # "hours" | "days" | "weeks" | None

    model_config = {
        "json_schema_extra": {
            "example": {
                "symptoms": ["fièvre", "toux", "fatigue"],
                "onset": "brutal",
                "duration": "days",
            }
        }
    }


class ParseSymptomsRequest(BaseModel):
    text: str


class Diagnosis(BaseModel):
    name: str
    probability: float
    key_symptoms: List[str] = []


class Tests(BaseModel):
    required: List[str]
    optional: List[str]


class Cost(BaseModel):
    required: int
    optional: int
    savings: int


class Comparison(BaseModel):
    standard_tests: List[str]
    standard_cost: int
    optimized_tests: List[str]
    optimized_cost: int
    savings: int
    savings_multiplier: str
    cost_note: str = ""


class AnalyzeResponse(BaseModel):
    diagnoses: List[Diagnosis]
    tests: Tests
    cost: Cost
    explanation: str
    comparison: Comparison

    # Niveaux
    confidence_level: str = "modéré"   # élevé | modéré | faible  (SGL)
    urgency_level: str = "faible"       # élevé | modéré | faible  (RME)

    # RFE — red flags (étape 3)
    emergency_flag: bool = False
    emergency_reason: str = ""

    # TCS — seuil de décision (étape 8)
    tcs_level: str = "incertain"        # fort | besoin_tests | incertain

    # SGL — warnings (étape 10)
    sgl_warnings: List[str] = []

    # Détails analyses
    test_explanations: dict = {}
    test_probabilities: dict = {}
    test_costs: dict = {}               # prix par analyse — source: data/tests.py
    consultation_cost: int = 30         # tarif consultation AM — source: data/tests.py