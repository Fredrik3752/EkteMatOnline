from collections import OrderedDict, defaultdict
from typing import Dict, List, Optional

from app.models.event_category import EventCategory
from app.models.food_item import FoodItem
from app.models.reference import Allergen, DietaryLabel
from app.models.repositories.database import get_db

_COLUMNS = ("id, name, description, price_ore, min_order_qty, image_path, origin, "
            "is_published, created_at, updated_at")


class FoodItemRepository:
    """All storage of food items and their category/allergen/diet links (A1, C1)."""

    def add(self, item: FoodItem) -> FoodItem:
        item.validate()
        db = get_db()
        with db:
            cur = db.execute(
                "INSERT INTO food_items (name, description, price_ore, min_order_qty, image_path,"
                " origin, is_published) VALUES (?, ?, ?, ?, ?, ?, ?)",
                self._values(item),
            )
            self._write_links(cur.lastrowid, item)
        return self.get(cur.lastrowid)

    def update(self, item: FoodItem) -> FoodItem:
        if item.id is None:
            raise ValueError("Cannot update a food item without id")
        item.validate()
        db = get_db()
        with db:
            db.execute(
                "UPDATE food_items SET name = ?, description = ?, price_ore = ?, min_order_qty = ?,"
                " image_path = ?, origin = ?, is_published = ?, updated_at = CURRENT_TIMESTAMP"
                " WHERE id = ?",
                (*self._values(item), item.id),
            )
            for table in ("food_item_categories", "food_item_allergens", "food_item_dietary_labels"):
                db.execute(f"DELETE FROM {table} WHERE food_item_id = ?", (item.id,))
            self._write_links(item.id, item)
        return self.get(item.id)

    def delete(self, item_id: int) -> bool:
        db = get_db()
        with db:
            cur = db.execute("DELETE FROM food_items WHERE id = ?", (item_id,))
        return cur.rowcount > 0

    def get(self, item_id: int) -> Optional[FoodItem]:
        rows = get_db().execute(f"SELECT {_COLUMNS} FROM food_items WHERE id = ?", (item_id,)).fetchall()
        items = self._load(rows)
        return items[0] if items else None

    def get_many(self, item_ids) -> Dict[int, FoodItem]:
        ids = list({int(i) for i in item_ids})
        if not ids:
            return {}
        placeholders = ",".join("?" * len(ids))
        rows = get_db().execute(
            f"SELECT {_COLUMNS} FROM food_items WHERE id IN ({placeholders})", ids
        ).fetchall()
        return {item.id: item for item in self._load(rows)}

    def list_all(self, published_only: bool = False) -> List[FoodItem]:
        where = "WHERE is_published = 1" if published_only else ""
        rows = get_db().execute(f"SELECT {_COLUMNS} FROM food_items {where} ORDER BY name").fetchall()
        return self._load(rows)

    def list_published_by_category(self) -> "OrderedDict[EventCategory, List[FoodItem]]":
        """C1: published items grouped by event category, in category order."""
        items = self.list_all(published_only=True)
        groups: "OrderedDict[EventCategory, List[FoodItem]]" = OrderedDict()
        all_categories = sorted({c for item in items for c in item.categories},
                                key=lambda c: (c.sort_order, c.name))
        for category in all_categories:
            groups[category] = [i for i in items if category in i.categories]
        return groups

    # -- helpers ---------------------------------------------------------------

    @staticmethod
    def _values(item: FoodItem):
        return (item.name.strip(), item.description or "", item.price_ore, item.min_order_qty,
                item.image_path, item.origin, 1 if item.is_published else 0)

    @staticmethod
    def _write_links(item_id: int, item: FoodItem) -> None:
        db = get_db()
        db.executemany("INSERT INTO food_item_categories VALUES (?, ?)",
                       [(item_id, c.id) for c in item.categories])
        db.executemany("INSERT INTO food_item_allergens VALUES (?, ?)",
                       [(item_id, a.id) for a in item.allergens])
        db.executemany("INSERT INTO food_item_dietary_labels VALUES (?, ?)",
                       [(item_id, d.id) for d in item.dietary_labels])

    def _load(self, rows) -> List[FoodItem]:
        if not rows:
            return []
        ids = [r["id"] for r in rows]
        placeholders = ",".join("?" * len(ids))
        db = get_db()

        categories = defaultdict(list)
        for r in db.execute(
            "SELECT l.food_item_id, c.id, c.slug, c.name, c.sort_order FROM food_item_categories l"
            f" JOIN event_categories c ON c.id = l.event_category_id WHERE l.food_item_id IN ({placeholders})"
            " ORDER BY c.sort_order", ids,
        ):
            categories[r["food_item_id"]].append(
                EventCategory(id=r["id"], slug=r["slug"], name=r["name"], sort_order=r["sort_order"]))

        allergens = defaultdict(list)
        for r in db.execute(
            "SELECT l.food_item_id, a.id, a.code, a.name FROM food_item_allergens l"
            f" JOIN allergens a ON a.id = l.allergen_id WHERE l.food_item_id IN ({placeholders})"
            " ORDER BY a.id", ids,
        ):
            allergens[r["food_item_id"]].append(Allergen(id=r["id"], code=r["code"], name=r["name"]))

        diets = defaultdict(list)
        for r in db.execute(
            "SELECT l.food_item_id, d.id, d.code, d.name FROM food_item_dietary_labels l"
            f" JOIN dietary_labels d ON d.id = l.dietary_label_id WHERE l.food_item_id IN ({placeholders})"
            " ORDER BY d.id", ids,
        ):
            diets[r["food_item_id"]].append(DietaryLabel(id=r["id"], code=r["code"], name=r["name"]))

        return [
            FoodItem(
                id=r["id"], name=r["name"], description=r["description"], price_ore=r["price_ore"],
                min_order_qty=r["min_order_qty"], image_path=r["image_path"], origin=r["origin"],
                is_published=bool(r["is_published"]), created_at=r["created_at"],
                updated_at=r["updated_at"], categories=categories[r["id"]],
                allergens=allergens[r["id"]], dietary_labels=diets[r["id"]],
            )
            for r in rows
        ]
