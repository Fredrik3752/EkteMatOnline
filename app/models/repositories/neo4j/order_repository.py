from datetime import date
from typing import List, Optional

from app.models.order import GuestGroup, Order, OrderLine, OrderStatus, PaymentStatus
from app.models.repositories.base import OrderRepositoryBase
from app.models.repositories.neo4j.driver import next_id, read, utc_now, write

_LOAD = """
WITH u, o
OPTIONAL MATCH (o)-[:HAS_LINE]->(l:OrderLine)
OPTIONAL MATCH (l)-[:OF_ITEM]->(f:FoodItem)
WITH u, o, l, f ORDER BY l.id
WITH u, o, collect(l{.*, food_item_id: f.id}) AS lines
OPTIONAL MATCH (o)-[:HAS_GUEST_GROUP]->(g:GuestGroup)
WITH u, o, lines, g ORDER BY g.id
WITH u, o, lines, collect(g{.*}) AS groups
RETURN o{.*, customer_id: u.id} AS o, lines, groups
"""


def _to_order(record) -> Order:
    o = record["o"]
    event_date = o["event_date"]
    return Order(
        id=o["id"], customer_id=o["customer_id"],
        event_date=event_date.to_native() if hasattr(event_date, "to_native") else event_date,
        guest_count=o["guest_count"], delivery_address=o["delivery_address"], notes=o.get("notes", ""),
        status=OrderStatus(o["status"]), payment_status=PaymentStatus(o["payment_status"]),
        created_at=o.get("created_at"), updated_at=o.get("updated_at"),
        lines=[OrderLine(id=l["id"], food_item_id=l.get("food_item_id"), item_name=l["item_name"],
                         quantity=l["quantity"], unit_price_ore=l["unit_price_ore"])
               for l in record["lines"]],
        guest_groups=[GuestGroup(id=g["id"], description=g["description"], guest_count=g["guest_count"],
                                 allergy_notes=g.get("allergy_notes", ""), dietary_notes=g.get("dietary_notes", ""))
                      for g in record["groups"]],
    )


class Neo4jOrderRepository(OrderRepositoryBase):
    """(:User)-[:PLACED]->(:Order)-[:HAS_LINE]->(:OrderLine)-[:OF_ITEM]->(:FoodItem),
    (:Order)-[:HAS_GUEST_GROUP]->(:GuestGroup)."""

    def add(self, order: Order) -> Order:
        """Order, lines and guest groups in ONE write transaction (all or nothing)."""
        order.validate()

        def work(tx):
            order_id = next_id(tx, "Order")
            first_line = next_id(tx, "OrderLine", len(order.lines))
            first_group = next_id(tx, "GuestGroup", len(order.guest_groups)) if order.guest_groups else 0
            now = utc_now()
            created = tx.run(
                "MATCH (u:User {id: $customer_id}) "
                "CREATE (u)-[:PLACED]->(o:Order {id: $id, event_date: $event_date, guest_count: $guest_count, "
                "  delivery_address: $address, notes: $notes, status: $status, payment_status: $payment, "
                "  estimated_total_ore: $total, created_at: $now, updated_at: $now}) "
                "RETURN o.id AS id",
                customer_id=order.customer_id, id=order_id, event_date=order.event_date,
                guest_count=order.guest_count, address=order.delivery_address.strip(),
                notes=order.notes or "", status=order.status.value, payment=order.payment_status.value,
                total=order.total_ore, now=now,
            ).single()
            if created is None:  # same effect as SQLite's foreign key on customer_id
                raise ValueError(f"Unknown customer id {order.customer_id}")
            tx.run(
                "MATCH (o:Order {id: $id}) "
                "UNWIND $lines AS line "
                "CREATE (o)-[:HAS_LINE]->(l:OrderLine {id: line.id, item_name: line.item_name, "
                "  quantity: line.quantity, unit_price_ore: line.unit_price_ore}) "
                "WITH l, line "
                "OPTIONAL MATCH (f:FoodItem {id: line.food_item_id}) "
                "FOREACH (_ IN CASE WHEN f IS NULL THEN [] ELSE [1] END | CREATE (l)-[:OF_ITEM]->(f))",
                id=order_id,
                lines=[{"id": first_line + i, "item_name": l.item_name, "quantity": l.quantity,
                        "unit_price_ore": l.unit_price_ore, "food_item_id": l.food_item_id}
                       for i, l in enumerate(order.lines)],
            ).consume()
            tx.run(
                "MATCH (o:Order {id: $id}) "
                "UNWIND $groups AS g "
                "CREATE (o)-[:HAS_GUEST_GROUP]->(:GuestGroup {id: g.id, description: g.description, "
                "  guest_count: g.guest_count, allergy_notes: g.allergy_notes, dietary_notes: g.dietary_notes})",
                id=order_id,
                groups=[{"id": first_group + i, "description": g.description.strip(), "guest_count": g.guest_count,
                         "allergy_notes": g.allergy_notes or "", "dietary_notes": g.dietary_notes or ""}
                        for i, g in enumerate(order.guest_groups)],
            ).consume()
            return order_id
        return self.get(write(work))

    def get(self, order_id: int) -> Optional[Order]:
        records = read("MATCH (u:User)-[:PLACED]->(o:Order {id: $id})" + _LOAD, id=order_id)
        return _to_order(records[0]) if records else None

    def list(self, status=None, date_from: Optional[date] = None,
             date_to: Optional[date] = None) -> List[Order]:
        """A3: all orders, optionally filtered by status and event date range."""
        clauses, params = [], {}
        if status:
            clauses.append("o.status = $status")
            params["status"] = OrderStatus(status).value
        if date_from:
            clauses.append("o.event_date >= $date_from")
            params["date_from"] = date_from
        if date_to:
            clauses.append("o.event_date <= $date_to")
            params["date_to"] = date_to
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        records = read("MATCH (u:User)-[:PLACED]->(o:Order)" + where + _LOAD + " ORDER BY o.event_date, o.id",
                       **params)
        return [_to_order(r) for r in records]

    def list_for_customer(self, customer_id: int) -> List[Order]:
        records = read("MATCH (u:User {id: $cid})-[:PLACED]->(o:Order)" + _LOAD
                       + " ORDER BY o.event_date DESC, o.id DESC", cid=customer_id)
        return [_to_order(r) for r in records]

    def save_status(self, order: Order) -> Order:
        def work(tx):
            tx.run("MATCH (o:Order {id: $id}) SET o.status = $status, o.payment_status = $payment, "
                   "o.updated_at = $now",
                   id=order.id, status=order.status.value, payment=order.payment_status.value,
                   now=utc_now()).consume()
        write(work)
        return self.get(order.id)
