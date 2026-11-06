from datetime import date

import pytest

from app.models.errors import ValidationError
from app.models.event_category import EventCategory
from app.models.food_item import FoodItem
from app.models.order import GuestGroup, Order, OrderLine, OrderStatus, PaymentStatus
from app.models.question import Question
from app.models.repositories.database import get_db
from app.models.repositories.event_category_repository import EventCategoryRepository
from app.models.repositories.food_item_repository import FoodItemRepository
from app.models.repositories.order_repository import OrderRepository
from app.models.repositories.question_repository import QuestionRepository
from app.models.repositories.reference_repository import AllergenRepository, DietaryLabelRepository
from app.models.repositories.user_repository import UserRepository
from app.models.user import User


@pytest.fixture
def ctx(app):
    with app.app_context():
        yield


@pytest.fixture
def customer(ctx):
    return UserRepository().add(User.create("kunde@example.test", "Test Kunde", "passord-123"))


def lookup(repo):
    return {x.code if hasattr(x, "code") else x.slug: x for x in repo.list_all()}


def make_item(published=True, **kwargs):
    cats = lookup(EventCategoryRepository())
    alls = lookup(AllergenRepository())
    diets = lookup(DietaryLabelRepository())
    data = dict(name="Fiskesuppe", description="Med torsk", price_ore=18900, min_order_qty=10,
                is_published=published, origin="Bergen",
                categories=[cats["wedding"], cats["conference"]],
                allergens=[alls["fish"], alls["milk"]], dietary_labels=[diets["gluten-free"]])
    data.update(kwargs)
    return FoodItem(**data)


def make_order(customer_id, event_date=date(2027, 5, 1), **kwargs):
    data = dict(customer_id=customer_id, event_date=event_date, guest_count=20,
                delivery_address="Testveien 1, 5000 Bergen",
                lines=[OrderLine("Fiskesuppe", 20, 18900)],
                guest_groups=[GuestGroup("Nøtteallergi", 2, allergy_notes="Nøtter")])
    data.update(kwargs)
    return Order(**data)


# -- event categories ---------------------------------------------------------

def test_event_categories_in_order(ctx):
    categories = EventCategoryRepository().list_all()
    assert categories and all(isinstance(c, EventCategory) for c in categories)
    assert [c.sort_order for c in categories] == sorted(c.sort_order for c in categories)
    assert EventCategoryRepository().get_by_slug("wedding").name == "Bryllup"
    assert EventCategoryRepository().get_by_slug("does-not-exist") is None


# -- users --------------------------------------------------------------------

def test_user_roundtrip(customer):
    repo = UserRepository()
    assert repo.get(customer.id).email == "kunde@example.test"
    assert repo.get_by_email("  KUNDE@example.test ").id == customer.id
    assert repo.get_by_email("ukjent@example.test") is None
    assert repo.get(customer.id).check_password("passord-123")
    assert [u.id for u in repo.list_customers()] == [customer.id]


def test_duplicate_email_is_rejected(customer):
    with pytest.raises(ValidationError) as exc:
        UserRepository().add(User.create("kunde@example.test", "Annen", "passord-123"))
    assert "email" in exc.value.errors


# -- food items ---------------------------------------------------------------

def test_food_item_crud_with_links(ctx):
    repo = FoodItemRepository()
    item = repo.add(make_item())
    assert item.id and item.price_ore == 18900 and item.origin == "Bergen"
    assert {c.slug for c in item.categories} == {"wedding", "conference"}
    assert {a.code for a in item.allergens} == {"fish", "milk"}
    assert [d.code for d in item.dietary_labels] == ["gluten-free"]

    item.name = "Fiskesuppe deluxe"
    item.allergens = item.allergens[:1]
    item.categories = [EventCategoryRepository().get_by_slug("christmas-party")]
    updated = repo.update(item)
    assert updated.name == "Fiskesuppe deluxe"
    assert [a.code for a in updated.allergens] == ["fish"]
    assert [c.slug for c in updated.categories] == ["christmas-party"]

    assert repo.delete(item.id) is True
    assert repo.get(item.id) is None
    assert repo.delete(item.id) is False
    assert get_db().execute("SELECT COUNT(*) FROM food_item_allergens").fetchone()[0] == 0


def test_invalid_food_item_is_not_saved(ctx):
    with pytest.raises(ValidationError):
        FoodItemRepository().add(make_item(price_ore=-100))
    assert FoodItemRepository().list_all() == []


def test_published_items_grouped_by_category(ctx):
    repo = FoodItemRepository()
    repo.add(make_item(name="Publisert"))
    repo.add(make_item(name="Kladd", published=False))
    groups = repo.list_published_by_category()
    assert [c.slug for c in groups] == ["wedding", "conference"]  # category sort order
    assert all([i.name for i in items] == ["Publisert"] for items in groups.values())
    assert len(repo.list_all()) == 2
    assert [i.name for i in repo.list_all(published_only=True)] == ["Publisert"]


def test_get_many(ctx):
    repo = FoodItemRepository()
    a, b = repo.add(make_item(name="A")), repo.add(make_item(name="B"))
    assert set(repo.get_many([a.id, b.id, 9999])) == {a.id, b.id}
    assert repo.get_many([]) == {}


# -- orders -------------------------------------------------------------------

def test_order_roundtrip(customer):
    repo = OrderRepository()
    order = repo.add(make_order(customer.id, notes="Levering kl. 12"))
    assert order.id and order.status is OrderStatus.SUBMITTED
    assert order.payment_status is PaymentStatus.NOT_PAID
    assert order.event_date == date(2027, 5, 1)
    assert order.total_ore == 20 * 18900
    assert order.lines[0].item_name == "Fiskesuppe"
    assert order.guest_groups[0].allergy_notes == "Nøtter"
    stored_total = get_db().execute("SELECT estimated_total_ore FROM orders").fetchone()[0]
    assert stored_total == order.total_ore


def test_order_with_invalid_line_rolls_back(customer):
    bad = make_order(customer.id, lines=[OrderLine("A", 1, 100), OrderLine("B", 1, -5)])
    with pytest.raises(Exception):
        OrderRepository().add(bad)
    db = get_db()
    assert db.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM order_lines").fetchone()[0] == 0


def test_order_filters(customer):
    repo = OrderRepository()
    o1 = repo.add(make_order(customer.id, event_date=date(2027, 3, 1)))
    o2 = repo.add(make_order(customer.id, event_date=date(2027, 6, 1)))
    o2.change_status(OrderStatus.APPROVED)
    repo.save_status(o2)

    assert [o.id for o in repo.list()] == [o1.id, o2.id]
    assert [o.id for o in repo.list(status="approved")] == [o2.id]
    assert [o.id for o in repo.list(status=OrderStatus.SUBMITTED)] == [o1.id]
    assert [o.id for o in repo.list(date_from=date(2027, 4, 1))] == [o2.id]
    assert [o.id for o in repo.list(date_to=date(2027, 4, 1))] == [o1.id]
    assert repo.list(status="approved", date_to=date(2027, 4, 1)) == []


def test_orders_for_customer_only(customer):
    other = UserRepository().add(User.create("annen@example.test", "Annen Kunde", "passord-123"))
    repo = OrderRepository()
    mine = repo.add(make_order(customer.id))
    repo.add(make_order(other.id))
    assert [o.id for o in repo.list_for_customer(customer.id)] == [mine.id]


def test_save_status_persists(customer):
    repo = OrderRepository()
    order = repo.add(make_order(customer.id))
    order.change_status("approved")
    order.change_payment_status("deposit_paid")
    saved = repo.save_status(order)
    assert saved.status is OrderStatus.APPROVED
    assert saved.payment_status is PaymentStatus.DEPOSIT_PAID


# -- questions ----------------------------------------------------------------

def test_question_flow(customer):
    order = OrderRepository().add(make_order(customer.id))
    admin = UserRepository().add(User.create("admin@example.test", "Admin", "passord-123", role="admin"))
    repo = QuestionRepository()

    q = repo.add(Question(order_id=order.id, author_id=customer.id, body="Kan dere levere tidligere?"))
    assert [x.id for x in repo.list_for_order(order.id)] == [q.id]
    assert [x.id for x in repo.list_all(unanswered_only=True)] == [q.id]

    q.give_answer("Ja.", admin.id)
    saved = repo.save_answer(q)
    assert saved.is_answered and saved.answered_by == admin.id
    assert repo.list_all(unanswered_only=True) == []
    assert len(repo.list_all()) == 1


def test_empty_question_is_rejected(customer):
    order = OrderRepository().add(make_order(customer.id))
    with pytest.raises(ValidationError):
        QuestionRepository().add(Question(order_id=order.id, author_id=customer.id, body=" "))
