from typing import Dict, List, Optional

from neo4j.exceptions import ConstraintError

from app.models.errors import ValidationError
from app.models.repositories.base import UserRepositoryBase
from app.models.repositories.neo4j.driver import next_id, read, utc_now, write
from app.models.user import ROLE_CUSTOMER, User


def to_user(m) -> User:
    return User(id=m["id"], email=m["email"], name=m["name"], phone=m.get("phone"),
                role=m["role"], password_hash=m["password_hash"], created_at=m.get("created_at"))


class Neo4jUserRepository(UserRepositoryBase):
    def add(self, user: User) -> User:
        def work(tx):
            user_id = next_id(tx, "User")
            tx.run("CREATE (:User {id: $id, email: $email, name: $name, phone: $phone, role: $role, "
                   "password_hash: $password_hash, created_at: $created_at})",
                   id=user_id, email=user.email, name=user.name, phone=user.phone, role=user.role,
                   password_hash=user.password_hash, created_at=utc_now()).consume()
            return user_id
        try:
            user_id = write(work)
        except ConstraintError:  # unique e-mail; the reserved id is simply skipped
            raise ValidationError({"email": "Det finnes allerede en bruker med denne e-postadressen."})
        return self.get(user_id)

    def get(self, user_id: int) -> Optional[User]:
        records = read("MATCH (u:User {id: $id}) RETURN u{.*} AS u", id=user_id)
        return to_user(records[0]["u"]) if records else None

    def get_by_email(self, email: str) -> Optional[User]:
        records = read("MATCH (u:User {email: $email}) RETURN u{.*} AS u",
                       email=(email or "").strip().lower())
        return to_user(records[0]["u"]) if records else None

    def get_many(self, user_ids) -> Dict[int, User]:
        ids = list({int(i) for i in user_ids})
        if not ids:
            return {}
        records = read("MATCH (u:User) WHERE u.id IN $ids RETURN u{.*} AS u", ids=ids)
        return {r["u"]["id"]: to_user(r["u"]) for r in records}

    def list_customers(self) -> List[User]:
        records = read("MATCH (u:User {role: $role}) RETURN u{.*} AS u ORDER BY u.name", role=ROLE_CUSTOMER)
        return [to_user(r["u"]) for r in records]
