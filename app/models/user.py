from dataclasses import dataclass
from typing import Optional

from werkzeug.security import check_password_hash, generate_password_hash

from app.models.errors import ValidationError

ROLE_CUSTOMER = "customer"
ROLE_ADMIN = "admin"
MIN_PASSWORD_LENGTH = 8
# pbkdf2 works on every Python build (scrypt is missing on some, e.g. macOS system Python).
HASH_METHOD = "pbkdf2:sha256"


@dataclass
class User:
    email: str
    name: str
    password_hash: str = ""
    phone: Optional[str] = None
    role: str = ROLE_CUSTOMER
    id: Optional[int] = None
    created_at: Optional[str] = None

    @classmethod
    def create(cls, email, name, password, phone=None, role=ROLE_CUSTOMER):
        """Build a new, validated user with a hashed password."""
        user = cls(email=(email or "").strip().lower(), name=(name or "").strip(),
                   phone=(phone or "").strip() or None, role=role)
        errors = user._field_errors()
        if not password or len(password) < MIN_PASSWORD_LENGTH:
            errors["password"] = f"Passordet må ha minst {MIN_PASSWORD_LENGTH} tegn."
        if errors:
            raise ValidationError(errors)
        user.set_password(password)
        return user

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password, method=HASH_METHOD)

    def check_password(self, password: str) -> bool:
        return bool(self.password_hash) and check_password_hash(self.password_hash, password)

    def _field_errors(self):
        errors = {}
        if "@" not in self.email or "." not in self.email.split("@")[-1]:
            errors["email"] = "Oppgi en gyldig e-postadresse."
        if not self.name:
            errors["name"] = "Navn må fylles ut."
        if self.role not in (ROLE_CUSTOMER, ROLE_ADMIN):
            errors["role"] = "Ukjent rolle."
        return errors
