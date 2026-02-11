"""Dead letter queue — stores failed tasks/events for inspection and manual retry."""
from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass, field

import redis

logger = logging.getLogger(__name__)

# Redis key namespace
DLQ_KEY = "spf:dead_letter_queue"
DLQ_DETAIL_PREFIX = "spf:dlq:detail:"


@dataclass
class DeadLetter:
    """Represents a single failed task or event stored for later retry."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_type: str = ""  # "task" or "event"
    source_name: str = ""  # task name or event type
    payload: dict = field(default_factory=dict)
    error_message: str = ""
    error_type: str = ""
    retry_count: int = 0
    max_retries: int = 0
    created_at: float = field(default_factory=time.time)
    org_id: str | None = None
    correlation_id: str | None = None
    status: str = "pending"  # pending | retried | discarded

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> DeadLetter:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class DeadLetterQueue:
    """Manages dead-lettered tasks and events in Redis.

    Storage layout
    --------------
    * ``spf:dead_letter_queue`` — Redis sorted set (score = timestamp) of DL ids
    * ``spf:dlq:detail:<id>`` — JSON hash with full dead-letter metadata
    """

    def __init__(self, redis_client: redis.Redis) -> None:  # type: ignore[type-arg]
        self._redis: redis.Redis = redis_client  # type: ignore[type-arg,assignment]

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------
    def add(self, dead_letter: DeadLetter) -> str:
        """Store a new dead letter.  Returns the dead-letter id."""
        detail_key = f"{DLQ_DETAIL_PREFIX}{dead_letter.id}"
        pipe = self._redis.pipeline()
        pipe.set(detail_key, json.dumps(dead_letter.to_dict()))
        pipe.zadd(DLQ_KEY, {dead_letter.id: dead_letter.created_at})
        pipe.execute()
        logger.info("Dead letter stored | id=%s source=%s", dead_letter.id, dead_letter.source_name)
        return dead_letter.id

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------
    def get(self, dl_id: str) -> DeadLetter | None:
        """Fetch a single dead letter by id."""
        raw = self._redis.get(f"{DLQ_DETAIL_PREFIX}{dl_id}")  # type: ignore[assignment]
        if raw is None:
            return None
        raw_str = raw.decode() if isinstance(raw, bytes) else str(raw)
        return DeadLetter.from_dict(json.loads(raw_str))

    def list(self, offset: int = 0, limit: int = 50, status: str | None = None) -> list[DeadLetter]:
        """List dead letters ordered newest-first."""
        ids = self._redis.zrevrange(DLQ_KEY, offset, offset + limit - 1)  # type: ignore[arg-type]
        results: list[DeadLetter] = []
        for dl_id in ids:  # type: ignore[union-attr]
            dl_id_str = dl_id if isinstance(dl_id, str) else dl_id.decode()
            dl = self.get(dl_id_str)
            if dl is None:
                continue
            if status is not None and dl.status != status:
                continue
            results.append(dl)
        return results

    def count(self) -> int:
        """Return total number of dead letters."""
        result = self._redis.zcard(DLQ_KEY)  # type: ignore[assignment]
        return int(result) if result else 0  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # Retry / discard
    # ------------------------------------------------------------------
    def mark_retried(self, dl_id: str) -> bool:
        """Mark a dead letter as retried.  Returns ``True`` on success."""
        return self._update_status(dl_id, "retried")

    def mark_discarded(self, dl_id: str) -> bool:
        """Mark a dead letter as discarded.  Returns ``True`` on success."""
        return self._update_status(dl_id, "discarded")

    def remove(self, dl_id: str) -> bool:
        """Permanently remove a dead letter from the queue."""
        pipe = self._redis.pipeline()
        pipe.delete(f"{DLQ_DETAIL_PREFIX}{dl_id}")
        pipe.zrem(DLQ_KEY, dl_id)
        results = pipe.execute()
        return bool(results[0])

    def purge(self) -> int:
        """Remove all dead letters.  Returns the number purged."""
        count = self.count()
        ids = self._redis.zrange(DLQ_KEY, 0, -1)  # type: ignore[arg-type]
        if ids:
            pipe = self._redis.pipeline()
            for dl_id in ids:  # type: ignore[union-attr]
                dl_id_str = dl_id if isinstance(dl_id, str) else dl_id.decode()
                pipe.delete(f"{DLQ_DETAIL_PREFIX}{dl_id_str}")
            pipe.delete(DLQ_KEY)
            pipe.execute()
        return count

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _update_status(self, dl_id: str, new_status: str) -> bool:
        dl = self.get(dl_id)
        if dl is None:
            return False
        dl.status = new_status
        self._redis.set(f"{DLQ_DETAIL_PREFIX}{dl_id}", json.dumps(dl.to_dict()))
        return True
