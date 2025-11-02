from flask import Blueprint, render_template
from ..services.supabase_client import get_supabase

bp = Blueprint("home", __name__)


@bp.get("/")
def index():
    # Make Supabase optional for the home page
    content = None
    sb = None
    try:
        sb = get_supabase()
    except Exception:
        sb = None

    if sb is not None:
        try:
            res = sb.table('site_content').select('*').eq('page', 'home').execute()
            if getattr(res, 'data', None) and len(res.data) > 0:
                row = res.data[0]
                content = row.get('data') if isinstance(row, dict) else getattr(row, 'data', None)
        except Exception:
            content = None

    return render_template("home.html", content=content or {})


@bp.get("/contact")
def contact():
    return render_template("contact.html")
