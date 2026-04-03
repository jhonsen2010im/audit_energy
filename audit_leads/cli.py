"""CLI interface for the Energy Audit Lead Generation Tool."""

import csv
import sys

import click

from .db import Database
from .scoring import score_lead, explain_score, score_all_leads
from .sources.csv_import import import_csv
from .sources.scraper import scrape_commercial_listings, scrape_government_energy_data
from .sources.search import search_prospects
from .outreach import generate_email, generate_call_script, list_templates


pass_db = click.make_pass_decorator(Database, ensure=True)


@click.group()
@click.option("--db", "db_path", default="leads.db", help="Path to SQLite database file.")
@click.pass_context
def cli(ctx, db_path):
    """Energy Audit Lead Generation Tool.

    Find, score, and manage leads for energy audit services.
    """
    ctx.ensure_object(dict)
    ctx.obj = Database(db_path)


@cli.result_callback()
@click.pass_context
def cleanup(ctx, *args, **kwargs):
    ctx.obj.close()


# ==================== Lead Sources ====================

@cli.command("import-csv")
@click.argument("filepath", type=click.Path(exists=True))
@click.option("--rescore/--no-rescore", default=True, help="Auto-score after import.")
@click.pass_obj
def cmd_import_csv(db, filepath, rescore):
    """Import leads from a CSV file."""
    imported, skipped = import_csv(db, filepath)
    click.echo(f"Imported {imported} leads, skipped {skipped} duplicates.")
    if rescore and imported > 0:
        count = score_all_leads(db)
        click.echo(f"Scored {count} leads.")


@cli.command("scrape")
@click.option("--location", required=True, help="City/region to search (e.g., 'Chicago, IL').")
@click.option("--max-results", default=50, help="Maximum results to fetch.")
@click.option("--government/--no-government", default=False, help="Show government data sources.")
@click.pass_obj
def cmd_scrape(db, location, max_results, government):
    """Scrape web sources for potential leads."""
    if government:
        parts = [p.strip() for p in location.split(",")]
        state = parts[1] if len(parts) > 1 else parts[0]
        scrape_government_energy_data(db, state=state, city=parts[0])
    else:
        scrape_commercial_listings(db, location, max_results)


@cli.command("search")
@click.option("--query", help="Custom search query.")
@click.option("--location", help="Location to search in.")
@click.option("--industry", help="Industry to target.")
@click.option("--max-results", default=20, help="Maximum results.")
@click.pass_obj
def cmd_search(db, query, location, industry, max_results):
    """Search the web for potential energy audit leads."""
    search_prospects(db, query=query, location=location,
                     industry=industry, max_results=max_results)


# ==================== Lead Management ====================

@cli.command("list")
@click.option("--status", type=click.Choice(
    ["new", "contacted", "qualified", "proposal", "won", "lost"]))
@click.option("--min-score", type=float, help="Minimum lead score.")
@click.option("--limit", default=50, help="Max leads to show.")
@click.pass_obj
def cmd_list(db, status, min_score, limit):
    """List leads, optionally filtered by status and score."""
    leads = db.list_leads(status=status, min_score=min_score, limit=limit)
    if not leads:
        click.echo("No leads found.")
        return

    # Table header
    click.echo(f"{'ID':>5}  {'Score':>5}  {'Status':<11}  {'Company':<30}  {'City':<15}  {'Industry':<15}")
    click.echo("-" * 90)
    for lead in leads:
        click.echo(
            f"{lead['id']:>5}  "
            f"{lead['score']:>5.0f}  "
            f"{lead['status']:<11}  "
            f"{(lead['company_name'] or '')[:30]:<30}  "
            f"{(lead['city'] or '')[:15]:<15}  "
            f"{(lead['industry'] or '')[:15]:<15}"
        )
    click.echo(f"\nTotal: {len(leads)} leads")


@cli.command("show")
@click.argument("lead_id", type=int)
@click.pass_obj
def cmd_show(db, lead_id):
    """Show detailed information about a lead."""
    lead = db.get_lead(lead_id)
    if not lead:
        click.echo(f"Lead {lead_id} not found.")
        return

    click.echo(f"\n{'=' * 50}")
    click.echo(f"Lead #{lead['id']}: {lead['company_name']}")
    click.echo(f"{'=' * 50}")
    click.echo(f"  Status:    {lead['status']}")
    click.echo(f"  Score:     {lead['score']:.0f}/100")
    click.echo(f"  Source:    {lead['source']}")
    if lead['address']:
        click.echo(f"  Address:   {lead['address']}")
    if lead['city'] or lead['state']:
        click.echo(f"  Location:  {lead['city'] or ''}, {lead['state'] or ''} {lead['zip_code'] or ''}")
    if lead['industry']:
        click.echo(f"  Industry:  {lead['industry']}")
    if lead['building_sqft']:
        click.echo(f"  Size:      {lead['building_sqft']:,} sq ft")
    if lead['building_year_built']:
        click.echo(f"  Built:     {lead['building_year_built']}")
    if lead['estimated_energy_spend']:
        click.echo(f"  Energy $:  ${lead['estimated_energy_spend']:,.0f}/yr")
    if lead['notes']:
        click.echo(f"  Notes:     {lead['notes']}")

    # Contacts
    contacts = db.get_contacts(lead_id)
    if contacts:
        click.echo(f"\n  Contacts:")
        for c in contacts:
            primary = " (primary)" if c['is_primary'] else ""
            click.echo(f"    - {c['name']}{primary}")
            if c['title']:
                click.echo(f"      Title: {c['title']}")
            if c['email']:
                click.echo(f"      Email: {c['email']}")
            if c['phone']:
                click.echo(f"      Phone: {c['phone']}")

    # Recent interactions
    interactions = db.get_interactions(lead_id)
    if interactions:
        click.echo(f"\n  Recent Interactions:")
        for i in interactions[:5]:
            click.echo(f"    [{i['occurred_at']}] {i['type']}: {i.get('subject', '')}")
    click.echo()


@cli.command("set-status")
@click.argument("lead_id", type=int)
@click.argument("new_status", type=click.Choice(
    ["new", "contacted", "qualified", "proposal", "won", "lost"]))
@click.pass_obj
def cmd_set_status(db, lead_id, new_status):
    """Update a lead's status."""
    lead = db.get_lead(lead_id)
    if not lead:
        click.echo(f"Lead {lead_id} not found.")
        return
    old_status = lead['status']
    db.update_lead(lead_id, status=new_status)
    click.echo(f"Lead #{lead_id} ({lead['company_name']}): {old_status} -> {new_status}")


@cli.command("add-note")
@click.argument("lead_id", type=int)
@click.argument("note")
@click.pass_obj
def cmd_add_note(db, lead_id, note):
    """Add a note to a lead."""
    lead = db.get_lead(lead_id)
    if not lead:
        click.echo(f"Lead {lead_id} not found.")
        return
    existing = lead.get('notes') or ''
    updated = f"{existing}\n{note}".strip() if existing else note
    db.update_lead(lead_id, notes=updated)
    click.echo(f"Note added to lead #{lead_id}.")


@cli.command("find")
@click.argument("query")
@click.pass_obj
def cmd_find(db, query):
    """Search leads by company name, city, or industry."""
    leads = db.search_leads(query)
    if not leads:
        click.echo(f"No leads matching '{query}'.")
        return
    click.echo(f"{'ID':>5}  {'Score':>5}  {'Status':<11}  {'Company':<30}  {'City':<15}")
    click.echo("-" * 75)
    for lead in leads:
        click.echo(
            f"{lead['id']:>5}  "
            f"{lead['score']:>5.0f}  "
            f"{lead['status']:<11}  "
            f"{(lead['company_name'] or '')[:30]:<30}  "
            f"{(lead['city'] or '')[:15]:<15}"
        )


# ==================== Scoring ====================

@cli.command("rescore")
@click.pass_obj
def cmd_rescore(db):
    """Re-score all leads."""
    count = score_all_leads(db)
    click.echo(f"Updated scores for {count} leads.")


@cli.command("explain-score")
@click.argument("lead_id", type=int)
@click.pass_obj
def cmd_explain_score(db, lead_id):
    """Show the scoring breakdown for a lead."""
    lead = db.get_lead(lead_id)
    if not lead:
        click.echo(f"Lead {lead_id} not found.")
        return

    result = explain_score(lead)
    click.echo(f"\nScoring Breakdown: {lead['company_name']}")
    click.echo(f"{'=' * 55}")
    for name, info in result["factors"].items():
        click.echo(
            f"  {name:<15}  {info['score']:>5.0f} x {info['weight']:.2f} = {info['weighted']:>5.1f}  "
            f"  {info['explanation']}"
        )
    click.echo(f"{'─' * 55}")
    click.echo(f"  {'TOTAL':<15}  {'':>14} = {result['total']:>5.1f}")
    click.echo()


# ==================== Outreach ====================

@cli.command("draft-email")
@click.argument("lead_id", type=int)
@click.option("--template", default="initial",
              help=f"Template name (initial, followup).")
@click.pass_obj
def cmd_draft_email(db, lead_id, template):
    """Generate a personalized email for a lead."""
    try:
        email = generate_email(db, lead_id, template)
        click.echo(email)
    except ValueError as e:
        click.echo(f"Error: {e}")


@cli.command("call-script")
@click.argument("lead_id", type=int)
@click.pass_obj
def cmd_call_script(db, lead_id):
    """Generate a call script for a lead."""
    try:
        script = generate_call_script(db, lead_id)
        click.echo(script)
    except ValueError as e:
        click.echo(f"Error: {e}")


# ==================== Interactions ====================

@cli.command("log-interaction")
@click.argument("lead_id", type=int)
@click.option("--type", "interaction_type", required=True,
              type=click.Choice(["email", "call", "meeting", "note"]))
@click.option("--subject", default="", help="Subject/summary.")
@click.option("--body", default="", help="Detailed notes.")
@click.pass_obj
def cmd_log_interaction(db, lead_id, interaction_type, subject, body):
    """Log an interaction with a lead."""
    lead = db.get_lead(lead_id)
    if not lead:
        click.echo(f"Lead {lead_id} not found.")
        return
    db.add_interaction(lead_id, type=interaction_type, subject=subject, body=body)
    click.echo(f"Logged {interaction_type} interaction for lead #{lead_id} ({lead['company_name']}).")


@cli.command("history")
@click.argument("lead_id", type=int)
@click.pass_obj
def cmd_history(db, lead_id):
    """Show interaction history for a lead."""
    lead = db.get_lead(lead_id)
    if not lead:
        click.echo(f"Lead {lead_id} not found.")
        return

    interactions = db.get_interactions(lead_id)
    if not interactions:
        click.echo(f"No interactions for lead #{lead_id}.")
        return

    click.echo(f"\nInteraction History: {lead['company_name']}")
    click.echo(f"{'=' * 60}")
    for i in interactions:
        click.echo(f"  [{i['occurred_at']}] {i['type'].upper()}")
        if i.get('subject'):
            click.echo(f"    Subject: {i['subject']}")
        if i.get('body'):
            click.echo(f"    {i['body']}")
        click.echo()


# ==================== Export ====================

@cli.command("export")
@click.option("--output", default="leads_export.csv", help="Output CSV file path.")
@click.option("--status", help="Filter by status.")
@click.pass_obj
def cmd_export(db, output, status):
    """Export leads to CSV."""
    leads = db.list_leads(status=status, limit=10000)
    if not leads:
        click.echo("No leads to export.")
        return

    fieldnames = [
        "id", "company_name", "address", "city", "state", "zip_code",
        "industry", "building_sqft", "building_year_built",
        "estimated_energy_spend", "source", "score", "status", "notes",
    ]

    with open(output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(leads)

    click.echo(f"Exported {len(leads)} leads to {output}.")


if __name__ == "__main__":
    cli()
