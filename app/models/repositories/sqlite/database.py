"""SQLite connection handling.

This package (repositories/sqlite) is the ONLY code that touches SQLite. Controllers
and views talk to repositories and get domain objects back.
"""
import os
import sqlite3
from importlib import resources

from flask import current_app, g


def get_db():
    """Return the SQLite connection for the current request."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Drop all tables and create the schema with reference data."""
    schema = resources.files(__package__).joinpath("schema.sql").read_text(encoding="utf-8")
    get_db().executescript(schema)


def describe(app) -> str:
    return f"SQLite {app.config['DATABASE']}"


def init_app(app):
    app.teardown_appcontext(close_db)
    # Create the database automatically on first start.
    if not os.path.exists(app.config["DATABASE"]):
        with app.app_context():
            init_db()
