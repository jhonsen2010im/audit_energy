"""Tests for the lead scoring engine."""

from audit_leads.scoring import score_lead, explain_score


def test_score_lead_all_high():
    lead = {
        "building_year_built": 1970,
        "building_sqft": 120000,
        "industry": "manufacturing",
        "estimated_energy_spend": 250000,
    }
    score = score_lead(lead)
    assert score >= 90.0


def test_score_lead_all_low():
    lead = {
        "building_year_built": 2024,
        "building_sqft": 2000,
        "industry": "unknown_niche",
        "estimated_energy_spend": 5000,
    }
    score = score_lead(lead)
    assert score <= 30.0


def test_score_lead_missing_data():
    lead = {"company_name": "No Data Corp"}
    score = score_lead(lead)
    assert score == 50.0  # All defaults


def test_score_lead_partial_data():
    lead = {
        "building_year_built": 1985,
        "industry": "healthcare",
    }
    score = score_lead(lead)
    assert 50.0 < score < 90.0


def test_explain_score_has_all_factors():
    lead = {
        "building_year_built": 1990,
        "building_sqft": 30000,
        "industry": "office",
        "estimated_energy_spend": 80000,
    }
    result = explain_score(lead)
    assert "total" in result
    assert "factors" in result
    assert set(result["factors"].keys()) == {"building_age", "building_size", "industry", "energy_spend"}
    for factor in result["factors"].values():
        assert "score" in factor
        assert "weight" in factor
        assert "explanation" in factor


def test_score_range():
    """All scores should be between 0 and 100."""
    test_cases = [
        {},
        {"building_year_built": 1900, "building_sqft": 500000,
         "industry": "manufacturing", "estimated_energy_spend": 1000000},
        {"building_year_built": 2025, "building_sqft": 100,
         "industry": "niche", "estimated_energy_spend": 100},
    ]
    for lead in test_cases:
        score = score_lead(lead)
        assert 0.0 <= score <= 100.0, f"Score {score} out of range for {lead}"
