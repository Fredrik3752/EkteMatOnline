import pytest

import app.models.user as user_module
from app import create_app
from app.models.repositories.user_repository import UserRepository
from app.models.user import ROLE_ADMIN, User

CSRF = "test-csrf-token"
PASSWORD = "passord-123"


@pytest.fixture(autouse=True)
def fast_password_hashing(monkeypatch):
    """Few pbkdf2 iterations in tests only – the app uses Werkzeug's secure default."""
    monkeypatch.setattr(user_module, "HASH_METHOD", "pbkdf2:sha256:1000")


@pytest.fixture
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test",
        "DATABASE": str(tmp_path / "test.db"),
    })
    yield app


@pytest.fixture
def client(app):
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["csrf_token"] = CSRF
    return client


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


def post(client, url, data=None, **kwargs):
    """POST with a valid CSRF token (re-set first, since login/logout clear the session)."""
    with client.session_transaction() as sess:
        sess["csrf_token"] = CSRF
    return client.post(url, data={"csrf_token": CSRF, **(data or {})}, **kwargs)


def login(client, email, password=PASSWORD):
    return post(client, "/logg-inn", {"email": email, "password": password})


@pytest.fixture
def make_user(app):
    def _make(email="kunde@example.test", name="Test Kunde", role="customer"):
        with app.app_context():
            return UserRepository().add(User.create(email, name, PASSWORD, role=role))
    return _make


@pytest.fixture
def customer(make_user):
    return make_user()


@pytest.fixture
def admin(make_user):
    return make_user("admin@example.test", "Test Admin", ROLE_ADMIN)
