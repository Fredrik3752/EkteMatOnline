"""C1: menu by event, as cards."""
import pytest

from app.models.food_item import FoodItem
from app.models.repositories.event_category_repository import EventCategoryRepository
from app.models.repositories.food_item_repository import FoodItemRepository
from app.models.repositories.reference_repository import AllergenRepository


@pytest.fixture
def items(app):
    with app.app_context():
        cats = {c.slug: c for c in EventCategoryRepository().list_all()}
        alls = {a.code: a for a in AllergenRepository().list_all()}
        repo = FoodItemRepository()
        return {
            "lam": repo.add(FoodItem(
                name="Vossalam", price_ore=24500, min_order_qty=15, is_published=True,
                origin="Småbruk på Voss", categories=[cats["wedding"], cats["christmas-party"]],
                allergens=[alls["milk"], alls["celery"]])),
            "kake": repo.add(FoodItem(
                name="Bløtkake", price_ore=69000, min_order_qty=1, is_published=True,
                categories=[cats["birthday"]], allergens=[alls["eggs"]])),
            "kladd": repo.add(FoodItem(
                name="Hemmelig kladd", price_ore=10000, is_published=False,
                categories=[cats["wedding"]])),
        }


def test_menu_shows_published_items_as_cards(client, items):
    html = client.get("/meny").get_data(as_text=True)
    assert "Vossalam" in html and "Bløtkake" in html
    assert "Hemmelig kladd" not in html
    assert html.count('class="food-card"') == 3  # Vossalam in two categories + Bløtkake


def test_menu_groups_by_event_in_category_order(client, items):
    html = client.get("/meny").get_data(as_text=True)
    birthday, wedding, julebord = (html.index(f'id="{s}"') for s in ("birthday", "wedding", "christmas-party"))
    assert birthday < wedding < julebord
    assert 'id="conference"' not in html  # no published items for conference


def test_card_shows_price_minimum_allergens_origin(client, items):
    html = client.get("/meny/wedding").get_data(as_text=True)
    assert "245,00 kr" in html
    assert "15 stk." in html
    assert "Melk" in html and "Selleri" in html
    assert "Småbruk på Voss" in html
    assert "food-image placeholder" in html  # no picture yet


def test_card_uses_uploaded_image(app, client, items):
    with app.app_context():
        item = items["kake"]
        item.image_path = "uploads/kake.jpg"
        FoodItemRepository().update(item)
    assert 'src="/static/uploads/kake.jpg"' in client.get("/meny/birthday").get_data(as_text=True)


def test_menu_category_filters(client, items):
    html = client.get("/meny/birthday").get_data(as_text=True)
    assert "Bløtkake" in html and "Vossalam" not in html
    assert "Meny for bursdag" in html


def test_empty_category_has_message(client, items):
    response = client.get("/meny/conference")
    assert response.status_code == 200
    assert "ingen retter" in response.get_data(as_text=True)


def test_unknown_category_is_404(client):
    assert client.get("/meny/finnes-ikke").status_code == 404


def test_front_page_links_to_categories(client):
    html = client.get("/").get_data(as_text=True)
    assert 'href="/meny/wedding"' in html and 'href="/meny"' in html


def test_menu_works_without_login_and_when_empty(client):
    response = client.get("/meny")
    assert response.status_code == 200
    assert "Menyen er tom" in response.get_data(as_text=True)
