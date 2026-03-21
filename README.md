# ClairDiag

Demo diagnostic API: symptom-based diagnosis assistant.

## What it does

Принимает список симптомов, возвращает:
- вероятные диагнозы с относительной вероятностью
- необходимые и опциональные анализы
- стоимость и потенциальную экономию
- сравнение стандартного и оптимизированного пути

## How it works

Простая логика связей:

```
симптом → диагноз → анализы
```

Вероятности — **относительные веса**, не клиническая статистика.
Система не выполняет реальную медицинскую диагностику.

## Run

```bash
docker-compose up --build
```

Swagger UI: `http://localhost:8005/docs`

Demo для демонстрации в браузере: `http://localhost:8005/v1/demo`

## Run tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Endpoints

| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/v1/analyze` | Анализ симптомов |
| GET | `/v1/scenarios` | Готовые сценарии для демо |
| GET | `/v1/demo` | Читаемый демо-вывод в браузере |
| GET | `/v1/health` | Health check |

## Example

Request:
```json
{"symptoms": ["температура", "кашель"]}
```

Response:
```json
{
  "diagnoses": [
    {"name": "Грипп", "probability": 0.63},
    {"name": "ОРВИ", "probability": 0.45}
  ],
  "tests": {
    "required": ["CRP", "Общий анализ крови", "Рентген"],
    "optional": ["КТ грудной клетки", "ПЦР на грипп"]
  },
  "cost": {"required": 400, "optional": 1300, "savings": 1300},
  "explanation": "По симптомам «температура», «кашель» наиболее вероятен Грипп (63%)...",
  "comparison": {
    "standard_cost": 1700,
    "optimized_cost": 400,
    "savings": 1300,
    "savings_multiplier": "~4.2x дешевле"
  }
}
```