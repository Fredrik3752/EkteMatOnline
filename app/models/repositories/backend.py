"""Chooses the storage backend from app.config['STORAGE_BACKEND'] ('sqlite' or 'neo4j').

Each backend package exposes REPOSITORIES (public name -> class), init_app(app),
reset() and describe(app). Backends are imported lazily, so the neo4j driver is only
needed when the Neo4j backend is actually used.
"""
import importlib

from flask import current_app

BACKENDS = {
    "sqlite": "app.models.repositories.sqlite",
    "neo4j": "app.models.repositories.neo4j",
}
DEFAULT_BACKEND = "sqlite"


def backend_name(app=None) -> str:
    name = (app or current_app).config.get("STORAGE_BACKEND") or DEFAULT_BACKEND
    name = str(name).strip().lower()
    if name not in BACKENDS:
        raise ValueError(f"Unknown STORAGE_BACKEND {name!r}. Use one of: {', '.join(BACKENDS)}")
    return name


def backend_module(app=None):
    return importlib.import_module(BACKENDS[backend_name(app)])


def implementation(public_name: str):
    """The repository class for the active backend, e.g. implementation('OrderRepository')."""
    module = backend_module()
    try:
        return module.REPOSITORIES[public_name]
    except KeyError:
        raise NotImplementedError(
            f"Lagringen {backend_name()!r} har ingen implementasjon av {public_name} ennå") from None
