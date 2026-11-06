from typing import List, Optional

from app.models.event_category import EventCategory
from app.models.repositories.base import EventCategoryRepositoryBase
from app.models.repositories.sqlite.database import get_db


class SqliteEventCategoryRepository(EventCategoryRepositoryBase):
    """Reads event categories. Returns domain objects, never database rows."""

    def list_all(self) -> List[EventCategory]:
        rows = get_db().execute(
            "SELECT id, slug, name, sort_order FROM event_categories ORDER BY sort_order, name"
        ).fetchall()
        return [self._to_domain(r) for r in rows]

    def get_by_slug(self, slug: str) -> Optional[EventCategory]:
        row = get_db().execute(
            "SELECT id, slug, name, sort_order FROM event_categories WHERE slug = ?", (slug,)
        ).fetchone()
        return self._to_domain(row) if row else None

    @staticmethod
    def _to_domain(row) -> EventCategory:
        return EventCategory(id=row["id"], slug=row["slug"], name=row["name"], sort_order=row["sort_order"])
