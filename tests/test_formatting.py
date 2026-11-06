from datetime import datetime, timedelta, timezone

import pytest

from app.controllers.formatting import local_time
from app.models.question import Question


@pytest.mark.parametrize("utc, expected", [
    ("2026-11-06 02:35:38", "06.11.2026 kl. 03:35"),  # winter: UTC+1
    ("2027-07-01 10:00:00", "01.07.2027 kl. 12:00"),  # summer: UTC+2
    ("2026-12-31 23:30:00", "01.01.2027 kl. 00:30"),  # crosses midnight
])
def test_local_time_converts_utc_to_norwegian_time(utc, expected):
    assert local_time(utc) == expected


@pytest.mark.parametrize("value, expected", [(None, ""), ("", ""), ("ikke en dato", "ikke en dato")])
def test_local_time_handles_missing_and_invalid(value, expected):
    assert local_time(value) == expected


def test_answer_timestamp_is_stored_in_utc():
    q = Question(order_id=1, author_id=1, body="?")
    q.give_answer("Svar", admin_id=2, when=datetime(2027, 7, 1, 12, 0, tzinfo=timezone(timedelta(hours=2))))
    assert q.answered_at == "2027-07-01 10:00:00"
    assert local_time(q.answered_at) == "01.07.2027 kl. 12:00"


def test_admin_order_page_shows_local_time(app, client, admin, customer, make_order):
    from tests.conftest import login
    order = make_order(customer.id)
    login(client, "admin@example.test")
    html = client.get(f"/admin/ordrer/{order.id}").get_data(as_text=True)
    assert f"Bestilt {local_time(order.created_at)}" in html
    assert " kl. " in html
