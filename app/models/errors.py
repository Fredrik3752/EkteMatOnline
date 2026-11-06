"""Domain errors. Controllers catch these and show the message to the user."""


class DomainError(Exception):
    """Base class for rule violations in the domain."""


class ValidationError(DomainError):
    """One or more fields are invalid. `errors` maps field name -> message."""

    def __init__(self, errors):
        self.errors = dict(errors)
        super().__init__("; ".join(f"{k}: {v}" for k, v in self.errors.items()))


class InvalidStatusTransition(DomainError):
    """An order status change that the state machine does not allow."""
