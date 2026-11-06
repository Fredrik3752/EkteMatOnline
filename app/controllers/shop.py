"""Customer-facing shop: front page (later: menu, cart, checkout)."""
from flask import Blueprint, render_template

from app.models.repositories.event_category_repository import EventCategoryRepository

bp = Blueprint("shop", __name__)


@bp.route("/")
def index():
    categories = EventCategoryRepository().list_all()
    return render_template("shop/index.html", categories=categories)
