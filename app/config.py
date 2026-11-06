"""Application configuration, read from environment variables (.env)."""
import os

from dotenv import load_dotenv

# Must run before the class body below reads os.environ – otherwise values in .env are ignored.
load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    # "sqlite" (default) or "neo4j" – see app/models/repositories/backend.py
    STORAGE_BACKEND = os.environ.get("STORAGE_BACKEND", "sqlite")
    # SQLite file. Relative paths are resolved against the Flask instance folder.
    DATABASE = os.environ.get("DATABASE", "ektemat.db")
    # Neo4j (used when STORAGE_BACKEND=neo4j). Values come from .env – see .env.example.
    NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "")
    NEO4J_DATABASE = os.environ.get("NEO4J_DATABASE", "neo4j")
    TESTING = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    TIMEZONE = "Europe/Oslo"  # stored timestamps are UTC; shown in this zone
    # A2 images: requests above this size are rejected before they are read (413).
    MAX_CONTENT_LENGTH = 6 * 1024 * 1024
    # Set in create_app when not given: <app>/static/uploads/food and <instance>/image_previews
    IMAGE_UPLOAD_DIR = None
    IMAGE_PREVIEW_DIR = None
