"""Repository contracts.

Every storage backend (SQLite, Neo4j) implements these. Controllers only ever see these
methods and the domain objects they return, so the backend can be swapped through
configuration (STORAGE_BACKEND) without touching controllers or views.
"""
from abc import ABC, abstractmethod
from collections import OrderedDict
from datetime import date
from typing import Dict, Iterable, List, Optional

from app.models.event_category import EventCategory
from app.models.food_item import FoodItem
from app.models.order import Order
from app.models.question import Question
from app.models.reference import Allergen, DietaryLabel
from app.models.user import User


class EventCategoryRepositoryBase(ABC):
    @abstractmethod
    def list_all(self) -> List[EventCategory]:
        """All categories ordered by sort_order, then name."""

    @abstractmethod
    def get_by_slug(self, slug: str) -> Optional[EventCategory]:
        ...


class AllergenRepositoryBase(ABC):
    @abstractmethod
    def list_all(self) -> List[Allergen]:
        """All allergens in their fixed order (by id)."""


class DietaryLabelRepositoryBase(ABC):
    @abstractmethod
    def list_all(self) -> List[DietaryLabel]:
        """All dietary labels in their fixed order (by id)."""


class UserRepositoryBase(ABC):
    @abstractmethod
    def add(self, user: User) -> User:
        """Store a new user. Raises ValidationError({'email': ...}) if the e-mail is taken."""

    @abstractmethod
    def get(self, user_id: int) -> Optional[User]:
        ...

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Case-insensitive, surrounding whitespace ignored."""

    @abstractmethod
    def get_many(self, user_ids: Iterable[int]) -> Dict[int, User]:
        ...

    @abstractmethod
    def list_customers(self) -> List[User]:
        """Users with role 'customer', ordered by name."""


class FoodItemRepositoryBase(ABC):
    @abstractmethod
    def add(self, item: FoodItem) -> FoodItem:
        """Validate and store a new item with its category/allergen/diet links."""

    @abstractmethod
    def update(self, item: FoodItem) -> FoodItem:
        """Validate and replace all fields and links of an existing item."""

    @abstractmethod
    def delete(self, item_id: int) -> bool:
        """Delete the item. Existing order lines keep name and price (food_item_id becomes None)."""

    @abstractmethod
    def get(self, item_id: int) -> Optional[FoodItem]:
        ...

    @abstractmethod
    def get_many(self, item_ids: Iterable[int]) -> Dict[int, FoodItem]:
        ...

    @abstractmethod
    def list_all(self, published_only: bool = False) -> List[FoodItem]:
        """Ordered by name."""

    @abstractmethod
    def list_published_in_category(self, category_id: int) -> List[FoodItem]:
        """Published items in one category, ordered by name."""

    def list_published_by_category(self) -> "OrderedDict[EventCategory, List[FoodItem]]":
        """C1: published items grouped by event category, in category order. Same for every backend."""
        items = self.list_all(published_only=True)
        groups: "OrderedDict[EventCategory, List[FoodItem]]" = OrderedDict()
        for category in sorted({c for item in items for c in item.categories},
                               key=lambda c: (c.sort_order, c.name)):
            groups[category] = [i for i in items if category in i.categories]
        return groups


class OrderRepositoryBase(ABC):
    @abstractmethod
    def add(self, order: Order) -> Order:
        """Validate and store order, lines and guest groups atomically (all or nothing)."""

    @abstractmethod
    def get(self, order_id: int) -> Optional[Order]:
        ...

    @abstractmethod
    def list(self, status=None, date_from: Optional[date] = None,
             date_to: Optional[date] = None) -> List[Order]:
        """All orders, optionally filtered; ordered by event date, then id."""

    @abstractmethod
    def list_for_customer(self, customer_id: int) -> List[Order]:
        """A customer's orders, newest event first (then highest id)."""

    @abstractmethod
    def save_status(self, order: Order) -> Order:
        """Persist status and payment status (already validated by the domain)."""


class QuestionRepositoryBase(ABC):
    @abstractmethod
    def add(self, question: Question) -> Question:
        ...

    @abstractmethod
    def get(self, question_id: int) -> Optional[Question]:
        ...

    @abstractmethod
    def list_for_order(self, order_id: int) -> List[Question]:
        """Oldest first."""

    @abstractmethod
    def list_all(self, unanswered_only: bool = False) -> List[Question]:
        """Newest first."""

    @abstractmethod
    def count_unanswered(self) -> int:
        ...

    @abstractmethod
    def save_answer(self, question: Question) -> Question:
        ...
