"""Application configuration, read from environment variables (.env)."""
import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    # Relative paths are resolved against the Flask instance folder.
    DATABASE = os.environ.get("DATABASE", "ektemat.db")
    TESTING = False
