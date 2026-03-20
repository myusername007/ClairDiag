from fastapi import APIRouter
from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.logic.engine import analyze, DEMO_SCENARIOS

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse, summary="Analyze symptoms")
def analyze_symptoms(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Приймає список симптомів, повертає:
    - вірогідні діагнози з вірогідністю
    - необхідні та опціональні аналізи
    - приблизну вартість
    - пояснення вибору аналізів
    - порівняння стандартного і оптимізованого набору
    """
    return analyze(request.symptoms)


@router.get("/scenarios", summary="Demo scenarios")
def get_scenarios() -> dict:
    """
    Повертає готові сценарії для демонстрації.
    Можна використовувати як вхідні дані для /analyze.
    """
    return {
        "scenarios": [
            {"name": name, "symptoms": symptoms}
            for name, symptoms in DEMO_SCENARIOS.items()
        ]
    }
