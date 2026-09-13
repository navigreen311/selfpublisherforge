"""
Per-endpoint rate limit configuration with wildcard support.

Defines rate limits for specific endpoints and tier-based multipliers.
Supports pattern matching with wildcards (*) for flexible endpoint grouping.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.schemas.common import PlanTier


@dataclass
class RateLimitRule:
    """A single rate limit rule with limit and window."""

    limit: int  # Number of requests allowed
    window: int  # Time window in seconds


# Tier-based multipliers for scaling limits
TIER_MULTIPLIERS: dict[PlanTier, float] = {
    PlanTier.FREE: 1.0,
    PlanTier.STARTER: 2.0,
    PlanTier.PRO: 5.0,
    PlanTier.BUSINESS: 10.0,
    PlanTier.ENTERPRISE: 50.0,
}


# Per-endpoint rate limits (base limits for FREE tier)
# Format: "{METHOD} {path_pattern}": RateLimitRule(limit, window_seconds)
# Patterns support wildcards (*) for flexible matching
RATE_LIMITS: dict[str, RateLimitRule] = {
    # Auth endpoints (strict - security critical)
    "POST /api/v1/auth/login": RateLimitRule(limit=5, window=300),  # 5 per 5 min
    "POST /api/v1/auth/register": RateLimitRule(limit=3, window=3600),  # 3 per hour
    "POST /api/v1/auth/reset-password": RateLimitRule(limit=3, window=3600),  # 3 per hour
    "POST /api/v1/auth/*": RateLimitRule(limit=10, window=300),  # Catch-all for auth
    # AI endpoints (costly - high resource usage)
    "POST /api/v1/ai/writing/*": RateLimitRule(limit=20, window=3600),  # 20 per hour
    "POST /api/v1/ai/covers/*": RateLimitRule(limit=10, window=3600),  # 10 per hour
    "POST /api/v1/ai/outlines/*": RateLimitRule(limit=20, window=3600),  # 20 per hour
    "POST /api/v1/ai/*": RateLimitRule(limit=15, window=3600),  # AI catch-all
    # Generation endpoints (also costly)
    "POST /api/v1/generation/*": RateLimitRule(limit=15, window=3600),  # 15 per hour
    # General API (generous for normal operations)
    "GET /api/v1/*": RateLimitRule(limit=100, window=60),  # 100 per minute
    "POST /api/v1/*": RateLimitRule(limit=30, window=60),  # 30 per minute
    "PUT /api/v1/*": RateLimitRule(limit=30, window=60),  # 30 per minute
    "PATCH /api/v1/*": RateLimitRule(limit=30, window=60),  # 30 per minute
    "DELETE /api/v1/*": RateLimitRule(limit=20, window=60),  # 20 per minute
    # Webhooks (very generous - external integrations)
    "POST /api/v1/billing/webhook": RateLimitRule(limit=1000, window=60),  # 1k per min
    "POST /api/v1/webhooks/*": RateLimitRule(limit=500, window=60),  # 500 per min
}


def match_pattern(pattern: str, path: str) -> bool:
    """
    Check if a path matches a pattern with wildcard support.

    Args:
        pattern: Pattern string that may contain wildcards (*)
        path: Actual path to match against

    Returns:
        True if path matches pattern, False otherwise

    Examples:
        >>> match_pattern("/api/v1/ai/*", "/api/v1/ai/generate")
        True
        >>> match_pattern("/api/v1/ai/writing/*", "/api/v1/ai/covers/create")
        False
        >>> match_pattern("/api/v1/*", "/api/v1/books/list")
        True
    """
    # Split both pattern and path into segments
    pattern_parts = pattern.split("/")
    path_parts = path.split("/")

    # If pattern has fewer parts than path (without wildcard at end), no match
    if len(pattern_parts) > len(path_parts):
        return False

    # Check each segment
    for i, pattern_part in enumerate(pattern_parts):
        if pattern_part == "*":
            # Wildcard matches everything from this point
            return True

        if i >= len(path_parts):
            # Path is shorter than pattern (without wildcard)
            return False

        if pattern_part != path_parts[i]:
            # Segment mismatch
            return False

    # All segments matched, but check if lengths are equal (exact match)
    # or if pattern ends with wildcard (already handled above)
    return len(pattern_parts) == len(path_parts)


def find_rate_limit(method: str, path: str, tier: PlanTier = PlanTier.FREE) -> tuple[int, int]:
    """
    Find the applicable rate limit for a given method, path, and tier.

    Searches for the most specific matching pattern and applies tier multiplier.
    More specific patterns (fewer wildcards, longer paths) take precedence.

    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        tier: User's subscription tier

    Returns:
        Tuple of (limit, window_seconds) with tier multiplier applied

    Examples:
        >>> find_rate_limit("POST", "/api/v1/auth/login", PlanTier.FREE)
        (5, 300)
        >>> find_rate_limit("POST", "/api/v1/auth/login", PlanTier.PRO)
        (25, 300)  # 5 * 5x multiplier
        >>> find_rate_limit("GET", "/api/v1/books/list", PlanTier.STARTER)
        (200, 60)  # 100 * 2x multiplier
    """
    matches: list[tuple[str, RateLimitRule, int]] = []

    # Find all matching patterns with their specificity scores
    for pattern, rule in RATE_LIMITS.items():
        pattern_method, pattern_path = pattern.split(" ", 1)

        # Check method match
        if pattern_method != method:
            continue

        # Check path match
        if match_pattern(pattern_path, path):
            # Calculate specificity: longer patterns and fewer wildcards are more specific
            specificity = len(pattern_path) - pattern_path.count("*") * 100
            matches.append((pattern, rule, specificity))

    # No matches found, use a sensible default
    if not matches:
        # Default: 60 requests per minute for FREE tier
        default_rule = RateLimitRule(limit=60, window=60)
        multiplier = TIER_MULTIPLIERS.get(tier, 1.0)
        return int(default_rule.limit * multiplier), default_rule.window

    # Sort by specificity (highest first) and take the most specific match
    matches.sort(key=lambda x: x[2], reverse=True)
    _, rule, _ = matches[0]

    # Apply tier multiplier to the limit
    multiplier = TIER_MULTIPLIERS.get(tier, 1.0)
    adjusted_limit = int(rule.limit * multiplier)

    return adjusted_limit, rule.window
