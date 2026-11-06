"""Minimal CSRF protection: one random token per session, checked on every POST."""
import secrets

from flask import abort, request, session

SESSION_KEY = "csrf_token"
FIELD_NAME = "csrf_token"


def csrf_token():
    if SESSION_KEY not in session:
        session[SESSION_KEY] = secrets.token_urlsafe(32)
    return session[SESSION_KEY]


def check_csrf():
    """before_app_request: reject state-changing requests without a valid token."""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    sent = request.form.get(FIELD_NAME) or request.headers.get("X-CSRF-Token", "")
    expected = session.get(SESSION_KEY, "")
    if not expected or not secrets.compare_digest(sent, expected):
        abort(400, description="Skjemaet er utløpt eller ugyldig. Last inn siden og prøv igjen.")
