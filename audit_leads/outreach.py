"""Outreach template rendering for energy audit leads."""

import os
from datetime import datetime, timedelta
from string import Template

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")


def _next_weekday(start: datetime, weekday: int) -> str:
    """Get the next occurrence of a weekday (0=Mon, 1=Tue, ..., 6=Sun)."""
    days_ahead = weekday - start.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    target = start + timedelta(days=days_ahead)
    return target.strftime("%A, %B %d")


def _build_context(lead: dict, contacts: list[dict]) -> dict:
    """Build template context from lead and contact data."""
    now = datetime.now()
    year_built = lead.get("building_year_built")
    building_age = (now.year - year_built) if year_built else None

    if building_age and lead.get("building_sqft"):
        building_description = f"{lead['building_sqft']:,} sq ft facility built in {year_built}"
    elif year_built:
        building_description = f"facility built in {year_built}"
    elif lead.get("building_sqft"):
        building_description = f"{lead['building_sqft']:,} sq ft facility"
    else:
        building_description = "commercial facility"

    # Score-based reason
    score = lead.get("score", 0)
    if score >= 80:
        score_reason = "Based on our analysis, your building profile suggests significant potential for energy savings."
    elif score >= 60:
        score_reason = "Buildings with similar characteristics to yours often benefit from a professional energy assessment."
    else:
        score_reason = "We help businesses like yours identify opportunities to reduce energy costs."

    primary_contact = None
    for c in contacts:
        if c.get("is_primary"):
            primary_contact = c
            break
    if not primary_contact and contacts:
        primary_contact = contacts[0]

    return {
        "company_name": lead.get("company_name", "your company"),
        "contact_name": primary_contact.get("name", "there") if primary_contact else "there",
        "contact_title": primary_contact.get("title", "") if primary_contact else "",
        "city": lead.get("city", "your area"),
        "state": lead.get("state", ""),
        "industry": lead.get("industry", "your industry"),
        "building_description": building_description,
        "building_age": str(building_age) if building_age else "unknown",
        "building_sqft": f"{lead['building_sqft']:,}" if lead.get("building_sqft") else "unknown",
        "score": str(int(score)),
        "score_reason": score_reason,
        "next_tuesday": _next_weekday(now, 1),
        "next_thursday": _next_weekday(now, 3),
        "sender_name": "[Your Name]",
        "sender_company": "[Your Company]",
        "sender_phone": "[Your Phone]",
        "sender_email": "[Your Email]",
    }


def generate_email(db, lead_id: int, template_name: str = "initial") -> str:
    lead = db.get_lead(lead_id)
    if not lead:
        raise ValueError(f"Lead {lead_id} not found")
    contacts = db.get_contacts(lead_id)
    context = _build_context(lead, contacts)
    template_file = os.path.join(TEMPLATES_DIR, f"email_{template_name}.txt")
    if not os.path.exists(template_file):
        raise ValueError(f"Template '{template_name}' not found. Available: {list_templates()}")
    with open(template_file) as f:
        tmpl = Template(f.read())
    return tmpl.safe_substitute(context)


def generate_call_script(db, lead_id: int) -> str:
    lead = db.get_lead(lead_id)
    if not lead:
        raise ValueError(f"Lead {lead_id} not found")
    contacts = db.get_contacts(lead_id)
    context = _build_context(lead, contacts)
    template_file = os.path.join(TEMPLATES_DIR, "call_script.txt")
    with open(template_file) as f:
        tmpl = Template(f.read())
    return tmpl.safe_substitute(context)


def list_templates() -> list[str]:
    templates = []
    for f in os.listdir(TEMPLATES_DIR):
        if f.startswith("email_") and f.endswith(".txt"):
            templates.append(f.replace("email_", "").replace(".txt", ""))
    return templates
