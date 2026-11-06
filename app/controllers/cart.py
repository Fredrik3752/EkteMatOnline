"""Shopping cart (C2). Quantities live in the Flask session as {"<item_id>": qty}."""
from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from app.controllers.auth import is_safe_next
from app.models.cart import Cart, check_quantity
from app.models.errors import ValidationError
from app.models.repositories.food_item_repository import FoodItemRepository

bp = Blueprint("cart", __name__, url_prefix="/handlekurv")

SESSION_KEY = "cart"


# -- session helpers (also used by checkout and login) ------------------------------

def get_quantities():
    return dict(session.get(SESSION_KEY, {}))


def save_quantities(quantities):
    session[SESSION_KEY] = {str(k): int(v) for k, v in quantities.items()}


def clear_cart():
    session.pop(SESSION_KEY, None)


def load_cart(notify=True) -> Cart:
    """Build the Cart from the session and drop items that are no longer for sale."""
    quantities = get_quantities()
    cart = Cart.build(quantities, FoodItemRepository().get_many(quantities.keys()))
    if cart.removed:
        save_quantities(cart.to_quantities())
        if notify:
            flash("Noen retter er ikke lenger tilgjengelige og er fjernet fra handlekurven: "
                  + ", ".join(cart.removed) + ".", "info")
    return cart


def cart_count():
    return len(session.get(SESSION_KEY, {}))


# -- routes -------------------------------------------------------------------------

def _published_item_or_404():
    item_id = request.form.get("item_id", "")
    item = FoodItemRepository().get(int(item_id)) if item_id.isdigit() else None
    if item is None or not item.is_published:
        abort(404)
    return item


def _back(default="cart.view"):
    target = request.form.get("next", "")
    return redirect(target if is_safe_next(target) else url_for(default))


@bp.route("")
def view():
    return render_template("cart/cart.html", cart=load_cart())


@bp.route("/legg-til", methods=["POST"])
def add():
    item = _published_item_or_404()
    quantities = get_quantities()
    current = quantities.get(str(item.id), 0)
    try:
        added = int(request.form.get("quantity", ""))
        if added < 1:
            raise ValueError
        quantities[str(item.id)] = check_quantity(item, current + added)
    except ValueError:
        flash("Oppgi antall som et helt tall større enn 0.", "error")
        return _back()
    except ValidationError as exc:
        flash(exc.errors["quantity"], "error")
        return _back()
    save_quantities(quantities)
    flash(f"{added} × «{item.name}» er lagt i handlekurven.", "success")
    return _back()


@bp.route("/oppdater", methods=["POST"])
def update():
    item = _published_item_or_404()
    quantities = get_quantities()
    if str(item.id) not in quantities:
        abort(404)
    try:
        quantities[str(item.id)] = check_quantity(item, request.form.get("quantity", ""))
    except ValidationError as exc:
        flash(exc.errors["quantity"], "error")
        return redirect(url_for("cart.view"))
    save_quantities(quantities)
    flash(f"Antallet for «{item.name}» er oppdatert.", "success")
    return redirect(url_for("cart.view"))


@bp.route("/fjern", methods=["POST"])
def remove():
    item_id = request.form.get("item_id", "")
    quantities = get_quantities()
    if quantities.pop(item_id, None) is not None:
        save_quantities(quantities)
        flash("Retten er fjernet fra handlekurven.", "success")
    return redirect(url_for("cart.view"))
