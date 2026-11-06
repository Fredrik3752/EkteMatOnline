"""SQLite storage backend (the default)."""
from app.models.repositories.sqlite import database
from app.models.repositories.sqlite.event_category_repository import SqliteEventCategoryRepository
from app.models.repositories.sqlite.food_item_repository import SqliteFoodItemRepository
from app.models.repositories.sqlite.order_repository import SqliteOrderRepository
from app.models.repositories.sqlite.question_repository import SqliteQuestionRepository
from app.models.repositories.sqlite.reference_repository import (SqliteAllergenRepository,
                                                                  SqliteDietaryLabelRepository)
from app.models.repositories.sqlite.user_repository import SqliteUserRepository

REPOSITORIES = {
    "EventCategoryRepository": SqliteEventCategoryRepository,
    "AllergenRepository": SqliteAllergenRepository,
    "DietaryLabelRepository": SqliteDietaryLabelRepository,
    "UserRepository": SqliteUserRepository,
    "FoodItemRepository": SqliteFoodItemRepository,
    "OrderRepository": SqliteOrderRepository,
    "QuestionRepository": SqliteQuestionRepository,
}


def init_app(app):
    database.init_app(app)


def reset():
    """Delete everything and recreate schema + reference data."""
    database.init_db()


def describe(app) -> str:
    return database.describe(app)
