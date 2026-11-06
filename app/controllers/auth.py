"""Login state and access control shared by all blueprints."""
from functools import wraps
from urllib.parse import urlparse

from flask import abort, flash, g, redirect, request, session, url_for

from app.models.repositories.user_repository import UserRepository


def load_logged_in_user():
    """before_app_request: put the logged-in User (or None) on g.user."""
    user_id = session.get("user_id")
    g.user = UserRepository().get(user_id) if user_id else None
    if user_id and g.user is None:  # user was deleted
        session.clear()


def log_in(user):
    session.clear()  # prevents session fixation
    session["user_id"] = user.id
    g.user = user


def log_out():
    session.clear()
    g.user = None


def is_safe_next(target):
    """Only allow relative paths like '/kurv' – never another host."""
    if not target or not target.startswith("/") or target.startswith("//") or "\\" in target:
        return False
    parsed = urlparse(target)
    return not parsed.scheme and not parsed.netloc


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.get("user") is None:
            flash("Du må logge inn først.", "info")
            return redirect(url_for("account.login", next=request.full_path.rstrip("?")))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not g.user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapped
