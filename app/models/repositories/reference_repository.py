"""Public repository name used by controllers. The class is chosen by STORAGE_BACKEND."""
from app.models.repositories.backend import implementation
from app.models.repositories.base import AllergenRepositoryBase, DietaryLabelRepositoryBase


class AllergenRepository(AllergenRepositoryBase):
    """Repository for allergens.

    `AllergenRepository()` returns the implementation for the configured backend
    (SqliteAllergenRepository or Neo4jAllergenRepository); see base.AllergenRepositoryBase for the contract.
    """

    def __new__(cls, *args, **kwargs):
        return implementation("AllergenRepository")(*args, **kwargs)


class DietaryLabelRepository(DietaryLabelRepositoryBase):
    """Repository for dietary labels.

    `DietaryLabelRepository()` returns the implementation for the configured backend
    (SqliteDietaryLabelRepository or Neo4jDietaryLabelRepository); see base.DietaryLabelRepositoryBase for the contract.
    """

    def __new__(cls, *args, **kwargs):
        return implementation("DietaryLabelRepository")(*args, **kwargs)
