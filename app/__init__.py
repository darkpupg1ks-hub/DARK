from flask import Flask


def create_app():
    app = Flask(__name__)

    # Load config and register extensions
    try:
        from .config import load_config
        load_config(app)
    except Exception:
        # Fallback: Flask will still run with defaults
        pass

    try:
        from .extensions import register_extensions
        register_extensions(app)
    except Exception:
        pass

    # Register blueprints
    from .blueprints.dashboard import bp as dash_bp
    from .blueprints.home import bp as home_bp
    from .blueprints.shop import bp as shop_bp
    from .blueprints.tools import bp as tools_bp
    from .blueprints.auth import bp as auth_bp
    from .blueprints.api_ai import bp as api_ai_bp

    app.register_blueprint(home_bp)  # "/" and basic pages
    app.register_blueprint(shop_bp, url_prefix="/shop")
    app.register_blueprint(tools_bp, url_prefix="/tools")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dash_bp, url_prefix="/dashboard")
    app.register_blueprint(api_ai_bp, url_prefix="/api")

    return app


