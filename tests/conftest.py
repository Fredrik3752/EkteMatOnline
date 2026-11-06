import os

import pytest

import app.models.user as user_module
from app import create_app
from app.config import Config  # also loads .env
from app.models.repositories.user_repository import UserRepository
from app.models.user import ROLE_ADMIN, User

CSRF = "test-csrf-token"
PASSWORD = "passord-123"

# Which storage the normal test suite runs against. Never taken from STORAGE_BACKEND in .env,
# so a developer's .env can never point the tests at the development database.
TEST_STORAGE_BACKEND = os.environ.get("TEST_STORAGE_BACKEND", "sqlite").strip().lower()


def neo4j_test_config():
    """Config for the throw-away Neo4j test database, or a pytest.skip reason."""
    uri = os.environ.get("NEO4J_TEST_URI", "").strip()
    password = os.environ.get("NEO4J_TEST_PASSWORD", "")
    if not uri or not password:
        pytest.skip("Neo4j-tester: NEO4J_TEST_URI/NEO4J_TEST_PASSWORD er ikke satt (se .env.example)")
    if uri == Config.NEO4J_URI:
        pytest.fail("NEO4J_TEST_URI er lik NEO4J_URI – testene ville tømt utviklingsdatabasen")
    return {
        "STORAGE_BACKEND": "neo4j",
        "NEO4J_URI": uri,
        "NEO4J_USER": os.environ.get("NEO4J_TEST_USER", Config.NEO4J_USER),
        "NEO4J_PASSWORD": password,
        "NEO4J_DATABASE": os.environ.get("NEO4J_TEST_DATABASE", "neo4j"),
    }


def make_test_app(tmp_path, backend):
    config = {
        "TESTING": True,
        "SECRET_KEY": "test",
        "STORAGE_BACKEND": "sqlite",
        "DATABASE": str(tmp_path / "test.db"),
        "IMAGE_UPLOAD_DIR": str(tmp_path / "uploads"),
        "IMAGE_PREVIEW_DIR": str(tmp_path / "previews"),
    }
    if backend == "neo4j":
        config.update(neo4j_test_config())
        from app.models.repositories.neo4j.driver import Neo4jUnavailable
        try:
            app = create_app(config)
        except Neo4jUnavailable as exc:
            pytest.skip(f"Neo4j-tester: {exc}")
        from app.models.repositories.storage import reset_storage
        with app.app_context():
            reset_storage()  # every test starts from an empty graph with reference data
        return app
    return create_app(config)


def close_app(app):
    driver = app.extensions.pop("neo4j_driver", None)
    if driver is not None:
        driver.close()


@pytest.fixture(autouse=True)
def fast_password_hashing(monkeypatch):
    """Few pbkdf2 iterations in tests only – the app uses Werkzeug's secure default."""
    monkeypatch.setattr(user_module, "HASH_METHOD", "pbkdf2:sha256:1000")


@pytest.fixture
def app(tmp_path):
    """The app under test, on TEST_STORAGE_BACKEND (default: SQLite in a temp folder)."""
    app = make_test_app(tmp_path, TEST_STORAGE_BACKEND)
    yield app
    close_app(app)


@pytest.fixture
def sqlite_app(tmp_path):
    """Always SQLite – for tests of SQLite itself (schema, CHECK constraints, raw SQL)."""
    app = make_test_app(tmp_path, "sqlite")
    yield app
    close_app(app)


@pytest.fixture
def neo4j_app(tmp_path):
    """Always Neo4j (the test container) – for Neo4j-specific tests. Skipped if it is not running."""
    app = make_test_app(tmp_path, "neo4j")
    yield app
    close_app(app)


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


@pytest.fixture
def menu_items(app):
    """Two published items and one unpublished, for cart/checkout tests."""
    from app.models.food_item import FoodItem
    from app.models.repositories.event_category_repository import EventCategoryRepository
    from app.models.repositories.food_item_repository import FoodItemRepository

    with app.app_context():
        wedding = EventCategoryRepository().get_by_slug("wedding")
        repo = FoodItemRepository()
        return {
            "suppe": repo.add(FoodItem(name="Fiskesuppe", price_ore=18900, min_order_qty=10,
                                       is_published=True, categories=[wedding])),
            "kake": repo.add(FoodItem(name="Bløtkake", price_ore=69000, min_order_qty=1,
                                      is_published=True, categories=[wedding])),
            "kladd": repo.add(FoodItem(name="Kladd", price_ore=1000, min_order_qty=1,
                                       is_published=False, categories=[wedding])),
        }


def cart_in_session(client):
    with client.session_transaction() as sess:
        return dict(sess.get("cart", {}))


@pytest.fixture
def make_order(app):
    """Create an order directly through the repository."""
    from datetime import date

    from app.models.order import GuestGroup, Order, OrderLine
    from app.models.repositories.order_repository import OrderRepository

    def _make(customer_id, event_date=date(2027, 5, 1), status=None, **kwargs):
        data = dict(customer_id=customer_id, event_date=event_date, guest_count=20,
                    delivery_address="Testveien 1, 5000 Bergen",
                    lines=[OrderLine("Fiskesuppe", 20, 18900)],
                    guest_groups=[GuestGroup("Nøtteallergi", 2, allergy_notes="Nøtter")])
        data.update(kwargs)
        with app.app_context():
            repo = OrderRepository()
            order = repo.add(Order(**data))
            if status is not None:
                order.status = status  # test setup only – bypasses the state machine
                order = repo.save_status(order)
            return order
    return _make


def get_order(app, order_id):
    from app.models.repositories.order_repository import OrderRepository
    with app.app_context():
        return OrderRepository().get(order_id)
