"""Application configuration, read from environment variables (.env)."""
import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    # Relative paths are resolved against the Flask instance folder.
    DATABASE = os.environ.get("DATABASE", "ektemat.db")
    TESTING = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    TIMEZONE = "Europe/Oslo"  # stored timestamps are UTC; shown in this zone
    # A2 images: requests above this size are rejected before they are read (413).
    MAX_CONTENT_LENGTH = 6 * 1024 * 1024
    # Set in create_app when not given: <app>/static/uploads/food and <instance>/image_previews
    IMAGE_UPLOAD_DIR = None
    IMAGE_PREVIEW_DIR = None
