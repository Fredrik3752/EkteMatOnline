from typing import List, Optional

from app.models.event_category import EventCategory
from app.models.reference import Allergen, DietaryLabel
from app.models.repositories.base import (AllergenRepositoryBase, DietaryLabelRepositoryBase,
                                          EventCategoryRepositoryBase)
from app.models.repositories.neo4j.driver import read


def to_category(m) -> EventCategory:
    return EventCategory(id=m["id"], slug=m["slug"], name=m["name"], sort_order=m["sort_order"])


def to_allergen(m) -> Allergen:
    return Allergen(id=m["id"], code=m["code"], name=m["name"])


def to_dietary_label(m) -> DietaryLabel:
    return DietaryLabel(id=m["id"], code=m["code"], name=m["name"])


class Neo4jEventCategoryRepository(EventCategoryRepositoryBase):
    def list_all(self) -> List[EventCategory]:
        records = read("MATCH (c:EventCategory) RETURN c{.*} AS c ORDER BY c.sort_order, c.name")
        return [to_category(r["c"]) for r in records]

    def get_by_slug(self, slug: str) -> Optional[EventCategory]:
        records = read("MATCH (c:EventCategory {slug: $slug}) RETURN c{.*} AS c", slug=slug)
        return to_category(records[0]["c"]) if records else None


class Neo4jAllergenRepository(AllergenRepositoryBase):
    def list_all(self) -> List[Allergen]:
        return [to_allergen(r["a"]) for r in read("MATCH (a:Allergen) RETURN a{.*} AS a ORDER BY a.id")]


class Neo4jDietaryLabelRepository(DietaryLabelRepositoryBase):
    def list_all(self) -> List[DietaryLabel]:
        return [to_dietary_label(r["d"]) for r in read("MATCH (d:DietaryLabel) RETURN d{.*} AS d ORDER BY d.id")]
