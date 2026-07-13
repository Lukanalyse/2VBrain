from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from core.settings import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from database.base import Base
    from models import library_item, object_connection  # noqa: F401

    Base.metadata.create_all(bind=engine)
    ensure_library_item_columns()


def ensure_library_item_columns() -> None:
    inspector = inspect(engine)
    if "library_items" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("library_items")}
    columns = {
        "title": "VARCHAR(512)",
        "authors": "TEXT",
        "journal": "VARCHAR(512)",
        "conference": "VARCHAR(512)",
        "year": "INTEGER",
        "doi": "VARCHAR(255)",
        "abstract": "TEXT",
        "keywords": "TEXT",
        "collection_status": "VARCHAR(32) NOT NULL DEFAULT 'inbox'",
        "project_id": "VARCHAR(512)",
        "publisher": "VARCHAR(512)",
        "source_url": "VARCHAR(1024)",
        "metadata_source": "VARCHAR(64)",
        "metadata_confidence": "VARCHAR(32)",
        "metadata_updated_at": "DATETIME",
        "reading_progress": "INTEGER NOT NULL DEFAULT 0",
        "importance": "VARCHAR(32)",
        "priority": "VARCHAR(32)",
        "domain": "VARCHAR(128)",
        "method": "VARCHAR(128)",
        "difficulty": "VARCHAR(32)",
        "personal_tags": "TEXT",
    }

    with engine.begin() as connection:
        for name, definition in columns.items():
            if name not in existing:
                connection.execute(
                    text(f"ALTER TABLE library_items ADD COLUMN {name} {definition}")
                )
