"""Customer-facing shop: front page and menu by event (C1). Cart/checkout come later."""
from flask import Blueprint, abort, render_template

from app.models.repositories.event_category_repository import EventCategoryRepository
from app.models.repositories.food_item_repository import FoodItemRepository

bp = Blueprint("shop", __name__)


@bp.route("/")
def index():
    categories = EventCategoryRepository().list_all()
    return render_template("shop/index.html", categories=categories)


@bp.route("/meny")
def menu():
    groups = FoodItemRepository().list_published_by_category()
    return render_template("shop/menu.html", groups=groups,
                           categories=EventCategoryRepository().list_all(), current=None)


@bp.route("/meny/<slug>")
def menu_category(slug):
    category = EventCategoryRepository().get_by_slug(slug)
    if category is None:
        abort(404)
    items = FoodItemRepository().list_published_in_category(category.id)
    return render_template("shop/menu.html", groups={category: items},
                           categories=EventCategoryRepository().list_all(), current=category)
