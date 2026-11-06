from typing import List

from app.models.reference import Allergen, DietaryLabel
from app.models.repositories.base import AllergenRepositoryBase, DietaryLabelRepositoryBase
from app.models.repositories.sqlite.database import get_db


class SqliteAllergenRepository(AllergenRepositoryBase):
    def list_all(self) -> List[Allergen]:
        rows = get_db().execute("SELECT id, code, name FROM allergens ORDER BY id").fetchall()
        return [Allergen(id=r["id"], code=r["code"], name=r["name"]) for r in rows]


class SqliteDietaryLabelRepository(DietaryLabelRepositoryBase):
    def list_all(self) -> List[DietaryLabel]:
        rows = get_db().execute("SELECT id, code, name FROM dietary_labels ORDER BY id").fetchall()
        return [DietaryLabel(id=r["id"], code=r["code"], name=r["name"]) for r in rows]
