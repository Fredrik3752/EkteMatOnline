from datetime import date

from app.models.order import OrderStatus
from app.models.repositories.food_item_repository import FoodItemRepository
from app.models.repositories.order_repository import OrderRepository
from app.models.repositories.question_repository import QuestionRepository
from app.models.repositories.user_repository import UserRepository
from app.seed import ADMIN, DEFAULT_ADMIN_PASSWORD, DEFAULT_CUSTOMER_PASSWORD, seed_database


def test_seed_creates_sample_data(app, monkeypatch):
    monkeypatch.delenv("SEED_ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("SEED_CUSTOMER_PASSWORD", raising=False)
    with app.app_context():
        summary = seed_database(today=date(2027, 1, 10))
        assert summary == {"users": 3, "food_items": 13, "orders": 4, "questions": 2}

        admin = UserRepository().get_by_email(ADMIN["email"])
        assert admin.is_admin and admin.check_password(DEFAULT_ADMIN_PASSWORD)
        customers = UserRepository().list_customers()
        assert len(customers) == 2
        assert all(c.check_password(DEFAULT_CUSTOMER_PASSWORD) for c in customers)

        items = FoodItemRepository().list_all()
        assert len(FoodItemRepository().list_all(published_only=True)) == len(items) - 1
        assert all(i.categories for i in items)
        grouped = FoodItemRepository().list_published_by_category()
        assert {"wedding", "christmas-party", "conference", "birthday"} <= {c.slug for c in grouped}

        statuses = {o.status for o in OrderRepository().list()}
        assert {OrderStatus.SUBMITTED, OrderStatus.APPROVED, OrderStatus.DELIVERED} <= statuses
        assert len(QuestionRepository().list_all(unanswered_only=True)) == 1


def test_seed_uses_only_synthetic_email_domains(app):
    with app.app_context():
        seed_database()
        users = UserRepository().list_customers() + [UserRepository().get_by_email(ADMIN["email"])]
    assert all(u.email.endswith(".test") for u in users)


def test_seed_password_from_environment(app, monkeypatch):
    monkeypatch.setenv("SEED_ADMIN_PASSWORD", "annet-test-passord")
    with app.app_context():
        seed_database()
        assert UserRepository().get_by_email(ADMIN["email"]).check_password("annet-test-passord")


def test_seed_cli_command(runner):
    result = runner.invoke(args=["seed"])
    assert result.exit_code == 0
    assert "food_items=13" in result.output
