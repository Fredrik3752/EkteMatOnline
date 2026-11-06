"""Neo4j schema: uniqueness constraints, reference data and a safe reset.

Neo4j Community has no CHECK constraints like SQLite; value rules (order status,
prices, quantities) are enforced by the domain classes. Uniqueness is enforced here.
"""
from app.models.repositories.neo4j.driver import get_driver, database_name

MARKER_LABEL = "EkteMatStorage"
MARKER_APP = "ekte-mat-online"
SCHEMA_VERSION = 1

ID_LABELS = ["User", "EventCategory", "Allergen", "DietaryLabel", "FoodItem",
             "Order", "OrderLine", "GuestGroup", "Question"]

CONSTRAINTS = (
    [f"CREATE CONSTRAINT {label.lower()}_id IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE"
     for label in ID_LABELS]
    + [
        "CREATE CONSTRAINT user_email IF NOT EXISTS FOR (u:User) REQUIRE u.email IS UNIQUE",
        "CREATE CONSTRAINT event_category_slug IF NOT EXISTS FOR (c:EventCategory) REQUIRE c.slug IS UNIQUE",
        "CREATE CONSTRAINT allergen_code IF NOT EXISTS FOR (a:Allergen) REQUIRE a.code IS UNIQUE",
        "CREATE CONSTRAINT dietary_label_code IF NOT EXISTS FOR (d:DietaryLabel) REQUIRE d.code IS UNIQUE",
        "CREATE CONSTRAINT counter_name IF NOT EXISTS FOR (c:Counter) REQUIRE c.name IS UNIQUE",
    ]
)

# Same reference data, in the same order (and therefore the same ids), as sqlite/schema.sql.
EVENT_CATEGORIES = [
    ("birthday", "Bursdag", 10),
    ("confirmation", "Konfirmasjon", 20),
    ("wedding", "Bryllup", 30),
    ("conference", "Konferanse og møte", 40),
    ("christmas-party", "Julebord", 50),
    ("corporate-lunch", "Firmalunsj", 60),
    ("memorial", "Minnesamvær", 70),
]
ALLERGENS = [
    ("gluten", "Gluten"), ("crustaceans", "Skalldyr"), ("eggs", "Egg"), ("fish", "Fisk"),
    ("peanuts", "Peanøtter"), ("soy", "Soya"), ("milk", "Melk"), ("nuts", "Nøtter"),
    ("celery", "Selleri"), ("mustard", "Sennep"), ("sesame", "Sesam"), ("sulphites", "Sulfitt"),
    ("lupin", "Lupin"), ("molluscs", "Bløtdyr"),
]
DIETARY_LABELS = [
    ("vegetarian", "Vegetar"), ("vegan", "Vegansk"), ("gluten-free", "Glutenfri"),
    ("lactose-free", "Laktosefri"), ("halal", "Halal"),
]


class UnsafeResetError(RuntimeError):
    """Refuse to wipe a Neo4j database that holds data from something else."""


def _count(query: str) -> int:
    records, _, _ = get_driver().execute_query(query, database_=database_name())
    return records[0][0]


def is_initialised() -> bool:
    return _count(f"MATCH (m:{MARKER_LABEL} {{app: '{MARKER_APP}'}}) RETURN count(m)") > 0


def is_empty() -> bool:
    return _count("MATCH (n) RETURN count(n)") == 0


def reset() -> None:
    """Delete all Ekte Mat data and recreate constraints and reference data.

    Only allowed on an empty database or one created by this app (marker node), so a
    wrong NEO4J_URI can never wipe somebody else's graph.
    """
    if not (is_empty() or is_initialised()):
        raise UnsafeResetError(
            "Neo4j-databasen inneholder data som ikke er laget av Ekte Mat Online. "
            "Den blir ikke tømt. Bruk en tom database (f.eks. containeren i docker-compose.yml).")
    driver, db = get_driver(), database_name()

    driver.execute_query("MATCH (n) DETACH DELETE n", database_=db)
    for statement in CONSTRAINTS:  # schema changes must run outside data transactions
        driver.execute_query(statement, database_=db)

    def load(tx):
        tx.run(f"CREATE (:{MARKER_LABEL} {{app: $app, schema_version: $version}})",
               app=MARKER_APP, version=SCHEMA_VERSION)
        tx.run("UNWIND range(0, size($rows) - 1) AS i "
               "CREATE (:EventCategory {id: i + 1, slug: $rows[i][0], name: $rows[i][1], sort_order: $rows[i][2]})",
               rows=[list(r) for r in EVENT_CATEGORIES])
        tx.run("UNWIND range(0, size($rows) - 1) AS i "
               "CREATE (:Allergen {id: i + 1, code: $rows[i][0], name: $rows[i][1]})",
               rows=[list(r) for r in ALLERGENS])
        tx.run("UNWIND range(0, size($rows) - 1) AS i "
               "CREATE (:DietaryLabel {id: i + 1, code: $rows[i][0], name: $rows[i][1]})",
               rows=[list(r) for r in DIETARY_LABELS])
        tx.run("UNWIND $counters AS c CREATE (:Counter {name: c[0], value: c[1]})",
               counters=[["EventCategory", len(EVENT_CATEGORIES)], ["Allergen", len(ALLERGENS)],
                         ["DietaryLabel", len(DIETARY_LABELS)]])

    with driver.session(database=db) as session:
        session.execute_write(load)
