"""C3: checkout – login, order form with guest groups, receipt."""
from datetime import date, timedelta

import pytest

from app.models.order import OrderStatus, PaymentStatus
from app.models.repositories.food_item_repository import FoodItemRepository
from app.models.repositories.order_repository import OrderRepository
from tests.conftest import cart_in_session, login, post

TOMORROW = (date.today() + timedelta(days=1)).isoformat()
NEXT_MONTH = (date.today() + timedelta(days=30)).isoformat()


def fill_cart(client, items):
    post(client, "/handlekurv/legg-til", {"item_id": items["suppe"].id, "quantity": 20})
    post(client, "/handlekurv/legg-til", {"item_id": items["kake"].id, "quantity": 2})


def order_form(**overrides):
    data = {
        "event_date": NEXT_MONTH,
        "guest_count": "20",
        "delivery_address": "Testveien 1\n5000 Bergen",
        "notes": "Servering kl. 12",
        "group_description": ["Voksne", "Nøtteallergi", ""],
        "group_count": ["17", "3", ""],
        "group_allergies": ["", "Nøtter", ""],
        "group_diets": ["", "", ""],
    }
    data.update(overrides)
    return data


def orders(app):
    with app.app_context():
        return OrderRepository().list()


@pytest.fixture
def shopper(client, customer, menu_items):
    fill_cart(client, menu_items)
    login(client, "kunde@example.test")
    return client


# -- access and preconditions -----------------------------------------------------

def test_checkout_requires_login(client, menu_items):
    fill_cart(client, menu_items)
    response = client.get("/bestilling")
    assert response.status_code == 302
    assert response.headers["Location"].startswith("/logg-inn?next=/bestilling")


def test_cart_survives_login(client, customer, menu_items):
    fill_cart(client, menu_items)
    before = cart_in_session(client)
    response = post(client, "/logg-inn", {"email": "kunde@example.test", "password": "passord-123",
                                          "next": "/bestilling"})
    assert response.headers["Location"] == "/bestilling"
    assert cart_in_session(client) == before
    assert client.get("/bestilling").status_code == 200


def test_cart_survives_registration(client, menu_items):
    fill_cart(client, menu_items)
    post(client, "/registrer", {"name": "Ny", "email": "ny@example.test", "password": "passord-123",
                                "password_confirm": "passord-123", "next": "/bestilling"})
    assert len(cart_in_session(client)) == 2


def test_empty_cart_redirects_to_cart(client, customer):
    login(client, "kunde@example.test")
    response = client.get("/bestilling")
    assert response.status_code == 302 and response.headers["Location"] == "/handlekurv"


def test_form_shows_summary_and_group_rows(shopper):
    html = shopper.get("/bestilling").get_data(as_text=True)
    assert "Fiskesuppe" in html and "20 × Fiskesuppe" in html
    assert "5 160,00 kr" in html  # 20×189 + 2×690
    assert html.count('name="group_description"') == 3
    assert 'value="Alle gjester"' in html
    assert f'min="{TOMORROW}"' in html


# -- successful order -------------------------------------------------------------

def test_submit_order(app, shopper, customer):
    response = post(shopper, "/bestilling", order_form())
    assert response.status_code == 302
    [order] = orders(app)
    assert response.headers["Location"] == f"/bestilling/{order.id}/kvittering"

    assert order.customer_id == customer.id
    assert order.event_date.isoformat() == NEXT_MONTH
    assert order.guest_count == 20 and order.delivery_address == "Testveien 1\n5000 Bergen"
    assert order.status is OrderStatus.SUBMITTED and order.payment_status is PaymentStatus.NOT_PAID
    assert sorted((l.item_name, l.quantity, l.unit_price_ore) for l in order.lines) == [
        ("Bløtkake", 2, 69000), ("Fiskesuppe", 20, 18900)]
    assert [(g.description, g.guest_count, g.allergy_notes) for g in order.guest_groups] == [
        ("Voksne", 17, ""), ("Nøtteallergi", 3, "Nøtter")]
    assert order.total_ore == 20 * 18900 + 2 * 69000
    assert cart_in_session(shopper) == {}


def test_receipt_page(app, shopper):
    post(shopper, "/bestilling", order_form())
    [order] = orders(app)
    html = shopper.get(f"/bestilling/{order.id}/kvittering").get_data(as_text=True)
    assert f"Bestilling nr. {order.id}" in html
    assert "Sendt inn" in html and "Ikke betalt" in html
    assert "Nøtteallergi" in html and "Nøtter" in html


def test_order_keeps_price_when_menu_changes(app, shopper, menu_items):
    post(shopper, "/bestilling", order_form())
    with app.app_context():
        item = menu_items["suppe"]
        item.price_ore = 99900
        FoodItemRepository().update(item)
        order = OrderRepository().list()[0]
    assert {l.item_name: l.unit_price_ore for l in order.lines}["Fiskesuppe"] == 18900


# -- validation -------------------------------------------------------------------

@pytest.mark.parametrize("overrides, message", [
    ({"event_date": ""}, "gyldig dato"),
    ({"event_date": "31.12.2027"}, "gyldig dato"),
    ({"event_date": date.today().isoformat()}, "etter i dag"),
    ({"guest_count": "0"}, "minst 1"),
    ({"guest_count": "mange"}, "minst 1"),
    ({"delivery_address": "  "}, "Leveringsadresse"),
    ({"group_description": ["", "", ""], "group_count": ["", "", ""],
      "group_allergies": ["", "", ""]}, "minst én gjestegruppe"),
    ({"group_count": ["17", "", ""]}, "antall gjester (minst 1)"),
    ({"group_count": ["30", "3", ""]}, "flere gjester enn bestillingen"),
])
def test_invalid_order(app, shopper, overrides, message):
    response = post(shopper, "/bestilling", order_form(**overrides))
    assert response.status_code == 400
    assert message in response.get_data(as_text=True)
    assert orders(app) == []
    assert len(cart_in_session(shopper)) == 2  # cart is kept


def test_invalid_order_keeps_entered_values(shopper):
    html = post(shopper, "/bestilling", order_form(event_date="")).get_data(as_text=True)
    assert 'value="Nøtteallergi"' in html and 'value="Nøtter"' in html
    assert "Servering kl. 12" in html


def test_minimum_raised_blocks_checkout(app, shopper, menu_items):
    with app.app_context():
        item = menu_items["suppe"]
        item.min_order_qty = 50
        FoodItemRepository().update(item)
    response = post(shopper, "/bestilling", order_form())
    assert response.status_code == 302 and response.headers["Location"] == "/handlekurv"
    assert orders(app) == []


def test_checkout_requires_csrf(app, shopper):
    data = order_form()
    response = shopper.post("/bestilling", data=data)
    assert response.status_code == 400
    assert orders(app) == []


# -- receipt access ---------------------------------------------------------------

def test_receipt_only_for_owner(app, client, make_user, menu_items):
    make_user("a@example.test", "Kunde A")
    make_user("b@example.test", "Kunde B")
    fill_cart(client, menu_items)
    login(client, "a@example.test")
    post(client, "/bestilling", order_form())
    [order] = orders(app)

    post(client, "/logg-ut")
    login(client, "b@example.test")
    assert client.get(f"/bestilling/{order.id}/kvittering").status_code == 404
    assert client.get("/bestilling/999/kvittering").status_code == 404


def test_receipt_requires_login(client):
    assert client.get("/bestilling/1/kvittering").status_code == 302
