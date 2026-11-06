from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.models.errors import ValidationError

MAX_QUESTION_LENGTH = 2000
MAX_ANSWER_LENGTH = 4000


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
        body = (self.body or "").strip()
        if not body:
            raise ValidationError({"body": "Spørsmålet kan ikke være tomt."})
        if len(body) > MAX_QUESTION_LENGTH:
            raise ValidationError({"body": f"Spørsmålet kan være høyst {MAX_QUESTION_LENGTH} tegn."})

    def give_answer(self, text: str, admin_id: int, when: Optional[datetime] = None) -> None:
        if self.is_answered:
            # Prevents two staff members from silently overwriting each other's answer.
            raise ValidationError({"answer": "Spørsmålet er allerede besvart."})
        text = (text or "").strip()
        if not text:
            raise ValidationError({"answer": "Svaret kan ikke være tomt."})
        if len(text) > MAX_ANSWER_LENGTH:
            raise ValidationError({"answer": f"Svaret kan være høyst {MAX_ANSWER_LENGTH} tegn."})
        self.answer = text
        self.answered_by = admin_id
        # Stored in UTC like SQLite CURRENT_TIMESTAMP, so all timestamps are comparable.
        moment = (when or datetime.now(timezone.utc)).astimezone(timezone.utc)
        self.answered_at = moment.strftime("%Y-%m-%d %H:%M:%S")
