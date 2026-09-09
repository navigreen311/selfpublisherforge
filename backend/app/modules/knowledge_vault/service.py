"""Knowledge Vault business logic: CRUD, search delegation, import, AI ops."""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from typing import Any, ClassVar
from uuid import UUID

import httpx
from sqlalchemy import and_, select
from sqlalchemy import func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.knowledge_vault import importer
from app.modules.knowledge_vault.models import KnowledgeAttachment, KnowledgeEntry
from app.modules.knowledge_vault.schemas import (
    CreateEntryRequest,
    UpdateEntryRequest,
)
from app.modules.knowledge_vault.search import KnowledgeSearchService

logger = logging.getLogger(__name__)


class KnowledgeService:
    """Encapsulates all Knowledge Vault operations."""

    # Class-level set of entry IDs that failed ES indexing and need retry.
    _pending_reindex: ClassVar[set[str]] = set()

    def __init__(self, db: AsyncSession, search: KnowledgeSearchService | None = None):
        self.db = db
        self.search = search or KnowledgeSearchService()

    # ── CRUD ─────────────────────────────────────────────────────

    async def create_entry(self, org_id: UUID, payload: CreateEntryRequest) -> KnowledgeEntry:
        entry = KnowledgeEntry(
            org_id=org_id,
            title=payload.title,
            content=payload.content,
            source_url=payload.source_url,
            source_type=payload.source_type,
            tags=payload.tags,
            credibility_score=payload.credibility_score,
            category=payload.category,
            project_id=payload.project_id,
            metadata_=payload.metadata,
        )
        self.db.add(entry)
        await self.db.flush()
        await self.db.refresh(entry)

        # Index in Elasticsearch (best-effort)
        search_index_status = "indexed"
        try:
            await self.search.index_entry(entry.to_dict())
        except (ConnectionError, OSError):
            logger.error("Failed to index entry %s in Elasticsearch: connection error", entry.id, exc_info=True)
            KnowledgeService._pending_reindex.add(str(entry.id))
            search_index_status = "pending_index"
        except ValueError:
            logger.error("Failed to index entry %s in Elasticsearch: invalid data", entry.id, exc_info=True)
            KnowledgeService._pending_reindex.add(str(entry.id))
            search_index_status = "pending_index"

        # Attach index status so callers can see if search is lagging
        entry.search_index_status = search_index_status  # type: ignore[attr-defined]
        return entry

    async def get_entry(self, org_id: UUID, entry_id: UUID) -> KnowledgeEntry | None:
        result = await self.db.execute(
            select(KnowledgeEntry).where(
                and_(
                    KnowledgeEntry.id == entry_id,
                    KnowledgeEntry.org_id == org_id,
                    KnowledgeEntry.deleted_at.is_(None),
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_entries(
        self,
        org_id: UUID,
        *,
        tags: list[str] | None = None,
        source_type: str | None = None,
        category: str | None = None,
        cursor: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        stmt = (
            select(KnowledgeEntry)
            .where(
                and_(
                    KnowledgeEntry.org_id == org_id,
                    KnowledgeEntry.deleted_at.is_(None),
                )
            )
            .order_by(KnowledgeEntry.created_at.desc())
        )

        if tags:
            stmt = stmt.where(KnowledgeEntry.tags.overlap(tags))
        if source_type:
            stmt = stmt.where(KnowledgeEntry.source_type == source_type)
        if category:
            stmt = stmt.where(KnowledgeEntry.category == category)
        if cursor:
            stmt = stmt.where(KnowledgeEntry.created_at < cursor)

        stmt = stmt.limit(limit + 1)
        result = await self.db.execute(stmt)
        rows = list(result.scalars().all())

        has_more = len(rows) > limit
        items = rows[:limit]

        # Total count
        count_stmt = (
            select(sa_func.count())
            .select_from(KnowledgeEntry)
            .where(
                and_(
                    KnowledgeEntry.org_id == org_id,
                    KnowledgeEntry.deleted_at.is_(None),
                )
            )
        )
        total_result = await self.db.execute(count_stmt)
        total_count = total_result.scalar()

        next_cursor = items[-1].created_at.isoformat() if has_more and items else None

        return {
            "items": items,
            "next_cursor": next_cursor,
            "has_more": has_more,
            "total_count": total_count,
        }

    async def update_entry(self, org_id: UUID, entry_id: UUID, payload: UpdateEntryRequest) -> KnowledgeEntry | None:
        entry = await self.get_entry(org_id, entry_id)
        if not entry:
            return None

        update_data = payload.model_dump(exclude_unset=True)
        if "metadata" in update_data:
            update_data["metadata_"] = update_data.pop("metadata")

        for key, value in update_data.items():
            setattr(entry, key, value)

        await self.db.flush()
        await self.db.refresh(entry)

        search_index_status = "indexed"
        try:
            await self.search.index_entry(entry.to_dict())
            # If re-index succeeds, remove from pending queue if present
            KnowledgeService._pending_reindex.discard(str(entry.id))
        except (ConnectionError, OSError):
            logger.error("Failed to re-index entry %s: connection error", entry.id, exc_info=True)
            KnowledgeService._pending_reindex.add(str(entry.id))
            search_index_status = "pending_index"
        except ValueError:
            logger.error("Failed to re-index entry %s: invalid data", entry.id, exc_info=True)
            KnowledgeService._pending_reindex.add(str(entry.id))
            search_index_status = "pending_index"

        entry.search_index_status = search_index_status  # type: ignore[attr-defined]
        return entry

    async def delete_entry(self, org_id: UUID, entry_id: UUID) -> bool:
        entry = await self.get_entry(org_id, entry_id)
        if not entry:
            return False

        entry.deleted_at = datetime.now(UTC)
        await self.db.flush()

        try:
            await self.search.delete_entry(str(entry_id))
            # Entry deleted; no longer needs re-indexing
            KnowledgeService._pending_reindex.discard(str(entry_id))
        except (ConnectionError, OSError):
            logger.error("Failed to remove entry %s from search index: connection error", entry_id, exc_info=True)
        except ValueError:
            logger.error("Failed to remove entry %s from search index: invalid data", entry_id, exc_info=True)

        return True

    # ── Reindex pending entries ──────────────────────────────────

    async def reindex_pending(self) -> dict[str, Any]:
        """Retry Elasticsearch indexing for entries that previously failed.

        Returns a summary with counts of succeeded and still-failing entries.
        """
        if not KnowledgeService._pending_reindex:
            return {"pending": 0, "succeeded": 0, "failed": 0}

        pending_ids = list(KnowledgeService._pending_reindex)
        succeeded = 0
        failed_ids: list[str] = []

        for entry_id_str in pending_ids:
            try:
                entry_id = UUID(entry_id_str)
            except ValueError:
                logger.warning("Invalid UUID in pending reindex set: %s", entry_id_str)
                KnowledgeService._pending_reindex.discard(entry_id_str)
                continue

            # Fetch the entry from DB (across all orgs since we only have the ID)
            result = await self.db.execute(
                select(KnowledgeEntry).where(
                    and_(
                        KnowledgeEntry.id == entry_id,
                        KnowledgeEntry.deleted_at.is_(None),
                    )
                )
            )
            entry = result.scalar_one_or_none()

            if entry is None:
                # Entry was deleted or doesn't exist; drop from queue
                KnowledgeService._pending_reindex.discard(entry_id_str)
                continue

            try:
                await self.search.index_entry(entry.to_dict())
                KnowledgeService._pending_reindex.discard(entry_id_str)
                succeeded += 1
            except (ConnectionError, OSError):
                logger.error("Reindex retry failed for entry %s: connection error", entry_id, exc_info=True)
                failed_ids.append(entry_id_str)
            except ValueError:
                logger.error("Reindex retry failed for entry %s: invalid data", entry_id, exc_info=True)
                failed_ids.append(entry_id_str)

        return {
            "pending": len(pending_ids),
            "succeeded": succeeded,
            "failed": len(failed_ids),
            "failed_ids": failed_ids,
        }

    @classmethod
    def get_pending_reindex_ids(cls) -> list[str]:
        """Return the list of entry IDs currently awaiting re-indexing."""
        return list(cls._pending_reindex)

    # ── Search ───────────────────────────────────────────────────

    async def full_text_search(
        self,
        org_id: UUID,
        query: str,
        tags: list[str] | None = None,
        source_type: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        return await self.search.search(
            org_id=str(org_id),
            query=query,
            tags=tags,
            source_type=source_type,
            limit=limit,
            offset=offset,
        )

    # ── Import ───────────────────────────────────────────────────

    async def import_entry(
        self,
        org_id: UUID,
        url: str | None = None,
        file_name: str | None = None,
        file_content_base64: str | None = None,
        extract_facts: bool = True,
    ) -> KnowledgeEntry:
        if url:
            extracted = await importer.extract_from_url(url)
        elif file_name and file_content_base64:
            extracted = await importer.extract_from_file(file_name, file_content_base64)
        else:
            raise ValueError("Provide either a URL or file_name + file_content_base64")

        tags: list[str] = []
        credibility: float | None = None

        if extract_facts and extracted.get("content"):
            facts = await importer.extract_key_facts(extracted["content"])
            tags = facts.get("tags", [])
            credibility = facts.get("credibility_score")
            if facts.get("key_facts"):
                extracted["content"] += f"\n\n--- Key Facts ---\n{facts['key_facts']}"

        create_req = CreateEntryRequest(
            title=extracted["title"],
            content=extracted["content"],
            source_url=extracted.get("source_url"),
            source_type=extracted.get("source_type", "manual"),
            tags=tags,
            credibility_score=credibility,
        )
        return await self.create_entry(org_id, create_req)

    # ── AI Summarize ─────────────────────────────────────────────

    async def summarize_entry(self, org_id: UUID, entry_id: UUID) -> dict[str, Any] | None:
        entry = await self.get_entry(org_id, entry_id)
        if not entry:
            return None
        result = await importer.summarize_content(entry.content)
        return {
            "entry_id": str(entry.id),
            "summary": result["summary"],
            "key_points": result["key_points"],
            "suggested_tags": result["suggested_tags"],
        }

    # ── Tags ─────────────────────────────────────────────────────

    async def get_all_tags(self, org_id: UUID) -> dict[str, Any]:
        """Return distinct tags and their counts from the database."""
        stmt = (
            select(
                sa_func.unnest(KnowledgeEntry.tags).label("tag"),
                sa_func.count().label("cnt"),
            )
            .where(
                and_(
                    KnowledgeEntry.org_id == org_id,
                    KnowledgeEntry.deleted_at.is_(None),
                )
            )
            .group_by("tag")
            .order_by(sa_func.count().desc())
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        tags = [r.tag for r in rows]
        counts = {r.tag: r.cnt for r in rows}
        return {"tags": tags, "counts": counts}

    # ── AI Suggestions ───────────────────────────────────────────

    async def get_suggestions(self, org_id: UUID) -> list[dict[str, str]]:
        tag_data = await self.get_all_tags(org_id)
        existing_tags = tag_data.get("tags", [])

        # Get recent titles
        stmt = (
            select(KnowledgeEntry.title)
            .where(
                and_(
                    KnowledgeEntry.org_id == org_id,
                    KnowledgeEntry.deleted_at.is_(None),
                )
            )
            .order_by(KnowledgeEntry.created_at.desc())
            .limit(20)
        )
        result = await self.db.execute(stmt)
        recent_titles = [r[0] for r in result.all()]

        return await importer.suggest_research(existing_tags, recent_titles)


# ── Standalone helper functions ─────────────────────────────────────


def _word_count(text: str | None) -> int:
    """Return the number of whitespace-delimited words in *text*."""
    if not text:
        return 0
    return len(text.split())


async def create_entry_full(
    db: AsyncSession,
    org_id: UUID,
    payload: CreateEntryRequest,
) -> KnowledgeEntry:
    """Create a KnowledgeEntry with category, project_id, and word_count calculation.

    Accepts the standard *CreateEntryRequest* and enriches the stored metadata
    with ``word_count``, and optionally ``category`` / ``project_id`` if
    present in ``payload.metadata``.
    """
    merged_meta: dict[str, Any] = dict(payload.metadata) if payload.metadata else {}
    merged_meta["word_count"] = _word_count(payload.content)

    entry = KnowledgeEntry(
        org_id=org_id,
        title=payload.title,
        content=payload.content,
        source_url=payload.source_url,
        source_type=payload.source_type,
        tags=payload.tags,
        credibility_score=payload.credibility_score,
        metadata_=merged_meta,
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


async def update_entry(
    db: AsyncSession,
    entry_id: UUID,
    org_id: UUID,
    payload: UpdateEntryRequest,
) -> KnowledgeEntry | None:
    """Update all mutable fields on an existing KnowledgeEntry.

    Returns ``None`` when the entry does not exist or belongs to a different org.
    """
    result = await db.execute(
        select(KnowledgeEntry).where(
            and_(
                KnowledgeEntry.id == entry_id,
                KnowledgeEntry.org_id == org_id,
                KnowledgeEntry.deleted_at.is_(None),
            )
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    if "metadata" in update_data:
        update_data["metadata_"] = update_data.pop("metadata")

    # Recalculate word_count when content changes
    if "content" in update_data:
        meta = dict(entry.metadata_) if entry.metadata_ else {}
        meta["word_count"] = _word_count(update_data["content"])
        update_data["metadata_"] = {**meta, **update_data.get("metadata_", {})}

    for key, value in update_data.items():
        setattr(entry, key, value)

    await db.flush()
    await db.refresh(entry)
    return entry


async def upload_attachment(
    db: AsyncSession,
    entry_id: UUID,
    org_id: UUID,
    file_name: str,
    file_url: str,
    file_size: int | None = None,
    mime_type: str | None = None,
) -> KnowledgeAttachment:
    """Insert a new row into ``knowledge_attachments``."""
    attachment = KnowledgeAttachment(
        org_id=org_id,
        entry_id=entry_id,
        file_name=file_name,
        file_url=file_url,
        file_size=file_size,
        mime_type=mime_type,
    )
    db.add(attachment)
    await db.flush()
    await db.refresh(attachment)
    return attachment


async def list_attachments(
    db: AsyncSession,
    entry_id: UUID,
    org_id: UUID,
) -> list[KnowledgeAttachment]:
    """Return all non-deleted attachments for a given entry and org."""
    result = await db.execute(
        select(KnowledgeAttachment)
        .where(
            and_(
                KnowledgeAttachment.entry_id == entry_id,
                KnowledgeAttachment.org_id == org_id,
                KnowledgeAttachment.deleted_at.is_(None),
            )
        )
        .order_by(KnowledgeAttachment.created_at.desc())
    )
    return list(result.scalars().all())


async def delete_attachment(
    db: AsyncSession,
    entry_id: UUID,
    attachment_id: UUID,
    org_id: UUID,
) -> bool:
    """Soft-delete an attachment. Returns ``True`` if a row was found and marked."""
    result = await db.execute(
        select(KnowledgeAttachment).where(
            and_(
                KnowledgeAttachment.id == attachment_id,
                KnowledgeAttachment.entry_id == entry_id,
                KnowledgeAttachment.org_id == org_id,
                KnowledgeAttachment.deleted_at.is_(None),
            )
        )
    )
    attachment = result.scalar_one_or_none()
    if not attachment:
        return False

    attachment.deleted_at = datetime.now(UTC)
    await db.flush()
    return True


async def import_from_url(
    db: AsyncSession,
    org_id: UUID,
    url: str,
) -> KnowledgeEntry:
    """Fetch *url* via httpx, strip HTML tags, and create a KnowledgeEntry."""
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "SelfPublisherForge/1.0"})
        resp.raise_for_status()
        html = resp.text

    # Extract title
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else url

    # Strip HTML to plain text
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<(br|/p|/div|/h[1-6])[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    content = text.strip()

    if len(content) > 50_000:
        content = content[:50_000] + "\n...[truncated]"

    payload = CreateEntryRequest(
        title=title,
        content=content,
        source_url=url,
        source_type="url",
    )
    return await create_entry_full(db, org_id, payload)
