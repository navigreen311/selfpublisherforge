"""Enhanced Celery configuration with task routing, priority queues, and retry policies."""

from kombu import Exchange, Queue

# ---------------------------------------------------------------------------
# Exchanges
# ---------------------------------------------------------------------------
default_exchange = Exchange("default", type="direct")
ai_exchange = Exchange("ai", type="direct")
email_exchange = Exchange("email", type="direct")
file_exchange = Exchange("file", type="direct")
analytics_exchange = Exchange("analytics", type="direct")
dlq_exchange = Exchange("dlq", type="direct")

# ---------------------------------------------------------------------------
# Priority Queues — Celery/Redis uses 0 (highest) to 9 (lowest)
# ---------------------------------------------------------------------------
PRIORITY_HIGH = 0
PRIORITY_DEFAULT = 5
PRIORITY_LOW = 9

# ---------------------------------------------------------------------------
# Queue Definitions
# ---------------------------------------------------------------------------
TASK_QUEUES = (
    Queue("default", default_exchange, routing_key="default", queue_arguments={"x-max-priority": 10}),
    Queue("ai_queue", ai_exchange, routing_key="ai", queue_arguments={"x-max-priority": 10}),
    Queue("email_queue", email_exchange, routing_key="email", queue_arguments={"x-max-priority": 10}),
    Queue("file_queue", file_exchange, routing_key="file", queue_arguments={"x-max-priority": 10}),
    Queue("analytics_queue", analytics_exchange, routing_key="analytics", queue_arguments={"x-max-priority": 10}),
    Queue("dead_letter_queue", dlq_exchange, routing_key="dlq"),
)

# ---------------------------------------------------------------------------
# Routing Map — maps task name prefixes to queues
# ---------------------------------------------------------------------------
TASK_ROUTES = {
    "app.tasks.ai_tasks.*": {"queue": "ai_queue", "routing_key": "ai"},
    "app.tasks.email_tasks.*": {"queue": "email_queue", "routing_key": "email"},
    "app.tasks.file_tasks.*": {"queue": "file_queue", "routing_key": "file"},
    "app.tasks.analytics_tasks.*": {"queue": "analytics_queue", "routing_key": "analytics"},
    "app.tasks.advertising.*": {"queue": "default", "routing_key": "default"},
}

# ---------------------------------------------------------------------------
# Retry Policies per task-type prefix
# ---------------------------------------------------------------------------
RETRY_POLICIES = {
    "ai_tasks": {
        "max_retries": 3,
        "retry_backoff": True,
        "retry_backoff_max": 600,  # 10 min ceiling
        "retry_jitter": True,
    },
    "email_tasks": {
        "max_retries": 5,
        "retry_backoff": True,
        "retry_backoff_max": 300,
        "retry_jitter": True,
    },
    "file_tasks": {
        "max_retries": 3,
        "retry_backoff": True,
        "retry_backoff_max": 120,
        "retry_jitter": False,
    },
    "analytics_tasks": {
        "max_retries": 2,
        "retry_backoff": True,
        "retry_backoff_max": 60,
        "retry_jitter": False,
    },
    "default": {
        "max_retries": 3,
        "retry_backoff": True,
        "retry_backoff_max": 300,
        "retry_jitter": True,
    },
}


def get_retry_policy(task_name: str) -> dict:
    """Resolve the retry policy for a given fully-qualified task name."""
    for prefix, policy in RETRY_POLICIES.items():
        if prefix != "default" and prefix in task_name:
            return policy
    return RETRY_POLICIES["default"]


# ---------------------------------------------------------------------------
# Celery Configuration dict — applied to the Celery app at startup
# ---------------------------------------------------------------------------
CELERY_CONFIG = {
    # Serialization
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    # Timezone
    "timezone": "UTC",
    "enable_utc": True,
    # Task tracking
    "task_track_started": True,
    "task_time_limit": 3600,
    "task_soft_time_limit": 3300,
    # Worker tuning
    "worker_prefetch_multiplier": 1,
    "worker_max_tasks_per_child": 1000,
    # Queues & routing
    "task_queues": TASK_QUEUES,
    "task_routes": TASK_ROUTES,
    "task_default_queue": "default",
    "task_default_exchange": "default",
    "task_default_routing_key": "default",
    # Result backend
    "result_expires": 86400,  # 24 hours
    "result_extended": True,
    # Late acks — only ack after task completes (avoid lost tasks)
    "task_acks_late": True,
    "task_reject_on_worker_lost": True,
    # Default retry
    "task_default_retry_delay": 60,
}
