from flask import Blueprint, render_template, session, request, redirect, url_for, flash, jsonify
from ..services.supabase_client import get_supabase
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

# âœ… Ù„Ø§Ø²Ù… Ù†Ø¹Ø±Ù‘Ù Ø§Ù„Ù€ Blueprint Ø£ÙˆÙ„Ø§Ù‹
bp = Blueprint("dashboard", __name__)


# simple decorator to require admin for new API endpoints
def require_admin(fn):
    from functools import wraps

    @wraps(fn)
    def wrapper(*a, **kw):
        if not session.get("is_admin"):
            return redirect(url_for("dashboard.admin_login"))
        return fn(*a, **kw)

    return wrapper


# --- Background job: remove expired license keys periodically ---
def delete_expired_keys():
    try:
        sb = get_supabase()
        now_iso = datetime.utcnow().isoformat()
        # delete any license_keys where expires_at is before now
        sb.table("license_keys").delete().lt("expires_at", now_iso).execute()
        print("[scheduler] expired keys cleanup ran at", now_iso)
    except Exception as e:
        print("[scheduler] expired keys cleanup failed:", e)


# start scheduler (runs in background)
try:
    scheduler = BackgroundScheduler()
    scheduler.add_job(delete_expired_keys, "interval", seconds=60, id="cleanup_license_keys")
    scheduler.start()
except Exception:
    # scheduler may already be running in some environments (reloader), ignore
    pass


# âœ… ØµÙØ­Ø© Ù„ÙˆØ­Ø© Ø§Ù„ØªØ­ÙƒÙ… Ø§Ù„Ø±Ø¦ÙŠØ³ÙŠØ© (welcome)
@bp.route("/welcome")
def welcome():
    if not session.get("is_admin"):
        return redirect(url_for("dashboard.admin_login"))
    return render_template("admin_welcome.html", hide_nav=True)

# âœ… ØµÙØ­Ø© Ø§Ù„Ù…ÙØ§ØªÙŠØ­
@bp.route("/keys")
def keys():
    if not session.get("is_admin"):
        return redirect(url_for("dashboard.admin_login"))
    # Try to use Supabase; if not configured, we'll save locally
    try:
        sb = get_supabase()
    except Exception:
        sb = None
    keys = sb.table("license_keys").select("*").order("id").execute().data
    return render_template("admin_keys.html", keys=keys, hide_nav=True)


# Add a new license key
@bp.route('/keys/add', methods=['GET', 'POST'])
def add_key():
    if not session.get('is_admin'):
        return redirect(url_for('dashboard.admin_login'))

    if request.method == 'POST':
        key = (request.form.get('key') or '').strip()
        product_id = request.form.get('product_id') or None
        sb = get_supabase()
        try:
            payload = {'key': key, 'product_id': product_id, 'is_used': False}
            try:
                res = sb.table('license_keys').insert(payload).execute()
            except Exception:
                # try alternate field name if schema differs
                alt = payload.copy()
                if 'key' in alt:
                    alt['key_value'] = alt.pop('key')
                res = sb.table('license_keys').insert(alt).execute()

            flash('✅ Key added', 'success')
            return redirect(url_for('dashboard.keys'))
        except Exception as e:
            flash(f'Error adding key: {e}', 'error')

    return render_template('admin_add_key.html', hide_nav=True)


# Edit existing license key
@bp.route('/keys/<int:key_id>/edit', methods=['GET', 'POST'])
def edit_key(key_id):
    if not session.get('is_admin'):
        return redirect(url_for('dashboard.admin_login'))

    sb = get_supabase()
    # fetch existing
    rec = sb.table('license_keys').select('*').eq('id', key_id).single().execute()
    if request.method == 'POST':
        key = (request.form.get('key') or '').strip()
        product_id = request.form.get('product_id') or None
        is_used = True if request.form.get('is_used') in ('1', 'true', 'on', 'True') else False
        try:
            sb.table('license_keys').update({'key': key, 'product_id': product_id, 'is_used': is_used}).eq('id', key_id).execute()
            flash('✅ Key updated', 'success')
            return redirect(url_for('dashboard.keys'))
        except Exception as e:
            flash(f'Error updating key: {e}', 'error')

    data = getattr(rec, 'data', None) or rec
    # if using supabase-py, .data may be list/single - normalize
    if isinstance(data, list) and len(data) > 0:
        record = data[0]
    else:
        record = data

    return render_template('admin_edit_key.html', key=record, hide_nav=True)


# Delete a license key
@bp.route('/keys/<int:key_id>/delete', methods=['POST'])
def delete_key(key_id):
    if not session.get('is_admin'):
        return redirect(url_for('dashboard.admin_login'))

    sb = get_supabase()
    try:
        sb.table('license_keys').delete().eq('id', key_id).execute()
        flash('✅ Key deleted', 'info')
    except Exception as e:
        flash(f'Error deleting key: {e}', 'error')

    return redirect(url_for('dashboard.keys'))


# --- JSON API for keys CRUD (admin only) ---
@bp.route('/api/keys', methods=['GET'])
@require_admin
def api_list_keys():
    """List keys with Supabase first; fallback to local JSON if unavailable."""
    try:
        sb = get_supabase()
    except Exception:
        sb = None

    if sb is not None:
        try:
            # supabase-py v2: order signature is order(column, desc=False)
            res = sb.table('license_keys').select('*').order('id', desc=False).execute()
            data = getattr(res, 'data', None) or res
            rows = []
            if isinstance(data, list):
                for r in data:
                    if isinstance(r, dict):
                        if 'key' in r and 'key_value' not in r:
                            r['key_value'] = r.get('key')
                        if 'is_used' in r and 'used' not in r:
                            r['used'] = r.get('is_used')
                    rows.append(r)
            else:
                r = data
                if isinstance(r, dict):
                    if 'key' in r and 'key_value' not in r:
                        r['key_value'] = r.get('key')
                    if 'is_used' in r and 'used' not in r:
                        r['used'] = r.get('is_used')
                rows = [r]
            return jsonify(rows)
        except Exception as e:
            print('[api_list_keys] supabase error, falling back:', repr(e))

    # local fallback
    try:
        import os, json
        p = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'keys.json')
        p = os.path.normpath(p)
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                rows = json.load(f) or []
        else:
            rows = []
        return jsonify(rows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/keys', methods=['POST'])
@require_admin
def api_create_key():
    data = request.get_json() or {}
    username = data.get('username')
    product = data.get('product') or data.get('product_id')
    duration = data.get('duration')  # {'unit':'minute','value':1} or {'unit':'lifetime'}

    # allow client to supply key_value (optional); otherwise generate a secure random key
    key_value = data.get('key_value') or str(uuid.uuid4()).replace('-', '').upper()[:24]
    expires_at = None
    if duration and duration.get('unit') != 'lifetime':
        unit = duration.get('unit')
        val = int(duration.get('value', 0) or 0)
        now = datetime.utcnow()
        if unit == 'minute':
            expires_at = (now + timedelta(minutes=val)).isoformat()
        elif unit == 'hour':
            expires_at = (now + timedelta(hours=val)).isoformat()
        elif unit == 'day':
            expires_at = (now + timedelta(days=val)).isoformat()
        elif unit == 'week':
            expires_at = (now + timedelta(weeks=val)).isoformat()
        elif unit == 'month':
            expires_at = (now + timedelta(days=30 * val)).isoformat()

    payload = {
        'key': key_value,
        'username': username,
        'product': product,
        'expires_at': expires_at,
        'is_used': False,
        'used': False,
    }
    sb = get_supabase()

    def _extract_error(res):
        # supabase client may return an object or dict; try common places for an error
        try:
            if res is None:
                return 'empty_response'
            # object-like (supabase-py Response)
            err = getattr(res, 'error', None)
            if err:
                return err
            # dict-like
            if isinstance(res, dict) and res.get('error'):
                return res.get('error')
            return None
        except Exception:
            return None

    def _normalize_rows(created):
        rows = []
        if isinstance(created, list):
            iterable = created
        else:
            iterable = [created]
        for r in iterable:
            if isinstance(r, dict):
                if 'key' in r and 'key_value' not in r:
                    r['key_value'] = r.get('key')
                if 'is_used' in r and 'used' not in r:
                    r['used'] = r.get('is_used')
            rows.append(r)
        return rows
    if sb is not None:
        # Try minimal-to-broader payloads to adapt to different table schemas
        attempts = []
        attempts.append({'key': key_value})
        attempts.append({'key': key_value, 'is_used': False})
        if product:
            attempts.append({'key': key_value, 'product': product})
            attempts.append({'key': key_value, 'product': product, 'is_used': False})
        if expires_at:
            attempts.append({'key': key_value, 'expires_at': expires_at})
            attempts.append({'key': key_value, 'is_used': False, 'expires_at': expires_at})
        # key_value variants
        attempts.append({'key_value': key_value})
        attempts.append({'key_value': key_value, 'is_used': False})
        if product:
            attempts.append({'key_value': key_value, 'product': product})
            attempts.append({'key_value': key_value, 'product': product, 'is_used': False})
        if expires_at:
            attempts.append({'key_value': key_value, 'expires_at': expires_at})
            attempts.append({'key_value': key_value, 'is_used': False, 'expires_at': expires_at})

        errors = []
        for pay in attempts:
            try:
                res = sb.table('license_keys').insert(pay).execute()
                err = _extract_error(res)
                if err:
                    raise Exception(err)
                created = getattr(res, 'data', None) or res
                rows = _normalize_rows(created)
                if not rows or not isinstance(rows[0], dict) or ((('key' not in rows[0]) and ('key_value' not in rows[0]))):
                    rows = [{
                        'key_value': key_value,
                        'username': username,
                        'product': product,
                        'expires_at': expires_at,
                        'is_used': False,
                        'used': False,
                    }]
                return jsonify({'ok': True, 'row': rows, 'key_value': key_value}), 201
            except Exception as e:
                try:
                    errors.append({'attempt': list(pay.keys()), 'error': str(e)})
                except Exception:
                    errors.append(str(e))
                continue
        print('[api_create_key] all supabase insert attempts failed:', errors)
        # fall through to local fallback below

    # Local fallback: store in data/keys.json so UI still works without Supabase
    try:
        import os, json, time
        p = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'keys.json')
        p = os.path.normpath(p)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        existing = []
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                try:
                    existing = json.load(f) or []
                except Exception:
                    existing = []
        new_id = (max([int(k.get('id', 0)) for k in existing]) + 1) if existing else 1
        row = {
            'id': new_id,
            'key': key_value,
            'key_value': key_value,
            'username': username,
            'product': product,
            'expires_at': expires_at,
            'is_used': False,
            'used': False,
            'created_at': time.time(),
        }
        existing.append(row)
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        return jsonify({'ok': True, 'row': [row], 'key_value': key_value, 'source': 'local'}), 201
    except Exception as e3:
        return jsonify({'error': f'local_fallback_failed: {str(e3)}'}), 500


@bp.route('/api/keys/<int:key_id>', methods=['PUT'])
@require_admin
def api_edit_key(key_id):
    data = request.get_json() or {}
    update = {}
    for f in ('username', 'product', 'is_used', 'used'):
        if f in data:
            update[f] = data[f]

    if 'duration' in data:
        dur = data['duration']
        if dur.get('unit') == 'lifetime':
            update['expires_at'] = None
        else:
            unit = dur.get('unit'); val = int(dur.get('value', 0) or 0)
            now = datetime.utcnow()
            if unit == 'minute':
                exp = now + timedelta(minutes=val)
            elif unit == 'hour':
                exp = now + timedelta(hours=val)
            elif unit == 'day':
                exp = now + timedelta(days=val)
            elif unit == 'week':
                exp = now + timedelta(weeks=val)
            elif unit == 'month':
                exp = now + timedelta(days=30 * val)
            update['expires_at'] = exp.isoformat()

    sb = get_supabase()
    try:
        sb.table('license_keys').update(update).eq('id', key_id).execute()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/keys/<int:key_id>', methods=['DELETE'])
@require_admin
def api_delete_key(key_id):
    # Try Supabase first, then fall back to local file
    try:
        sb = get_supabase()
    except Exception:
        sb = None
    if sb is not None:
        try:
            sb.table('license_keys').delete().eq('id', key_id).execute()
            return jsonify({'ok': True})
        except Exception:
            pass
    try:
        import os, json
        p = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'keys.json')
        p = os.path.normpath(p)
        if not os.path.exists(p):
            return jsonify({'ok': True, 'source': 'local'})
        with open(p, 'r', encoding='utf-8') as f:
            lst = json.load(f) or []
        lst = [r for r in lst if int(r.get('id', 0)) != int(key_id)]
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(lst, f, ensure_ascii=False, indent=2)
        return jsonify({'ok': True, 'source': 'local'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# public endpoint: check a key (used by site auth/clients)
@bp.route('/api/check_key', methods=['POST'])
def api_check_key():
    data = request.get_json() or {}
    key_value = data.get('key') or data.get('key_value') or data.get('license')
    if not key_value:
        return jsonify({'valid': False}), 400
    sb = get_supabase()
    try:
        res = sb.table('license_keys').select('*').eq('key', key_value).execute()
        rows = getattr(res, 'data', None) or res
        if not rows:
            return jsonify({'valid': False}), 404
        # support row being list or dict
        row = rows[0] if isinstance(rows, list) else rows

        # check expiry
        if row.get('expires_at'):
            try:
                expires = datetime.fromisoformat(row['expires_at'])
                if datetime.utcnow() >= expires:
                    # expired: remove and return invalid
                    sb.table('license_keys').delete().eq('id', row.get('id')).execute()
                    return jsonify({'valid': False, 'reason': 'expired'}), 401
            except Exception:
                pass

        # mark used
        try:
            sb.table('license_keys').update({'is_used': True, 'used': True}).eq('id', row.get('id')).execute()
        except Exception:
            pass

        # normalize key field
        if 'key' in row and 'key_value' not in row:
            row['key_value'] = row.get('key')
        return jsonify({'valid': True, 'username': row.get('username'), 'product': row.get('product'), 'key_value': row.get('key_value')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Note: Admin "Edit Home" page removed per user request.
# The previous `/home` GET and POST handlers were intentionally removed
# so the admin cannot edit the public Home page from the dashboard anymore.
# If you later want to restore this functionality, re-add the handlers and
# the `admin_home.html` template, or implement a different content workflow.

# âœ… ØµÙØ­Ø© About
# Admin About page removed per user request

# ✅ صفحة Tools
@bp.route("/tools")
def tools():
    if not session.get("is_admin"):
        return redirect(url_for("dashboard.admin_login"))

    sb = get_supabase()
    tools = []

    try:
        # Include optional image fields so cards show thumbnails/backgrounds
        res = sb.table('downloads') \
            .select('id,title,link,version,notes,visible,bg_image,thumb_image') \
            .order('id') \
            .execute()

        # احصل على البيانات بشكل آمن
        tools = getattr(res, 'data', None) or res

        # تأكد إن الناتج قائمة من القواميس فقط
        if isinstance(tools, dict) and 'data' in tools:
            tools = tools['data']
        elif isinstance(tools, tuple):
            # حول tuple لقائمة من dicts (بشكل آمن)
            tools = [dict(id=i, value=v) if isinstance(v, (list, tuple)) else {"value": v} for i, v in enumerate(tools)]
        elif not isinstance(tools, list):
            tools = []

    except Exception:
        # fallback to local JSON file
        try:
            import json, os
            p = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'downloads.json')
            p = os.path.normpath(p)
            if os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as f:
                    tools = json.load(f) or []
            else:
                tools = []
        except Exception:
            tools = []

    return render_template("admin_tools.html", tools=tools or [], hide_nav=True)



@bp.route('/tools/add', methods=['GET', 'POST'])
def add_tool():
    if not session.get('is_admin'):
        return redirect(url_for('dashboard.admin_login'))

    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        notes = (request.form.get('notes') or '').strip()
        link = (request.form.get('link') or '').strip()
        version = (request.form.get('version') or '').strip()
        bg_image = (request.form.get('bg_image') or '').strip()
        thumb_image = (request.form.get('thumb_image') or '').strip()
        visible = True if request.form.get('visible') in ('1', 'on', 'true', 'True') else False

        # map admin fields -> public downloads table fields
        payload = {
            'title': title,
            'notes': notes,
            'link': link,
            'version': version,
            'visible': visible,
            'bg_image': bg_image or None,
            'thumb_image': thumb_image or None,
        }

        sb = get_supabase()
        try:
            sb.table('downloads').insert(payload).execute()
            flash('✅ Tool added', 'success')
            return redirect(url_for('dashboard.tools'))
        except Exception as e:
            # fallback: save to local JSON
            try:
                import json, os
                p = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'downloads.json')
                p = os.path.normpath(p)
                data = []
                if os.path.exists(p):
                    with open(p, 'r', encoding='utf-8') as f:
                        try:
                            data = json.load(f) or []
                        except Exception:
                            data = []
                # assign an id
                next_id = (max([t.get('id', 0) for t in data]) + 1) if data else 1
                # map payload to local format (title/link/version/notes/visible)
                local = {
                    'id': next_id,
                    'title': payload.get('title'),
                    'link': payload.get('link'),
                    'version': payload.get('version',''),
                    'notes': payload.get('notes',''),
                    'visible': payload.get('visible', True),
                    'bg_image': payload.get('bg_image') or '',
                    'thumb_image': payload.get('thumb_image') or '',
                }
                data.append(local)
                with open(p, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                flash(f"Saved locally (Supabase error): {e}", 'warning')
                return redirect(url_for('dashboard.tools'))
            except Exception as e2:
                flash(f'Error saving tool: {e} / fallback failed: {e2}', 'error')

    return render_template('admin_add_tool.html', hide_nav=True)


@bp.route('/tools/<int:tool_id>/edit', methods=['GET', 'POST'])
def edit_tool(tool_id):
    if not session.get('is_admin'):
        return redirect(url_for('dashboard.admin_login'))

    sb = get_supabase()
    tool = None
    try:
        res = sb.table('downloads').select('id,title,link,version,notes,visible,bg_image,thumb_image').eq('id', tool_id).single().execute()
        data = getattr(res, 'data', None) or res
        if isinstance(data, list) and len(data) > 0:
            tool = data[0]
        else:
            tool = data
    except Exception:
        # fallback to local JSON
        try:
            import json, os
            p = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'downloads.json')
            p = os.path.normpath(p)
            if os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f) or []
                    for t in data:
                        if int(t.get('id', 0)) == int(tool_id):
                            tool = t
                            break
        except Exception:
            tool = None

    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        notes = (request.form.get('notes') or '').strip()
        link = (request.form.get('link') or '').strip()
        version = (request.form.get('version') or '').strip()
        bg_image = (request.form.get('bg_image') or '').strip()
        thumb_image = (request.form.get('thumb_image') or '').strip()
        visible = True if request.form.get('visible') in ('1', 'on', 'true', 'True') else False

        # map fields to downloads table
        payload = {
            'title': title,
            'notes': notes,
            'link': link,
            'version': version,
            'visible': visible,
            'bg_image': bg_image or None,
            'thumb_image': thumb_image or None,
        }

        try:
            sb.table('downloads').update(payload).eq('id', tool_id).execute()
            flash('✅ Tool updated', 'success')
            return redirect(url_for('dashboard.tools'))
        except Exception as e:
            # fallback local update
            try:
                import json, os
                p = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'downloads.json')
                p = os.path.normpath(p)
                data = []
                if os.path.exists(p):
                    with open(p, 'r', encoding='utf-8') as f:
                        try:
                            data = json.load(f) or []
                        except Exception:
                            data = []
                updated = False
                for i, t in enumerate(data):
                    if int(t.get('id', 0)) == int(tool_id):
                        # keep id, update other fields
                        data[i] = {
                            'id': tool_id,
                            'title': payload.get('title'),
                            'link': payload.get('link'),
                            'version': payload.get('version',''),
                            'notes': payload.get('notes',''),
                            'visible': payload.get('visible', True),
                            'bg_image': payload.get('bg_image') or '',
                            'thumb_image': payload.get('thumb_image') or '',
                        }
                        updated = True
                        break
                if updated:
                    with open(p, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    flash(f"Saved locally (Supabase error): {e}", 'warning')
                    return redirect(url_for('dashboard.tools'))
            except Exception as e2:
                flash(f'Error updating tool: {e} / fallback failed: {e2}', 'error')

    return render_template('admin_edit_tool.html', tool=tool or {}, hide_nav=True)


@bp.route('/tools/<int:tool_id>/delete', methods=['POST'])
def delete_tool(tool_id):
    if not session.get('is_admin'):
        return redirect(url_for('dashboard.admin_login'))

    sb = get_supabase()
    try:
        sb.table('downloads').delete().eq('id', tool_id).execute()
        flash('✅ Tool deleted', 'info')
        return redirect(url_for('dashboard.tools'))
    except Exception as e:
        # fallback local delete
        try:
            import json, os
            p = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'downloads.json')
            p = os.path.normpath(p)
            data = []
            if os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f) or []
                    except Exception:
                        data = []
            data = [t for t in data if int(t.get('id', 0)) != int(tool_id)]
            with open(p, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            flash(f"Deleted locally (Supabase error): {e}", 'warning')
            return redirect(url_for('dashboard.tools'))
        except Exception as e2:
            flash(f'Error deleting tool: {e} / fallback failed: {e2}', 'error')
            return redirect(url_for('dashboard.tools'))

# âœ… ØµÙØ­Ø© Shop
@bp.route("/shop")
def shop():
    if not session.get("is_admin"):
        return redirect(url_for("dashboard.admin_login"))
    # Load a small preview list of products for inline management UI
    products = []
    try:
        sb = get_supabase()
        res = sb.table('products').select('*').order('id').execute()
        data = getattr(res, 'data', None)
        if data is None and isinstance(res, dict):
            data = res.get('data')
        products = data if isinstance(data, list) else (list(data) if data else [])
    except Exception:
        try:
            import os, json
            p = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'products.json')
            p = os.path.normpath(p)
            if os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as f:
                    products = json.load(f) or []
        except Exception:
            products = []
    # Render the card-based admin shop
    return render_template("admin_shop.html", products=products or [], hide_nav=True)


# -----------------------------
# Products management (Admin)
# -----------------------------

@bp.route('/products')
def products():
    # Deprecate old list page and use the unified admin shop UI
    if not session.get('is_admin'):
        return redirect(url_for('dashboard.admin_login'))
    return redirect(url_for('dashboard.shop'))


@bp.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if not session.get('is_admin'):
        return redirect(url_for('dashboard.admin_login'))

    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        price = _parse_price(request.form.get('price'))
        thumb = (request.form.get('thumb') or '').strip()
        short_desc = (request.form.get('short_desc') or '').strip()
        long_desc = (request.form.get('long_desc') or '').strip()
        # New: separate images/videos fields; still accept legacy 'gallery'
        images_text = (request.form.get('images') or '').strip()
        videos_text = (request.form.get('videos') or '').strip()
        legacy_gallery = (request.form.get('gallery') or '').strip()

        media = []
        for line in images_text.splitlines():
            u = (line or '').strip()
            if u:
                media.append({'type': 'image', 'url': u})
        for line in videos_text.splitlines():
            u = (line or '').strip()
            if u:
                media.append({'type': 'video', 'url': u})
        if not media and legacy_gallery:
            for line in legacy_gallery.splitlines():
                u = line.strip()
                if not u:
                    continue
                typ = 'video' if any(ext in u.lower() for ext in ['.mp4', 'youtube.com', 'youtu.be']) else 'image'
                media.append({'type': typ, 'url': u})

        payload = {
            'name': name,
            'price': price,
            'thumb': thumb,
            'short_desc': short_desc,
            'long_desc': long_desc,
        }
        # Only add media if present (بعض المخططات لا تحتوي العمود media)
        if media:
            payload['media'] = media

        def _try_insert(sb, pay):
            """Insert with/without media; return (ok, created_rows).
            created_rows is a list of dicts if available.
            """
            attempts = []
            base = {k: v for k, v in pay.items() if k != 'media'}
            attempts.append(base)
            if 'media' in pay:
                attempts.append(pay)
            for p in attempts:
                try:
                    res = sb.table('products').insert(p).execute()
                    err = getattr(res, 'error', None)
                    if err:
                        raise Exception(err)
                    data = getattr(res, 'data', None)
                    if isinstance(data, list):
                        return True, data
                    elif isinstance(data, dict):
                        return True, [data]
                    else:
                        return True, []
                except Exception:
                    continue
            return False, []

        try:
            sb = get_supabase()
            ok, created = _try_insert(sb, payload)
            if ok:
                # If DB schema lacks media, persist media locally mapped to product id
                try:
                    new_id = None
                    if created and isinstance(created, list) and isinstance(created[0], dict):
                        new_id = created[0].get('id')
                    if new_id and media:
                        import os, json
                        mp = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'product_media.json')
                        mp = os.path.normpath(mp)
                        os.makedirs(os.path.dirname(mp), exist_ok=True)
                        current = []
                        if os.path.exists(mp):
                            with open(mp, 'r', encoding='utf-8') as f:
                                try:
                                    current = json.load(f) or []
                                except Exception:
                                    current = []
                        # replace or append
                        replaced = False
                        for r in current:
                            if int(r.get('id', 0)) == int(new_id):
                                r['media'] = media
                                replaced = True
                                break
                        if not replaced:
                            current.append({'id': int(new_id), 'media': media})
                        with open(mp, 'w', encoding='utf-8') as f:
                            json.dump(current, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
                flash('Product added', 'success')
                return redirect(url_for('dashboard.shop'))
            else:
                raise Exception('insert_failed')
        except Exception as e:
            # fallback local save
            try:
                import os, json
                p = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'products.json')
                p = os.path.normpath(p)
                os.makedirs(os.path.dirname(p), exist_ok=True)
                data = []
                if os.path.exists(p):
                    with open(p, 'r', encoding='utf-8') as f:
                        try:
                            data = json.load(f) or []
                        except Exception:
                            data = []
                new_id = (max([int(v.get('id', 0)) for v in data]) + 1) if data else 1
                payload_local = {
                    'id': new_id,
                    'name': name,
                    'price': price,
                    'thumb': thumb,
                    'short_desc': short_desc,
                    'long_desc': long_desc,
                    'media': media,
                }
                data.append(payload_local)
                with open(p, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                # رسالة أنيقة مختصرة بدون تفاصيل تقنية طويلة
                flash("Saved locally (DB connection failed)", 'warning')
                return redirect(url_for('dashboard.shop'))
            except Exception as e2:
                flash(f'Error saving product: {e} / fallback failed: {e2}', 'error')

    return render_template('admin_add_product.html', hide_nav=True)


@bp.route('/products/<int:pid>/edit', methods=['GET', 'POST'])
def edit_product(pid):
    if not session.get('is_admin'):
        return redirect(url_for('dashboard.admin_login'))

    sb = None
    try:
        sb = get_supabase()
    except Exception:
        sb = None

    product = None
    if sb is not None:
        try:
            res = sb.table('products').select('*').eq('id', pid).limit(1).execute()
            data = getattr(res, 'data', None) or []
            product = data[0] if data else None
        except Exception:
            product = None
    if product is None:
        # try local file
        try:
            import os, json
            p = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'products.json')
            p = os.path.normpath(p)
            if os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as f:
                    arr = json.load(f) or []
                for r in arr:
                    if int(r.get('id', 0)) == int(pid):
                        product = r
                        break
        except Exception:
            product = None

    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        price = _parse_price(request.form.get('price'))
        thumb = (request.form.get('thumb') or '').strip()
        short_desc = (request.form.get('short_desc') or '').strip()
        long_desc = (request.form.get('long_desc') or '').strip()
        images_text = (request.form.get('images') or '').strip()
        videos_text = (request.form.get('videos') or '').strip()
        legacy_gallery = (request.form.get('gallery') or '').strip()
        media = []
        for line in images_text.splitlines():
            u = (line or '').strip()
            if u:
                media.append({'type': 'image', 'url': u})
        for line in videos_text.splitlines():
            u = (line or '').strip()
            if u:
                media.append({'type': 'video', 'url': u})
        if not media and legacy_gallery:
            for line in legacy_gallery.splitlines():
                u = line.strip()
                if not u:
                    continue
                typ = 'video' if any(ext in u.lower() for ext in ['.mp4', 'youtube.com', 'youtu.be']) else 'image'
                media.append({'type': typ, 'url': u})
        update = {
            'name': name,
            'price': price,
            'thumb': thumb,
            'short_desc': short_desc,
            'long_desc': long_desc,
            'media': media,
        }
        try:
            if sb is not None:
                sb.table('products').update(update).eq('id', pid).execute()
                # persist media locally if needed
                try:
                    if update.get('media'):
                        import os, json
                        mp = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'product_media.json')
                        mp = os.path.normpath(mp)
                        os.makedirs(os.path.dirname(mp), exist_ok=True)
                        current = []
                        if os.path.exists(mp):
                            with open(mp, 'r', encoding='utf-8') as f:
                                try:
                                    current = json.load(f) or []
                                except Exception:
                                    current = []
                        found = False
                        for r in current:
                            if int(r.get('id', 0)) == int(pid):
                                r['media'] = update['media']
                                found = True
                                break
                        if not found:
                            current.append({'id': int(pid), 'media': update['media']})
                        with open(mp, 'w', encoding='utf-8') as f:
                            json.dump(current, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
                flash('Product updated', 'success')
                return redirect(url_for('dashboard.products'))
        except Exception as e:
            pass
        # local fallback edit
        try:
            import os, json
            p = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'products.json')
            p = os.path.normpath(p)
            data = []
            if os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f) or []
            changed = False
            for i, r in enumerate(data):
                if int(r.get('id', 0)) == int(pid):
                    r.update(update)
                    data[i] = r
                    changed = True
                    break
            if changed:
                with open(p, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                flash('Updated locally', 'warning')
                return redirect(url_for('dashboard.products'))
            else:
                flash('Product not found in local storage', 'error')
        except Exception as e2:
            flash(f'Error updating product: {e2}', 'error')

    # normalize media into two textarea lists
    images_text = ''
    videos_text = ''
    if product and isinstance(product, dict):
        m = product.get('media')
        if isinstance(m, list):
            images_text = "\n".join([str(x.get('url','')) for x in m if isinstance(x, dict) and x.get('type')=='image'])
            videos_text = "\n".join([str(x.get('url','')) for x in m if isinstance(x, dict) and x.get('type')=='video'])
        else:
            try:
                import json
                arr = json.loads(m) if m else []
                images_text = "\n".join([str(x.get('url','')) for x in arr if isinstance(x, dict) and x.get('type')=='image'])
                videos_text = "\n".join([str(x.get('url','')) for x in arr if isinstance(x, dict) and x.get('type')=='video'])
            except Exception:
                images_text = ''
                videos_text = ''

    return render_template('admin_edit_product.html', product=product or {}, images_text=images_text, videos_text=videos_text, hide_nav=True)


@bp.route('/products/<int:pid>/delete', methods=['POST'])
def delete_product(pid):
    if not session.get('is_admin'):
        return redirect(url_for('dashboard.admin_login'))

    # Try Supabase first, then local
    try:
        sb = get_supabase()
        sb.table('products').delete().eq('id', pid).execute()
        flash('Product deleted', 'info')
        return redirect(url_for('dashboard.products'))
    except Exception:
        pass
    try:
        import os, json
        p = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'products.json')
        p = os.path.normpath(p)
        data = []
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                data = json.load(f) or []
        data = [r for r in data if int(r.get('id', 0)) != int(pid)]
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # remove media mapping if any
        try:
            mp = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'product_media.json')
            mp = os.path.normpath(mp)
            if os.path.exists(mp):
                with open(mp, 'r', encoding='utf-8') as f:
                    cur = json.load(f) or []
                cur = [r for r in cur if int(r.get('id', 0)) != int(pid)]
                with open(mp, 'w', encoding='utf-8') as f:
                    json.dump(cur, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        flash('Deleted locally', 'warning')
    except Exception as e:
        flash(f'Error deleting product: {e}', 'error')
    return redirect(url_for('dashboard.products'))


# ØµÙØ­Ø© ØªØ³Ø¬ÙŠÙ„ Ø§Ù„Ø¯Ø®ÙˆÙ„ Ù„Ù„Ø£Ø¯Ù…Ù† (Ø¥Ø¹Ø§Ø¯Ø© Ø¥Ø¶Ø§ÙØªÙ‡Ø§ Ù„Ø£Ù† Ø§Ù„Ù…Ø³Ø§Ø± ÙƒØ§Ù† Ù…ÙÙ‚ÙˆØ¯)
@bp.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        entered_key = (request.form.get("password") or "").strip()
        sb = get_supabase()
        result = sb.table("license_keys").select("*").eq("key", entered_key).execute()

        if result and getattr(result, 'data', None) and len(result.data) > 0:
            session["is_admin"] = True
            flash("✅ Logged in successfully", "success")
            return redirect(url_for("dashboard.welcome"))
        else:
            flash("Invalid or non-existent key.", "error")

    return render_template("admin_login.html", hide_nav=True)


# Logout route for admin
@bp.route('/logout')
def logout():
    # Remove admin flag from session
    session.pop('is_admin', None)
    flash('✅ Logged out', 'info')
    return redirect(url_for('dashboard.admin_login'))
 


# --- helpers ---
def _parse_price(val):
    """Convert user input to float safely. Accepts numbers with comma/space.
    Returns 0.0 on failure to avoid crashing the view.
    """
    try:
        if val is None:
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        s = str(val)
        # keep digits, dot and comma; normalize comma to dot; remove currency text
        import re
        s = re.sub(r"[^0-9,\.]", "", s)
        s = s.replace(",", ".")
        if s.strip() == "":
            return 0.0
        return float(s)
    except Exception:
        return 0.0





