"""Seed the database with SYNTHETIC data only.

All people, companies and addresses below are invented. Nothing is read from
the data pack's customer or order exports. Test passwords come from .env
(see .env.example) so they are not hard-coded in the app.
"""
import os
from datetime import date, timedelta

import click
from flask.cli import with_appcontext

from app.models.food_item import FoodItem
from app.models.order import GuestGroup, Order, OrderLine, OrderStatus, PaymentStatus
from app.models.question import Question
from app.models.repositories.database import init_db
from app.models.repositories.event_category_repository import EventCategoryRepository
from app.models.repositories.food_item_repository import FoodItemRepository
from app.models.repositories.image_store import ImageStore
from app.models.repositories.order_repository import OrderRepository
from app.models.repositories.question_repository import QuestionRepository
from app.models.repositories.reference_repository import AllergenRepository, DietaryLabelRepository
from app.models.repositories.user_repository import UserRepository
from app.models.user import ROLE_ADMIN, User

DEFAULT_ADMIN_PASSWORD = "admin-test-1234"
DEFAULT_CUSTOMER_PASSWORD = "kunde-test-1234"

ADMIN = {"email": "admin@ektemat.example.test", "name": "Admin Testbruker"}
CUSTOMERS = [
    {"email": "kari.testkunde@example.test", "name": "Kari Testkunde"},
    {"email": "bedrift.test@example.test", "name": "Fjelltest AS (testbedrift)"},
]

# (name, description, price NOK, min qty, categories, allergens, diets, origin, published)
FOOD_ITEMS = [
    ("Fiskesuppe", "Kremet fiskesuppe med torsk, rotgrønnsaker og surdeigsbrød.",
     189, 10, ["conference", "corporate-lunch", "memorial"], ["fish", "milk", "gluten", "celery"], [],
     "Torsk fra kystfiske utenfor Bergen", True),
    ("Langtidsbakt lam med byggrisotto", "Lammeskulder bakt i 12 timer, servert med byggrisotto.",
     245, 15, ["wedding", "confirmation", "christmas-party"], ["milk", "gluten", "celery"], ["lactose-free"],
     "Lam fra småbruk på Voss", True),
    ("Rødbet- og kikertsalat", "Bakte rødbeter, kikerter og geitost fra Hardanger.",
     165, 10, ["conference", "corporate-lunch", "birthday"], ["milk", "mustard"], ["vegetarian", "gluten-free"],
     "Geitost fra Hardanger", True),
    ("Rakfisksmaking", "Sesongrett i november: rakfisk med lefse, løk og rømme.",
     210, 10, ["christmas-party"], ["fish", "milk", "gluten"], [],
     "Ørret fra Valdres", True),
    ("Ribbe med tilbehør", "Julebordklassiker med surkål, rødkål, medisterkaker og saus.",
     395, 20, ["christmas-party"], ["gluten", "milk", "celery", "mustard"], [],
     "Svin fra Jæren", True),
    ("Pinnekjøtt", "Røkt og tørket lammeribbe med kålrabistappe og poteter.",
     425, 20, ["christmas-party"], ["milk"], ["gluten-free"],
     "Lam fra Vestlandet", True),
    ("Tapasfat", "Spekemat, oster, oliven, hummus og brød – passer til stående mingling.",
     159, 10, ["birthday", "confirmation", "wedding", "conference"], ["milk", "gluten", "sesame", "nuts"], [],
     None, True),
    ("Bløtkake (12 stykker)", "Klassisk bløtkake med vaniljekrem og norske jordbær.",
     690, 1, ["birthday", "confirmation", "wedding"], ["eggs", "milk", "gluten"], ["vegetarian"],
     "Jordbær fra Sogn", True),
    ("Bryllupsmeny – tre retter", "Forrett, hovedrett og dessert. Menyen avtales med kjøkkensjefen.",
     895, 30, ["wedding"], ["fish", "milk", "gluten", "eggs", "nuts"], [],
     "Råvarer fra Vestlandet", True),
    ("Påsmurt lunsjbaguette", "Baguetter med kylling, ost/skinke eller hummus og grønnsaker.",
     95, 10, ["conference", "corporate-lunch"], ["gluten", "milk", "eggs", "mustard"], [],
     None, True),
    ("Vegansk linsegryte", "Krydret gryte med røde linser, søtpotet og kokos. Serveres med ris.",
     175, 10, ["conference", "corporate-lunch", "birthday"], ["celery"], ["vegan", "vegetarian", "gluten-free", "lactose-free"],
     None, True),
    ("Kaffe og te (per person)", "Kaffe, te og melk servert på termos.",
     35, 10, ["conference", "corporate-lunch", "memorial", "confirmation"], ["milk"], ["vegetarian"],
     None, True),
    ("Vinterens viltgryte (kladd)", "Ikke publisert ennå – venter på leverandøravtale.",
     289, 15, ["christmas-party", "wedding"], ["milk", "celery"], ["gluten-free"],
     "Hjort fra Sunnfjord", False),
]


def seed_database(today=None):
    """Reset the database and insert synthetic sample data. Returns a summary dict."""
    today = today or date.today()
    init_db()
    ImageStore().delete_all_public()  # uploads belonged to the items we just deleted

    users = UserRepository()
    admin_pw = os.environ.get("SEED_ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)
    customer_pw = os.environ.get("SEED_CUSTOMER_PASSWORD", DEFAULT_CUSTOMER_PASSWORD)
    admin = users.add(User.create(password=admin_pw, role=ROLE_ADMIN, **ADMIN))
    customers = [users.add(User.create(password=customer_pw, **c)) for c in CUSTOMERS]

    categories = {c.slug: c for c in EventCategoryRepository().list_all()}
    allergens = {a.code: a for a in AllergenRepository().list_all()}
    diets = {d.code: d for d in DietaryLabelRepository().list_all()}

    food_repo = FoodItemRepository()
    items = {}
    for name, desc, price, min_qty, cats, alls, dts, origin, published in FOOD_ITEMS:
        item = food_repo.add(FoodItem(
            name=name, description=desc, price_ore=price * 100, min_order_qty=min_qty,
            categories=[categories[c] for c in cats], allergens=[allergens[a] for a in alls],
            dietary_labels=[diets[d] for d in dts], origin=origin, is_published=published,
        ))
        items[name] = item

    def line(name, qty):
        item = items[name]
        return OrderLine(food_item_id=item.id, item_name=item.name, quantity=qty, unit_price_ore=item.price_ore)

    orders = OrderRepository()
    kari, company = customers

    wedding = orders.add(Order(
        customer_id=kari.id, event_date=today + timedelta(days=60), guest_count=80,
        delivery_address="Testveien 1, 5000 Bergen",
        lines=[line("Bryllupsmeny – tre retter", 80), line("Bløtkake (12 stykker)", 7)],
        guest_groups=[
            GuestGroup("Voksne uten spesielle behov", 70),
            GuestGroup("Gjester med nøtteallergi", 6, allergy_notes="Nøtter (alvorlig)"),
            GuestGroup("Vegetarianere", 4, dietary_notes="Vegetar"),
        ],
        notes="Servering kl. 17:00. Vi ønsker å smake hovedretten på forhånd.",
    ))

    lunch = orders.add(Order(
        customer_id=company.id, event_date=today + timedelta(days=7), guest_count=25,
        delivery_address="Kontorgata 10, 5003 Bergen",
        lines=[line("Påsmurt lunsjbaguette", 25), line("Kaffe og te (per person)", 25)],
        guest_groups=[GuestGroup("Ansatte", 22), GuestGroup("Glutenfritt", 3, allergy_notes="Gluten")],
    ))
    lunch.change_status(OrderStatus.APPROVED)
    lunch.change_payment_status(PaymentStatus.INVOICED)
    orders.save_status(lunch)

    julebord = orders.add(Order(
        customer_id=company.id, event_date=today + timedelta(days=30), guest_count=40,
        delivery_address="Kontorgata 10, 5003 Bergen",
        lines=[line("Ribbe med tilbehør", 25), line("Pinnekjøtt", 15)],
        guest_groups=[GuestGroup("Alle gjester", 40, dietary_notes="2 uten svinekjøtt – får pinnekjøtt")],
    ))

    delivered = orders.add(Order(
        customer_id=kari.id, event_date=today - timedelta(days=14), guest_count=15,
        delivery_address="Testveien 1, 5000 Bergen",
        lines=[line("Tapasfat", 15), line("Bløtkake (12 stykker)", 2)],
        guest_groups=[GuestGroup("Bursdagsgjester", 15)],
    ))
    for status in (OrderStatus.APPROVED, OrderStatus.IN_PREPARATION, OrderStatus.DELIVERED):
        delivered.change_status(status)
    delivered.change_payment_status(PaymentStatus.PAID)
    orders.save_status(delivered)

    questions = QuestionRepository()
    answered = questions.add(Question(order_id=wedding.id, author_id=kari.id,
                                      body="Kan vi få smake hovedretten to uker før bryllupet?"))
    answered.give_answer("Ja, vi setter opp en smaksprøve. Koordinatoren tar kontakt for å avtale tid.", admin.id)
    questions.save_answer(answered)
    questions.add(Question(order_id=julebord.id, author_id=company.id,
                           body="Kan dere levere allerede kl. 16:30?"))

    return {
        "users": 1 + len(customers),
        "food_items": len(items),
        "orders": 4,
        "questions": 2,
    }


@click.command("seed")
@with_appcontext
def seed_command():
    """Reset the database and load synthetic sample data."""
    summary = seed_database()
    click.echo("Database seeded with synthetic data: " +
               ", ".join(f"{k}={v}" for k, v in summary.items()))
    click.echo(f"Admin: {ADMIN['email']}  ·  Test customers: "
               + ", ".join(c["email"] for c in CUSTOMERS))
    click.echo("Passwords: SEED_ADMIN_PASSWORD / SEED_CUSTOMER_PASSWORD in .env (defaults in .env.example)")
