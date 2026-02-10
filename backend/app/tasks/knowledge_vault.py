"""Celery tasks for async Knowledge Vault import and indexing."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from app.tasks import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="knowledge_vault.import_from_url",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def import_from_url_task(self, org_id: str, url: str, extract_facts: bool = True):
    """
    Async Celery task to import a knowledge entry from a URL.
    Runs the import pipeline: fetch -> extract -> AI facts -> persist -> index.
    """
    import asyncio
    from app.database import async_session
    from app.modules.knowledge_vault.service import KnowledgeService

    async def _run():
        async with async_session() as db:
            try:
                service = KnowledgeService(db=db)
                entry = await service.import_entry(
                    org_id=UUID(org_id),
                    url=url,
                    extract_facts=extract_facts,
                )
                await db.commit()
                logger.info("Imported URL %s as entry %s", url, entry.id)
                return {"entry_id": str(entry.id), "title": entry.title, "status": "completed"}
            except SQLAlchemyError as exc:
                await db.rollback()
                logger.error("Database error importing URL %s: %s", url, exc, exc_info=True)
                raise self.retry(exc=exc)
            except (ConnectionError, OSError, TimeoutError) as exc:
                await db.rollback()
                logger.error("Network error importing URL %s: %s", url, exc, exc_info=True)
                raise self.retry(exc=exc)

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()


@celery_app.task(
    name="knowledge_vault.import_from_file",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def import_from_file_task(
    self,
    org_id: str,
    file_name: str,
    file_content_base64: str,
    extract_facts: bool = True,
):
    """
    Async Celery task to import a knowledge entry from an uploaded file.
    """
    import asyncio
    from app.database import async_session
    from app.modules.knowledge_vault.service import KnowledgeService

    async def _run():
        async with async_session() as db:
            try:
                service = KnowledgeService(db=db)
                entry = await service.import_entry(
                    org_id=UUID(org_id),
                    file_name=file_name,
                    file_content_base64=file_content_base64,
                    extract_facts=extract_facts,
                )
                await db.commit()
                logger.info("Imported file %s as entry %s", file_name, entry.id)
                return {"entry_id": str(entry.id), "title": entry.title, "status": "completed"}
            except SQLAlchemyError as exc:
                await db.rollback()
                logger.error("Database error importing file %s: %s", file_name, exc, exc_info=True)
                raise self.retry(exc=exc)
            except (ValueError, UnicodeDecodeError) as exc:
                await db.rollback()
                logger.error("File parsing error importing file %s: %s", file_name, exc, exc_info=True)
                raise self.retry(exc=exc)

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()


@celery_app.task(name="knowledge_vault.reindex_all", bind=True)
def reindex_all_task(self, org_id: str):
    """
    Re-index all non-deleted knowledge entries for an org in Elasticsearch.
    Useful after schema changes or index rebuilds.
    """
    import asyncio
    from sqlalchemy import select, and_
    from app.database import async_session
    from app.modules.knowledge_vault.models import KnowledgeEntry
    from app.modules.knowledge_vault.search import KnowledgeSearchService

    async def _run():
        search = KnowledgeSearchService()
        await search.ensure_index()
        count = 0

        async with async_session() as db:
            stmt = select(KnowledgeEntry).where(
                and_(
                    KnowledgeEntry.org_id == org_id,
                    KnowledgeEntry.deleted_at.is_(None),
                )
            )
            result = await db.execute(stmt)
            entries = result.scalars().all()

            for entry in entries:
                await search.index_entry(entry.to_dict())
                count += 1

        await search.close()
        logger.info("Re-indexed %d entries for org %s", count, org_id)
        return {"reindexed": count, "org_id": org_id}

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()
