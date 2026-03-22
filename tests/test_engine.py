import pytest
from app.logic.engine import analyze, parse_symptoms
from app.models.schemas import AnalyzeResponse


# ── Structure de la réponse ───────────────────────────────────────────────

def test_analyze_returns_correct_structure():
    result = analyze(["fièvre", "toux"])
    assert isinstance(result, AnalyzeResponse)
    assert hasattr(result, "diagnoses")
    assert hasattr(result, "tests")
    assert hasattr(result, "cost")
    assert hasattr(result, "explanation")
    assert hasattr(result, "comparison")
    assert hasattr(result, "confidence_level")
    assert hasattr(result, "urgency_level")


# ── Diagnostics ───────────────────────────────────────────────────────────

def test_analyze_returns_diagnoses_for_known_symptoms():
    result = analyze(["fièvre", "toux"])
    assert len(result.diagnoses) > 0


def test_diagnoses_have_probability_between_0_and_1():
    result = analyze(["fièvre", "toux"])
    for d in result.diagnoses:
        assert 0 < d.probability <= 1.0


def test_diagnoses_probability_capped_at_75():
    result = analyze(["fièvre", "toux", "fatigue", "céphalées"])
    for d in result.diagnoses:
        assert d.probability <= 0.75


def test_diagnoses_sorted_by_probability_desc():
    result = analyze(["fièvre", "toux"])
    probs = [d.probability for d in result.diagnoses]
    assert probs == sorted(probs, reverse=True)


def test_diagnoses_have_distinct_probabilities():
    result = analyze(["fièvre", "toux", "fatigue"])
    probs = [d.probability for d in result.diagnoses]
    assert len(probs) == len(set(probs))


def test_common_symptoms_include_expected_diagnosis():
    result = analyze(["fièvre", "toux", "céphalées", "fatigue"])
    names = [d.name for d in result.diagnoses]
    assert "Grippe" in names or "Bronchite" in names


def test_diagnoses_have_key_symptoms():
    result = analyze(["fièvre", "toux"])
    for d in result.diagnoses:
        assert isinstance(d.key_symptoms, list)


def test_unknown_symptoms_return_empty_diagnoses():
    result = analyze(["symptôme_inexistant"])
    assert result.diagnoses == []


def test_empty_symptoms_return_empty_response():
    result = analyze([])
    assert result.diagnoses == []
    assert result.tests.required == []
    assert result.tests.optional == []


# ── Analyses ──────────────────────────────────────────────────────────────

def test_required_tests_not_empty_for_known_symptoms():
    result = analyze(["fièvre", "toux"])
    assert len(result.tests.required) > 0


def test_optional_tests_not_in_required():
    result = analyze(["fièvre", "toux"])
    overlap = set(result.tests.required) & set(result.tests.optional)
    assert overlap == set()


def test_required_tests_come_from_diagnosis_tests():
    """required = analyses essentielles selon DIAGNOSIS_TESTS pour les diagnostics détectés"""
    from app.logic.engine import DIAGNOSIS_TESTS
    result = analyze(["fièvre", "toux"])
    all_required_possible: set = set()
    for diag in result.diagnoses:
        all_required_possible.update(DIAGNOSIS_TESTS.get(diag.name, {}).get("required", []))
    for t in result.tests.required:
        assert t in all_required_possible


# ── Coûts ─────────────────────────────────────────────────────────────────

def test_required_cost_greater_than_zero():
    result = analyze(["fièvre", "toux"])
    assert result.cost.required > 0


def test_savings_positive_when_optional_tests_exist():
    """savings = standard_cost - optimized_cost (weighted optional prescriptions)"""
    result = analyze(["fièvre", "toux"])
    if result.tests.optional:
        assert result.cost.savings > 0
    assert result.comparison.savings == result.comparison.standard_cost - result.comparison.optimized_cost


def test_cost_is_zero_for_unknown_symptoms():
    result = analyze(["symptôme_inexistant"])
    assert result.cost.required == 0
    assert result.cost.optional == 0


# ── Explication ───────────────────────────────────────────────────────────

def test_explanation_is_non_empty_string():
    result = analyze(["fièvre", "toux"])
    assert isinstance(result.explanation, str)
    assert len(result.explanation) > 0


def test_explanation_for_unknown_symptoms_is_fallback():
    result = analyze(["symptôme_inexistant"])
    expl = result.explanation.lower()
    assert "médecin" in expl or "identifier" in expl


# ── Comparaison ───────────────────────────────────────────────────────────

def test_comparison_standard_cost_gte_optimized():
    result = analyze(["fièvre", "toux"])
    assert result.comparison.standard_cost >= result.comparison.optimized_cost


def test_comparison_savings_correct():
    result = analyze(["fièvre", "toux"])
    expected = result.comparison.standard_cost - result.comparison.optimized_cost
    assert result.comparison.savings == expected


def test_comparison_optimized_tests_subset_of_standard():
    result = analyze(["fièvre", "toux"])
    optimized = set(result.comparison.optimized_tests)
    standard = set(result.comparison.standard_tests)
    assert optimized.issubset(standard)


def test_comparison_has_exact_costs():
    """Exact costs per scenario (no abstract ranges)"""
    result = analyze(["fièvre", "toux"])
    assert result.comparison.standard_cost > 0
    assert result.comparison.optimized_cost > 0
    assert result.comparison.standard_cost >= result.comparison.optimized_cost


# ── Confiance & Urgence ───────────────────────────────────────────────────

def test_confidence_level_valid_value():
    result = analyze(["fièvre", "toux"])
    assert result.confidence_level in {"élevé", "modéré", "faible"}


def test_urgency_level_valid_value():
    result = analyze(["fièvre", "toux"])
    assert result.urgency_level in {"élevé", "modéré", "faible"}


def test_urgency_elevated_for_pneumonie():
    result = analyze(["fièvre", "toux", "essoufflement", "douleur thoracique"])
    names = [d.name for d in result.diagnoses]
    if "Pneumonie" in names:
        assert result.urgency_level in {"élevé", "modéré"}


# ── parse_symptoms ────────────────────────────────────────────────────────

def test_parse_symptoms_detects_known():
    detected = parse_symptoms("j'ai de la fièvre et je tousse")
    assert "fièvre" in detected or "toux" in detected


def test_parse_symptoms_returns_list():
    result = parse_symptoms("fatigue et céphalées")
    assert isinstance(result, list)


def test_parse_symptoms_empty_text():
    result = parse_symptoms("")
    assert result == []


def test_parse_symptoms_unknown_text():
    result = parse_symptoms("rien de connu ici xyz")
    assert result == []
