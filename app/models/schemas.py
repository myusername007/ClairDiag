from pydantic import BaseModel
from typing import List


class AnalyzeRequest(BaseModel):
    symptoms: List[str]

    model_config = {
        "json_schema_extra": {
            "example": {
                "symptoms": ["fièvre", "toux", "fatigue"]
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
    standard_range: str = ""
    optimized_range: str = ""
    savings_range: str = ""
    cost_note: str = ""


class AnalyzeResponse(BaseModel):
    diagnoses: List[Diagnosis]
    tests: Tests
    cost: Cost
    explanation: str
    comparison: Comparison
    confidence_level: str = "modéré"
    urgency_level: str = "faible"
