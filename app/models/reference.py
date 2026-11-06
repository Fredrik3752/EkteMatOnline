"""Reference data: allergens and dietary labels (event categories live in event_category.py)."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Allergen:
    id: int
    code: str
    name: str


@dataclass(frozen=True)
class DietaryLabel:
    id: int
    code: str
    name: str
