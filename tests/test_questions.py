"""C5: customers ask about an order. A4: Ekte Mat reads and answers."""
import pytest

from app.models.question import MAX_QUESTION_LENGTH, Question
from app.models.repositories.question_repository import QuestionRepository
from tests.conftest import login, post


@pytest.fixture
def order(customer, make_order):
    return make_order(customer.id)


def questions_for(app, order_id):
    with app.app_context():
        return QuestionRepository().list_for_order(order_id)


def add_question(app, order, author_id, body="Kan dere levere kl. 11?"):
    with app.app_context():
        return QuestionRepository().add(Question(order_id=order.id, author_id=author_id, body=body))


# -- C5: customer --------------------------------------------------------------------

def test_order_page_has_question_form(client, customer, order):
    login(client, "kunde@example.test")
    html = client.get(f"/mine-ordrer/{order.id}").get_data(as_text=True)
    assert "Spørsmål om ordren" in html and "Ingen spørsmål ennå" in html
    assert f'action="/mine-ordrer/{order.id}/sporsmal#sporsmal"' in html


def test_ask_question(app, client, customer, order):
    login(client, "kunde@example.test")
    response = post(client, f"/mine-ordrer/{order.id}/sporsmal", {"body": "  Kan dere levere kl. 11?  "})
    assert response.status_code == 302
    assert response.headers["Location"].endswith(f"/mine-ordrer/{order.id}#sporsmal")
    [q] = questions_for(app, order.id)
    assert q.body == "Kan dere levere kl. 11?" and q.author_id == customer.id and not q.is_answered
    html = client.get(f"/mine-ordrer/{order.id}").get_data(as_text=True)
    assert "Kan dere levere kl. 11?" in html and "Venter på svar" in html


@pytest.mark.parametrize("body, message", [
    ("   ", "kan ikke være tomt"),
    ("x" * (MAX_QUESTION_LENGTH + 1), f"høyst {MAX_QUESTION_LENGTH} tegn"),
])
def test_invalid_question(app, client, customer, order, body, message):
    login(client, "kunde@example.test")
    response = post(client, f"/mine-ordrer/{order.id}/sporsmal", {"body": body})
    assert response.status_code == 400
    assert message in response.get_data(as_text=True)
    assert questions_for(app, order.id) == []


def test_cannot_ask_about_other_customers_order(app, client, make_user, order):
    make_user("annen@example.test", "Annen")
    login(client, "annen@example.test")
    assert post(client, f"/mine-ordrer/{order.id}/sporsmal", {"body": "Hei"}).status_code == 404
    assert questions_for(app, order.id) == []


def test_ask_requires_login_and_csrf(app, client, customer, order):
    assert post(client, f"/mine-ordrer/{order.id}/sporsmal", {"body": "Hei"}).status_code == 302
    login(client, "kunde@example.test")
    assert client.post(f"/mine-ordrer/{order.id}/sporsmal", data={"body": "Hei"}).status_code == 400
    assert questions_for(app, order.id) == []


def test_customer_sees_answer(app, client, customer, admin, order):
    q = add_question(app, order, customer.id)
    with app.app_context():
        q.give_answer("Ja, det går fint.", admin.id)
        QuestionRepository().save_answer(q)
    login(client, "kunde@example.test")
    html = client.get(f"/mine-ordrer/{order.id}").get_data(as_text=True)
    assert "Svar fra Ekte Mat" in html and "Ja, det går fint." in html
    assert "Venter på svar" not in html


def test_question_text_is_escaped(app, client, customer, order):
    add_question(app, order, customer.id, body="<script>alert(1)</script>")
    login(client, "kunde@example.test")
    assert "<script>alert(1)</script>" not in client.get(f"/mine-ordrer/{order.id}").get_data(as_text=True)


# -- A4: admin ------------------------------------------------------------------------

@pytest.fixture
def admin_client(client, admin):
    login(client, "admin@example.test")
    return client


def test_admin_questions_requires_admin(client, customer):
    assert client.get("/admin/sporsmal").status_code == 302
    login(client, "kunde@example.test")
    assert client.get("/admin/sporsmal").status_code == 403


def test_customer_cannot_answer(app, client, customer, order):
    q = add_question(app, order, customer.id)
    login(client, "kunde@example.test")
    assert post(client, f"/admin/sporsmal/{q.id}/svar", {"answer": "Selvsvar"}).status_code == 403
    assert not questions_for(app, order.id)[0].is_answered


def test_list_shows_unanswered_by_default(app, admin_client, customer, admin, order):
    first = add_question(app, order, customer.id, body="Første spørsmål")
    add_question(app, order, customer.id, body="Andre spørsmål")
    done = add_question(app, order, customer.id, body="Besvart spørsmål")
    with app.app_context():
        done.give_answer("Svar", admin.id)
        QuestionRepository().save_answer(done)

    html = admin_client.get("/admin/sporsmal").get_data(as_text=True)
    assert "Første spørsmål" in html and "Andre spørsmål" in html
    assert "Besvart spørsmål" not in html
    assert html.index("Første spørsmål") < html.index("Andre spørsmål")  # oldest first
    assert "Test Kunde" in html and f'href="/admin/ordrer/{order.id}#sporsmal"' in html
    assert first.body in html

    all_html = admin_client.get("/admin/sporsmal?vis=alle").get_data(as_text=True)
    assert "Besvart spørsmål" in all_html and "Første spørsmål" in all_html


def test_empty_list_message(admin_client):
    assert "Ingen ubesvarte spørsmål" in admin_client.get("/admin/sporsmal").get_data(as_text=True)


def test_answer_from_list(app, admin_client, customer, admin, order):
    q = add_question(app, order, customer.id)
    response = post(admin_client, f"/admin/sporsmal/{q.id}/svar",
                    {"answer": "Ja, kl. 11 går fint.", "next": "/admin/sporsmal"})
    assert response.status_code == 302 and response.headers["Location"] == "/admin/sporsmal"
    [saved] = questions_for(app, order.id)
    assert saved.answer == "Ja, kl. 11 går fint." and saved.answered_by == admin.id and saved.answered_at
    assert "Ingen ubesvarte spørsmål" in admin_client.get("/admin/sporsmal").get_data(as_text=True)


def test_answer_from_order_page(app, admin_client, customer, order):
    q = add_question(app, order, customer.id)
    html = admin_client.get(f"/admin/ordrer/{order.id}").get_data(as_text=True)
    assert "Spørsmål fra kunden" in html and q.body in html
    assert f'action="/admin/sporsmal/{q.id}/svar"' in html
    response = post(admin_client, f"/admin/sporsmal/{q.id}/svar",
                    {"answer": "Svar fra ordresiden", "next": f"/admin/ordrer/{order.id}"})
    assert response.headers["Location"] == f"/admin/ordrer/{order.id}"
    assert questions_for(app, order.id)[0].answer == "Svar fra ordresiden"


def test_answer_ignores_unsafe_next(app, admin_client, customer, order):
    q = add_question(app, order, customer.id)
    response = post(admin_client, f"/admin/sporsmal/{q.id}/svar", {"answer": "Ok", "next": "https://evil.example"})
    assert response.headers["Location"] == "/admin/sporsmal"


def test_empty_answer_is_rejected(app, admin_client, customer, order):
    q = add_question(app, order, customer.id)
    html = post(admin_client, f"/admin/sporsmal/{q.id}/svar", {"answer": "  "},
                follow_redirects=True).get_data(as_text=True)
    assert "Svaret kan ikke være tomt" in html
    assert not questions_for(app, order.id)[0].is_answered


def test_second_answer_is_rejected(app, admin_client, customer, order):
    q = add_question(app, order, customer.id)
    post(admin_client, f"/admin/sporsmal/{q.id}/svar", {"answer": "Første"})
    html = post(admin_client, f"/admin/sporsmal/{q.id}/svar", {"answer": "Andre"},
                follow_redirects=True).get_data(as_text=True)
    assert "allerede besvart" in html
    assert questions_for(app, order.id)[0].answer == "Første"


def test_answer_unknown_question_is_404(admin_client):
    assert post(admin_client, "/admin/sporsmal/999/svar", {"answer": "Hei"}).status_code == 404


def test_answer_requires_csrf(app, admin_client, customer, order):
    q = add_question(app, order, customer.id)
    assert admin_client.post(f"/admin/sporsmal/{q.id}/svar", data={"answer": "Hei"}).status_code == 400


def test_menu_badge_and_overview_count(app, admin_client, customer, order):
    add_question(app, order, customer.id)
    add_question(app, order, customer.id)
    html = admin_client.get("/admin/").get_data(as_text=True)
    assert 'Spørsmål <span class="cart-count">2</span>' in html
    assert 'href="/admin/sporsmal"' in html


def test_full_round_trip(app, client, customer, admin, order):
    login(client, "kunde@example.test")
    post(client, f"/mine-ordrer/{order.id}/sporsmal", {"body": "Har dere glutenfritt brød?"})
    post(client, "/logg-ut")

    login(client, "admin@example.test")
    [q] = questions_for(app, order.id)
    assert "Har dere glutenfritt brød?" in client.get("/admin/sporsmal").get_data(as_text=True)
    post(client, f"/admin/sporsmal/{q.id}/svar", {"answer": "Ja, vi lager glutenfritt brød."})
    post(client, "/logg-ut")

    login(client, "kunde@example.test")
    html = client.get(f"/mine-ordrer/{order.id}").get_data(as_text=True)
    assert "Ja, vi lager glutenfritt brød." in html
