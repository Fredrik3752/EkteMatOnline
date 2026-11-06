"""Domain rules for food item pictures (A2)."""
from app.models.errors import ValidationError

MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_TYPES = {"jpg": "JPEG", "png": "PNG", "webp": "WebP"}


def detect_image_type(data: bytes) -> str:
    """Return 'jpg', 'png' or 'webp' based on the file content (magic bytes), never the filename."""
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    raise ValidationError({"image": "Filen må være et bilde i formatet JPEG, PNG eller WebP."})


def validate_image(data: bytes) -> str:
    """Check size and type. Returns the file extension to store the image with."""
    if not data:
        raise ValidationError({"image": "Velg en bildefil."})
    if len(data) > MAX_IMAGE_BYTES:
        raise ValidationError({"image": f"Bildet er for stort. Maks {MAX_IMAGE_BYTES // (1024 * 1024)} MB."})
    return detect_image_type(data)
