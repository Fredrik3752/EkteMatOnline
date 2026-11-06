"""A1: admin management of food items."""
from datetime import date

import pytest

from app.models.order import Order, OrderLine
from app.models.repositories.database import get_db
from app.models.repositories.event_category_repository import EventCategoryRepository
from app.models.repositories.food_item_repository import FoodItemRepository
from app.models.repositories.order_repository import OrderRepository
from app.models.repositories.reference_repository import AllergenRepository, DietaryLabelRepository
from tests.conftest import login, post


@pytest.fixture
def admin_client(client, admin):
    login(client, "admin@example.test")
    return client


@pytest.fixture
def ids(app):
    with app.app_context():
        return {
            "cat": {c.slug: c.id for c in EventCategoryRepository().list_all()},
            "all": {a.code: a.id for a in AllergenRepository().list_all()},
            "diet": {d.code: d.id for d in DietaryLabelRepository().list_all()},
        }


def form_data(ids, **overrides):
    data = {
        "name": "Fiskesuppe", "description": "Med torsk", "price": "189,50", "min_order_qty": "10",
        "origin": "Torsk fra Bergen", "is_published": "1",
        "categories": [ids["cat"]["wedding"], ids["cat"]["conference"]],
        "allergens": [ids["all"]["fish"], ids["all"]["milk"]],
        "dietary_labels": [ids["diet"]["gluten-free"]],
    }
    data.update(overrides)
    return data


def all_items(app):
    with app.app_context():
        return FoodItemRepository().list_all()


def create_item(app, ids, **overrides):
    with app.app_context():
        from app.models.food_item import FoodItem
        cats = {c.id: c for c in EventCategoryRepository().list_all()}
        data = dict(name="Lam", price_ore=24500, min_order_qty=15, is_published=True,
                    image_path="uploads/lam.jpg", categories=[cats[ids["cat"]["wedding"]]])
        data.update(overrides)
        return FoodItemRepository().add(FoodItem(**data))


# -- access -------------------------------------------------------------------

ADMIN_URLS = ["/admin/matretter", "/admin/matretter/ny"]


@pytest.mark.parametrize("url", ADMIN_URLS)
def test_anonymous_is_redirected_to_login(client, url):
    response = client.get(url)
    assert response.status_code == 302 and "/logg-inn" in response.headers["Location"]


@pytest.mark.parametrize("url", ADMIN_URLS)
def test_customer_is_forbidden(client, customer, url):
    login(client, "kunde@example.test")
    assert client.get(url).status_code == 403


def test_customer_cannot_delete(app, client, customer, ids):
    item = create_item(app, ids)
    login(client, "kunde@example.test")
    assert post(client, f"/admin/matretter/{item.id}/slett").status_code == 403
    assert len(all_items(app)) == 1


# -- list and create -----------------------------------------------------------

def test_list_shows_items(app, admin_client, ids):
    create_item(app, ids, name="Lam", is_published=True)
    create_item(app, ids, name="Kladdrett", is_published=False)
    html = admin_client.get("/admin/matretter").get_data(as_text=True)
    assert "Lam" in html and "Kladdrett" in html
    assert "Publisert" in html and "Skjult" in html
    assert "245,00" in html


def test_new_form_renders_all_choices(admin_client):
    html = admin_client.get("/admin/matretter/ny").get_data(as_text=True)
    for text in ("Bryllup", "Julebord", "Nøtter", "Bløtdyr", "Vegansk", 'name="price"', 'name="csrf_token"'):
        assert text in html


def test_create_item(app, admin_client, ids):
    response = post(admin_client, "/admin/matretter/ny", form_data(ids))
    assert response.status_code == 302 and response.headers["Location"] == "/admin/matretter"
    [item] = all_items(app)
    assert item.name == "Fiskesuppe" and item.price_ore == 18950 and item.min_order_qty == 10
    assert item.is_published and item.origin == "Torsk fra Bergen"
    assert {c.slug for c in item.categories} == {"wedding", "conference"}
    assert {a.code for a in item.allergens} == {"fish", "milk"}
    assert [d.code for d in item.dietary_labels] == ["gluten-free"]


def test_create_unpublished_when_box_unchecked(app, admin_client, ids):
    data = form_data(ids)
    del data["is_published"]
    post(admin_client, "/admin/matretter/ny", data)
    assert all_items(app)[0].is_published is False


@pytest.mark.parametrize("overrides, message", [
    ({"name": "  "}, "Navn må fylles ut"),
    ({"price": "gratis"}, "gyldig pris"),
    ({"price": "-10"}, "gyldig pris"),
    ({"min_order_qty": "0"}, "Minimum bestilling"),
    ({"min_order_qty": "ti"}, "Minimum bestilling"),
    ({"categories": []}, "minst ett arrangement"),
])
def test_create_invalid_item(app, admin_client, ids, overrides, message):
    response = post(admin_client, "/admin/matretter/ny", form_data(ids, **overrides))
    assert response.status_code == 400
    assert message in response.get_data(as_text=True)
    assert all_items(app) == []


def test_invalid_form_keeps_entered_values(admin_client, ids):
    html = post(admin_client, "/admin/matretter/ny",
                form_data(ids, price="abc", name="Min rett")).get_data(as_text=True)
    assert 'value="Min rett"' in html and 'value="abc"' in html
    assert f'value="{ids["all"]["fish"]}" checked' in html


# -- edit, publish, delete -------------------------------------------------------

def test_edit_form_is_prefilled(app, admin_client, ids):
    item = create_item(app, ids, price_ore=24550)
    html = admin_client.get(f"/admin/matretter/{item.id}/rediger").get_data(as_text=True)
    assert 'value="Lam"' in html and 'value="245,50"' in html and 'value="15"' in html
    assert f'value="{ids["cat"]["wedding"]}" checked' in html


def test_edit_item_keeps_image(app, admin_client, ids):
    item = create_item(app, ids)
    data = form_data(ids, name="Lam deluxe", price="300", categories=[ids["cat"]["christmas-party"]],
                     allergens=[], dietary_labels=[])
    response = post(admin_client, f"/admin/matretter/{item.id}/rediger", data)
    assert response.status_code == 302
    [updated] = all_items(app)
    assert updated.name == "Lam deluxe" and updated.price_ore == 30000
    assert [c.slug for c in updated.categories] == ["christmas-party"]
    assert updated.allergens == [] and updated.image_path == "uploads/lam.jpg"


def test_edit_invalid_does_not_change_item(app, admin_client, ids):
    item = create_item(app, ids)
    response = post(admin_client, f"/admin/matretter/{item.id}/rediger", form_data(ids, price=""))
    assert response.status_code == 400
    assert all_items(app)[0].price_ore == 24500


def test_toggle_published(app, admin_client, ids):
    item = create_item(app, ids, is_published=True)
    post(admin_client, f"/admin/matretter/{item.id}/publiser")
    assert all_items(app)[0].is_published is False
    post(admin_client, f"/admin/matretter/{item.id}/publiser")
    assert all_items(app)[0].is_published is True


def test_delete_item(app, admin_client, ids):
    item = create_item(app, ids)
    response = post(admin_client, f"/admin/matretter/{item.id}/slett")
    assert response.status_code == 302
    assert all_items(app) == []


def test_delete_requires_post_and_csrf(app, admin_client, ids):
    item = create_item(app, ids)
    assert admin_client.get(f"/admin/matretter/{item.id}/slett").status_code == 405
    assert admin_client.post(f"/admin/matretter/{item.id}/slett").status_code == 400
    assert len(all_items(app)) == 1


def test_deleted_item_stays_on_existing_orders(app, admin_client, customer, ids):
    item = create_item(app, ids)
    with app.app_context():
        order = OrderRepository().add(Order(
            customer_id=customer.id, event_date=date(2027, 5, 1), guest_count=20,
            delivery_address="Testveien 1",
            lines=[OrderLine(item.name, 20, item.price_ore, food_item_id=item.id)]))
    post(admin_client, f"/admin/matretter/{item.id}/slett")
    with app.app_context():
        line = OrderRepository().get(order.id).lines[0]
        assert line.item_name == "Lam" and line.unit_price_ore == 24500 and line.food_item_id is None
        assert get_db().execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 1


@pytest.mark.parametrize("method, url", [
    ("get", "/admin/matretter/999/rediger"),
    ("post", "/admin/matretter/999/rediger"),
    ("post", "/admin/matretter/999/publiser"),
    ("post", "/admin/matretter/999/slett"),
])
def test_unknown_item_returns_404(admin_client, method, url):
    response = admin_client.get(url) if method == "get" else post(admin_client, url)
    assert response.status_code == 404


def test_item_name_is_escaped_in_list(app, admin_client, ids):
    create_item(app, ids, name="O'Brien <script>alert(1)</script>")
    html = admin_client.get("/admin/matretter").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in html
