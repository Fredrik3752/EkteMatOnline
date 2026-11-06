"""Customer accounts: register, log in, log out."""
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from app.controllers.auth import is_safe_next, log_in, log_out
from app.models.errors import ValidationError
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
