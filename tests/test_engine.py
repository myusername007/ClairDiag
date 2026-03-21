import pytest
from app.logic.engine import analyze
from app.models.schemas import AnalyzeResponse


# ── Структура відповіді ───────────────────────────────────────────────

def test_analyze_returns_correct_structure():
    result = analyze(["температура", "кашель"])
    assert isinstance(result, AnalyzeResponse)
    assert hasattr(result, "diagnoses")
    assert hasattr(result, "tests")
    assert hasattr(result, "cost")
    assert hasattr(result, "explanation")
    assert hasattr(result, "comparison")


# ── Діагнози ─────────────────────────────────────────────────────────

def test_analyze_returns_diagnoses_for_known_symptoms():
    result = analyze(["температура", "кашель"])
    assert len(result.diagnoses) > 0


def test_diagnoses_have_probability_between_0_and_1():
    result = analyze(["температура", "кашель"])
    for d in result.diagnoses:
        assert 0 < d.probability <= 1.0


def test_diagnoses_sorted_by_probability_desc():
    result = analyze(["температура", "кашель"])
    probs = [d.probability for d in result.diagnoses]
    assert probs == sorted(probs, reverse=True)


def test_common_symptoms_include_expected_diagnosis():
    result = analyze(["температура", "кашель"])
    names = [d.name for d in result.diagnoses]
    assert "Грипп" in names or "ОРВИ" in names


def test_unknown_symptoms_return_empty_diagnoses():
    result = analyze(["несуществующий симптом"])
    assert result.diagnoses == []


def test_empty_symptoms_return_empty_response():
    result = analyze([])
    assert result.diagnoses == []
    assert result.tests.required == []
    assert result.tests.optional == []


# ── Аналізи ──────────────────────────────────────────────────────────

def test_required_tests_not_empty_for_known_symptoms():
    result = analyze(["температура", "кашель"])
    assert len(result.tests.required) > 0


def test_optional_tests_not_in_required():
    result = analyze(["температура", "кашель"])
    overlap = set(result.tests.required) & set(result.tests.optional)
    assert overlap == set()


# ── Вартість ─────────────────────────────────────────────────────────

def test_required_cost_greater_than_zero():
    result = analyze(["температура", "кашель"])
    assert result.cost.required > 0


def test_savings_equals_optional_cost():
    result = analyze(["температура", "кашель"])
    assert result.cost.savings == result.cost.optional


def test_cost_is_zero_for_unknown_symptoms():
    result = analyze(["несуществующий симптом"])
    assert result.cost.required == 0
    assert result.cost.optional == 0


# ── Explanation ───────────────────────────────────────────────────────

def test_explanation_is_non_empty_string():
    result = analyze(["температура", "кашель"])
    assert isinstance(result.explanation, str)
    assert len(result.explanation) > 0


def test_explanation_for_unknown_symptoms_is_fallback():
    result = analyze(["несуществующий симптом"])
    assert "врач" in result.explanation.lower() or "не удалось" in result.explanation.lower()


# ── Comparison ────────────────────────────────────────────────────────

def test_comparison_standard_cost_gte_optimized():
    result = analyze(["температура", "кашель"])
    assert result.comparison.standard_cost >= result.comparison.optimized_cost


def test_comparison_savings_correct():
    result = analyze(["температура", "кашель"])
    expected = result.comparison.standard_cost - result.comparison.optimized_cost
    assert result.comparison.savings == expected


def test_comparison_optimized_tests_subset_of_standard():
    result = analyze(["температура", "кашель"])
    optimized = set(result.comparison.optimized_tests)
    standard = set(result.comparison.standard_tests)
    assert optimized.issubset(standard)