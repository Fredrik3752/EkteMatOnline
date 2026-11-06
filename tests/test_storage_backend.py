"""Choosing the storage backend through configuration (Oblig 5)."""
import pytest

from app import create_app
from app.models.repositories import base
from app.models.repositories.backend import backend_name
from app.models.repositories.event_category_repository import EventCategoryRepository
from app.models.repositories.food_item_repository import FoodItemRepository
from app.models.repositories.order_repository import OrderRepository
from app.models.repositories.question_repository import QuestionRepository
from app.models.repositories.reference_repository import AllergenRepository, DietaryLabelRepository
from app.models.repositories.sqlite import REPOSITORIES as SQLITE_REPOSITORIES
from app.models.repositories.user_repository import UserRepository

PUBLIC = {
    "EventCategoryRepository": (EventCategoryRepository, base.EventCategoryRepositoryBase),
    "AllergenRepository": (AllergenRepository, base.AllergenRepositoryBase),
    "DietaryLabelRepository": (DietaryLabelRepository, base.DietaryLabelRepositoryBase),
    "UserRepository": (UserRepository, base.UserRepositoryBase),
    "FoodItemRepository": (FoodItemRepository, base.FoodItemRepositoryBase),
    "OrderRepository": (OrderRepository, base.OrderRepositoryBase),
    "QuestionRepository": (QuestionRepository, base.QuestionRepositoryBase),
}


def test_sqlite_is_the_default(app):
    assert backend_name(app) == "sqlite"


@pytest.mark.parametrize("name", sorted(PUBLIC))
def test_public_names_give_the_sqlite_implementation(app, name):
    public_cls, contract = PUBLIC[name]
    with app.app_context():
        repo = public_cls()
    assert type(repo) is SQLITE_REPOSITORIES[name]
    assert isinstance(repo, contract)


def test_sqlite_backend_implements_every_contract():
    assert set(SQLITE_REPOSITORIES) == set(PUBLIC)
    for name, cls in SQLITE_REPOSITORIES.items():
        assert issubclass(cls, PUBLIC[name][1])
        assert not getattr(cls, "__abstractmethods__", None), f"{name} misses methods"


def test_unknown_backend_fails_at_start_up(tmp_path):
    with pytest.raises(ValueError, match="Unknown STORAGE_BACKEND"):
        create_app({"STORAGE_BACKEND": "mongodb", "DATABASE": str(tmp_path / "x.db")})


def test_backend_name_is_case_insensitive(tmp_path):
    app = create_app({"STORAGE_BACKEND": " SQLite ", "DATABASE": str(tmp_path / "x.db"),
                      "IMAGE_UPLOAD_DIR": str(tmp_path / "u"), "IMAGE_PREVIEW_DIR": str(tmp_path / "p")})
    assert backend_name(app) == "sqlite"


def test_init_db_reports_backend(runner):
    result = runner.invoke(args=["init-db"])
    assert result.exit_code == 0 and "Database initialised: SQLite" in result.output
