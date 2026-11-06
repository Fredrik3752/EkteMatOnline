from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.models.errors import ValidationError


@dataclass
class Question:
    """A customer's question about one order, and Ekte Mat's answer (A4, C5)."""

    order_id: int
    author_id: int
    body: str
    answer: Optional[str] = None
    answered_by: Optional[int] = None
    answered_at: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[str] = None

    @property
    def is_answered(self) -> bool:
        return bool(self.answer)

    def validate(self) -> None:
        if not (self.body or "").strip():
            raise ValidationError({"body": "Spørsmålet kan ikke være tomt."})

    def give_answer(self, text: str, admin_id: int, when: Optional[datetime] = None) -> None:
        if not (text or "").strip():
            raise ValidationError({"answer": "Svaret kan ikke være tomt."})
        self.answer = text.strip()
        self.answered_by = admin_id
        # Stored in UTC like SQLite CURRENT_TIMESTAMP, so all timestamps are comparable.
        moment = (when or datetime.now(timezone.utc)).astimezone(timezone.utc)
        self.answered_at = moment.strftime("%Y-%m-%d %H:%M:%S")
