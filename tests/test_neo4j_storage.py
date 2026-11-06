"""Neo4j infrastructure (Oblig 5, phase N2). Runs against the neo4j-test container; skipped if it is down."""
import pytest

from app.models.repositories.neo4j import schema
from app.models.repositories.neo4j.driver import get_driver, next_id, read, write
from app.models.repositories.sqlite import database as sqlite_db
from app.models.repositories.storage import describe_storage, reset_storage


def labels_count(label):
    return read(f"MATCH (n:{label}) RETURN count(n) AS c")[0]["c"]


def test_reset_creates_marker_reference_data_and_counters(neo4j_app):
    with neo4j_app.app_context():
        assert schema.is_initialised()
        assert labels_count("EventCategory") == len(schema.EVENT_CATEGORIES)
        assert labels_count("Allergen") == 14
        assert labels_count("DietaryLabel") == len(schema.DIETARY_LABELS)
        counters = {r["name"]: r["value"] for r in read("MATCH (c:Counter) RETURN c.name AS name, c.value AS value")}
        assert counters == {"EventCategory": 7, "Allergen": 14, "DietaryLabel": 5}


def test_reference_data_matches_sqlite(neo4j_app, sqlite_app):
    """Same ids, codes and names in both backends – forms post these ids."""
    with neo4j_app.app_context():
        neo = {
            "cat": [tuple(r) for r in read("MATCH (c:EventCategory) RETURN c.id, c.slug, c.name, c.sort_order ORDER BY c.id")],
            "all": [tuple(r) for r in read("MATCH (a:Allergen) RETURN a.id, a.code, a.name ORDER BY a.id")],
            "diet": [tuple(r) for r in read("MATCH (d:DietaryLabel) RETURN d.id, d.code, d.name ORDER BY d.id")],
        }
    with sqlite_app.app_context():
        db = sqlite_db.get_db()
        sql = {
            "cat": [tuple(r) for r in db.execute("SELECT id, slug, name, sort_order FROM event_categories ORDER BY id")],
            "all": [tuple(r) for r in db.execute("SELECT id, code, name FROM allergens ORDER BY id")],
            "diet": [tuple(r) for r in db.execute("SELECT id, code, name FROM dietary_labels ORDER BY id")],
        }
    assert neo == sql


def test_constraints_exist(neo4j_app):
    with neo4j_app.app_context():
        names = {r["name"] for r in read("SHOW CONSTRAINTS YIELD name RETURN name")}
    assert {"user_id", "user_email", "fooditem_id", "order_id", "question_id", "counter_name",
            "event_category_slug", "allergen_code"} <= names


def test_unique_email_is_enforced(neo4j_app):
    from neo4j.exceptions import ConstraintError
    with neo4j_app.app_context():
        write(lambda tx: tx.run("CREATE (:User {id: 1, email: 'a@example.test'})").consume())
        with pytest.raises(ConstraintError):
            write(lambda tx: tx.run("CREATE (:User {id: 2, email: 'a@example.test'})").consume())


def test_next_id_reserves_consecutive_ids(neo4j_app):
    with neo4j_app.app_context():
        assert write(next_id, "Order") == 1
        assert write(next_id, "Order") == 2
        assert write(next_id, "Order", 5) == 3   # reserves 3..7
        assert write(next_id, "Order") == 8
        assert write(next_id, "FoodItem") == 1   # counters are independent


def test_failed_transaction_rolls_back(neo4j_app):
    def work(tx):
        tx.run("CREATE (:FoodItem {id: 99, name: 'Halvferdig'})").consume()
        raise RuntimeError("boom")
    with neo4j_app.app_context():
        with pytest.raises(RuntimeError):
            write(work)
        assert labels_count("FoodItem") == 0


def test_reset_wipes_app_data(neo4j_app):
    with neo4j_app.app_context():
        write(lambda tx: tx.run("CREATE (:FoodItem {id: 1, name: 'X'})").consume())
        reset_storage()
        assert labels_count("FoodItem") == 0
        assert labels_count("Allergen") == 14


def test_reset_refuses_foreign_database(neo4j_app):
    """A database with someone else's data (no marker node) is never wiped."""
    with neo4j_app.app_context():
        driver = get_driver()
        driver.execute_query("MATCH (n) DETACH DELETE n")
        driver.execute_query("CREATE (:Movie {title: 'Ikke vår'})")
        try:
            with pytest.raises(schema.UnsafeResetError):
                reset_storage()
            assert labels_count("Movie") == 1
        finally:
            driver.execute_query("MATCH (n) DETACH DELETE n")  # leave the test DB empty


def test_describe_and_cli(neo4j_app):
    with neo4j_app.app_context():
        assert describe_storage().startswith("Neo4j bolt://")
    result = neo4j_app.test_cli_runner().invoke(args=["init-db"])
    assert result.exit_code == 0 and "Database initialised: Neo4j" in result.output


def test_wrong_password_gives_clear_error(tmp_path):
    from app import create_app
    from app.models.repositories.neo4j.driver import Neo4jUnavailable
    from tests.conftest import neo4j_test_config
    config = {**neo4j_test_config(), "NEO4J_PASSWORD": "feil-passord-123",
              "DATABASE": str(tmp_path / "x.db")}
    with pytest.raises(Neo4jUnavailable, match="avviste"):
        create_app(config)


def test_unreachable_server_gives_clear_error(tmp_path):
    from app import create_app
    from app.models.repositories.neo4j.driver import Neo4jUnavailable
    with pytest.raises(Neo4jUnavailable, match="docker compose up"):
        create_app({"STORAGE_BACKEND": "neo4j", "NEO4J_URI": "bolt://127.0.0.1:1",
                    "NEO4J_PASSWORD": "x", "DATABASE": str(tmp_path / "x.db")})


def test_neo4j_backend_implements_every_contract(neo4j_app):
    from app.models.repositories.neo4j import REPOSITORIES
    from app.models.repositories.sqlite import REPOSITORIES as SQLITE
    from app.models.repositories.order_repository import OrderRepository
    assert set(REPOSITORIES) == set(SQLITE)
    for name, cls in REPOSITORIES.items():
        assert not getattr(cls, "__abstractmethods__", None), f"{name} misses methods"
    with neo4j_app.app_context():
        assert type(OrderRepository()).__name__ == "Neo4jOrderRepository"


def test_seed_runs_without_neo4j_warnings(neo4j_app, caplog):
    """Guards against deprecated Cypher (the server reports it as a notification)."""
    import logging
    from app.seed import seed_database
    with caplog.at_level(logging.WARNING, logger="neo4j"):
        with neo4j_app.app_context():
            seed_database()
    notifications = [r.getMessage()[:160] for r in caplog.records if "notification" in r.getMessage().lower()]
    assert notifications == []
