import logging

from core.settings import get_settings
from database.session import SessionLocal
from repositories.library_repository import LibraryRepository
from services.concept_manager import ConceptManager
from services.linking_engine import LinkingEngine
from services.vault_manager import VaultManager

logger = logging.getLogger(__name__)


def warm_knowledge_catalog() -> None:
    """Warm derived read caches while the desktop splash window is hidden."""
    settings = get_settings()
    vault_manager = VaultManager(settings)
    status = vault_manager.get_storage_status()
    if not status.is_configured:
        return

    db = SessionLocal()
    try:
        repository = LibraryRepository(db)
        concept_manager = ConceptManager(
            vault_manager=vault_manager, library_repository=repository
        )
        linking_engine = LinkingEngine(
            vault_manager=vault_manager,
            library_repository=repository,
            concept_manager=concept_manager,
        )
        object_count, edge_count = linking_engine.warm()
        logger.info(
            "Knowledge catalog warmed",
            extra={"object_count": object_count, "edge_count": edge_count},
        )
    except Exception:
        logger.exception("Unable to warm knowledge catalog")
    finally:
        db.close()
