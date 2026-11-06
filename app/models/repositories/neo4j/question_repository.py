from typing import List, Optional

from app.models.question import Question
from app.models.repositories.base import QuestionRepositoryBase
from app.models.repositories.neo4j.driver import next_id, read, utc_now, write

_MATCH = ("MATCH (author:User)-[:ASKED]->(q:Question)-[:ABOUT]->(o:Order) "
          "OPTIONAL MATCH (admin:User)-[:ANSWERED]->(q) ")
_RETURN = "RETURN q{.*, order_id: o.id, author_id: author.id, answered_by: admin.id} AS q"


def _to_question(m) -> Question:
    return Question(id=m["id"], order_id=m["order_id"], author_id=m["author_id"], body=m["body"],
                    created_at=m.get("created_at"), answer=m.get("answer"),
                    answered_by=m.get("answered_by"), answered_at=m.get("answered_at"))


class Neo4jQuestionRepository(QuestionRepositoryBase):
    """(:User)-[:ASKED]->(:Question)-[:ABOUT]->(:Order), (:User)-[:ANSWERED]->(:Question)."""

    def add(self, question: Question) -> Question:
        question.validate()

        def work(tx):
            question_id = next_id(tx, "Question")
            created = tx.run(
                "MATCH (u:User {id: $author_id}), (o:Order {id: $order_id}) "
                "CREATE (u)-[:ASKED]->(q:Question {id: $id, body: $body, created_at: $now})-[:ABOUT]->(o) "
                "RETURN q.id AS id",
                author_id=question.author_id, order_id=question.order_id, id=question_id,
                body=question.body.strip(), now=utc_now(),
            ).single()
            if created is None:  # same effect as SQLite's foreign keys
                raise ValueError("Unknown author or order")
            return question_id
        return self.get(write(work))

    def get(self, question_id: int) -> Optional[Question]:
        records = read(_MATCH + "WITH q, o, author, admin WHERE q.id = $id " + _RETURN, id=question_id)
        return _to_question(records[0]["q"]) if records else None

    def list_for_order(self, order_id: int) -> List[Question]:
        records = read(_MATCH + "WITH q, o, author, admin WHERE o.id = $oid "
                       + _RETURN + " ORDER BY q.created_at, q.id", oid=order_id)
        return [_to_question(r["q"]) for r in records]

    def list_all(self, unanswered_only: bool = False) -> List[Question]:
        where = "WITH q, o, author, admin WHERE q.answer IS NULL " if unanswered_only else ""
        records = read(_MATCH + where + _RETURN + " ORDER BY q.created_at DESC, q.id DESC")
        return [_to_question(r["q"]) for r in records]

    def count_unanswered(self) -> int:
        return read("MATCH (q:Question) WHERE q.answer IS NULL RETURN count(q) AS n")[0]["n"]

    def save_answer(self, question: Question) -> Question:
        def work(tx):
            tx.run(
                "MATCH (q:Question {id: $id}) SET q.answer = $answer, q.answered_at = $answered_at "
                "WITH q OPTIONAL MATCH (:User)-[old:ANSWERED]->(q) DELETE old "
                "WITH DISTINCT q MATCH (a:User {id: $admin_id}) CREATE (a)-[:ANSWERED]->(q)",
                id=question.id, answer=question.answer, answered_at=question.answered_at,
                admin_id=question.answered_by,
            ).consume()
        write(work)
        return self.get(question.id)
