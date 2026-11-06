def test_create_app_uses_test_config(app):
    assert app.config["TESTING"] is True
    assert app.config["DATABASE"].endswith("test.db")


def test_front_page_renders_categories(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Ekte Mat" in html
    assert "Bryllup" in html
    assert "Julebord" in html


def test_unknown_page_returns_404(client):
    assert client.get("/finnes-ikke").status_code == 404
