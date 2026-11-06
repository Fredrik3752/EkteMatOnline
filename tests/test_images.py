"""A2: upload a picture, preview it, then save (or discard)."""
import io
import os

import pytest

from app.models.errors import ValidationError
from app.models.image import MAX_IMAGE_BYTES, detect_image_type, validate_image
from app.models.repositories.food_item_repository import FoodItemRepository
from tests.conftest import CSRF, login, post

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
WEBP = b"RIFF\x24\x00\x00\x00WEBPVP8 " + b"\x00" * 64


# -- domain ---------------------------------------------------------------------

@pytest.mark.parametrize("data, ext", [(PNG, "png"), (JPEG, "jpg"), (WEBP, "webp")])
def test_detect_image_type(data, ext):
    assert detect_image_type(data) == ext


@pytest.mark.parametrize("data", [b"hello world", b"GIF89a" + b"\x00" * 20, b"<svg></svg>", b"RIFF1234WAVE"])
def test_rejects_non_images(data):
    with pytest.raises(ValidationError):
        detect_image_type(data)


def test_validate_image_size_and_empty():
    with pytest.raises(ValidationError) as exc:
        validate_image(b"")
    assert "Velg en bildefil" in exc.value.errors["image"]
    with pytest.raises(ValidationError) as exc:
        validate_image(PNG + b"\x00" * MAX_IMAGE_BYTES)
    assert "for stort" in exc.value.errors["image"]


# -- helpers --------------------------------------------------------------------

@pytest.fixture
def admin_client(client, admin):
    login(client, "admin@example.test")
    return client


@pytest.fixture
def item(menu_items):
    return menu_items["suppe"]


def upload(client, item_id, data=PNG, filename="bilde.png"):
    with client.session_transaction() as sess:  # login clears the session, incl. the CSRF token
        sess["csrf_token"] = CSRF
    return client.post(
        f"/admin/matretter/{item_id}/bilde/forhandsvis",
        data={"csrf_token": CSRF, "image": (io.BytesIO(data), filename)},
        content_type="multipart/form-data",
    )


def pending(client):
    with client.session_transaction() as sess:
        return sess.get("image_preview")


def get_item(app, item_id):
    with app.app_context():
        return FoodItemRepository().get(item_id)


def files_in(path):
    return sorted(os.listdir(path)) if os.path.isdir(path) else []


# -- upload and preview -----------------------------------------------------------

def test_image_page(admin_client, item):
    html = admin_client.get(f"/admin/matretter/{item.id}/bilde").get_data(as_text=True)
    assert "Last opp nytt bilde" in html and 'enctype="multipart/form-data"' in html
    assert 'accept="image/jpeg,image/png,image/webp"' in html
    assert "Retten har ikke bilde" in html


def test_upload_creates_preview_but_does_not_save(app, admin_client, item):
    response = upload(admin_client, item.id)
    assert response.status_code == 302
    assert response.headers["Location"] == f"/admin/matretter/{item.id}/bilde/forhandsvisning"
    preview = pending(admin_client)
    assert preview["item_id"] == item.id and preview["ext"] == "png"
    assert files_in(app.config["IMAGE_PREVIEW_DIR"]) == [f"{preview['token']}.png"]
    assert get_item(app, item.id).image_path is None          # not saved yet
    assert files_in(app.config["IMAGE_UPLOAD_DIR"]) == []      # nothing public yet


def test_preview_page_shows_current_and_new(admin_client, item):
    upload(admin_client, item.id)
    token = pending(admin_client)["token"]
    html = admin_client.get(f"/admin/matretter/{item.id}/bilde/forhandsvisning").get_data(as_text=True)
    assert "ikke lagret ennå" in html
    assert f'src="/admin/bilder/forhandsvisning/{token}.png"' in html
    assert f'name="token" value="{token}"' in html
    assert "Lagre bildet" in html and "Forkast" in html


def test_preview_file_is_served_to_admin_only(client, admin, customer, item):
    login(client, "admin@example.test")
    upload(client, item.id)
    token = pending(client)["token"]
    response = client.get(f"/admin/bilder/forhandsvisning/{token}.png")
    assert response.status_code == 200 and response.mimetype == "image/png"
    assert response.data == PNG and response.headers["Cache-Control"] == "no-store"

    post(client, "/logg-ut")
    login(client, "kunde@example.test")
    assert client.get(f"/admin/bilder/forhandsvisning/{token}.png").status_code == 403


@pytest.mark.parametrize("path", ["0" * 32 + ".png", "../../etc/passwd.png", "abc.png", "0" * 32 + ".exe"])
def test_preview_file_bad_token_is_404(admin_client, path):
    assert admin_client.get(f"/admin/bilder/forhandsvisning/{path}").status_code == 404


def test_preview_page_without_upload_redirects(admin_client, item):
    response = admin_client.get(f"/admin/matretter/{item.id}/bilde/forhandsvisning")
    assert response.status_code == 302 and response.headers["Location"] == f"/admin/matretter/{item.id}/bilde"


@pytest.mark.parametrize("data, filename, message", [
    (b"not an image", "bilde.png", "JPEG, PNG eller WebP"),   # wrong content despite .png name
    (b"GIF89a" + b"\x00" * 20, "anim.gif", "JPEG, PNG eller WebP"),
    (b"", "tom.png", "Velg en bildefil"),
])
def test_invalid_upload(app, admin_client, item, data, filename, message):
    response = upload(admin_client, item.id, data, filename)
    assert response.status_code == 400
    assert message in response.get_data(as_text=True)
    assert pending(admin_client) is None
    assert files_in(app.config["IMAGE_PREVIEW_DIR"]) == []


def test_missing_file_field(admin_client, item):
    response = post(admin_client, f"/admin/matretter/{item.id}/bilde/forhandsvis")
    assert response.status_code == 400 and "Velg en bildefil" in response.get_data(as_text=True)


def test_too_large_upload(app, admin_client, item):
    big = PNG + b"\x00" * (MAX_IMAGE_BYTES + 10)  # below MAX_CONTENT_LENGTH, above our limit
    response = upload(admin_client, item.id, big)
    assert response.status_code == 400 and "for stort" in response.get_data(as_text=True)


def test_request_above_max_content_length_is_413(app, admin_client, item):
    huge = PNG + b"\x00" * (app.config["MAX_CONTENT_LENGTH"] + 10)
    response = upload(admin_client, item.id, huge)
    assert response.status_code == 413
    assert "Filen er for stor" in response.get_data(as_text=True)


def test_user_filename_is_never_used(app, admin_client, item):
    upload(admin_client, item.id, filename="../../../evil.png")
    token = pending(admin_client)["token"]
    post(admin_client, f"/admin/matretter/{item.id}/bilde/lagre", {"token": token})
    [saved] = files_in(app.config["IMAGE_UPLOAD_DIR"])
    assert "evil" not in saved and saved.startswith(f"{item.id}-") and saved.endswith(".png")


# -- save, discard, replace, remove -----------------------------------------------

def test_save_preview(app, admin_client, item):
    upload(admin_client, item.id)
    token = pending(admin_client)["token"]
    response = post(admin_client, f"/admin/matretter/{item.id}/bilde/lagre", {"token": token})
    assert response.status_code == 302

    saved = get_item(app, item.id)
    assert saved.image_path.startswith("uploads/food/") and saved.image_path.endswith(".png")
    filename = saved.image_path.rsplit("/", 1)[1]
    assert files_in(app.config["IMAGE_UPLOAD_DIR"]) == [filename]
    with open(os.path.join(app.config["IMAGE_UPLOAD_DIR"], filename), "rb") as f:
        assert f.read() == PNG
    assert files_in(app.config["IMAGE_PREVIEW_DIR"]) == []
    assert pending(admin_client) is None


def test_saved_image_is_shown_on_menu_and_admin(app, client, admin, item):
    login(client, "admin@example.test")
    upload(client, item.id)
    post(client, f"/admin/matretter/{item.id}/bilde/lagre", {"token": pending(client)["token"]})
    path = get_item(app, item.id).image_path
    assert f'src="/static/{path}"' in client.get("/meny/wedding").get_data(as_text=True)
    assert f'src="/static/{path}"' in client.get("/admin/matretter").get_data(as_text=True)


def test_save_without_preview_is_refused(app, admin_client, item):
    html = post(admin_client, f"/admin/matretter/{item.id}/bilde/lagre", {"token": "0" * 32},
                follow_redirects=True).get_data(as_text=True)
    assert "finnes ikke lenger" in html
    assert get_item(app, item.id).image_path is None


def test_save_with_wrong_token_is_refused(app, admin_client, item):
    upload(admin_client, item.id)
    post(admin_client, f"/admin/matretter/{item.id}/bilde/lagre", {"token": "f" * 32})
    assert get_item(app, item.id).image_path is None


def test_preview_cannot_be_saved_on_another_item(app, admin_client, menu_items):
    suppe, kake = menu_items["suppe"], menu_items["kake"]
    upload(admin_client, suppe.id)
    token = pending(admin_client)["token"]
    post(admin_client, f"/admin/matretter/{kake.id}/bilde/lagre", {"token": token})
    assert get_item(app, kake.id).image_path is None
    assert get_item(app, suppe.id).image_path is None


def test_discard_preview(app, admin_client, item):
    upload(admin_client, item.id)
    response = post(admin_client, f"/admin/matretter/{item.id}/bilde/forkast", follow_redirects=True)
    assert "Bildet er ikke endret" in response.get_data(as_text=True)
    assert files_in(app.config["IMAGE_PREVIEW_DIR"]) == []
    assert pending(admin_client) is None
    assert get_item(app, item.id).image_path is None


def test_new_upload_replaces_old_preview(app, admin_client, item):
    upload(admin_client, item.id, PNG)
    upload(admin_client, item.id, JPEG, "ny.jpg")
    assert files_in(app.config["IMAGE_PREVIEW_DIR"]) == [f"{pending(admin_client)['token']}.jpg"]


def test_replacing_image_deletes_old_file(app, admin_client, item):
    upload(admin_client, item.id, PNG)
    post(admin_client, f"/admin/matretter/{item.id}/bilde/lagre", {"token": pending(admin_client)["token"]})
    first = get_item(app, item.id).image_path
    upload(admin_client, item.id, JPEG, "ny.jpg")
    post(admin_client, f"/admin/matretter/{item.id}/bilde/lagre", {"token": pending(admin_client)["token"]})
    second = get_item(app, item.id).image_path
    assert second != first and second.endswith(".jpg")
    assert files_in(app.config["IMAGE_UPLOAD_DIR"]) == [second.rsplit("/", 1)[1]]


def test_remove_image(app, admin_client, item):
    upload(admin_client, item.id)
    post(admin_client, f"/admin/matretter/{item.id}/bilde/lagre", {"token": pending(admin_client)["token"]})
    post(admin_client, f"/admin/matretter/{item.id}/bilde/fjern")
    assert get_item(app, item.id).image_path is None
    assert files_in(app.config["IMAGE_UPLOAD_DIR"]) == []


def test_remove_never_deletes_files_outside_uploads(app, admin_client, item):
    with app.app_context():
        fresh = FoodItemRepository().get(item.id)
        fresh.image_path = "css/style.css"
        FoodItemRepository().update(fresh)
    post(admin_client, f"/admin/matretter/{item.id}/bilde/fjern")
    assert os.path.isfile(os.path.join(app.static_folder, "css", "style.css"))
    assert get_item(app, item.id).image_path is None


def test_deleting_item_deletes_its_image(app, admin_client, item):
    upload(admin_client, item.id)
    post(admin_client, f"/admin/matretter/{item.id}/bilde/lagre", {"token": pending(admin_client)["token"]})
    post(admin_client, f"/admin/matretter/{item.id}/slett")
    assert files_in(app.config["IMAGE_UPLOAD_DIR"]) == []


def test_editing_item_keeps_image(app, admin_client, item):
    upload(admin_client, item.id)
    post(admin_client, f"/admin/matretter/{item.id}/bilde/lagre", {"token": pending(admin_client)["token"]})
    path = get_item(app, item.id).image_path
    html = admin_client.get(f"/admin/matretter/{item.id}/rediger").get_data(as_text=True)
    assert "Endre bilde" in html
    with app.app_context():
        wedding_id = get_item(app, item.id).categories[0].id
    post(admin_client, f"/admin/matretter/{item.id}/rediger",
         {"name": "Ny suppe", "price": "200", "min_order_qty": "10", "categories": [wedding_id]})
    assert get_item(app, item.id).image_path == path


# -- access and CSRF --------------------------------------------------------------

def test_upload_requires_csrf(app, admin_client, item):
    response = admin_client.post(f"/admin/matretter/{item.id}/bilde/forhandsvis",
                                 data={"image": (io.BytesIO(PNG), "bilde.png")},
                                 content_type="multipart/form-data")
    assert response.status_code == 400
    assert files_in(app.config["IMAGE_PREVIEW_DIR"]) == []


@pytest.mark.parametrize("method, suffix", [
    ("get", "bilde"), ("post", "bilde/forhandsvis"), ("get", "bilde/forhandsvisning"),
    ("post", "bilde/lagre"), ("post", "bilde/forkast"), ("post", "bilde/fjern"),
])
def test_customer_is_forbidden(client, customer, item, method, suffix):
    login(client, "kunde@example.test")
    url = f"/admin/matretter/{item.id}/{suffix}"
    response = client.get(url) if method == "get" else post(client, url)
    assert response.status_code == 403


@pytest.mark.parametrize("method, suffix", [("get", "bilde"), ("post", "bilde/forhandsvis"), ("post", "bilde/fjern")])
def test_unknown_item_is_404(admin_client, method, suffix):
    url = f"/admin/matretter/999/{suffix}"
    response = admin_client.get(url) if method == "get" else post(admin_client, url)
    assert response.status_code == 404


def test_seed_removes_orphaned_uploads(app, admin_client, item):
    from app.seed import seed_database
    upload(admin_client, item.id)
    post(admin_client, f"/admin/matretter/{item.id}/bilde/lagre", {"token": pending(admin_client)["token"]})
    upload_dir = app.config["IMAGE_UPLOAD_DIR"]
    open(os.path.join(upload_dir, ".gitkeep"), "w").close()
    with app.app_context():
        seed_database()
    assert files_in(upload_dir) == [".gitkeep"]
