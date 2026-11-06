from dataclasses import dataclass, field
from typing import List, Optional

from app.models.errors import ValidationError
from app.models.event_category import EventCategory
from app.models.money import format_nok
from app.models.reference import Allergen, DietaryLabel


@dataclass
class FoodItem:
    """A dish or product Ekte Mat caters (requirement A1)."""

    name: str
    price_ore: int
    description: str = ""
    min_order_qty: int = 1
    is_published: bool = False
    image_path: Optional[str] = None
    origin: Optional[str] = None
    categories: List[EventCategory] = field(default_factory=list)
    allergens: List[Allergen] = field(default_factory=list)
    dietary_labels: List[DietaryLabel] = field(default_factory=list)
    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @property
    def price_display(self) -> str:
        return format_nok(self.price_ore)

    def accepts_quantity(self, quantity: int) -> bool:
        """C2: quantities below the minimum order are not accepted."""
        return isinstance(quantity, int) and quantity >= self.min_order_qty

    def validate(self) -> None:
        errors = {}
        if not (self.name or "").strip():
            errors["name"] = "Navn må fylles ut."
        if not isinstance(self.price_ore, int) or self.price_ore < 0:
            errors["price"] = "Prisen må være 0 kr eller mer."
        if not isinstance(self.min_order_qty, int) or self.min_order_qty < 1:
            errors["min_order_qty"] = "Minimum bestilling må være minst 1."
        if errors:
            raise ValidationError(errors)
