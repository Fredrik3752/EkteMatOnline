"""Checkout (C3): turn the cart into an order with guest groups. No payment."""
from datetime import date

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from app.controllers.auth import login_required
from app.controllers.cart import clear_cart, load_cart
from app.models.errors import ValidationError
from app.models.order import GuestGroup, Order
from app.models.repositories.order_repository import OrderRepository

bp = Blueprint("checkout", __name__, url_prefix="/bestilling")

EMPTY_GROUP_ROWS = 3


def _parse_int(text):
    text = (text or "").strip()
    return int(text) if text.isdigit() else None


def _guest_groups_from_form(form):
    """Read the repeated guest-group rows. Completely empty rows are ignored."""
    groups, errors = [], {}
    rows = zip(form.getlist("group_description"), form.getlist("group_count"),
               form.getlist("group_allergies"), form.getlist("group_diets"))
    for description, count, allergies, diets in rows:
        if not any(v.strip() for v in (description, count, allergies, diets)):
            continue
        guest_count = _parse_int(count)
        if guest_count is None or guest_count < 1:
            errors["guest_groups"] = "Hver gjestegruppe må ha antall gjester (minst 1)."
            guest_count = 0
        groups.append(GuestGroup(description=description.strip(), guest_count=guest_count,
                                 allergy_notes=allergies.strip(), dietary_notes=diets.strip()))
    if not groups:
        errors["guest_groups"] = "Legg inn minst én gjestegruppe – også om ingen har allergier."
    return groups, errors


def _order_from_form(form, cart):
    errors = {}
    try:
        event_date = date.fromisoformat(form.get("event_date", "").strip())
    except ValueError:
        event_date = None
        errors["event_date"] = "Oppgi en gyldig dato."
    guest_count = _parse_int(form.get("guest_count"))
    groups, group_errors = _guest_groups_from_form(form)

    order = Order(
        customer_id=g.user.id,
        event_date=event_date,
        guest_count=guest_count if guest_count is not None else 0,
        delivery_address=form.get("delivery_address", "").strip(),
        notes=form.get("notes", "").strip(),
        lines=cart.to_order_lines(),
        guest_groups=[grp for grp in groups if grp.guest_count >= 1],
    )
    try:
        order.validate(today=date.today())
    except ValidationError as exc:
        errors = {**exc.errors, **errors}
    errors.update(group_errors)
    return order, errors


@bp.route("", methods=["GET", "POST"])
@login_required
def checkout():
    cart = load_cart()
    if cart.is_empty:
        flash("Handlekurven er tom. Legg til retter før du bestiller.", "info")
        return redirect(url_for("cart.view"))
    if cart.problems():
        flash("Rett opp antallene i handlekurven før du bestiller.", "error")
        return redirect(url_for("cart.view"))

    errors = {}
    if request.method == "POST":
        order, errors = _order_from_form(request.form, cart)
        if not errors:
            saved = OrderRepository().add(order)
            clear_cart()
            flash("Takk! Bestillingen er sendt inn.", "success")
            return redirect(url_for("checkout.receipt", order_id=saved.id))

    form = request.form
    group_rows = list(zip(form.getlist("group_description"), form.getlist("group_count"),
                          form.getlist("group_allergies"), form.getlist("group_diets")))
    if not group_rows:
        group_rows = [("Alle gjester", "", "", "")] + [("", "", "", "")] * (EMPTY_GROUP_ROWS - 1)
    return render_template(
        "checkout/checkout.html", cart=cart, form=form, errors=errors, group_rows=group_rows,
        min_date=date.fromordinal(date.today().toordinal() + 1).isoformat(),
    ), (400 if errors else 200)


@bp.route("/<int:order_id>/kvittering")
@login_required
def receipt(order_id):
    order = OrderRepository().get(order_id)
    if order is None or order.customer_id != g.user.id:
        abort(404)  # don't reveal that other customers' orders exist
    return render_template("checkout/receipt.html", order=order)
