"""Neo4j storage backend (Oblig 5). Selected with STORAGE_BACKEND=neo4j."""
from app.models.repositories.neo4j import driver as _driver
from app.models.repositories.neo4j import schema

# Filled in phase N3 – one Cypher implementation per contract in base.py.
REPOSITORIES = {}


def init_app(app):
    driver = _driver.create_driver(app)
    _driver.verify(driver, app)
    with app.app_context():
        # Like SQLite: set up an empty database automatically on first start.
        if schema.is_empty():
            schema.reset()
        elif not schema.is_initialised():
            raise schema.UnsafeResetError(
                f"Neo4j på {app.config['NEO4J_URI']} inneholder data som ikke er laget av "
                "Ekte Mat Online. Bruk en tom database.")


def reset():
    schema.reset()


def describe(app) -> str:
    return f"Neo4j {app.config['NEO4J_URI']} (database {app.config['NEO4J_DATABASE']})"
