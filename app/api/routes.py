import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.logic.engine import analyze, DEMO_SCENARIOS

router = APIRouter()
logger = logging.getLogger("clairdiag")


@router.get("/health", summary="Health check")
def health():
    return {"status": "ok"}


@router.post("/analyze", response_model=AnalyzeResponse, summary="Analyze symptoms")
def analyze_symptoms(request: AnalyzeRequest) -> AnalyzeResponse:
    symptoms = [s.strip() for s in request.symptoms if s.strip()]
    logger.info(f"Analyze request: {symptoms}")
    try:
        result = analyze(symptoms)
        logger.info(f"Result: {len(result.diagnoses)} diagnoses found")
        return result
    except Exception as e:
        logger.error(f"Analyze error: {e}")
        raise HTTPException(status_code=500, detail="Internal error during analysis")


@router.get("/demo", response_class=PlainTextResponse, summary="Live demo — open in browser")
def demo() -> str:
    lines = ["=" * 50, "  ClairDiag — Demo", "=" * 50, ""]

    for scenario_name, symptoms in DEMO_SCENARIOS.items():
        result = analyze(symptoms)

        top = result.diagnoses[0] if result.diagnoses else None
        others = [d.name for d in result.diagnoses[1:3]]

        std = result.comparison.standard_cost
        opt = result.comparison.optimized_cost
        savings_x = round(std / opt, 1) if opt > 0 else 0

        lines += [
            f"📋 Сценарій: {scenario_name}",
            f"   Симптоми: {', '.join(symptoms)}",
            "",
        ]

        if top:
            lines += [
                f"   Найімовірніший діагноз:  {top.name} ({int(top.probability * 100)}%)",
            ]
            if others:
                lines.append(f"   Також розглядаємо:       {', '.join(others)}")

        lines += [
            "",
            f"   ✅ Рекомендовані аналізи:  {', '.join(result.tests.required)}",
        ]
        if result.tests.optional:
            lines.append(f"   ⏭  Можна пропустити:       {', '.join(result.tests.optional)}")

        lines += [
            "",
            f"   💰 Стандартний шлях:       ~{std} грн",
            f"   💡 Рекомендований:         ~{opt} грн",
            f"   📉 Потенційна економія:    ~{savings_x}x дешевше",
            "",
            f"   💬 {result.explanation}",
            "",
            "-" * 50,
            "",
        ]

    lines.append("Для власного запиту: POST /v1/analyze")
    return "\n".join(lines)