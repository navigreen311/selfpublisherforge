"""Elasticsearch integration for Knowledge Vault full-text search."""

from __future__ import annotations

import logging
from typing import Any, Optional
from uuid import UUID

from elasticsearch import AsyncElasticsearch, NotFoundError

from app.config import get_settings

logger = logging.getLogger(__name__)

INDEX_NAME = "knowledge_entries"

# ── Index mapping ────────────────────────────────────────────────

INDEX_SETTINGS: dict[str, Any] = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "content_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "stop", "snowball"],
                }
            }
        },
    },
    "mappings": {
        "properties": {
            "entry_id": {"type": "keyword"},
            "org_id": {"type": "keyword"},
            "title": {
                "type": "text",
                "analyzer": "content_analyzer",
                "fields": {"keyword": {"type": "keyword"}},
            },
            "content": {"type": "text", "analyzer": "content_analyzer"},
            "source_url": {"type": "keyword"},
            "source_type": {"type": "keyword"},
            "tags": {"type": "keyword"},
            "credibility_score": {"type": "float"},
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"},
        }
    },
}


class KnowledgeSearchService:
    """Manages Elasticsearch interactions for Knowledge Vault entries."""

    def __init__(self, es_client: AsyncElasticsearch | None = None):
        settings = get_settings()
        self._client = es_client or AsyncElasticsearch(
            hosts=[settings.ELASTICSEARCH_URL],
            request_timeout=30,
        )

    async def ensure_index(self) -> None:
        """Create the index if it does not exist."""
        exists = await self._client.indices.exists(index=INDEX_NAME)
        if not exists:
            await self._client.indices.create(index=INDEX_NAME, body=INDEX_SETTINGS)
            logger.info("Created Elasticsearch index %s", INDEX_NAME)

    # ── Index / update / delete documents ────────────────────────

    async def index_entry(self, entry_dict: dict[str, Any]) -> None:
        """Index or re-index a knowledge entry."""
        doc_id = str(entry_dict["id"])
        body = {
            "entry_id": doc_id,
            "org_id": str(entry_dict.get("org_id", "")),
            "title": entry_dict.get("title", ""),
            "content": entry_dict.get("content", ""),
            "source_url": entry_dict.get("source_url"),
            "source_type": entry_dict.get("source_type", "manual"),
            "tags": entry_dict.get("tags", []),
            "credibility_score": entry_dict.get("credibility_score"),
            "created_at": entry_dict.get("created_at"),
            "updated_at": entry_dict.get("updated_at"),
        }
        await self._client.index(index=INDEX_NAME, id=doc_id, body=body, refresh="wait_for")

    async def delete_entry(self, entry_id: str) -> None:
        """Remove an entry from the search index."""
        try:
            await self._client.delete(index=INDEX_NAME, id=entry_id, refresh="wait_for")
        except NotFoundError:
            logger.warning("Entry %s not found in search index during delete", entry_id)

    # ── Full-text search ─────────────────────────────────────────

    async def search(
        self,
        org_id: str,
        query: str,
        tags: list[str] | None = None,
        source_type: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Full-text search across title and content, scoped to an org,
        with optional tag and source_type filters.
        Returns {"hits": [...], "total": int}.
        """
        must_clauses: list[dict] = [
            {"term": {"org_id": org_id}},
            {
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "content"],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                }
            },
        ]

        filter_clauses: list[dict] = []
        if tags:
            filter_clauses.append({"terms": {"tags": tags}})
        if source_type:
            filter_clauses.append({"term": {"source_type": source_type}})

        body: dict[str, Any] = {
            "query": {
                "bool": {
                    "must": must_clauses,
                    "filter": filter_clauses,
                }
            },
            "from": offset,
            "size": limit,
            "highlight": {
                "fields": {
                    "title": {"number_of_fragments": 1},
                    "content": {"fragment_size": 200, "number_of_fragments": 1},
                }
            },
        }

        resp = await self._client.search(index=INDEX_NAME, body=body)

        hits = []
        for hit in resp["hits"]["hits"]:
            source = hit["_source"]
            highlight = hit.get("highlight", {})
            content_snippet = (
                highlight.get("content", [source.get("content", "")[:200]])[0]
            )
            hits.append(
                {
                    "id": source["entry_id"],
                    "title": source["title"],
                    "content_snippet": content_snippet,
                    "source_type": source.get("source_type", "manual"),
                    "tags": source.get("tags", []),
                    "score": hit["_score"],
                    "credibility_score": source.get("credibility_score"),
                    "created_at": source.get("created_at"),
                }
            )

        total_value = resp["hits"]["total"]
        total = total_value["value"] if isinstance(total_value, dict) else total_value

        return {"hits": hits, "total": total}

    # ── Faceted tag aggregation ──────────────────────────────────

    async def get_tag_counts(self, org_id: str) -> dict[str, int]:
        """Return tag -> document count for the org."""
        body: dict[str, Any] = {
            "size": 0,
            "query": {"term": {"org_id": org_id}},
            "aggs": {"tag_counts": {"terms": {"field": "tags", "size": 500}}},
        }
        resp = await self._client.search(index=INDEX_NAME, body=body)
        buckets = resp["aggregations"]["tag_counts"]["buckets"]
        return {b["key"]: b["doc_count"] for b in buckets}

    async def close(self) -> None:
        await self._client.close()
