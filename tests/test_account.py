import pytest

from app.controllers.auth import is_safe_next
from app.models.repositories.user_repository import UserRepository
from tests.conftest import PASSWORD, login, post


def logged_in_user_id(client):
    with client.session_transaction() as sess:
        return sess.get("user_id")


# -- registration ---------------------------------------------------------------

def register_data(**overrides):
    data = {"name": "Ny Kunde", "email": "ny@example.test", "phone": "",
            "password": PASSWORD, "password_confirm": PASSWORD}
    data.update(overrides)
    return data


def test_register_page_renders(client):
    response = client.get("/registrer")
    assert response.status_code == 200
    assert 'name="csrf_token"' in response.get_data(as_text=True)


def test_register_creates_user_and_logs_in(app, client):
    response = post(client, "/registrer", register_data())
    assert response.status_code == 302 and response.headers["Location"] == "/"
    with app.app_context():
        user = UserRepository().get_by_email("ny@example.test")
    assert user is not None and not user.is_admin
    assert user.password_hash != PASSWORD
    assert logged_in_user_id(client) == user.id


def test_register_duplicate_email(client, customer):
    response = post(client, "/registrer", register_data(email="kunde@example.test"))
    assert response.status_code == 400
    assert "finnes allerede" in response.get_data(as_text=True)


@pytest.mark.parametrize("overrides, message", [
    ({"name": ""}, "Navn må fylles ut"),
    ({"email": "ugyldig"}, "gyldig e-postadresse"),
    ({"password": "kort", "password_confirm": "kort"}, "minst 8 tegn"),
    ({"password_confirm": "noe-annet-123"}, "ikke like"),
])
def test_register_validation(client, overrides, message):
    response = post(client, "/registrer", register_data(**overrides))
    assert response.status_code == 400
    assert message in response.get_data(as_text=True)
    assert logged_in_user_id(client) is None


def test_register_keeps_entered_values_but_not_password(client):
    html = post(client, "/registrer", register_data(name="")).get_data(as_text=True)
    assert 'value="ny@example.test"' in html
    assert PASSWORD not in html


# -- login / logout ---------------------------------------------------------------

def test_login_success_customer(client, customer):
    response = login(client, "kunde@example.test")
    assert response.status_code == 302 and response.headers["Location"] == "/"
    assert logged_in_user_id(client) == customer.id
    assert "Test Kunde" in client.get("/").get_data(as_text=True)


def test_login_admin_goes_to_admin_panel(client, admin):
    response = login(client, "admin@example.test")
    assert response.headers["Location"] == "/admin/"


def test_login_is_case_insensitive_for_email(client, customer):
    login(client, "KUNDE@Example.test")
    assert logged_in_user_id(client) == customer.id


@pytest.mark.parametrize("email, password", [
    ("kunde@example.test", "feil-passord"),
    ("ukjent@example.test", PASSWORD),
])
def test_login_failure_uses_same_message(client, customer, email, password):
    response = post(client, "/logg-inn", {"email": email, "password": password})
    assert response.status_code == 401
    assert "Feil e-post eller passord" in response.get_data(as_text=True)
    assert logged_in_user_id(client) is None


def test_login_redirects_to_safe_next(client, customer):
    response = post(client, "/logg-inn", {"email": "kunde@example.test", "password": PASSWORD,
                                          "next": "/admin/"})
    assert response.headers["Location"] == "/admin/"


def test_login_ignores_external_next(client, customer):
    response = post(client, "/logg-inn", {"email": "kunde@example.test", "password": PASSWORD,
                                          "next": "https://evil.example/"})
    assert response.headers["Location"] == "/"


@pytest.mark.parametrize("target, ok", [
    ("/kurv", True), ("/admin/?status=submitted", True),
    ("", False), ("https://evil.example", False), ("//evil.example", False),
    ("/\\evil.example", False), ("javascript:alert(1)", False),
])
def test_is_safe_next(target, ok):
    assert is_safe_next(target) is ok


def test_logout(client, customer):
    login(client, "kunde@example.test")
    response = post(client, "/logg-ut")
    assert response.status_code == 302
    assert logged_in_user_id(client) is None
    assert "Logg inn" in client.get("/").get_data(as_text=True)


def test_logout_requires_post(client):
    assert client.get("/logg-ut").status_code == 405


# -- access control -----------------------------------------------------------

def test_admin_requires_login(client):
    response = client.get("/admin/")
    assert response.status_code == 302
    assert response.headers["Location"].startswith("/logg-inn?next=/admin/")


def test_admin_forbidden_for_customer(client, customer):
    login(client, "kunde@example.test")
    response = client.get("/admin/")
    assert response.status_code == 403
    assert "Ingen tilgang" in response.get_data(as_text=True)


def test_admin_allowed_for_admin(client, admin):
    login(client, "admin@example.test")
    response = client.get("/admin/")
    assert response.status_code == 200
    assert "Administrasjon" in response.get_data(as_text=True)


def test_admin_link_only_for_admins(client, customer, admin):
    login(client, "kunde@example.test")
    assert 'href="/admin/"' not in client.get("/").get_data(as_text=True)
    post(client, "/logg-ut")
    login(client, "admin@example.test")
    assert 'href="/admin/"' in client.get("/").get_data(as_text=True)


# -- CSRF ---------------------------------------------------------------------

def test_post_without_csrf_token_is_rejected(client, customer):
    response = client.post("/logg-inn", data={"email": "kunde@example.test", "password": PASSWORD})
    assert response.status_code == 400
    assert logged_in_user_id(client) is None


def test_post_with_wrong_csrf_token_is_rejected(client):
    response = client.post("/registrer", data={**register_data(), "csrf_token": "feil"})
    assert response.status_code == 400


def test_session_cookie_flags(app):
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
