"""Neo4j storage backend (Oblig 5). Selected with STORAGE_BACKEND=neo4j."""
from app.models.repositories.neo4j import driver as _driver
from app.models.repositories.neo4j import schema
from app.models.repositories.neo4j.food_item_repository import Neo4jFoodItemRepository
from app.models.repositories.neo4j.order_repository import Neo4jOrderRepository
from app.models.repositories.neo4j.question_repository import Neo4jQuestionRepository
from app.models.repositories.neo4j.reference_repository import (Neo4jAllergenRepository,
                                                                Neo4jDietaryLabelRepository,
                                                                Neo4jEventCategoryRepository)
from app.models.repositories.neo4j.user_repository import Neo4jUserRepository

REPOSITORIES = {
    "EventCategoryRepository": Neo4jEventCategoryRepository,
    "AllergenRepository": Neo4jAllergenRepository,
    "DietaryLabelRepository": Neo4jDietaryLabelRepository,
    "UserRepository": Neo4jUserRepository,
    "FoodItemRepository": Neo4jFoodItemRepository,
    "OrderRepository": Neo4jOrderRepository,
    "QuestionRepository": Neo4jQuestionRepository,
}


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
