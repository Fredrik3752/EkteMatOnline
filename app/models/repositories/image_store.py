"""File storage for food item pictures (A2).

Like the database repositories, this is the only code that reads or writes image
files. Previews live in a private folder (not web-accessible) until the admin
saves them; saved pictures go to the public static folder.
"""
import os
import re
import secrets
import time
from typing import Optional

from flask import current_app

from app.models.image import ALLOWED_TYPES

PUBLIC_PREFIX = "uploads/food"  # path under /static, stored in food_items.image_path
_TOKEN = re.compile(r"^[0-9a-f]{32}$")
PREVIEW_MAX_AGE_SECONDS = 24 * 3600


class ImageStore:
    def __init__(self, upload_dir: Optional[str] = None, preview_dir: Optional[str] = None):
        cfg = current_app.config
        self.upload_dir = upload_dir or cfg["IMAGE_UPLOAD_DIR"]
        self.preview_dir = preview_dir or cfg["IMAGE_PREVIEW_DIR"]

    # -- previews (private, temporary) ---------------------------------------------

    def save_preview(self, data: bytes, ext: str) -> str:
        """Store a validated image as a private preview. Returns its token."""
        if ext not in ALLOWED_TYPES:
            raise ValueError(f"unsupported extension {ext!r}")
        os.makedirs(self.preview_dir, exist_ok=True)
        self._remove_stale_previews()
        token = secrets.token_hex(16)
        with open(self._preview_path(token, ext), "wb") as f:
            f.write(data)
        return token

    def preview_file(self, token: str, ext: str) -> Optional[str]:
        """Absolute path of a preview, or None if the token is invalid or gone."""
        if not self.is_valid_token(token) or ext not in ALLOWED_TYPES:
            return None
        path = self._preview_path(token, ext)
        return path if os.path.isfile(path) else None

    def discard_preview(self, token: str, ext: str) -> None:
        path = self.preview_file(token, ext)
        if path:
            os.remove(path)

    def promote_preview(self, token: str, ext: str, item_id: int) -> str:
        """Move a preview to the public folder. Returns the image_path to store on the item."""
        source = self.preview_file(token, ext)
        if source is None:
            raise FileNotFoundError("preview not found")
        os.makedirs(self.upload_dir, exist_ok=True)
        filename = f"{int(item_id)}-{secrets.token_hex(8)}.{ext}"
        os.replace(source, os.path.join(self.upload_dir, filename))
        return f"{PUBLIC_PREFIX}/{filename}"

    # -- saved pictures --------------------------------------------------------------

    def delete_public(self, image_path: Optional[str]) -> bool:
        """Delete a saved upload. Only files we created under uploads/food/ are ever deleted."""
        if not image_path or not image_path.startswith(PUBLIC_PREFIX + "/"):
            return False
        filename = image_path[len(PUBLIC_PREFIX) + 1:]
        if "/" in filename or "\\" in filename or filename.startswith("."):
            return False
        path = os.path.join(self.upload_dir, filename)
        if os.path.isfile(path):
            os.remove(path)
            return True
        return False

    def delete_all_public(self) -> int:
        """Remove every saved upload (used when the database is reset by `flask seed`)."""
        if not os.path.isdir(self.upload_dir):
            return 0
        removed = 0
        for name in os.listdir(self.upload_dir):
            if name.startswith("."):
                continue  # keep .gitkeep
            path = os.path.join(self.upload_dir, name)
            if os.path.isfile(path):
                os.remove(path)
                removed += 1
        return removed

    # -- helpers -------------------------------------------------------------------

    @staticmethod
    def is_valid_token(token: str) -> bool:
        return bool(token) and bool(_TOKEN.match(token))

    def _preview_path(self, token: str, ext: str) -> str:
        return os.path.join(self.preview_dir, f"{token}.{ext}")

    def _remove_stale_previews(self) -> None:
        cutoff = time.time() - PREVIEW_MAX_AGE_SECONDS
        for name in os.listdir(self.preview_dir):
            path = os.path.join(self.preview_dir, name)
            if os.path.isfile(path) and os.path.getmtime(path) < cutoff:
                os.remove(path)
