"""Dashboard and authenticated views."""

from flask import Blueprint, render_template, session

from .auth import login_required, get_db

views_bp = Blueprint("views", __name__, url_prefix="/")


@views_bp.route("/")
@login_required
def dashboard():
    db = get_db()
    user = db.get_user(session["user_id"])
    leads = db.list_leads(limit=10000)

    status_counts = {}
    for lead in leads:
        s = lead["status"]
        status_counts[s] = status_counts.get(s, 0) + 1

    top_leads = db.list_leads(limit=10)

    return render_template(
        "dashboard.html",
        user=user,
        total_leads=len(leads),
        status_counts=status_counts,
        top_leads=top_leads,
    )
