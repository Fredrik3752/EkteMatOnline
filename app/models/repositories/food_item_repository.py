"""Public repository name used by controllers. The class is chosen by STORAGE_BACKEND."""
from app.models.repositories.backend import implementation
from app.models.repositories.base import FoodItemRepositoryBase


class FoodItemRepository(FoodItemRepositoryBase):
    """Repository for food items (A1, C1).

    `FoodItemRepository()` returns the implementation for the configured backend
    (SqliteFoodItemRepository or Neo4jFoodItemRepository); see base.FoodItemRepositoryBase for the contract.
    """

    def __new__(cls, *args, **kwargs):
        return implementation("FoodItemRepository")(*args, **kwargs)
