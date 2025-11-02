import os
try:
    from dotenv import load_dotenv
except Exception:
    # python-dotenv not installed in this environment; provide a no-op loader
    def load_dotenv(*args, **kwargs):
        return None

# Load environment variables from .env file (no-op if dotenv missing)
load_dotenv()

class Config:
    # Flask
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-super-secret")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")

    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    # Discord
    DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
    DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
    DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")

    # AI
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "none")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

def load_config(app):
    app.config.from_object(Config)
