from authlib.integrations.flask_client import OAuth
from flask import current_app

_oauth = None

def get_oauth(app=None):
    global _oauth
    if _oauth is None:
        _oauth = OAuth(app)
        _oauth.register(
            name="discord",
            client_id=current_app.config["DISCORD_CLIENT_ID"],
            client_secret=current_app.config["DISCORD_CLIENT_SECRET"],
            access_token_url="https://discord.com/api/oauth2/token",
            authorize_url="https://discord.com/api/oauth2/authorize",
            api_base_url="https://discord.com/api/",
            client_kwargs={"token_endpoint_auth_method": "client_secret_post", "scope": "identify email"},
        )
    return _oauth
