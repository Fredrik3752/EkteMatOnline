from collections import defaultdict
from datetime import date
from typing import List, Optional

from app.models.order import GuestGroup, Order, OrderLine, OrderStatus, PaymentStatus
from app.models.repositories.database import get_db

_COLUMNS = ("id, customer_id, event_date, guest_count, delivery_address, notes, status,"
            " payment_status, estimated_total_ore, created_at, updated_at")


class OrderRepository:
    """Orders with their lines and guest groups (A3, C3, C4)."""

    def add(self, order: Order) -> Order:
        """Store a new order, its lines and guest groups in one transaction."""
        order.validate()
        db = get_db()
        with db:
            cur = db.execute(
                "INSERT INTO orders (customer_id, event_date, guest_count, delivery_address, notes,"
                " status, payment_status, estimated_total_ore) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (order.customer_id, order.event_date.isoformat(), order.guest_count,
                 order.delivery_address.strip(), order.notes or "", order.status.value,
                 order.payment_status.value, order.total_ore),
            )
            order_id = cur.lastrowid
            db.executemany(
                "INSERT INTO order_lines (order_id, food_item_id, item_name, quantity, unit_price_ore)"
                " VALUES (?, ?, ?, ?, ?)",
                [(order_id, l.food_item_id, l.item_name, l.quantity, l.unit_price_ore) for l in order.lines],
            )
            db.executemany(
                "INSERT INTO guest_groups (order_id, description, guest_count, allergy_notes, dietary_notes)"
                " VALUES (?, ?, ?, ?, ?)",
                [(order_id, g.description.strip(), g.guest_count, g.allergy_notes or "", g.dietary_notes or "")
                 for g in order.guest_groups],
            )
        return self.get(order_id)

    def get(self, order_id: int) -> Optional[Order]:
        rows = get_db().execute(f"SELECT {_COLUMNS} FROM orders WHERE id = ?", (order_id,)).fetchall()
        orders = self._load(rows)
        return orders[0] if orders else None

    def list(self, status=None, date_from: Optional[date] = None,
             date_to: Optional[date] = None) -> List[Order]:
        """A3: all orders, optionally filtered by status and event date range."""
        clauses, params = [], []
        if status:
            clauses.append("status = ?")
            params.append(OrderStatus(status).value)
        if date_from:
            clauses.append("event_date >= ?")
            params.append(date_from.isoformat())
        if date_to:
            clauses.append("event_date <= ?")
            params.append(date_to.isoformat())
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = get_db().execute(
            f"SELECT {_COLUMNS} FROM orders {where} ORDER BY event_date, id", params
        ).fetchall()
        return self._load(rows)

    def list_for_customer(self, customer_id: int) -> List[Order]:
        """C4: a customer's own orders, newest event first."""
        rows = get_db().execute(
            f"SELECT {_COLUMNS} FROM orders WHERE customer_id = ? ORDER BY event_date DESC, id DESC",
            (customer_id,),
        ).fetchall()
        return self._load(rows)

    def save_status(self, order: Order) -> Order:
        """Persist status and payment status after the domain object has changed them."""
        db = get_db()
        with db:
            db.execute(
                "UPDATE orders SET status = ?, payment_status = ?, updated_at = CURRENT_TIMESTAMP"
                " WHERE id = ?",
                (order.status.value, order.payment_status.value, order.id),
            )
        return self.get(order.id)

    def _load(self, rows) -> List[Order]:
        if not rows:
            return []
        ids = [r["id"] for r in rows]
        placeholders = ",".join("?" * len(ids))
        db = get_db()

        lines = defaultdict(list)
        for r in db.execute(
            "SELECT id, order_id, food_item_id, item_name, quantity, unit_price_ore FROM order_lines"
            f" WHERE order_id IN ({placeholders}) ORDER BY id", ids,
        ):
            lines[r["order_id"]].append(OrderLine(
                id=r["id"], food_item_id=r["food_item_id"], item_name=r["item_name"],
                quantity=r["quantity"], unit_price_ore=r["unit_price_ore"]))

        groups = defaultdict(list)
        for r in db.execute(
            "SELECT id, order_id, description, guest_count, allergy_notes, dietary_notes FROM guest_groups"
            f" WHERE order_id IN ({placeholders}) ORDER BY id", ids,
        ):
            groups[r["order_id"]].append(GuestGroup(
                id=r["id"], description=r["description"], guest_count=r["guest_count"],
                allergy_notes=r["allergy_notes"], dietary_notes=r["dietary_notes"]))

        return [
            Order(
                id=r["id"], customer_id=r["customer_id"], event_date=date.fromisoformat(r["event_date"]),
                guest_count=r["guest_count"], delivery_address=r["delivery_address"], notes=r["notes"],
                status=OrderStatus(r["status"]), payment_status=PaymentStatus(r["payment_status"]),
                created_at=r["created_at"], updated_at=r["updated_at"],
                lines=lines[r["id"]], guest_groups=groups[r["id"]],
            )
            for r in rows
        ]
