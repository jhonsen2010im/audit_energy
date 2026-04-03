# Energy Audit Lead Generation Tool

A Python CLI tool to find, score, and manage leads for energy audit services.

## Features

- **Multiple lead sources**: Import from CSV, scrape property listings, search the web
- **Lead scoring**: Automatically rank leads by audit-readiness (building age, size, industry, energy spend)
- **Outreach templates**: Generate personalized emails and call scripts
- **CRM tracking**: Track lead status, contacts, notes, and interaction history
- **Export**: Export filtered leads to CSV

## Installation

```bash
pip install -e .
```

## Quick Start

```bash
# Import leads from a CSV file
audit-leads import-csv contacts.csv

# View top-scoring leads
audit-leads list --min-score 60

# Show lead details
audit-leads show 1

# See why a lead scored high
audit-leads explain-score 1

# Generate a personalized email
audit-leads draft-email 1 --template initial

# Generate a call script
audit-leads call-script 1

# Update lead status after contact
audit-leads set-status 1 contacted

# Log an interaction
audit-leads log-interaction 1 --type email --subject "Initial outreach sent"

# Search for leads by keyword
audit-leads find "manufacturing"

# Export leads to CSV
audit-leads export --output top_leads.csv --status new
```

## Lead Sources

### CSV Import
The most reliable way to add leads. Automatically maps common column names:
- Company: `company`, `company_name`, `business`, `name`
- Size: `sqft`, `square_feet`, `size`, `area`
- Year: `year_built`, `built`, `year`, `construction_year`
- Energy: `energy_spend`, `energy_cost`, `utility_cost`
- Contact: `contact_name`, `email`, `phone`

```bash
audit-leads import-csv my_contacts.csv
```

### Web Scraping
Search commercial property listings and government energy databases:
```bash
audit-leads scrape --location "Chicago, IL"
audit-leads scrape --location "New York, NY" --government
```

### Web Search
Search for prospects using SerpAPI (requires API key):
```bash
export SERPAPI_KEY=your_key_here
audit-leads search --query "manufacturing" --location "Chicago, IL"
```

## Lead Scoring

Leads are scored 0-100 based on four equally weighted factors:

| Factor | High Score | Low Score |
|--------|-----------|-----------|
| Building Age | Pre-1985 | Post-2020 |
| Building Size | >50,000 sq ft | <5,000 sq ft |
| Industry | Manufacturing, Healthcare, Hospitality | Unknown |
| Energy Spend | >$100k/yr | <$10k/yr |

Use `audit-leads explain-score <id>` to see the full breakdown.

## Lead Statuses

`new` -> `contacted` -> `qualified` -> `proposal` -> `won` / `lost`

## Running Tests

```bash
pip install pytest
pytest tests/
```
