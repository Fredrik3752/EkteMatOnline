"""Admin panel for Ekte Mat staff (A1–A4 are added in later phases)."""
from flask import Blueprint, render_template

from app.controllers.auth import admin_required
from app.models.order import OrderStatus
from app.models.repositories.food_item_repository import FoodItemRepository
from app.models.repositories.order_repository import OrderRepository
from app.models.repositories.question_repository import QuestionRepository

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/")
@admin_required
def index():
    orders = OrderRepository().list()
    counts = {status: sum(1 for o in orders if o.status == status) for status in OrderStatus}
    items = FoodItemRepository().list_all()
    return render_template(
        "admin/index.html",
        status_counts=counts,
        order_total=len(orders),
        item_total=len(items),
        published_total=sum(1 for i in items if i.is_published),
        unanswered=len(QuestionRepository().list_all(unanswered_only=True)),
    )
