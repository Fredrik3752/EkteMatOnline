"""A3: admin order list with filters and order management."""
from datetime import date

import pytest

from app.models.order import OrderStatus as S
from app.models.order import PaymentStatus as P
from tests.conftest import get_order, login, post


@pytest.fixture
def admin_client(client, admin):
    login(client, "admin@example.test")
    return client


@pytest.fixture
def three_orders(customer, make_user, make_order):
    other = make_user("annen@example.test", "Annen Kunde")
    return [
        make_order(customer.id, event_date=date(2027, 3, 1)),
        make_order(other.id, event_date=date(2027, 5, 1), status=S.APPROVED),
        make_order(customer.id, event_date=date(2027, 8, 1), status=S.DELIVERED),
    ]


def listed_ids(html):
    import re
    return [int(n) for n in re.findall(r'href="/admin/ordrer/(\d+)"', html)]


# -- access ------------------------------------------------------------------------

@pytest.mark.parametrize("url", ["/admin/ordrer", "/admin/ordrer/1"])
def test_customer_is_forbidden(client, customer, make_order, url):
    make_order(customer.id)
    login(client, "kunde@example.test")
    assert client.get(url).status_code == 403


def test_customer_cannot_change_status(app, client, customer, make_order):
    order = make_order(customer.id)
    login(client, "kunde@example.test")
    assert post(client, f"/admin/ordrer/{order.id}/status", {"status": "approved"}).status_code == 403
    assert get_order(app, order.id).status is S.SUBMITTED


def test_anonymous_is_redirected(client):
    assert client.get("/admin/ordrer").status_code == 302


# -- list and filters ---------------------------------------------------------------

def test_list_shows_all_orders(admin_client, three_orders):
    html = admin_client.get("/admin/ordrer").get_data(as_text=True)
    assert listed_ids(html) == [o.id for o in three_orders]  # sorted by event date
    assert "Test Kunde" in html and "Annen Kunde" in html
    assert "3 780,00 kr" in html  # 20 × 189
    assert "3 ordrer." in html


@pytest.mark.parametrize("query, expected", [
    ("?status=approved", [1]),
    ("?status=delivered", [2]),
    ("?status=rejected", []),
    ("?fra=2027-04-01", [1, 2]),
    ("?til=2027-05-01", [0, 1]),
    ("?fra=2027-04-01&til=2027-06-01", [1]),
    ("?status=submitted&fra=2027-04-01", []),
])
def test_filters(admin_client, three_orders, query, expected):
    html = admin_client.get("/admin/ordrer" + query).get_data(as_text=True)
    assert listed_ids(html) == [three_orders[i].id for i in expected]


def test_filter_form_keeps_values(admin_client, three_orders):
    html = admin_client.get("/admin/ordrer?status=approved&fra=2027-04-01").get_data(as_text=True)
    assert '<option value="approved" selected>' in html
    assert 'value="2027-04-01"' in html and "Nullstill" in html


@pytest.mark.parametrize("query", ["?status=shipped", "?fra=01.04.2027", "?til=i-morgen"])
def test_invalid_filter_is_ignored_with_message(admin_client, three_orders, query):
    response = admin_client.get("/admin/ordrer" + query)
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "filteret er ignorert" in html
    assert len(listed_ids(html)) == 3


def test_overview_links_to_filtered_lists(admin_client, three_orders):
    html = admin_client.get("/admin/").get_data(as_text=True)
    assert 'href="/admin/ordrer?status=approved"' in html


# -- order detail and status ---------------------------------------------------------

def test_detail_page(admin_client, customer, make_order):
    order = make_order(customer.id, notes="Levering bakdøren")
    html = admin_client.get(f"/admin/ordrer/{order.id}").get_data(as_text=True)
    assert f"Ordre nr. {order.id}" in html
    assert "Test Kunde" in html and "kunde@example.test" in html
    assert "Fiskesuppe" in html and "Nøtteallergi" in html and "Levering bakdøren" in html
    assert '<span class="allergy">Nøtter</span>' in html
    # only the legal next steps from "submitted" are offered
    assert "Godkjenn" in html and "Avvis" in html and "Kanseller" in html
    assert "Marker som levert" not in html and "Start tilberedning" not in html


def test_full_status_flow(app, admin_client, customer, make_order):
    order = make_order(customer.id)
    for status in ("approved", "in_preparation", "delivered"):
        response = post(admin_client, f"/admin/ordrer/{order.id}/status", {"status": status})
        assert response.status_code == 302
        assert get_order(app, order.id).status.value == status
    html = admin_client.get(f"/admin/ordrer/{order.id}").get_data(as_text=True)
    assert "avsluttet og kan ikke endre status" in html


@pytest.mark.parametrize("start, target", [
    (None, "delivered"), (None, "in_preparation"), (S.APPROVED, "rejected"),
    (S.DELIVERED, "cancelled"), (S.CANCELLED, "approved"),
])
def test_illegal_transition_is_refused(app, admin_client, customer, make_order, start, target):
    order = make_order(customer.id, status=start)
    before = get_order(app, order.id).status
    response = post(admin_client, f"/admin/ordrer/{order.id}/status", {"status": target}, follow_redirects=True)
    assert "Kan ikke endre status" in response.get_data(as_text=True)
    assert get_order(app, order.id).status is before


def test_unknown_status_value(app, admin_client, customer, make_order):
    order = make_order(customer.id)
    html = post(admin_client, f"/admin/ordrer/{order.id}/status", {"status": "shipped"},
                follow_redirects=True).get_data(as_text=True)
    assert "Ukjent status" in html
    assert get_order(app, order.id).status is S.SUBMITTED


def test_change_payment_status(app, admin_client, customer, make_order):
    order = make_order(customer.id)
    for payment in ("deposit_paid", "invoiced", "paid", "not_paid"):
        post(admin_client, f"/admin/ordrer/{order.id}/betaling", {"payment_status": payment})
        assert get_order(app, order.id).payment_status.value == payment
    assert get_order(app, order.id).status is S.SUBMITTED  # order status untouched


def test_unknown_payment_status(app, admin_client, customer, make_order):
    order = make_order(customer.id)
    html = post(admin_client, f"/admin/ordrer/{order.id}/betaling", {"payment_status": "refunded"},
                follow_redirects=True).get_data(as_text=True)
    assert "Ukjent betalingsstatus" in html
    assert get_order(app, order.id).payment_status is P.NOT_PAID


def test_status_change_requires_csrf(app, admin_client, customer, make_order):
    order = make_order(customer.id)
    assert admin_client.post(f"/admin/ordrer/{order.id}/status", data={"status": "approved"}).status_code == 400
    assert get_order(app, order.id).status is S.SUBMITTED


@pytest.mark.parametrize("method, url", [
    ("get", "/admin/ordrer/999"), ("post", "/admin/ordrer/999/status"), ("post", "/admin/ordrer/999/betaling"),
])
def test_unknown_order_is_404(admin_client, method, url):
    response = admin_client.get(url) if method == "get" else post(admin_client, url, {"status": "approved"})
    assert response.status_code == 404
