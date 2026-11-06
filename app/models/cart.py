"""Shopping cart (C2). Pure domain logic – where the quantities are stored is up to the caller."""
from dataclasses import dataclass, field
from typing import Dict, List, Mapping

from app.models.errors import ValidationError
from app.models.food_item import FoodItem
from app.models.money import format_nok
from app.models.order import OrderLine

MAX_QUANTITY = 10_000


def check_quantity(item: FoodItem, quantity) -> int:
    """Return the quantity as int, or raise ValidationError (C2: minimum order rule)."""
    try:
        qty = int(str(quantity).strip())
    except (TypeError, ValueError):
        raise ValidationError({"quantity": "Oppgi antall som et helt tall."})
    if qty < item.min_order_qty:
        raise ValidationError({"quantity": f"Minimum bestilling for «{item.name}» er {item.min_order_qty} stk."})
    if qty > MAX_QUANTITY:
        raise ValidationError({"quantity": f"Største antall per rett er {MAX_QUANTITY} stk. Kontakt oss for større bestillinger."})
    return qty


@dataclass
class CartLine:
    item: FoodItem
    quantity: int

    @property
    def line_total_ore(self) -> int:
        return self.item.price_ore * self.quantity

    @property
    def meets_minimum(self) -> bool:
        return self.item.accepts_quantity(self.quantity)


@dataclass
class Cart:
    lines: List[CartLine] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)  # names of items no longer available

    @classmethod
    def build(cls, quantities: Mapping, items: Dict[int, FoodItem]) -> "Cart":
        """Combine stored {item_id: qty} with current FoodItems. Drops unknown/unpublished items."""
        cart = cls()
        for raw_id, qty in quantities.items():
            item = items.get(int(raw_id))
            if item is None or not item.is_published:
                cart.removed.append(item.name if item else f"#{raw_id}")
                continue
            cart.lines.append(CartLine(item=item, quantity=int(qty)))
        cart.lines.sort(key=lambda line: line.item.name)
        return cart

    @property
    def is_empty(self) -> bool:
        return not self.lines

    @property
    def total_ore(self) -> int:
        return sum(line.line_total_ore for line in self.lines)

    @property
    def total_display(self) -> str:
        return format_nok(self.total_ore)

    @property
    def item_count(self) -> int:
        return len(self.lines)

    def problems(self) -> List[str]:
        """Lines that no longer meet the minimum (e.g. admin raised it after the item was added)."""
        return [
            f"«{line.item.name}» krever minst {line.item.min_order_qty} stk. – du har {line.quantity}."
            for line in self.lines if not line.meets_minimum
        ]

    def to_quantities(self) -> Dict[str, int]:
        return {str(line.item.id): line.quantity for line in self.lines}

    def to_order_lines(self) -> List[OrderLine]:
        """Copy name and price now, so later menu changes don't alter the order."""
        return [
            OrderLine(food_item_id=line.item.id, item_name=line.item.name,
                      quantity=line.quantity, unit_price_ore=line.item.price_ore)
            for line in self.lines
        ]
