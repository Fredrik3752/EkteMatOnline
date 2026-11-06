import sqlite3

import pytest

from app.models.repositories.sqlite.database import get_db


@pytest.fixture
def app(sqlite_app):
    """SQLite schema tests always run on SQLite, whatever TEST_STORAGE_BACKEND says."""
    return sqlite_app


EXPECTED_TABLES = {
    "users", "event_categories", "allergens", "dietary_labels", "food_items",
    "food_item_categories", "food_item_allergens", "food_item_dietary_labels",
    "orders", "order_lines", "guest_groups", "questions",
}


def test_schema_creates_all_tables(app):
    with app.app_context():
        rows = get_db().execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    assert {r["name"] for r in rows} == EXPECTED_TABLES


def test_reference_data_is_loaded(app):
    with app.app_context():
        db = get_db()
        assert db.execute("SELECT COUNT(*) FROM allergens").fetchone()[0] == 14
        assert db.execute("SELECT COUNT(*) FROM event_categories").fetchone()[0] >= 5
        assert db.execute("SELECT COUNT(*) FROM dietary_labels").fetchone()[0] >= 4


def test_foreign_keys_are_enforced(app):
    with app.app_context():
        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute(
                "INSERT INTO orders (customer_id, event_date, guest_count, delivery_address)"
                " VALUES (999, '2027-05-01', 10, 'Testveien 1')"
            )


def test_invalid_order_status_is_rejected(app):
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO users (email, password_hash, name) VALUES ('kunde@example.test', 'x', 'Test Kunde')"
        )
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO orders (customer_id, event_date, guest_count, delivery_address, status)"
                " VALUES (1, '2027-05-01', 10, 'Testveien 1', 'shipped')"
            )


def test_init_db_command_resets_data(app, runner):
    with app.app_context():
        db = get_db()
        db.execute("INSERT INTO users (email, password_hash, name) VALUES ('a@example.test', 'x', 'A')")
        db.commit()

    result = runner.invoke(args=["init-db"])
    assert "Database initialised" in result.output

    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0
