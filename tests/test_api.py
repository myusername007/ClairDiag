import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

SYMPTOMS = ["fièvre", "toux"]


# ── Root / Health ──────────────────────────────────────────────────────────

def test_root_returns_200():
    response = client.get("/")
    assert response.status_code == 200


def test_health_returns_200():
    response = client.get("/v1/health")
    assert response.status_code == 200


def test_health_returns_ok_status():
    assert client.get("/v1/health").json()["status"] == "ok"


# ── POST /v1/analyze — structure ──────────────────────────────────────────

def test_analyze_returns_200():
    response = client.post("/v1/analyze", json={"symptoms": SYMPTOMS})
    assert response.status_code == 200


def test_analyze_response_has_all_fields():
    data = client.post("/v1/analyze", json={"symptoms": SYMPTOMS}).json()
    for field in ("diagnoses", "tests", "cost", "explanation", "comparison",
                  "confidence_level", "urgency_level"):
        assert field in data


def test_analyze_tests_has_required_and_optional():
    data = client.post("/v1/analyze", json={"symptoms": SYMPTOMS}).json()
    assert "required" in data["tests"]
    assert "optional" in data["tests"]


def test_analyze_cost_has_all_fields():
    data = client.post("/v1/analyze", json={"symptoms": SYMPTOMS}).json()
    for field in ("required", "optional", "savings"):
        assert field in data["cost"]


def test_analyze_comparison_has_savings_multiplier():
    data = client.post("/v1/analyze", json={"symptoms": SYMPTOMS}).json()
    assert "savings_multiplier" in data["comparison"]
    mult = data["comparison"]["savings_multiplier"]
    assert "x" in mult or mult == "—"


def test_analyze_comparison_has_all_fields():
    data = client.post("/v1/analyze", json={"symptoms": SYMPTOMS}).json()
    c = data["comparison"]
    for field in ("standard_tests", "standard_cost", "optimized_tests",
                  "optimized_cost", "savings", "savings_multiplier", "cost_note"):
        assert field in c


def test_analyze_diagnoses_have_key_symptoms():
    data = client.post("/v1/analyze", json={"symptoms": SYMPTOMS}).json()
    for d in data["diagnoses"]:
        assert "key_symptoms" in d


def test_analyze_confidence_level_valid():
    data = client.post("/v1/analyze", json={"symptoms": SYMPTOMS}).json()
    assert data["confidence_level"] in ("élevé", "modéré", "faible")


def test_analyze_urgency_level_valid():
    data = client.post("/v1/analyze", json={"symptoms": SYMPTOMS}).json()
    assert data["urgency_level"] in ("élevé", "modéré", "faible")


def test_analyze_explanation_is_string():
    data = client.post("/v1/analyze", json={"symptoms": SYMPTOMS}).json()
    assert isinstance(data["explanation"], str)
    assert len(data["explanation"]) > 0


def test_analyze_diagnoses_are_list():
    data = client.post("/v1/analyze", json={"symptoms": ["toux"]}).json()
    assert isinstance(data["diagnoses"], list)


# ── GET /v1/scenarios ──────────────────────────────────────────────────────

def test_scenarios_returns_200():
    assert client.get("/v1/scenarios").status_code == 200


def test_scenarios_returns_list():
    data = client.get("/v1/scenarios").json()
    assert "scenarios" in data
    assert isinstance(data["scenarios"], list)
    assert len(data["scenarios"]) > 0


def test_scenarios_have_name_and_symptoms():
    for s in client.get("/v1/scenarios").json()["scenarios"]:
        assert "name" in s
        assert "symptoms" in s


# ── POST /v1/parse-symptoms ────────────────────────────────────────────────

def test_parse_symptoms_returns_200():
    response = client.post("/v1/parse-symptoms", json={"text": "j'ai de la fièvre"})
    assert response.status_code == 200


def test_parse_symptoms_returns_detected_list():
    data = client.post("/v1/parse-symptoms", json={"text": "fièvre et toux"}).json()
    assert "detected" in data
    assert isinstance(data["detected"], list)


def test_parse_symptoms_detects_known():
    data = client.post("/v1/parse-symptoms", json={"text": "j'ai de la fièvre et je tousse"}).json()
    assert len(data["detected"]) > 0


def test_parse_symptoms_empty_text():
    data = client.post("/v1/parse-symptoms", json={"text": ""}).json()
    assert data["detected"] == []


# ── Edge cases ─────────────────────────────────────────────────────────────

def test_analyze_unknown_symptoms_returns_empty_diagnoses():
    response = client.post("/v1/analyze", json={"symptoms": ["symptôme_inexistant"]})
    assert response.status_code == 200
    assert response.json()["diagnoses"] == []


def test_analyze_empty_symptoms_returns_200():
    assert client.post("/v1/analyze", json={"symptoms": []}).status_code == 200


def test_analyze_empty_symptoms_returns_empty_diagnoses():
    assert client.post("/v1/analyze", json={"symptoms": []}).json()["diagnoses"] == []


# ── Validation ─────────────────────────────────────────────────────────────

def test_analyze_missing_body_returns_422():
    assert client.post("/v1/analyze").status_code == 422


def test_analyze_wrong_type_returns_422():
    assert client.post("/v1/analyze", json={"symptoms": "fièvre"}).status_code == 422


def test_analyze_invalid_field_returns_422():
    assert client.post("/v1/analyze", json={"wrong_field": ["fièvre"]}).status_code == 422
