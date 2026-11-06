"""C2: shopping cart – domain rules and routes."""
import pytest

from app.models.cart import MAX_QUANTITY, Cart, check_quantity
from app.models.errors import ValidationError
from app.models.food_item import FoodItem
from app.models.repositories.food_item_repository import FoodItemRepository
from tests.conftest import cart_in_session, post

SUPPE = FoodItem(id=1, name="Fiskesuppe", price_ore=18900, min_order_qty=10, is_published=True)
KAKE = FoodItem(id=2, name="Bløtkake", price_ore=69000, min_order_qty=1, is_published=True)
SKJULT = FoodItem(id=3, name="Skjult", price_ore=100, is_published=False)


# -- domain ---------------------------------------------------------------------

@pytest.mark.parametrize("qty, ok", [(10, True), ("12", True), (9, False), (0, False), (-1, False),
                                     ("tre", False), ("", False), (MAX_QUANTITY + 1, False)])
def test_check_quantity(qty, ok):
    if ok:
        assert check_quantity(SUPPE, qty) == int(qty)
    else:
        with pytest.raises(ValidationError):
            check_quantity(SUPPE, qty)


def test_check_quantity_message_names_minimum():
    with pytest.raises(ValidationError) as exc:
        check_quantity(SUPPE, 5)
    assert "Minimum bestilling for «Fiskesuppe» er 10 stk." == exc.value.errors["quantity"]


def test_cart_build_and_total():
    cart = Cart.build({"1": 10, "2": 2}, {1: SUPPE, 2: KAKE})
    assert [line.item.name for line in cart.lines] == ["Bløtkake", "Fiskesuppe"]
    assert cart.total_ore == 10 * 18900 + 2 * 69000
    assert cart.item_count == 2 and not cart.is_empty and cart.problems() == []


def test_cart_drops_unpublished_and_missing_items():
    cart = Cart.build({"1": 10, "3": 1, "99": 4}, {1: SUPPE, 3: SKJULT})
    assert [line.item.id for line in cart.lines] == [1]
    assert cart.removed == ["Skjult", "#99"]
    assert cart.to_quantities() == {"1": 10}


def test_cart_problems_when_minimum_raised():
    cart = Cart.build({"1": 5}, {1: SUPPE})
    assert cart.problems() == ["«Fiskesuppe» krever minst 10 stk. – du har 5."]


def test_cart_to_order_lines_copies_name_and_price():
    [line] = Cart.build({"1": 12}, {1: SUPPE}).to_order_lines()
    assert (line.food_item_id, line.item_name, line.quantity, line.unit_price_ore) == (1, "Fiskesuppe", 12, 18900)


# -- routes -----------------------------------------------------------------------

def add(client, item, quantity, **extra):
    return post(client, "/handlekurv/legg-til", {"item_id": item.id, "quantity": quantity, **extra})


def test_empty_cart_page(client):
    html = client.get("/handlekurv").get_data(as_text=True)
    assert "Handlekurven er tom" in html


def test_add_to_cart(client, menu_items):
    response = add(client, menu_items["suppe"], 10)
    assert response.status_code == 302 and response.headers["Location"] == "/handlekurv"
    assert cart_in_session(client) == {str(menu_items["suppe"].id): 10}


def test_add_below_minimum_is_rejected(client, menu_items):
    response = add(client, menu_items["suppe"], 9)
    assert response.status_code == 302
    assert cart_in_session(client) == {}
    html = client.get("/handlekurv").get_data(as_text=True)
    assert "Minimum bestilling for «Fiskesuppe» er 10 stk." in html


@pytest.mark.parametrize("quantity", ["0", "-3", "abc", ""])
def test_add_invalid_quantity(client, menu_items, quantity):
    add(client, menu_items["kake"], quantity)
    assert cart_in_session(client) == {}


def test_add_accumulates_quantity(client, menu_items):
    add(client, menu_items["suppe"], 10)
    add(client, menu_items["suppe"], 5)  # 15 in total – fine even though 5 < minimum
    assert cart_in_session(client) == {str(menu_items["suppe"].id): 15}


def test_add_returns_to_safe_next(client, menu_items):
    assert add(client, menu_items["kake"], 1, next="/meny/wedding").headers["Location"] == "/meny/wedding"
    assert add(client, menu_items["kake"], 1, next="https://evil.example").headers["Location"] == "/handlekurv"


@pytest.mark.parametrize("key", ["kladd", None])
def test_add_unpublished_or_unknown_item_is_404(client, menu_items, key):
    item_id = menu_items[key].id if key else 999
    response = post(client, "/handlekurv/legg-til", {"item_id": item_id, "quantity": 1})
    assert response.status_code == 404


def test_add_requires_csrf(client, menu_items):
    response = client.post("/handlekurv/legg-til", data={"item_id": menu_items["kake"].id, "quantity": 1})
    assert response.status_code == 400


def test_cart_page_shows_lines_and_total(client, menu_items):
    add(client, menu_items["suppe"], 10)
    add(client, menu_items["kake"], 2)
    html = client.get("/handlekurv").get_data(as_text=True)
    assert "Fiskesuppe" in html and "Bløtkake" in html
    assert "1 890,00 kr" in html            # 10 × 189
    assert "3 270,00 kr" in html            # 1890 + 1380
    assert "Gå til bestilling" in html


def test_nav_shows_cart_count(client, menu_items):
    add(client, menu_items["suppe"], 10)
    add(client, menu_items["kake"], 1)
    assert '<span class="cart-count">2</span>' in client.get("/").get_data(as_text=True)


def test_update_quantity(client, menu_items):
    add(client, menu_items["suppe"], 10)
    post(client, "/handlekurv/oppdater", {"item_id": menu_items["suppe"].id, "quantity": 25})
    assert cart_in_session(client) == {str(menu_items["suppe"].id): 25}


def test_update_below_minimum_keeps_old_quantity(client, menu_items):
    add(client, menu_items["suppe"], 10)
    post(client, "/handlekurv/oppdater", {"item_id": menu_items["suppe"].id, "quantity": 3})
    assert cart_in_session(client) == {str(menu_items["suppe"].id): 10}


def test_update_item_not_in_cart_is_404(client, menu_items):
    response = post(client, "/handlekurv/oppdater", {"item_id": menu_items["kake"].id, "quantity": 2})
    assert response.status_code == 404


def test_remove_item(client, menu_items):
    add(client, menu_items["suppe"], 10)
    add(client, menu_items["kake"], 1)
    post(client, "/handlekurv/fjern", {"item_id": menu_items["suppe"].id})
    assert cart_in_session(client) == {str(menu_items["kake"].id): 1}


def test_unpublished_item_is_removed_from_cart(app, client, menu_items):
    add(client, menu_items["kake"], 1)
    with app.app_context():
        item = menu_items["kake"]
        item.is_published = False
        FoodItemRepository().update(item)
    html = client.get("/handlekurv").get_data(as_text=True)
    assert "ikke lenger tilgjengelige" in html and "Bløtkake" in html
    assert cart_in_session(client) == {}


def test_raised_minimum_blocks_checkout_button(app, client, menu_items):
    add(client, menu_items["kake"], 2)
    with app.app_context():
        item = menu_items["kake"]
        item.min_order_qty = 5
        FoodItemRepository().update(item)
    html = client.get("/handlekurv").get_data(as_text=True)
    assert "krever minst 5 stk." in html
    assert "Gå til bestilling" not in html


def test_menu_cards_have_add_to_cart_form(client, menu_items):
    html = client.get("/meny/wedding").get_data(as_text=True)
    assert 'action="/handlekurv/legg-til"' in html
    assert f'name="item_id" value="{menu_items["suppe"].id}"' in html
    assert 'value="10"' in html  # quantity pre-filled with the minimum


def test_menu_quantity_field_ids_are_unique(client, menu_items):
    import re
    html = client.get("/meny").get_data(as_text=True)
    ids = re.findall(r'id="(qty-[^"]+)"', html)
    assert ids and len(ids) == len(set(ids))
