# Webhook Event System

SelfPublisherForge emits webhook events so publishers can wire the platform into
Zapier, Make, Slack, Google Sheets, and any other HTTP-capable service.

## Event envelope

Every delivery posts JSON in the following shape:

```json
{
  "id": "evt_abc123def456",
  "type": "book.published",
  "created_at": "2026-04-13T14:30:00Z",
  "data": {
    "book_id": "…",
    "title": "…",
    "status": "published"
  }
}
```

## HMAC signature verification

Every request carries an `X-Webhook-Signature` header of the form
`sha256=<hex>` — the HMAC-SHA256 of the **raw request body** using the
endpoint's `signing_secret`.

Recommended verification (Python):

```python
import hmac, hashlib

def verify(secret: str, body: bytes, header: str) -> bool:
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header)
```

Always verify the signature **before** parsing the payload and always use a
constant-time comparison (`hmac.compare_digest` or equivalent).

## Retry policy

Deliveries that do not receive a 2xx response are retried via Celery with an
exponential backoff:

| Attempt | Delay      |
|:-------:|:----------:|
| 1       | 1 minute   |
| 2       | 5 minutes  |
| 3       | 15 minutes |
| 4       | 1 hour     |
| 5       | 6 hours    |

After 5 failed retries the delivery is marked permanently failed. The
"Retry" button in the delivery logs page re-attempts the specific payload on
demand (a fresh attempt — not rescheduled through the Celery backoff chain).

## Event catalog

| Event type                | Description                                             |
| ------------------------- | ------------------------------------------------------- |
| `book.created`            | A new book is created                                   |
| `book.published`          | A book is published to a distributor                    |
| `book.status_changed`     | Book status changes (draft → in_progress, etc.)         |
| `book.exported`           | A book PDF/file is exported                             |
| `book.deleted`            | A book is deleted                                       |
| `review.received`         | New review detected                                     |
| `review.negative`         | Review with ≤2 stars                                    |
| `analytics.daily`         | Daily sales summary (midnight UTC)                      |
| `analytics.bsr_change`    | Significant BSR movement (>20%)                         |
| `pipeline.stage_changed`  | Pipeline moves to a new stage                           |
| `pipeline.completed`      | Pipeline reaches final stage                            |
| `task.completed`          | A pipeline task is completed                            |
| `task.overdue`            | A task passes its due date                              |
| `generation.completed`    | AI generation job finishes                              |
| `batch.completed`         | Batch factory job completes                             |
| `export.completed`        | Export file is ready                                    |
| `price.changed`           | Price change executed                                   |
| `campaign.launched`       | Marketing campaign goes live                            |

The current milestone wires **book.created**, **book.status_changed**, and
**book.published** into the projects service. Adding new source sites is a
1-line call — import `dispatch_event` from `app.modules.webhooks.service` and
fire it after the side effect commits.

```python
from app.modules.webhooks.service import dispatch_event

dispatch_event("export.completed", {"book_id": str(book_id), "format": "epub"}, org_id=org_id)
```

Because `dispatch_event` enqueues Celery work and never blocks, you can call
it anywhere without worrying about request latency.

## Follow-ups

The following events exist in the catalog but are **not yet wired** to their
source modules — they should be emitted when those features next change:

- `book.exported`, `book.deleted`, `export.completed`
- `review.received`, `review.negative`
- `analytics.daily`, `analytics.bsr_change`
- `pipeline.*`, `task.*`
- `generation.completed`, `batch.completed`
- `price.changed`, `campaign.launched`
