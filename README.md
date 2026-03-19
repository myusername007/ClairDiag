# ClairDiag

Demo diagnostic API: symptom-based diagnosis assistant.

## What it does

`POST /analyze` — accepts a list of symptoms, returns:
- probable diagnoses with relative probability
- required and optional medical tests
- estimated cost and potential savings

## How it works

Simple hardcoded mapping:

symptom → diagnosis → tests

Probabilities are **relative weights**, not clinical statistics.
The system does not perform real medical diagnosis.

## Run
```bash
docker-compose up --build
```

Swagger UI: `http://localhost:8005/docs`

## Run tests
```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Example

Request:
```json
{"symptoms": ["температура", "кашель"]}
```

Response:
```json
{
  "diagnoses": [{"name": "Грипп", "probability": 1.0}],
  "tests": {
    "required": ["Общий анализ крови", "CRP"],
    "optional": ["ПЦР на грипп"]
  },
  "cost": {"required": 200, "optional": 350, "savings": 350}
}
```