from dataclasses import dataclass


@dataclass(frozen=True)
class EventCategory:
    """A kind of event the food can be ordered for (wedding, julebord, ...)."""

    id: int
    slug: str
    name: str
    sort_order: int = 0
