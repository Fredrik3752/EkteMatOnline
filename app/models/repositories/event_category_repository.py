"""Public repository name used by controllers. The class is chosen by STORAGE_BACKEND."""
from app.models.repositories.backend import implementation
from app.models.repositories.base import EventCategoryRepositoryBase


class EventCategoryRepository(EventCategoryRepositoryBase):
    """Repository for event categories.

    `EventCategoryRepository()` returns the implementation for the configured backend
    (SqliteEventCategoryRepository or Neo4jEventCategoryRepository); see base.EventCategoryRepositoryBase for the contract.
    """

    def __new__(cls, *args, **kwargs):
        return implementation("EventCategoryRepository")(*args, **kwargs)
