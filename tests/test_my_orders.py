"""C4: the customer's own orders, with status and payment status."""
from datetime import date

import pytest

from app.models.order import OrderStatus as S
from app.models.order import PaymentStatus as P
from tests.conftest import get_order, login, post


@pytest.fixture
def kunde(client, customer):
    login(client, "kunde@example.test")
    return client


def test_requires_login(client):
    response = client.get("/mine-ordrer")
    assert response.status_code == 302 and "/logg-inn" in response.headers["Location"]


def test_empty_list(kunde):
    assert "Du har ingen ordrer ennå" in kunde.get("/mine-ordrer").get_data(as_text=True)


def test_lists_only_own_orders_with_status(kunde, customer, make_user, make_order):
    other = make_user("annen@example.test", "Annen")
    mine_old = make_order(customer.id, event_date=date(2027, 3, 1), status=S.DELIVERED)
    mine_new = make_order(customer.id, event_date=date(2027, 9, 1), status=S.APPROVED,
                          payment_status=P.INVOICED)
    theirs = make_order(other.id)
    html = kunde.get("/mine-ordrer").get_data(as_text=True)
    assert f"#{mine_new.id}" in html and f"#{mine_old.id}" in html
    assert f"/mine-ordrer/{theirs.id}" not in html
    assert html.index(f"#{mine_new.id}") < html.index(f"#{mine_old.id}")  # newest event first
    assert "Godkjent" in html and "Levert" in html
    assert "Fakturert" in html  # payment status shown


def test_nav_has_my_orders_link_when_logged_in(client, kunde):
    assert 'href="/mine-ordrer"' in kunde.get("/").get_data(as_text=True)


def test_nav_has_no_my_orders_link_when_anonymous(client):
    assert 'href="/mine-ordrer"' not in client.get("/").get_data(as_text=True)


def test_detail_page(kunde, customer, make_order):
    order = make_order(customer.id)
    html = kunde.get(f"/mine-ordrer/{order.id}").get_data(as_text=True)
    assert f"Ordre nr. {order.id}" in html
    assert "Sendt inn" in html and "Ikke betalt" in html
    assert "Nøtteallergi" in html
    assert "Avbestill ordren" in html


def test_other_customers_order_is_404(kunde, make_user, make_order):
    other = make_user("annen@example.test", "Annen")
    order = make_order(other.id)
    assert kunde.get(f"/mine-ordrer/{order.id}").status_code == 404
    assert post(kunde, f"/mine-ordrer/{order.id}/avbestill").status_code == 404
    assert kunde.get("/mine-ordrer/999").status_code == 404


def test_cancel_submitted_order(app, kunde, customer, make_order):
    order = make_order(customer.id)
    response = post(kunde, f"/mine-ordrer/{order.id}/avbestill", follow_redirects=True)
    assert "er avbestilt" in response.get_data(as_text=True)
    assert get_order(app, order.id).status is S.CANCELLED
    assert "Avbestill ordren" not in kunde.get(f"/mine-ordrer/{order.id}").get_data(as_text=True)


@pytest.mark.parametrize("status", [S.APPROVED, S.IN_PREPARATION, S.DELIVERED, S.REJECTED])
def test_cannot_cancel_processed_order(app, kunde, customer, make_order, status):
    order = make_order(customer.id, status=status)
    assert "Avbestill ordren" not in kunde.get(f"/mine-ordrer/{order.id}").get_data(as_text=True)
    html = post(kunde, f"/mine-ordrer/{order.id}/avbestill", follow_redirects=True).get_data(as_text=True)
    assert "kan ikke avbestilles" in html
    assert get_order(app, order.id).status is status


def test_cancel_requires_post_and_csrf(app, kunde, customer, make_order):
    order = make_order(customer.id)
    assert kunde.get(f"/mine-ordrer/{order.id}/avbestill").status_code == 405
    assert kunde.post(f"/mine-ordrer/{order.id}/avbestill").status_code == 400
    assert get_order(app, order.id).status is S.SUBMITTED


def test_status_change_by_admin_is_visible_to_customer(app, client, customer, admin, make_order):
    order = make_order(customer.id)
    login(client, "admin@example.test")
    post(client, f"/admin/ordrer/{order.id}/status", {"status": "approved"})
    post(client, f"/admin/ordrer/{order.id}/betaling", {"payment_status": "deposit_paid"})
    post(client, "/logg-ut")
    login(client, "kunde@example.test")
    html = client.get("/mine-ordrer").get_data(as_text=True)
    assert "Godkjent" in html and "Depositum betalt" in html


def test_receipt_links_to_my_orders(kunde, customer, make_order):
    order = make_order(customer.id)
    assert 'href="/mine-ordrer"' in kunde.get(f"/bestilling/{order.id}/kvittering").get_data(as_text=True)
