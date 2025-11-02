from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from ..services.supabase_client import get_supabase

bp = Blueprint("shop", __name__)


@bp.get("/")
def shop_index():
    # Tolerate missing Supabase config by showing an empty list
    products = []
    try:
        sb = get_supabase()
        products = (
            sb.table("products")
            .select("id,name,price,thumb,short_desc")
            .execute()
            .data
        )
    except Exception:
        products = []
    return render_template("shop.html", products=products)


@bp.get("/<int:pid>")
def product_page(pid: int):
    try:
        sb = get_supabase()
        rows = (
            sb.table("products").select("*").eq("id", pid).limit(1).execute().data
        )
        product = rows[0] if rows else None
    except Exception:
        product = None

    # Parse optional media JSON for gallery; fallback to local mapping if missing
    media = []
    if product and isinstance(product, dict):
        m = product.get("media")
        if isinstance(m, list):
            media = m
        else:
            try:
                import json

                media = json.loads(m) if m else []
            except Exception:
                media = []

    # Local fallback: data/product_media.json
    if not media:
        try:
            import os, json

            mp = os.path.join(
                os.path.dirname(__file__), "..", "..", "data", "product_media.json"
            )
            mp = os.path.normpath(mp)
            if os.path.exists(mp):
                with open(mp, "r", encoding="utf-8") as f:
                    arr = json.load(f) or []
                for r in arr:
                    if int(r.get("id", 0)) == int(pid):
                        media = r.get("media") or []
                        break
        except Exception:
            media = media or []

    return render_template("product.html", product=product, media=media)


@bp.route("/verify", methods=["GET", "POST"])
def verify_key():
    if request.method == "POST":
        license_key = (request.form.get("license_key") or "").strip()

        if not license_key:
            flash("Please enter the key.", "error")
            return redirect(url_for("shop.verify_key"))

        sb = get_supabase()

        result = sb.table("license_keys").select("*").eq("key", license_key).execute()

        if not getattr(result, "data", None):
            flash("Invalid or non-existent key.", "error")
            return redirect(url_for("shop.verify_key"))

        key_data = result.data[0]

        if key_data.get("is_used"):
            flash("This key has already been used.", "error")
            return redirect(url_for("shop.verify_key"))

        sb.table("license_keys").update({"is_used": True}).eq("key", license_key).execute()

        session["is_admin"] = True
        flash("Key verified successfully ✅", "success")
        return redirect(url_for("dashboard.welcome"))

    return render_template("verify_key.html", hide_nav=True)


# -------------------------
# Simple session cart
# -------------------------


def _get_cart():
    cart = session.get("cart")
    if not isinstance(cart, list):
        cart = []
    return cart


def _save_cart(cart):
    session["cart"] = cart
    session.modified = True


@bp.route("/add/<int:pid>", methods=["POST", "GET"])
def add_to_cart(pid: int):
    # Fetch minimal product data
    product = None
    try:
        sb = get_supabase()
        res = (
            sb.table("products")
            .select("id,name,price,thumb")
            .eq("id", pid)
            .limit(1)
            .execute()
        )
        data = getattr(res, "data", None) or []
        product = data[0] if data else None
    except Exception:
        product = None

    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("shop.shop_index"))

    cart = _get_cart()
    found = False
    for item in cart:
        if int(item.get("id", 0)) == int(pid):
            item["qty"] = int(item.get("qty", 1)) + 1
            found = True
            break
    if not found:
        cart.append(
            {
                "id": product.get("id"),
                "name": product.get("name"),
                "price": product.get("price", 0),
                "thumb": product.get("thumb"),
                "qty": 1,
            }
        )
    _save_cart(cart)
    flash("Item added to cart.", "success")
    next_url = request.args.get("next")
    return redirect(next_url or url_for("shop.view_cart"))


@bp.get("/cart")
def view_cart():
    cart = _get_cart()
    total = 0.0
    for i in cart:
        try:
            total += float(i.get("price", 0)) * int(i.get("qty", 1))
        except Exception:
            pass
    return render_template("cart_v2.html", cart=cart, total=total)


@bp.post("/remove/<int:pid>")
def remove_from_cart(pid: int):
    cart = [i for i in _get_cart() if int(i.get("id", 0)) != int(pid)]
    _save_cart(cart)
    flash("Item removed from cart.", "info")
    return redirect(url_for("shop.view_cart"))


@bp.post("/update")
def update_cart():
    cart = _get_cart()
    for item in cart:
        pid = int(item.get("id", 0))
        new_qty = request.form.get(f"qty_{pid}")
        try:
            new_qty = max(1, int(new_qty))
            item["qty"] = new_qty
        except Exception:
            pass
    _save_cart(cart)
    flash("Cart updated.", "success")
    return redirect(url_for("shop.view_cart"))

