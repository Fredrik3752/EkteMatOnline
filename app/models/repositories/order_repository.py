"""Public repository name used by controllers. The class is chosen by STORAGE_BACKEND."""
from app.models.repositories.backend import implementation
from app.models.repositories.base import OrderRepositoryBase


class OrderRepository(OrderRepositoryBase):
    """Repository for orders with lines and guest groups (A3, C3, C4).

    `OrderRepository()` returns the implementation for the configured backend
    (SqliteOrderRepository or Neo4jOrderRepository); see base.OrderRepositoryBase for the contract.
    """

    def __new__(cls, *args, **kwargs):
        return implementation("OrderRepository")(*args, **kwargs)
