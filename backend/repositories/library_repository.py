from sqlalchemy import select
from sqlalchemy.orm import Session

from models.library_item import LibraryItem


class LibraryRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_items(self) -> list[LibraryItem]:
        statement = select(LibraryItem).order_by(LibraryItem.imported_at.desc())
        return list(self._db.scalars(statement).all())

    def get_by_id(self, item_id: int) -> LibraryItem | None:
        return self._db.get(LibraryItem, item_id)

    def delete_item(self, item: LibraryItem) -> None:
        self._db.delete(item)
        self._db.commit()

    def update_title(self, item: LibraryItem, title: str) -> LibraryItem:
        item.title = title
        self._db.commit()
        self._db.refresh(item)
        return item

    def get_by_original_filename(self, original_filename: str) -> LibraryItem | None:
        statement = select(LibraryItem).where(LibraryItem.original_filename == original_filename)
        return self._db.scalars(statement).first()

    def create_item(
        self,
        *,
        filename: str,
        original_filename: str,
        file_path: str,
        markdown_path: str,
        status: str = "unread",
        collection_status: str = "inbox",
        title: str | None = None,
        authors: str | None = None,
        journal: str | None = None,
        conference: str | None = None,
        year: int | None = None,
        doi: str | None = None,
        abstract: str | None = None,
        keywords: str | None = None,
        publisher: str | None = None,
        source_url: str | None = None,
        metadata_source: str | None = None,
        metadata_confidence: str | None = None,
        metadata_updated_at=None,
        reading_progress: int = 0,
        importance: str | None = None,
        priority: str | None = None,
        domain: str | None = None,
        method: str | None = None,
        difficulty: str | None = None,
        personal_tags: str | None = None,
        project_id: str | None = None,
    ) -> LibraryItem:
        item = LibraryItem(
            filename=filename,
            original_filename=original_filename,
            file_path=file_path,
            markdown_path=markdown_path,
            status=status,
            collection_status=collection_status,
            title=title,
            authors=authors,
            journal=journal,
            conference=conference,
            year=year,
            doi=doi,
            abstract=abstract,
            keywords=keywords,
            publisher=publisher,
            source_url=source_url,
            metadata_source=metadata_source,
            metadata_confidence=metadata_confidence,
            metadata_updated_at=metadata_updated_at,
            reading_progress=reading_progress,
            importance=importance,
            priority=priority,
            domain=domain,
            method=method,
            difficulty=difficulty,
            personal_tags=personal_tags,
            project_id=project_id,
        )
        self._db.add(item)
        self._db.commit()
        self._db.refresh(item)
        return item

    def replace_item(
        self,
        item: LibraryItem,
        *,
        filename: str,
        file_path: str,
        markdown_path: str,
        status: str = "unread",
        collection_status: str = "inbox",
        title: str | None = None,
        authors: str | None = None,
        journal: str | None = None,
        conference: str | None = None,
        year: int | None = None,
        doi: str | None = None,
        abstract: str | None = None,
        keywords: str | None = None,
        publisher: str | None = None,
        source_url: str | None = None,
        metadata_source: str | None = None,
        metadata_confidence: str | None = None,
        metadata_updated_at=None,
        reading_progress: int = 0,
        importance: str | None = None,
        priority: str | None = None,
        domain: str | None = None,
        method: str | None = None,
        difficulty: str | None = None,
        personal_tags: str | None = None,
        project_id: str | None = None,
    ) -> LibraryItem:
        item.filename = filename
        item.file_path = file_path
        item.markdown_path = markdown_path
        item.status = status
        item.collection_status = collection_status
        item.title = title
        item.authors = authors
        item.journal = journal
        item.conference = conference
        item.year = year
        item.doi = doi
        item.abstract = abstract
        item.keywords = keywords
        item.publisher = publisher
        item.source_url = source_url
        item.metadata_source = metadata_source
        item.metadata_confidence = metadata_confidence
        item.metadata_updated_at = metadata_updated_at
        item.reading_progress = reading_progress
        item.importance = importance
        item.priority = priority
        item.domain = domain
        item.method = method
        item.difficulty = difficulty
        item.personal_tags = personal_tags
        item.project_id = project_id
        self._db.commit()
        self._db.refresh(item)
        return item

    def update_status(self, item: LibraryItem, status: str) -> LibraryItem:
        item.status = status
        self._db.commit()
        self._db.refresh(item)
        return item

    def update_collection_status(self, item: LibraryItem, collection_status: str) -> LibraryItem:
        item.collection_status = collection_status
        self._db.commit()
        self._db.refresh(item)
        return item

    def update_project_id(self, item: LibraryItem, project_id: str | None) -> LibraryItem:
        item.project_id = project_id
        self._db.commit()
        self._db.refresh(item)
        return item

    def update_research_metadata(
        self,
        item: LibraryItem,
        *,
        status: str,
        reading_progress: int,
        importance: str | None,
        priority: str | None,
        domain: str | None,
        method: str | None,
        difficulty: str | None,
        personal_tags: str | None,
    ) -> LibraryItem:
        item.status = status
        item.reading_progress = reading_progress
        item.importance = importance
        item.priority = priority
        item.domain = domain
        item.method = method
        item.difficulty = difficulty
        item.personal_tags = personal_tags
        self._db.commit()
        self._db.refresh(item)
        return item
