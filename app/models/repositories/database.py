"""SQLite connection handling.

This module and the repository classes next to it are the ONLY code that may
touch SQLite. Controllers and views talk to repositories and get domain
objects back, so the storage can later be replaced by Neo4j.
"""
import os
import sqlite3
from importlib import resources

import click
from flask import current_app, g
from flask.cli import with_appcontext


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


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Reset the database (deletes all data)."""
    init_db()
    click.echo(f"Database initialised: {current_app.config['DATABASE']}")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    # Create the database automatically on first start.
    if not os.path.exists(app.config["DATABASE"]):
        with app.app_context():
            init_db()
