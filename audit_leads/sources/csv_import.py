"""CSV import with flexible column name matching."""

import csv

DEFAULT_COLUMN_MAP = {
    "company_name": ["company", "company_name", "business", "name", "business_name"],
    "address": ["address", "street", "street_address"],
    "city": ["city", "town"],
    "state": ["state", "st", "province"],
    "zip_code": ["zip", "zip_code", "postal", "postal_code", "zipcode"],
    "industry": ["industry", "sector", "type", "business_type"],
    "building_sqft": ["sqft", "square_feet", "size", "building_sqft", "sq_ft", "area"],
    "building_year_built": ["year_built", "built", "year", "construction_year", "building_year_built"],
    "estimated_energy_spend": ["energy_spend", "energy_cost", "utility_cost", "annual_energy", "estimated_energy_spend"],
    "contact_name": ["contact", "contact_name", "person", "contact_person"],
    "contact_email": ["email", "contact_email"],
    "contact_phone": ["phone", "contact_phone", "telephone"],
    "contact_title": ["title", "contact_title", "job_title", "position"],
}


def _match_columns(headers: list[str], column_map: dict = None) -> dict:
    """Match CSV headers to our field names. Returns {our_field: csv_header_index}."""
    cmap = column_map or DEFAULT_COLUMN_MAP
    matched = {}
    normalized_headers = [h.strip().lower().replace(" ", "_") for h in headers]

    for field_name, aliases in cmap.items():
        for alias in aliases:
            alias_norm = alias.lower().replace(" ", "_")
            if alias_norm in normalized_headers:
                idx = normalized_headers.index(alias_norm)
                matched[field_name] = idx
                break
    return matched


def import_csv(db, filepath: str, column_map: dict = None) -> tuple[int, int]:
    """Import leads from a CSV file. Returns (imported_count, skipped_count)."""
    imported = 0
    skipped = 0

    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        headers = next(reader)
        mapping = _match_columns(headers, column_map)

        if "company_name" not in mapping:
            raise ValueError(
                f"Cannot find a 'company_name' column. Headers found: {headers}. "
                "Use a column_map to specify the mapping."
            )

        lead_fields = {
            "company_name", "address", "city", "state", "zip_code",
            "industry", "building_sqft", "building_year_built",
            "estimated_energy_spend",
        }
        contact_fields = {"contact_name", "contact_email", "contact_phone", "contact_title"}

        for row in reader:
            if not row or not any(cell.strip() for cell in row):
                continue

            lead_data = {}
            for field_name in lead_fields:
                if field_name in mapping:
                    val = row[mapping[field_name]].strip()
                    if val:
                        if field_name == "building_sqft":
                            try:
                                lead_data[field_name] = int(float(val.replace(",", "")))
                            except ValueError:
                                pass
                        elif field_name == "building_year_built":
                            try:
                                lead_data[field_name] = int(float(val))
                            except ValueError:
                                pass
                        elif field_name == "estimated_energy_spend":
                            try:
                                lead_data[field_name] = float(val.replace(",", "").replace("$", ""))
                            except ValueError:
                                pass
                        else:
                            lead_data[field_name] = val

            company = lead_data.get("company_name")
            if not company:
                skipped += 1
                continue

            address = lead_data.get("address")
            if db.lead_exists(company, address):
                skipped += 1
                continue

            lead_data["source"] = "csv_import"
            lead_id = db.add_lead(**lead_data)

            # Add contact if available
            contact_data = {}
            for cf in contact_fields:
                if cf in mapping:
                    val = row[mapping[cf]].strip()
                    if val:
                        # Strip "contact_" prefix for db field names
                        db_field = cf.replace("contact_", "")
                        contact_data[db_field] = val

            if contact_data.get("name"):
                contact_data["is_primary"] = 1
                db.add_contact(lead_id, **contact_data)

            imported += 1

    return imported, skipped
