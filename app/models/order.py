from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import List, Optional

from app.models.errors import InvalidStatusTransition, ValidationError
from app.models.money import format_nok


class OrderStatus(str, Enum):
    SUBMITTED = "submitted"
    APPROVED = "approved"
    IN_PREPARATION = "in_preparation"
    DELIVERED = "delivered"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

    @property
    def label(self) -> str:
        return _STATUS_LABELS[self]

    @property
    def is_final(self) -> bool:
        return not ALLOWED_TRANSITIONS[self]

    @property
    def action_label(self) -> str:
        """Button text for moving an order INTO this status."""
        return _ACTION_LABELS[self]

    @property
    def needs_confirmation(self) -> bool:
        return self in (OrderStatus.REJECTED, OrderStatus.CANCELLED)


_STATUS_LABELS = {
    OrderStatus.SUBMITTED: "Sendt inn",
    OrderStatus.APPROVED: "Godkjent",
    OrderStatus.IN_PREPARATION: "Under tilberedning",
    OrderStatus.DELIVERED: "Levert",
    OrderStatus.REJECTED: "Avvist",
    OrderStatus.CANCELLED: "Avbestilt",
}

_ACTION_LABELS = {
    OrderStatus.SUBMITTED: "Sett til sendt inn",
    OrderStatus.APPROVED: "Godkjenn",
    OrderStatus.IN_PREPARATION: "Start tilberedning",
    OrderStatus.DELIVERED: "Marker som levert",
    OrderStatus.REJECTED: "Avvis",
    OrderStatus.CANCELLED: "Kanseller",
}

# State machine for order status (requirement A3).
ALLOWED_TRANSITIONS = {
    OrderStatus.SUBMITTED: {OrderStatus.APPROVED, OrderStatus.REJECTED, OrderStatus.CANCELLED},
    OrderStatus.APPROVED: {OrderStatus.IN_PREPARATION, OrderStatus.CANCELLED},
    OrderStatus.IN_PREPARATION: {OrderStatus.DELIVERED, OrderStatus.CANCELLED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.REJECTED: set(),
    OrderStatus.CANCELLED: set(),
}


class PaymentStatus(str, Enum):
    NOT_PAID = "not_paid"
    DEPOSIT_PAID = "deposit_paid"
    INVOICED = "invoiced"
    PAID = "paid"

    @property
    def label(self) -> str:
        return {
            PaymentStatus.NOT_PAID: "Ikke betalt",
            PaymentStatus.DEPOSIT_PAID: "Depositum betalt",
            PaymentStatus.INVOICED: "Fakturert",
            PaymentStatus.PAID: "Betalt",
        }[self]


@dataclass
class OrderLine:
    """A food item on an order. Name and price are copied at order time."""

    item_name: str
    quantity: int
    unit_price_ore: int
    food_item_id: Optional[int] = None
    id: Optional[int] = None

    @property
    def line_total_ore(self) -> int:
        return self.quantity * self.unit_price_ore


@dataclass
class GuestGroup:
    """Allergies and diets per group of guests, not per named guest (GDPR art. 9)."""

    description: str
    guest_count: int
    allergy_notes: str = ""
    dietary_notes: str = ""
    id: Optional[int] = None


@dataclass
class Order:
    customer_id: int
    event_date: date
    guest_count: int
    delivery_address: str
    lines: List[OrderLine] = field(default_factory=list)
    guest_groups: List[GuestGroup] = field(default_factory=list)
    notes: str = ""
    status: OrderStatus = OrderStatus.SUBMITTED
    payment_status: PaymentStatus = PaymentStatus.NOT_PAID
    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @property
    def total_ore(self) -> int:
        return sum(line.line_total_ore for line in self.lines)

    @property
    def total_display(self) -> str:
        return format_nok(self.total_ore)

    def allowed_next_statuses(self):
        return sorted(ALLOWED_TRANSITIONS[self.status], key=lambda s: list(OrderStatus).index(s))

    def change_status(self, new_status) -> None:
        new_status = OrderStatus(new_status)
        if new_status not in ALLOWED_TRANSITIONS[self.status]:
            raise InvalidStatusTransition(
                f"Kan ikke endre status fra «{self.status.label}» til «{new_status.label}»."
            )
        self.status = new_status

    def change_payment_status(self, new_status) -> None:
        self.payment_status = PaymentStatus(new_status)

    @property
    def can_be_cancelled_by_customer(self) -> bool:
        return self.status == OrderStatus.SUBMITTED

    def validate(self, today: Optional[date] = None) -> None:
        """Rules for a new order. Pass `today` to also reject past event dates."""
        errors = {}
        if not isinstance(self.event_date, date):
            errors["event_date"] = "Oppgi en gyldig dato."
        elif today is not None and self.event_date <= today:
            errors["event_date"] = "Arrangementet må være etter i dag."
        if not isinstance(self.guest_count, int) or self.guest_count < 1:
            errors["guest_count"] = "Antall gjester må være minst 1."
        if not (self.delivery_address or "").strip():
            errors["delivery_address"] = "Leveringsadresse må fylles ut."
        if not self.lines:
            errors["lines"] = "Bestillingen må inneholde minst én vare."
        elif any(line.quantity < 1 for line in self.lines):
            errors["lines"] = "Antall må være minst 1."
        for group in self.guest_groups:
            if not (group.description or "").strip() or group.guest_count < 1:
                errors["guest_groups"] = "Hver gjestegruppe må ha beskrivelse og minst 1 gjest."
                break
        if self.guest_groups and isinstance(self.guest_count, int) and \
                sum(g.guest_count for g in self.guest_groups) > self.guest_count:
            errors["guest_groups"] = "Gjestegruppene har flere gjester enn bestillingen."
        if errors:
            raise ValidationError(errors)
