from app.models.event_category import EventCategory
from app.models.repositories.event_category_repository import EventCategoryRepository


def test_list_all_returns_domain_objects_in_order(app):
    with app.app_context():
        categories = EventCategoryRepository().list_all()
    assert categories and all(isinstance(c, EventCategory) for c in categories)
    assert [c.sort_order for c in categories] == sorted(c.sort_order for c in categories)


def test_get_by_slug(app):
    with app.app_context():
        repo = EventCategoryRepository()
        assert repo.get_by_slug("wedding").name == "Bryllup"
        assert repo.get_by_slug("does-not-exist") is None
