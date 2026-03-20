from pydantic import BaseModel
from typing import List


class AnalyzeRequest(BaseModel):
    symptoms: List[str]

    class Config:
        json_schema_extra = {
            "example": {
                "symptoms": ["температура", "кашель"]
            }
        }


class Diagnosis(BaseModel):
    name: str
    probability: float


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


class AnalyzeResponse(BaseModel):
    diagnoses: List[Diagnosis]
    tests: Tests
    cost: Cost
    explanation: str
    comparison: Comparison
