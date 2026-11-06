"""Guards the MVC rule: only the repository backends may touch a database."""
import re
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent / "app"
REPO_DIR = APP_DIR / "models" / "repositories"


def files_mentioning(pattern, allowed_dir):
    regex = re.compile(pattern)
    return [
        str(path.relative_to(APP_DIR))
        for path in APP_DIR.rglob("*.py")
        if allowed_dir not in path.parents and regex.search(path.read_text(encoding="utf-8"))
    ]


def test_sqlite_is_only_used_in_the_sqlite_backend():
    assert files_mentioning(r"\bimport sqlite3\b|\bsqlite3\.", REPO_DIR / "sqlite") == []


def test_neo4j_driver_is_only_used_in_the_neo4j_backend():
    assert files_mentioning(r"^\s*(from|import) neo4j\b", REPO_DIR / "neo4j") == []


def test_controllers_and_views_only_use_public_repository_names():
    """Controllers must not import a specific backend – that is what keeps them storage-independent."""
    offenders = [
        str(path.relative_to(APP_DIR))
        for path in (APP_DIR / "controllers").rglob("*.py")
        if re.search(r"repositories\.(sqlite|neo4j)\b", path.read_text(encoding="utf-8"))
    ]
    assert offenders == []


def test_mvc_folders_exist():
    for folder in ("models", "models/repositories", "models/repositories/sqlite",
                   "controllers", "templates"):
        assert (APP_DIR / folder).is_dir()
