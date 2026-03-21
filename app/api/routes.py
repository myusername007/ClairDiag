import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.logic.engine import analyze, DEMO_SCENARIOS

router = APIRouter()
logger = logging.getLogger("clairdiag")


@router.get("/health", summary="Проверка работоспособности")
def health():
    return {"status": "ok"}


@router.post("/analyze", response_model=AnalyzeResponse, summary="Анализ симптомов")
def analyze_symptoms(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Принимает список симптомов, возвращает:
    - вероятные диагнозы
    - необходимые и опциональные анализы
    - стоимость и потенциальную экономию
    - объяснение для человека
    - сравнение стандартного и оптимизированного пути
    """
    symptoms = [s.strip() for s in request.symptoms if s.strip()]
    logger.info(f"Запрос на анализ: {symptoms}")
    try:
        result = analyze(symptoms)
        logger.info(f"Результат: найдено {len(result.diagnoses)} диагнозов")
        return result
    except Exception as e:
        logger.error(f"Ошибка анализа: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка при анализе")


@router.get("/scenarios", summary="Список готовых сценариев для демо")
def get_scenarios() -> dict:
    """Возвращает готовые сценарии. Можно использовать как вход для POST /v1/analyze."""
    return {
        "scenarios": [
            {"name": name, "symptoms": symptoms}
            for name, symptoms in DEMO_SCENARIOS.items()
        ]
    }


@router.get("/demo", response_class=PlainTextResponse, summary="Демо")
def demo() -> str:
    """Готовые сценарии для демонстрации. Открыть в браузере — результат виден сразу."""
    lines = ["=" * 50, "  ClairDiag — Демо", "=" * 50, ""]

    for scenario_name, symptoms in DEMO_SCENARIOS.items():
        result = analyze(symptoms)

        top = result.diagnoses[0] if result.diagnoses else None
        others = [d.name for d in result.diagnoses[1:3]]

        std = result.comparison.standard_cost
        opt = result.comparison.optimized_cost
        savings_x = round(std / opt, 1) if opt > 0 else 0

        lines += [
            f"📋 Сценарий: {scenario_name}",
            f"   Симптомы: {', '.join(symptoms)}",
            "",
        ]

        if top:
            lines.append(f"   Наиболее вероятный диагноз:  {top.name} ({int(top.probability * 100)}%)")
            if others:
                lines.append(f"   Также рассматриваем:         {', '.join(others)}")

        lines += [
            "",
            f"   ✅ Рекомендуемые анализы:     {', '.join(result.tests.required)}",
        ]
        if result.tests.optional:
            lines.append(f"   ⏭  Можно пропустить:          {', '.join(result.tests.optional)}")

        lines += [
            "",
            f"   💰 Стандартный путь:          ~{std} грн",
            f"   💡 Рекомендованный:           ~{opt} грн",
            f"   📉 Потенциальная экономия:    ~{savings_x}x дешевле",
            "",
            f"   💬 {result.explanation}",
            "",
            "-" * 50,
            "",
        ]

    lines.append("Для собственного запроса: POST /v1/analyze")
    return "\n".join(lines)