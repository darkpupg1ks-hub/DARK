from flask import Blueprint, redirect, url_for, session, request
from flask import current_app, render_template
from ..services.discord_oauth import get_oauth

bp = Blueprint("auth", __name__)

@bp.get("/login")
def login_page():
    return render_template("auth_login.html")

@bp.get("/discord")
def discord_login():
    oauth = get_oauth()
    redirect_uri = current_app.config["DISCORD_REDIRECT_URI"]
    return oauth.discord.authorize_redirect(redirect_uri)

@bp.get("/discord/callback")
def discord_callback():
    oauth = get_oauth()
    token = oauth.discord.authorize_access_token()
    user = oauth.discord.get("/users/@me").json()
    session["user"] = {"id": user["id"], "name": user.get("username"), "email": user.get("email")}
    return redirect(url_for("dashboard.index"))

@bp.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("home.index"))
