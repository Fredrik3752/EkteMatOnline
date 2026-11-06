"""Unit tests for domain classes – no database needed."""
from datetime import date

import pytest

from app.models.errors import InvalidStatusTransition, ValidationError
from app.models.food_item import FoodItem
from app.models.money import format_nok, nok_to_ore
from app.models.order import ALLOWED_TRANSITIONS, GuestGroup, Order, OrderLine, OrderStatus, PaymentStatus
from app.models.question import Question
from app.models.user import User

S = OrderStatus


def make_order(**kwargs):
    defaults = dict(customer_id=1, event_date=date(2027, 5, 1), guest_count=20,
                    delivery_address="Testveien 1, 5000 Bergen",
                    lines=[OrderLine("Fiskesuppe", 20, 18900)])
    defaults.update(kwargs)
    return Order(**defaults)


# -- money ---------------------------------------------------------------------

def test_format_nok():
    assert format_nok(18900) == "189,00 kr"
    assert format_nok(189050) == "1 890,50 kr"


@pytest.mark.parametrize("text, ore", [("189", 18900), ("189,5", 18950), ("1 890.25", 189025), ("0", 0)])
def test_nok_to_ore(text, ore):
    assert nok_to_ore(text) == ore


@pytest.mark.parametrize("text", ["", "abc", "-5", "1,234", "12.3.4"])
def test_nok_to_ore_rejects_invalid(text):
    with pytest.raises(ValueError):
        nok_to_ore(text)


# -- order status state machine -------------------------------------------------

@pytest.mark.parametrize("path", [
    [S.APPROVED, S.IN_PREPARATION, S.DELIVERED],
    [S.REJECTED],
    [S.CANCELLED],
    [S.APPROVED, S.CANCELLED],
    [S.APPROVED, S.IN_PREPARATION, S.CANCELLED],
])
def test_allowed_status_paths(path):
    order = make_order()
    for status in path:
        order.change_status(status)
    assert order.status == path[-1]


@pytest.mark.parametrize("start, target", [
    (S.SUBMITTED, S.DELIVERED),
    (S.SUBMITTED, S.IN_PREPARATION),
    (S.APPROVED, S.REJECTED),
    (S.APPROVED, S.SUBMITTED),
    (S.DELIVERED, S.CANCELLED),
    (S.REJECTED, S.APPROVED),
    (S.CANCELLED, S.SUBMITTED),
])
def test_forbidden_status_transitions(start, target):
    order = make_order(status=start)
    with pytest.raises(InvalidStatusTransition):
        order.change_status(target)
    assert order.status == start


def test_final_states_have_no_transitions():
    assert {s for s in OrderStatus if s.is_final} == {S.DELIVERED, S.REJECTED, S.CANCELLED}
    assert set(ALLOWED_TRANSITIONS) == set(OrderStatus)


def test_change_status_accepts_string_values():
    order = make_order()
    order.change_status("approved")
    assert order.status is S.APPROVED
    assert order.allowed_next_statuses() == [S.IN_PREPARATION, S.CANCELLED]


def test_customer_can_only_cancel_submitted_orders():
    assert make_order().can_be_cancelled_by_customer
    assert not make_order(status=S.APPROVED).can_be_cancelled_by_customer


def test_payment_status_is_independent_of_order_status():
    order = make_order()
    for p in PaymentStatus:
        order.change_payment_status(p.value)
        assert order.payment_status == p
    with pytest.raises(ValueError):
        order.change_payment_status("refunded")


# -- order validation and totals ----------------------------------------------

def test_order_total():
    order = make_order(lines=[OrderLine("A", 10, 18900), OrderLine("B", 2, 69000)])
    assert order.total_ore == 10 * 18900 + 2 * 69000


def test_valid_order_passes():
    make_order(guest_groups=[GuestGroup("Nøtteallergi", 3, allergy_notes="Nøtter")]).validate(
        today=date(2027, 1, 1))


@pytest.mark.parametrize("kwargs, field", [
    ({"guest_count": 0}, "guest_count"),
    ({"delivery_address": "  "}, "delivery_address"),
    ({"lines": []}, "lines"),
    ({"guest_groups": [GuestGroup("", 2)]}, "guest_groups"),
    ({"guest_groups": [GuestGroup("Alle", 30)]}, "guest_groups"),  # more than guest_count=20
    ({"event_date": date(2026, 12, 31)}, "event_date"),
])
def test_invalid_orders(kwargs, field):
    with pytest.raises(ValidationError) as exc:
        make_order(**kwargs).validate(today=date(2027, 1, 1))
    assert field in exc.value.errors


# -- food items ------------------------------------------------------------------

def test_food_item_minimum_quantity():
    item = FoodItem(name="Fiskesuppe", price_ore=18900, min_order_qty=10)
    assert not item.accepts_quantity(9)
    assert item.accepts_quantity(10)
    assert item.price_display == "189,00 kr"


@pytest.mark.parametrize("kwargs, field", [
    ({"name": " "}, "name"),
    ({"price_ore": -1}, "price"),
    ({"min_order_qty": 0}, "min_order_qty"),
])
def test_invalid_food_items(kwargs, field):
    data = dict(name="Fiskesuppe", price_ore=18900, min_order_qty=10)
    data.update(kwargs)
    with pytest.raises(ValidationError) as exc:
        FoodItem(**data).validate()
    assert field in exc.value.errors


# -- users and questions ---------------------------------------------------------

def test_password_is_hashed_and_checked():
    user = User.create("Test@Example.TEST", "Test Kunde", "hemmelig-123")
    assert user.email == "test@example.test"
    assert "hemmelig-123" not in user.password_hash
    assert user.check_password("hemmelig-123")
    assert not user.check_password("feil-passord")
    assert not user.is_admin


@pytest.mark.parametrize("email, name, password, field", [
    ("ikke-epost", "Navn", "langt-passord", "email"),
    ("a@example.test", "", "langt-passord", "name"),
    ("a@example.test", "Navn", "kort", "password"),
])
def test_invalid_users(email, name, password, field):
    with pytest.raises(ValidationError) as exc:
        User.create(email, name, password)
    assert field in exc.value.errors


def test_question_answer():
    q = Question(order_id=1, author_id=2, body="Kan dere levere tidligere?")
    assert not q.is_answered
    with pytest.raises(ValidationError):
        q.give_answer("   ", admin_id=1)
    q.give_answer("Ja, kl. 16:30 går fint.", admin_id=1)
    assert q.is_answered and q.answered_by == 1 and q.answered_at


def test_question_cannot_be_answered_twice():
    q = Question(order_id=1, author_id=2, body="Spørsmål")
    q.give_answer("Første svar", admin_id=1)
    with pytest.raises(ValidationError) as exc:
        q.give_answer("Andre svar", admin_id=3)
    assert "allerede besvart" in exc.value.errors["answer"]
    assert q.answer == "Første svar" and q.answered_by == 1


def test_question_length_limits():
    from app.models.question import MAX_ANSWER_LENGTH, MAX_QUESTION_LENGTH
    Question(order_id=1, author_id=2, body="x" * MAX_QUESTION_LENGTH).validate()
    with pytest.raises(ValidationError):
        Question(order_id=1, author_id=2, body="x" * (MAX_QUESTION_LENGTH + 1)).validate()
    with pytest.raises(ValidationError):
        Question(order_id=1, author_id=2, body="?").give_answer("x" * (MAX_ANSWER_LENGTH + 1), admin_id=1)
