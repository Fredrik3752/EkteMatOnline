import sqlite3
from typing import Dict, List, Optional

from app.models.errors import ValidationError
from app.models.repositories.database import get_db
from app.models.user import ROLE_CUSTOMER, User

_COLUMNS = "id, email, name, phone, role, password_hash, created_at"


class UserRepository:
    def add(self, user: User) -> User:
        db = get_db()
        try:
            with db:
                cur = db.execute(
                    "INSERT INTO users (email, name, phone, role, password_hash) VALUES (?, ?, ?, ?, ?)",
                    (user.email, user.name, user.phone, user.role, user.password_hash),
                )
        except sqlite3.IntegrityError:
            raise ValidationError({"email": "Det finnes allerede en bruker med denne e-postadressen."})
        return self.get(cur.lastrowid)

    def get(self, user_id: int) -> Optional[User]:
        row = get_db().execute(f"SELECT {_COLUMNS} FROM users WHERE id = ?", (user_id,)).fetchone()
        return self._to_domain(row) if row else None

    def get_by_email(self, email: str) -> Optional[User]:
        row = get_db().execute(
            f"SELECT {_COLUMNS} FROM users WHERE email = ?", ((email or "").strip().lower(),)
        ).fetchone()
        return self._to_domain(row) if row else None

    def get_many(self, user_ids) -> Dict[int, User]:
        ids = list({int(i) for i in user_ids})
        if not ids:
            return {}
        placeholders = ",".join("?" * len(ids))
        rows = get_db().execute(f"SELECT {_COLUMNS} FROM users WHERE id IN ({placeholders})", ids).fetchall()
        return {r["id"]: self._to_domain(r) for r in rows}

    def list_customers(self) -> List[User]:
        rows = get_db().execute(
            f"SELECT {_COLUMNS} FROM users WHERE role = ? ORDER BY name", (ROLE_CUSTOMER,)
        ).fetchall()
        return [self._to_domain(r) for r in rows]

    @staticmethod
    def _to_domain(row) -> User:
        return User(id=row["id"], email=row["email"], name=row["name"], phone=row["phone"],
                    role=row["role"], password_hash=row["password_hash"], created_at=row["created_at"])
