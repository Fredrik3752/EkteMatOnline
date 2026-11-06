from typing import List, Optional

from app.models.question import Question
from app.models.repositories.database import get_db

_COLUMNS = "id, order_id, author_id, body, created_at, answer, answered_by, answered_at"


class QuestionRepository:
    """Questions about orders and their answers (A4, C5)."""

    def add(self, question: Question) -> Question:
        question.validate()
        db = get_db()
        with db:
            cur = db.execute(
                "INSERT INTO questions (order_id, author_id, body) VALUES (?, ?, ?)",
                (question.order_id, question.author_id, question.body.strip()),
            )
        return self.get(cur.lastrowid)

    def get(self, question_id: int) -> Optional[Question]:
        row = get_db().execute(f"SELECT {_COLUMNS} FROM questions WHERE id = ?", (question_id,)).fetchone()
        return self._to_domain(row) if row else None

    def list_for_order(self, order_id: int) -> List[Question]:
        rows = get_db().execute(
            f"SELECT {_COLUMNS} FROM questions WHERE order_id = ? ORDER BY created_at, id", (order_id,)
        ).fetchall()
        return [self._to_domain(r) for r in rows]

    def list_all(self, unanswered_only: bool = False) -> List[Question]:
        where = "WHERE answer IS NULL" if unanswered_only else ""
        rows = get_db().execute(
            f"SELECT {_COLUMNS} FROM questions {where} ORDER BY created_at DESC, id DESC"
        ).fetchall()
        return [self._to_domain(r) for r in rows]

    def save_answer(self, question: Question) -> Question:
        db = get_db()
        with db:
            db.execute(
                "UPDATE questions SET answer = ?, answered_by = ?, answered_at = ? WHERE id = ?",
                (question.answer, question.answered_by, question.answered_at, question.id),
            )
        return self.get(question.id)

    @staticmethod
    def _to_domain(row) -> Question:
        return Question(id=row["id"], order_id=row["order_id"], author_id=row["author_id"],
                        body=row["body"], created_at=row["created_at"], answer=row["answer"],
                        answered_by=row["answered_by"], answered_at=row["answered_at"])
