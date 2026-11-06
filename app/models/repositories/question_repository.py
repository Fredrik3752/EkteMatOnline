"""Public repository name used by controllers. The class is chosen by STORAGE_BACKEND."""
from app.models.repositories.backend import implementation
from app.models.repositories.base import QuestionRepositoryBase


class QuestionRepository(QuestionRepositoryBase):
    """Repository for questions and answers (A4, C5).

    `QuestionRepository()` returns the implementation for the configured backend
    (SqliteQuestionRepository or Neo4jQuestionRepository); see base.QuestionRepositoryBase for the contract.
    """

    def __new__(cls, *args, **kwargs):
        return implementation("QuestionRepository")(*args, **kwargs)
