from typing import Dict, List, Optional

from app.models.food_item import FoodItem
from app.models.repositories.base import FoodItemRepositoryBase
from app.models.repositories.neo4j.driver import next_id, read, utc_now, write
from app.models.repositories.neo4j.reference_repository import (to_allergen, to_category,
                                                                to_dietary_label)

# Loads items matched by `f` together with their links in ONE query (no query per item).
# ORDER BY before collect() keeps the link lists in the same order as the SQLite backend.
_LOAD = """
WITH f
OPTIONAL MATCH (f)-[:SUITABLE_FOR]->(c:EventCategory)
WITH f, c ORDER BY c.sort_order, c.name
WITH f, collect(c{.*}) AS categories
OPTIONAL MATCH (f)-[:CONTAINS]->(a:Allergen)
WITH f, categories, a ORDER BY a.id
WITH f, categories, collect(a{.*}) AS allergens
OPTIONAL MATCH (f)-[:HAS_LABEL]->(d:DietaryLabel)
WITH f, categories, allergens, d ORDER BY d.id
WITH f, categories, allergens, collect(d{.*}) AS diets
RETURN f{.*} AS f, categories, allergens, diets
ORDER BY f.name, f.id
"""

_LINKS = """
WITH f
CALL {
  WITH f
  UNWIND $category_ids AS cid MATCH (c:EventCategory {id: cid}) CREATE (f)-[:SUITABLE_FOR]->(c)
}
CALL {
  WITH f
  UNWIND $allergen_ids AS aid MATCH (a:Allergen {id: aid}) CREATE (f)-[:CONTAINS]->(a)
}
CALL {
  WITH f
  UNWIND $diet_ids AS did MATCH (d:DietaryLabel {id: did}) CREATE (f)-[:HAS_LABEL]->(d)
}
"""


def _to_item(record) -> FoodItem:
    f = record["f"]
    return FoodItem(
        id=f["id"], name=f["name"], description=f.get("description", ""), price_ore=f["price_ore"],
        min_order_qty=f["min_order_qty"], image_path=f.get("image_path"), origin=f.get("origin"),
        is_published=bool(f["is_published"]), created_at=f.get("created_at"),
        updated_at=f.get("updated_at"),
        categories=[to_category(c) for c in record["categories"]],
        allergens=[to_allergen(a) for a in record["allergens"]],
        dietary_labels=[to_dietary_label(d) for d in record["diets"]],
    )


def _params(item: FoodItem) -> dict:
    return dict(
        name=item.name.strip(), description=item.description or "", price_ore=item.price_ore,
        min_order_qty=item.min_order_qty, image_path=item.image_path, origin=item.origin,
        is_published=bool(item.is_published),
        category_ids=[c.id for c in item.categories],
        allergen_ids=[a.id for a in item.allergens],
        diet_ids=[d.id for d in item.dietary_labels],
    )


class Neo4jFoodItemRepository(FoodItemRepositoryBase):
    """Food items as (:FoodItem) nodes linked to categories, allergens and dietary labels."""

    def add(self, item: FoodItem) -> FoodItem:
        item.validate()

        def work(tx):
            item_id = next_id(tx, "FoodItem")
            now = utc_now()
            tx.run(
                "CREATE (f:FoodItem {id: $id, name: $name, description: $description, "
                "price_ore: $price_ore, min_order_qty: $min_order_qty, image_path: $image_path, "
                "origin: $origin, is_published: $is_published, created_at: $now, updated_at: $now})"
                + _LINKS,
                id=item_id, now=now, **_params(item),
            ).consume()
            return item_id
        return self.get(write(work))

    def update(self, item: FoodItem) -> FoodItem:
        if item.id is None:
            raise ValueError("Cannot update a food item without id")
        item.validate()

        def work(tx):
            tx.run(
                "MATCH (f:FoodItem {id: $id}) "
                "SET f.name = $name, f.description = $description, f.price_ore = $price_ore, "
                "    f.min_order_qty = $min_order_qty, f.image_path = $image_path, f.origin = $origin, "
                "    f.is_published = $is_published, f.updated_at = $now "
                "WITH f OPTIONAL MATCH (f)-[r:SUITABLE_FOR|CONTAINS|HAS_LABEL]->() DELETE r "
                "WITH DISTINCT f" + _LINKS,
                id=item.id, now=utc_now(), **_params(item),
            ).consume()
        write(work)
        return self.get(item.id)

    def delete(self, item_id: int) -> bool:
        """DETACH DELETE also removes (:OrderLine)-[:OF_ITEM]-> – the line keeps name and price."""
        def work(tx):
            return tx.run("MATCH (f:FoodItem {id: $id}) DETACH DELETE f RETURN count(*) AS n",
                          id=item_id).single()["n"]
        return write(work) > 0

    def get(self, item_id: int) -> Optional[FoodItem]:
        records = read("MATCH (f:FoodItem {id: $id})" + _LOAD, id=item_id)
        return _to_item(records[0]) if records else None

    def get_many(self, item_ids) -> Dict[int, FoodItem]:
        ids = list({int(i) for i in item_ids})
        if not ids:
            return {}
        records = read("MATCH (f:FoodItem) WHERE f.id IN $ids" + _LOAD, ids=ids)
        return {r["f"]["id"]: _to_item(r) for r in records}

    def list_all(self, published_only: bool = False) -> List[FoodItem]:
        where = " WHERE f.is_published = true" if published_only else ""
        return [_to_item(r) for r in read("MATCH (f:FoodItem)" + where + _LOAD)]

    def list_published_in_category(self, category_id: int) -> List[FoodItem]:
        records = read(
            "MATCH (f:FoodItem {is_published: true})-[:SUITABLE_FOR]->(:EventCategory {id: $cid})" + _LOAD,
            cid=category_id)
        return [_to_item(r) for r in records]
