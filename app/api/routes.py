import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import AnalyzeRequest, AnalyzeResponse, ParseSymptomsRequest
from app.logic.engine import analyze, parse_symptoms, DEMO_SCENARIOS

router = APIRouter()
logger = logging.getLogger("clairdiag")


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_symptoms(request: AnalyzeRequest) -> AnalyzeResponse:
    symptoms = [s.strip() for s in request.symptoms if s.strip()]
    logger.info(f"Analyse: {symptoms}")
    try:
        result = analyze(symptoms)
        logger.info(f"Résultat: {len(result.diagnoses)} diagnostics")
        return result
    except Exception as e:
        logger.error(f"Erreur: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne")


@router.post("/parse-symptoms")
def parse_symptoms_endpoint(request: ParseSymptomsRequest) -> dict:
    """Détecte les symptômes connus dans un texte libre."""
    detected = parse_symptoms(request.text)
    return {"detected": detected, "count": len(detected)}


@router.get("/scenarios")
def get_scenarios() -> dict:
    return {
        "scenarios": [
            {"name": name, "symptoms": symptoms}
            for name, symptoms in DEMO_SCENARIOS.items()
        ]
    }
