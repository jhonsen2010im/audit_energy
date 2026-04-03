"""Tests for the database layer."""

import os
import tempfile
import pytest

from audit_leads.db import Database


@pytest.fixture
def db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    database = Database(path)
    yield database
    database.close()
    os.unlink(path)


def test_add_and_get_lead(db):
    lead_id = db.add_lead(company_name="Acme Corp", city="Chicago", state="IL")
    lead = db.get_lead(lead_id)
    assert lead is not None
    assert lead["company_name"] == "Acme Corp"
    assert lead["city"] == "Chicago"
    assert lead["status"] == "new"
    assert lead["score"] == 0.0


def test_update_lead(db):
    lead_id = db.add_lead(company_name="Test Co")
    db.update_lead(lead_id, status="contacted", score=75.5)
    lead = db.get_lead(lead_id)
    assert lead["status"] == "contacted"
    assert lead["score"] == 75.5


def test_list_leads_filter_status(db):
    db.add_lead(company_name="A", status="new")
    db.add_lead(company_name="B", status="contacted")
    db.add_lead(company_name="C", status="new")

    new_leads = db.list_leads(status="new")
    assert len(new_leads) == 2
    contacted = db.list_leads(status="contacted")
    assert len(contacted) == 1


def test_list_leads_filter_score(db):
    id1 = db.add_lead(company_name="Low")
    id2 = db.add_lead(company_name="High")
    db.update_lead(id1, score=30.0)
    db.update_lead(id2, score=80.0)

    high_leads = db.list_leads(min_score=60.0)
    assert len(high_leads) == 1
    assert high_leads[0]["company_name"] == "High"


def test_lead_exists(db):
    db.add_lead(company_name="Unique Corp", address="123 Main St")
    assert db.lead_exists("Unique Corp", "123 Main St") is True
    assert db.lead_exists("Unique Corp", "456 Other St") is False
    assert db.lead_exists("Nonexistent") is False


def test_search_leads(db):
    db.add_lead(company_name="Chicago Manufacturing", city="Chicago", industry="manufacturing")
    db.add_lead(company_name="Boston Office", city="Boston", industry="office")

    results = db.search_leads("Chicago")
    assert len(results) == 1
    assert results[0]["company_name"] == "Chicago Manufacturing"

    results = db.search_leads("office")
    assert len(results) == 1


def test_contacts(db):
    lead_id = db.add_lead(company_name="Contact Test")
    cid = db.add_contact(lead_id, name="John Doe", email="john@test.com", is_primary=1)
    assert cid is not None

    contacts = db.get_contacts(lead_id)
    assert len(contacts) == 1
    assert contacts[0]["name"] == "John Doe"
    assert contacts[0]["is_primary"] == 1


def test_interactions(db):
    lead_id = db.add_lead(company_name="Interaction Test")
    iid = db.add_interaction(lead_id, type="email", subject="Initial outreach")
    assert iid is not None

    interactions = db.get_interactions(lead_id)
    assert len(interactions) == 1
    assert interactions[0]["type"] == "email"
    assert interactions[0]["subject"] == "Initial outreach"
