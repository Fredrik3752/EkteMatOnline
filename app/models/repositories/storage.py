"""Storage set-up that works for every backend: app wiring, reset and the init-db command."""
import click
from flask import current_app
from flask.cli import with_appcontext

from app.models.repositories.backend import backend_module, backend_name


def init_app(app):
    backend_name(app)  # fail fast on a misspelled STORAGE_BACKEND
    backend_module(app).init_app(app)
    app.cli.add_command(init_db_command)


def reset_storage():
    """Delete all data and recreate schema and reference data in the active backend."""
    backend_module().reset()


def describe_storage() -> str:
    return backend_module().describe(current_app)


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Reset the database (deletes all data)."""
    reset_storage()
    click.echo(f"Database initialised: {describe_storage()}")
