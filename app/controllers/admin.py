"""Admin panel for Ekte Mat staff: overview, food items (A1), orders (A3) and questions (A4)."""
from datetime import date

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from app.controllers.auth import admin_required, is_safe_next
from app.models.errors import InvalidStatusTransition, ValidationError
from app.models.food_item import FoodItem
from app.models.money import nok_to_ore
from app.models.order import OrderStatus, PaymentStatus
from app.models.repositories.event_category_repository import EventCategoryRepository
from app.models.repositories.food_item_repository import FoodItemRepository
from app.models.repositories.order_repository import OrderRepository
from app.models.repositories.question_repository import QuestionRepository
from app.models.repositories.reference_repository import AllergenRepository, DietaryLabelRepository
from app.models.repositories.user_repository import UserRepository

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


# -- A1: food items -------------------------------------------------------------

def _choices():
    return {
        "categories": EventCategoryRepository().list_all(),
        "allergens": AllergenRepository().list_all(),
        "dietary_labels": DietaryLabelRepository().list_all(),
    }


def _selected(options, field):
    ids = {int(v) for v in request.form.getlist(field) if v.isdigit()}
    return [o for o in options if o.id in ids]


def _item_from_form(choices, existing=None):
    """Build a FoodItem from the submitted form. Returns (item, errors)."""
    form = request.form
    errors = {}
    try:
        price_ore = nok_to_ore(form.get("price", ""))
    except ValueError:
        price_ore = -1
        errors["price"] = "Oppgi en gyldig pris i kroner, f.eks. 189 eller 189,50."
    min_text = form.get("min_order_qty", "").strip()
    min_qty = int(min_text) if min_text.isdigit() else 0

    item = FoodItem(
        id=existing.id if existing else None,
        name=form.get("name", "").strip(),
        description=form.get("description", "").strip(),
        price_ore=price_ore,
        min_order_qty=min_qty,
        origin=form.get("origin", "").strip() or None,
        is_published=form.get("is_published") == "1",
        image_path=existing.image_path if existing else None,
        categories=_selected(choices["categories"], "categories"),
        allergens=_selected(choices["allergens"], "allergens"),
        dietary_labels=_selected(choices["dietary_labels"], "dietary_labels"),
    )
    try:
        item.validate()
    except ValidationError as exc:
        errors = {**exc.errors, **errors}
    if not item.categories:
        errors["categories"] = "Velg minst ett arrangement retten passer for."
    return item, errors


def _get_item_or_404(item_id):
    item = FoodItemRepository().get(item_id)
    if item is None:
        abort(404)
    return item


@bp.route("/matretter")
@admin_required
def food_items():
    return render_template("admin/food_items.html", items=FoodItemRepository().list_all())


@bp.route("/matretter/ny", methods=["GET", "POST"])
@admin_required
def food_item_new():
    choices = _choices()
    item, errors = FoodItem(name="", price_ore=0, min_order_qty=1), {}
    if request.method == "POST":
        item, errors = _item_from_form(choices)
        if not errors:
            saved = FoodItemRepository().add(item)
            flash(f"«{saved.name}» er lagt til.", "success")
            return redirect(url_for("admin.food_items"))
    return render_template("admin/food_item_form.html", item=item, errors=errors, is_new=True,
                           form=request.form, **choices), (400 if errors else 200)


@bp.route("/matretter/<int:item_id>/rediger", methods=["GET", "POST"])
@admin_required
def food_item_edit(item_id):
    existing = _get_item_or_404(item_id)
    choices = _choices()
    item, errors = existing, {}
    if request.method == "POST":
        item, errors = _item_from_form(choices, existing)
        if not errors:
            saved = FoodItemRepository().update(item)
            flash(f"«{saved.name}» er oppdatert.", "success")
            return redirect(url_for("admin.food_items"))
    return render_template("admin/food_item_form.html", item=item, errors=errors, is_new=False,
                           form=request.form, **choices), (400 if errors else 200)


@bp.route("/matretter/<int:item_id>/publiser", methods=["POST"])
@admin_required
def food_item_toggle_published(item_id):
    item = _get_item_or_404(item_id)
    item.is_published = not item.is_published
    FoodItemRepository().update(item)
    flash(f"«{item.name}» er {'publisert' if item.is_published else 'skjult fra menyen'}.", "success")
    return redirect(url_for("admin.food_items"))


@bp.route("/matretter/<int:item_id>/slett", methods=["POST"])
@admin_required
def food_item_delete(item_id):
    item = _get_item_or_404(item_id)
    FoodItemRepository().delete(item.id)
    flash(f"«{item.name}» er slettet. Eksisterende ordrer beholder navn og pris.", "success")
    return redirect(url_for("admin.food_items"))


# -- A3: orders -------------------------------------------------------------------

def _order_filters():
    """Read ?status=&fra=&til=. Invalid values are dropped with a message."""
    args, filters, problems = request.args, {}, []
    status = args.get("status", "").strip()
    if status:
        try:
            filters["status"] = OrderStatus(status)
        except ValueError:
            problems.append("Ukjent status")
    for arg, key in (("fra", "date_from"), ("til", "date_to")):
        value = args.get(arg, "").strip()
        if value:
            try:
                filters[key] = date.fromisoformat(value)
            except ValueError:
                problems.append(f"Ugyldig dato i «{arg}»")
    if problems:
        flash(", ".join(problems) + " – filteret er ignorert.", "error")
    return filters


def _get_order_or_404(order_id):
    order = OrderRepository().get(order_id)
    if order is None:
        abort(404)
    return order


@bp.route("/ordrer")
@admin_required
def orders():
    filters = _order_filters()
    order_list = OrderRepository().list(**filters)
    customers = UserRepository().get_many(o.customer_id for o in order_list)
    return render_template("admin/orders.html", orders=order_list, customers=customers,
                           filters=filters, statuses=list(OrderStatus))


@bp.route("/ordrer/<int:order_id>")
@admin_required
def order_detail(order_id):
    order = _get_order_or_404(order_id)
    customer = UserRepository().get(order.customer_id)
    return render_template("admin/order_detail.html", order=order, customer=customer,
                           payment_statuses=list(PaymentStatus),
                           questions=QuestionRepository().list_for_order(order.id))


@bp.route("/ordrer/<int:order_id>/status", methods=["POST"])
@admin_required
def order_status(order_id):
    order = _get_order_or_404(order_id)
    try:
        new_status = OrderStatus(request.form.get("status", ""))
        order.change_status(new_status)
    except ValueError:
        flash("Ukjent status.", "error")
    except InvalidStatusTransition as exc:
        flash(str(exc), "error")
    else:
        OrderRepository().save_status(order)
        flash(f"Ordre {order.id} har nå status «{new_status.label}».", "success")
    return redirect(url_for("admin.order_detail", order_id=order.id))


@bp.route("/ordrer/<int:order_id>/betaling", methods=["POST"])
@admin_required
def order_payment(order_id):
    order = _get_order_or_404(order_id)
    try:
        order.change_payment_status(request.form.get("payment_status", ""))
    except ValueError:
        flash("Ukjent betalingsstatus.", "error")
    else:
        OrderRepository().save_status(order)
        flash(f"Betalingsstatus for ordre {order.id} er «{order.payment_status.label}».", "success")
    return redirect(url_for("admin.order_detail", order_id=order.id))


# -- A4: questions ------------------------------------------------------------------

def unanswered_count():
    """Jinja global for the admin menu badge."""
    return QuestionRepository().count_unanswered()


@bp.route("/sporsmal")
@admin_required
def questions():
    show_all = request.args.get("vis") == "alle"
    question_list = QuestionRepository().list_all(unanswered_only=not show_all)
    if not show_all:
        question_list.reverse()  # oldest unanswered first – answer in the order they came in
    authors = UserRepository().get_many(q.author_id for q in question_list)
    return render_template("admin/questions.html", questions=question_list, authors=authors,
                           show_all=show_all)


@bp.route("/sporsmal/<int:question_id>/svar", methods=["POST"])
@admin_required
def answer_question(question_id):
    repo = QuestionRepository()
    question = repo.get(question_id)
    if question is None:
        abort(404)
    try:
        question.give_answer(request.form.get("answer", ""), admin_id=g.user.id)
    except ValidationError as exc:
        flash(exc.errors["answer"], "error")
    else:
        repo.save_answer(question)
        flash(f"Svaret på spørsmålet om ordre {question.order_id} er sendt.", "success")
    target = request.form.get("next", "")
    return redirect(target if is_safe_next(target) else url_for("admin.questions"))
