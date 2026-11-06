"""Customer accounts: register, log in, log out, my orders (C4) and questions (C5)."""
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from app.controllers.auth import is_safe_next, log_in, log_out, login_required
from app.models.errors import InvalidStatusTransition, ValidationError
from app.models.order import OrderStatus
from app.models.question import MAX_QUESTION_LENGTH, Question
from app.models.repositories.order_repository import OrderRepository
from app.models.repositories.question_repository import QuestionRepository
from app.models.repositories.user_repository import UserRepository
from app.models.user import User

bp = Blueprint("account", __name__)


def _redirect_after_login(user):
    target = request.values.get("next", "")
    if is_safe_next(target):
        return redirect(target)
    return redirect(url_for("admin.index") if user.is_admin else url_for("shop.index"))


@bp.route("/registrer", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(url_for("shop.index"))
    form, errors = {}, {}
    if request.method == "POST":
        form = {k: request.form.get(k, "") for k in ("name", "email", "phone")}
        password = request.form.get("password", "")
        if password != request.form.get("password_confirm", ""):
            errors["password_confirm"] = "Passordene er ikke like."
        try:
            user = User.create(form["email"], form["name"], password, phone=form["phone"])
        except ValidationError as exc:
            errors = {**exc.errors, **errors}
        if not errors:
            try:
                user = UserRepository().add(user)
            except ValidationError as exc:
                errors = exc.errors
        if not errors:
            log_in(user)
            flash(f"Velkommen, {user.name}! Kontoen din er opprettet.", "success")
            return _redirect_after_login(user)
    return render_template("account/register.html", form=form, errors=errors,
                           next=request.values.get("next", "")), (400 if errors else 200)


@bp.route("/logg-inn", methods=["GET", "POST"])
def login():
    if g.user:
        return _redirect_after_login(g.user)
    email, error = "", None
    if request.method == "POST":
        email = request.form.get("email", "")
        user = UserRepository().get_by_email(email)
        if user and user.check_password(request.form.get("password", "")):
            log_in(user)
            flash(f"Du er logget inn som {user.name}.", "success")
            return _redirect_after_login(user)
        error = "Feil e-post eller passord."
    return render_template("account/login.html", email=email, error=error,
                           next=request.values.get("next", "")), (401 if error else 200)


@bp.route("/logg-ut", methods=["POST"])
def logout():
    log_out()
    flash("Du er logget ut.", "info")
    return redirect(url_for("shop.index"))


# -- C4: my orders ------------------------------------------------------------------

def _own_order_or_404(order_id):
    order = OrderRepository().get(order_id)
    if order is None or order.customer_id != g.user.id:
        abort(404)  # don't reveal that other customers' orders exist
    return order


@bp.route("/mine-ordrer")
@login_required
def my_orders():
    return render_template("account/my_orders.html", orders=OrderRepository().list_for_customer(g.user.id))


def _render_my_order(order, question_body="", question_error=None):
    return render_template(
        "account/my_order.html", order=order,
        questions=QuestionRepository().list_for_order(order.id),
        question_body=question_body, question_error=question_error,
        max_question_length=MAX_QUESTION_LENGTH,
    ), (400 if question_error else 200)


@bp.route("/mine-ordrer/<int:order_id>")
@login_required
def my_order(order_id):
    return _render_my_order(_own_order_or_404(order_id))


@bp.route("/mine-ordrer/<int:order_id>/sporsmal", methods=["POST"])
@login_required
def ask_question(order_id):
    """C5: ask Ekte Mat a question about one of your own orders."""
    order = _own_order_or_404(order_id)
    body = request.form.get("body", "")
    try:
        QuestionRepository().add(Question(order_id=order.id, author_id=g.user.id, body=body))
    except ValidationError as exc:
        return _render_my_order(order, question_body=body, question_error=exc.errors["body"])
    flash("Spørsmålet er sendt. Du får svar her på ordresiden.", "success")
    return redirect(url_for("account.my_order", order_id=order.id) + "#sporsmal")


@bp.route("/mine-ordrer/<int:order_id>/avbestill", methods=["POST"])
@login_required
def cancel_order(order_id):
    order = _own_order_or_404(order_id)
    if not order.can_be_cancelled_by_customer:
        flash("Ordren er allerede behandlet og kan ikke avbestilles her. Send oss et spørsmål om ordren.", "error")
    else:
        try:
            order.change_status(OrderStatus.CANCELLED)
        except InvalidStatusTransition as exc:
            flash(str(exc), "error")
        else:
            OrderRepository().save_status(order)
            flash(f"Ordre nr. {order.id} er avbestilt.", "success")
    return redirect(url_for("account.my_order", order_id=order.id))
