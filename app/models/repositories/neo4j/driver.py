"""Neo4j connection handling: one driver per Flask app, short sessions per repository call."""
import atexit
from typing import Any, Callable, List

from flask import current_app
from neo4j import Driver, GraphDatabase, Record, RoutingControl
from neo4j.exceptions import AuthError, ServiceUnavailable

EXTENSION_KEY = "neo4j_driver"


class Neo4jUnavailable(RuntimeError):
    """Neo4j cannot be reached or rejects the credentials."""


def create_driver(app) -> Driver:
    cfg = app.config
    driver = GraphDatabase.driver(cfg["NEO4J_URI"], auth=(cfg["NEO4J_USER"], cfg["NEO4J_PASSWORD"]))
    app.extensions[EXTENSION_KEY] = driver
    atexit.register(driver.close)
    return driver


def verify(driver: Driver, app) -> None:
    try:
        driver.verify_connectivity()
    except (ServiceUnavailable, OSError) as exc:
        raise Neo4jUnavailable(
            f"Får ikke kontakt med Neo4j på {app.config['NEO4J_URI']}. "
            "Er containeren startet? Kjør `docker compose up -d`.") from exc
    except AuthError as exc:
        raise Neo4jUnavailable(
            "Neo4j avviste brukernavn/passord. Sjekk NEO4J_USER og NEO4J_PASSWORD i .env "
            "(passordet settes første gang containeren starter).") from exc


def get_driver(app=None) -> Driver:
    return (app or current_app).extensions[EXTENSION_KEY]


def database_name(app=None) -> str:
    return (app or current_app).config["NEO4J_DATABASE"]


def read(query: str, **params: Any) -> List[Record]:
    """Run a read-only query and return all records."""
    records, _, _ = get_driver().execute_query(
        query, params, database_=database_name(), routing_=RoutingControl.READ)
    return records


def write(work: Callable, *args: Any) -> Any:
    """Run `work(tx, *args)` in ONE write transaction – committed together or rolled back together."""
    with get_driver().session(database=database_name()) as session:
        return session.execute_write(work, *args)


def next_id(tx, counter: str, count: int = 1) -> int:
    """Reserve `count` consecutive integer ids for `counter` and return the first.

    Neo4j's own element ids are not stable integers, but the domain and the URLs use
    integer ids – so we keep one (:Counter) node per label. MERGE + SET takes a write
    lock on the counter node, so concurrent transactions never get the same id.
    """
    record = tx.run(
        "MERGE (c:Counter {name: $name}) ON CREATE SET c.value = 0 "
        "SET c.value = c.value + $count RETURN c.value AS value",
        name=counter, count=count,
    ).single()
    return record["value"] - count + 1
