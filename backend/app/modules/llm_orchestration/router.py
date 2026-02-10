"""
LLM Orchestration API Router

Provides status and configuration endpoints for the LLM orchestration layer.
This module is primarily a library consumed by other modules, but exposes
health/status and configuration introspection endpoints for operational use.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.modules.llm_orchestration.router_config import (
    MODEL_PROVIDER_MAP,
    ROUTING_TABLE,
    ModelID,
    ProviderName,
    TaskType,
)

router = APIRouter()


@router.get("/status")
async def llm_status():
    """Health/status check for the LLM orchestration layer."""
    return {
        "status": "operational",
        "providers": [p.value for p in ProviderName],
        "models": [m.value for m in ModelID],
        "task_types": [t.value for t in TaskType],
    }


@router.get("/models")
async def list_models():
    """List all supported models with their provider mappings."""
    return {
        "models": [
            {
                "model_id": model_id.value,
                "provider": provider.value,
            }
            for model_id, provider in MODEL_PROVIDER_MAP.items()
        ]
    }


@router.get("/routes")
async def list_routes():
    """List task-type routing configuration."""
    return {
        "routes": [
            {
                "task_type": task_type.value,
                "primary_model": route.primary.value,
                "fallbacks": [f.value for f in route.fallbacks],
                "max_tokens": route.max_tokens,
                "cache_ttl_seconds": route.cache_ttl_seconds,
            }
            for task_type, route in ROUTING_TABLE.items()
        ]
    }
