"""Tests for CSV import functionality."""

import os
import tempfile
import pytest

from audit_leads.db import Database
from audit_leads.sources.csv_import import import_csv, _match_columns


@pytest.fixture
def db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    database = Database(path)
    yield database
    database.close()
    os.unlink(path)


def _write_csv(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    with open(path, "w") as f:
        f.write(content)
    return path


def test_match_columns_standard():
    headers = ["Company Name", "City", "State", "Industry", "Square Feet"]
    mapping = _match_columns(headers)
    assert "company_name" in mapping
    assert "city" in mapping
    assert "state" in mapping
    assert "industry" in mapping
    assert "building_sqft" in mapping


def test_match_columns_alternate_names():
    headers = ["Business", "Town", "ST", "Sector", "Area"]
    mapping = _match_columns(headers)
    assert "company_name" in mapping
    assert "city" in mapping
    assert "state" in mapping
    assert "industry" in mapping
    assert "building_sqft" in mapping


def test_import_basic(db):
    csv_content = """Company Name,City,State,Industry,Square Feet,Year Built
Acme Manufacturing,Chicago,IL,manufacturing,50000,1985
Beta Corp,Boston,MA,office,25000,2005
"""
    path = _write_csv(csv_content)
    try:
        imported, skipped = import_csv(db, path)
        assert imported == 2
        assert skipped == 0

        leads = db.list_leads()
        assert len(leads) == 2
    finally:
        os.unlink(path)


def test_import_with_contacts(db):
    csv_content = """Company Name,City,Contact Name,Contact Email
Acme Corp,Chicago,John Doe,john@acme.com
"""
    path = _write_csv(csv_content)
    try:
        imported, _ = import_csv(db, path)
        assert imported == 1

        leads = db.list_leads()
        contacts = db.get_contacts(leads[0]["id"])
        assert len(contacts) == 1
        assert contacts[0]["name"] == "John Doe"
        assert contacts[0]["email"] == "john@acme.com"
    finally:
        os.unlink(path)


def test_import_deduplication(db):
    csv_content = """Company Name,Address
Acme Corp,123 Main St
Acme Corp,123 Main St
"""
    path = _write_csv(csv_content)
    try:
        imported, skipped = import_csv(db, path)
        assert imported == 1
        assert skipped == 1
    finally:
        os.unlink(path)


def test_import_missing_company_column(db):
    csv_content = """Foo,Bar,Baz
1,2,3
"""
    path = _write_csv(csv_content)
    try:
        with pytest.raises(ValueError, match="company_name"):
            import_csv(db, path)
    finally:
        os.unlink(path)


def test_import_numeric_fields(db):
    csv_content = """Company Name,Square Feet,Year Built,Energy Cost
Test Corp,"50,000",1990,"$120,000"
"""
    path = _write_csv(csv_content)
    try:
        imported, _ = import_csv(db, path)
        assert imported == 1
        lead = db.list_leads()[0]
        assert lead["building_sqft"] == 50000
        assert lead["building_year_built"] == 1990
        assert lead["estimated_energy_spend"] == 120000.0
    finally:
        os.unlink(path)
