"""
Billing & Subscriptions module.

Provides Stripe-based billing integration including plan management,
checkout sessions, billing portal, webhook processing, usage metering,
and invoice listing.
"""

from app.modules.billing.router import router

__all__ = ["router"]
