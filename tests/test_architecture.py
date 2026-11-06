"""Guards the MVC rule: only repositories may touch the storage layer."""
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent / "app"
REPO_DIR = APP_DIR / "models" / "repositories"


def test_sqlite_is_only_used_in_repositories():
    offenders = [
        str(path.relative_to(APP_DIR))
        for path in APP_DIR.rglob("*.py")
        if REPO_DIR not in path.parents and "sqlite3" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_mvc_folders_exist():
    for folder in ("models", "models/repositories", "controllers", "templates"):
        assert (APP_DIR / folder).is_dir()
