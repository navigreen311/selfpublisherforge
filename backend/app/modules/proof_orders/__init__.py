"""Print proof ordering module.

Scaffold — does NOT integrate with a real print provider. Orders are
generated with a mocked tracking number and estimated delivery.
Replace ``service._mock_provider_order`` with a real integration
(Lulu / KDP Print On Demand / IngramSpark API) before production.
"""

from app.modules.proof_orders.router import router

__all__ = ["router"]
