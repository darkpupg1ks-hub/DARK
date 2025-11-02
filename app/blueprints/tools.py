from flask import Blueprint, render_template, request, flash, redirect
from ..services.supabase_client import get_supabase
import os, json

bp = Blueprint("tools", __name__)

@bp.get("/")
def tools_index():
    tools = []
    # Try to fetch from Supabase if configured
    sb = None
    try:
        sb = get_supabase()
    except Exception:
        sb = None
    # Try progressively broader selects to tolerate missing optional columns
    select_variants = [
        "id,title,link,version,notes,visible,bg_image,thumb_image",
        "id,title,link,version,notes,visible",
        "id,title,link,version,notes",
        "*",
    ]
    if sb is not None:
        for cols in select_variants:
            try:
                res = sb.table("downloads").select(cols).order("id").execute()
                tools = getattr(res, 'data', None) or res or []
                if tools is None:
                    tools = []
                break
            except Exception:
                tools = []
                continue

    # Merge with local fallback file so items saved locally appear on the site too
    try:
        p = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'downloads.json')
        p = os.path.normpath(p)
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                local_list = json.load(f) or []
            if isinstance(local_list, list):
                existing_ids = set()
                if isinstance(tools, list):
                    try:
                        existing_ids = set([int((t.get('id') if isinstance(t, dict) else 0) or 0) for t in tools])
                    except Exception:
                        existing_ids = set()
                else:
                    tools = []
                for item in local_list:
                    try:
                        iid = int(item.get('id', 0))
                    except Exception:
                        iid = 0
                    if iid not in existing_ids:
                        tools.append(item)
    except Exception:
        pass
    return render_template("tools.html", tools=tools)

@bp.post("/redeem")
def redeem_key():
    """Redeem a license key and attach to current user (session mock)."""
    key = (request.form.get("key") or "").strip()
    sb = get_supabase()
    res = sb.rpc("redeem_license_key", {"p_key": key}).execute()
    if getattr(res, "data", None) == True:
        flash("Key redeemed successfully!", "success")
    else:
        flash("Invalid or already used key.", "error")
    return redirect("/tools")
