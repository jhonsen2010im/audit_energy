"""Lead scoring engine for energy audit prospects."""

from datetime import datetime

WEIGHTS = {
    "building_age": 0.25,
    "building_size": 0.25,
    "industry": 0.25,
    "energy_spend": 0.25,
}

HIGH_VALUE_INDUSTRIES = [
    "manufacturing", "healthcare", "hospitality", "retail",
    "food_service", "warehouse", "office", "education",
    "government", "data_center",
]

MEDIUM_VALUE_INDUSTRIES = [
    "residential", "agriculture", "nonprofit", "religious",
]


def score_lead(lead: dict) -> float:
    scores = {
        "building_age": _score_building_age(lead.get("building_year_built")),
        "building_size": _score_building_size(lead.get("building_sqft")),
        "industry": _score_industry(lead.get("industry")),
        "energy_spend": _score_energy_spend(lead.get("estimated_energy_spend")),
    }
    total = sum(scores[k] * WEIGHTS[k] for k in scores)
    return round(total, 1)


def explain_score(lead: dict) -> dict:
    scores = {
        "building_age": _score_building_age(lead.get("building_year_built")),
        "building_size": _score_building_size(lead.get("building_sqft")),
        "industry": _score_industry(lead.get("industry")),
        "energy_spend": _score_energy_spend(lead.get("estimated_energy_spend")),
    }
    explanations = {
        "building_age": _explain_building_age(lead.get("building_year_built"), scores["building_age"]),
        "building_size": _explain_building_size(lead.get("building_sqft"), scores["building_size"]),
        "industry": _explain_industry(lead.get("industry"), scores["industry"]),
        "energy_spend": _explain_energy_spend(lead.get("estimated_energy_spend"), scores["energy_spend"]),
    }
    total = sum(scores[k] * WEIGHTS[k] for k in scores)
    return {
        "total": round(total, 1),
        "factors": {k: {"score": scores[k], "weight": WEIGHTS[k],
                        "weighted": round(scores[k] * WEIGHTS[k], 1),
                        "explanation": explanations[k]} for k in scores},
    }


def score_all_leads(db) -> int:
    leads = db.get_all_leads()
    count = 0
    for lead in leads:
        new_score = score_lead(lead)
        if new_score != lead.get("score"):
            db.update_lead(lead["id"], score=new_score)
            count += 1
    return count


# --- Scoring functions ---

def _score_building_age(year_built: int | None) -> float:
    if year_built is None:
        return 50.0
    current_year = datetime.now().year
    age = current_year - year_built
    if age >= 40:
        return 100.0
    elif age >= 25:
        return 80.0
    elif age >= 15:
        return 60.0
    elif age >= 5:
        return 30.0
    else:
        return 10.0


def _score_building_size(sqft: int | None) -> float:
    if sqft is None:
        return 50.0
    if sqft >= 100000:
        return 100.0
    elif sqft >= 50000:
        return 85.0
    elif sqft >= 25000:
        return 70.0
    elif sqft >= 10000:
        return 55.0
    elif sqft >= 5000:
        return 40.0
    else:
        return 20.0


def _score_industry(industry: str | None) -> float:
    if industry is None:
        return 50.0
    industry_lower = industry.lower().replace(" ", "_")
    if any(ind in industry_lower for ind in HIGH_VALUE_INDUSTRIES):
        return 90.0
    elif any(ind in industry_lower for ind in MEDIUM_VALUE_INDUSTRIES):
        return 55.0
    else:
        return 40.0


def _score_energy_spend(spend: float | None) -> float:
    if spend is None:
        return 50.0
    if spend >= 200000:
        return 100.0
    elif spend >= 100000:
        return 85.0
    elif spend >= 50000:
        return 70.0
    elif spend >= 25000:
        return 55.0
    elif spend >= 10000:
        return 40.0
    else:
        return 20.0


# --- Explanation helpers ---

def _explain_building_age(year_built, score):
    if year_built is None:
        return "Unknown year built (default score)"
    age = datetime.now().year - year_built
    return f"Built in {year_built} ({age} years old) -> {score}/100"


def _explain_building_size(sqft, score):
    if sqft is None:
        return "Unknown building size (default score)"
    return f"{sqft:,} sq ft -> {score}/100"


def _explain_industry(industry, score):
    if industry is None:
        return "Unknown industry (default score)"
    return f"Industry: {industry} -> {score}/100"


def _explain_energy_spend(spend, score):
    if spend is None:
        return "Unknown energy spend (default score)"
    return f"Est. energy spend: ${spend:,.0f}/yr -> {score}/100"
