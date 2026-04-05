"""Authentication routes with Google OAuth."""

from functools import wraps

from flask import Blueprint, redirect, url_for, session, current_app, g

from ..db import Database
from . import oauth

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def get_db():
    if "db" not in g:
        g.db = Database(current_app.config["DB_PATH"])
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@auth_bp.record
def register_teardown(state):
    state.app.teardown_appcontext(close_db)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


@auth_bp.route("/login")
def login():
    if "user_id" in session:
        return redirect(url_for("views.dashboard"))
    from flask import render_template
    return render_template("login.html")


@auth_bp.route("/google")
def google_login():
    redirect_uri = url_for("auth.callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/callback")
def callback():
    token = oauth.google.authorize_access_token()
    userinfo = token.get("userinfo")
    if not userinfo:
        return redirect(url_for("auth.login"))

    db = get_db()
    user = db.upsert_user(
        google_id=userinfo["sub"],
        email=userinfo["email"],
        name=userinfo.get("name"),
        picture_url=userinfo.get("picture"),
    )
    session["user_id"] = user["id"]
    return redirect(url_for("views.dashboard"))


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
