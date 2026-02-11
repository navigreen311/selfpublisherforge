"""
LLM Orchestration Layer

Model-agnostic orchestration for AI generation tasks including:
- Model routing (Claude Opus/Sonnet/Haiku + GPT-4/GPT-4 Mini)
- Provider abstraction with fallback chains
- Semantic caching in Redis
- Token counting and cost tracking with per-org budgets
- Post-generation quality assurance
"""

from app.modules.llm_orchestration.cache import SemanticCache
from app.modules.llm_orchestration.cost_tracker import CostTracker
from app.modules.llm_orchestration.orchestrator import LLMOrchestrator
from app.modules.llm_orchestration.quality import QualityAssurance
from app.modules.llm_orchestration.router import router
from app.modules.llm_orchestration.router_config import ModelRouter, TaskType
from app.modules.llm_orchestration.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    CompletionRequest,
    CompletionResponse,
    CostEstimate,
    CostEstimateRequest,
    ModelConfig,
    QualityReport,
    UsageStats,
)
from app.modules.llm_orchestration.service import LLMOrchestrationService

__all__ = [
    "LLMOrchestrator",
    "LLMOrchestrationService",
    "ModelRouter",
    "TaskType",
    "CostTracker",
    "SemanticCache",
    "QualityAssurance",
    "router",
    # Schemas
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    "CompletionRequest",
    "CompletionResponse",
    "CostEstimate",
    "CostEstimateRequest",
    "ModelConfig",
    "QualityReport",
    "UsageStats",
]
