"""Web search for energy audit prospects."""

import os
import json

import click

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

SEARCH_QUERIES = [
    "{industry} businesses in {location} old building",
    "commercial buildings {location} energy efficiency",
    "large office building {location} built before 2000",
    "{location} warehouse manufacturing facility",
    "{location} commercial property energy costs",
]


def search_prospects(db, query: str = None, location: str = None,
                     industry: str = None, max_results: int = 20) -> int:
    """Search for businesses likely needing energy audits.

    Uses SerpAPI if SERPAPI_KEY is set in environment.
    Returns count of leads added.
    """
    if not HAS_REQUESTS:
        click.echo("Warning: requests library required. Install with: pip install requests")
        return 0

    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        click.echo("Note: Set SERPAPI_KEY environment variable for web search functionality.")
        click.echo("  export SERPAPI_KEY=your_api_key_here")
        click.echo()
        click.echo("Without an API key, you can still use:")
        click.echo("  - audit-leads import-csv  (import from CSV files)")
        click.echo("  - audit-leads scrape      (scrape property listings)")
        click.echo()
        click.echo("Alternative lead sources to search manually:")
        _suggest_manual_searches(location, industry)
        return 0

    # Build search queries
    search_terms = []
    if query:
        search_terms.append(query)
    else:
        for template in SEARCH_QUERIES:
            search_terms.append(template.format(
                location=location or "",
                industry=industry or "commercial",
            ))

    added = 0
    for term in search_terms[:3]:  # Limit API calls
        results = _serpapi_search(api_key, term, max_results)
        for result in results:
            company = result.get("title", "").strip()
            if not company or db.lead_exists(company):
                continue

            lead_data = {
                "company_name": company,
                "source": "search",
            }
            if location:
                # Try to parse city/state from location
                parts = [p.strip() for p in location.split(",")]
                if len(parts) >= 1:
                    lead_data["city"] = parts[0]
                if len(parts) >= 2:
                    lead_data["state"] = parts[1]
            if industry:
                lead_data["industry"] = industry

            db.add_lead(**lead_data)
            added += 1

            if added >= max_results:
                break
        if added >= max_results:
            break

    click.echo(f"Added {added} leads from web search.")
    return added


def _serpapi_search(api_key: str, query: str, max_results: int) -> list[dict]:
    """Execute a search via SerpAPI."""
    try:
        resp = requests.get(
            "https://serpapi.com/search",
            params={
                "q": query,
                "api_key": api_key,
                "num": min(max_results, 10),
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("organic_results", [])
    except Exception as e:
        click.echo(f"Search error: {e}")
        return []


def _suggest_manual_searches(location: str = None, industry: str = None):
    """Print suggestions for finding leads manually."""
    loc = location or "[your city]"
    ind = industry or "commercial"
    click.echo("Suggested manual search strategies:")
    click.echo(f"  1. Google: '{ind} buildings in {loc} energy audit'")
    click.echo(f"  2. Google Maps: search for '{ind}' in {loc}, filter by older buildings")
    click.echo(f"  3. Local chamber of commerce member directory")
    click.echo(f"  4. City/county property records (often public)")
    click.echo(f"  5. Commercial real estate listings in {loc}")
    click.echo(f"  6. Government energy benchmarking data (see 'audit-leads scrape --help')")
