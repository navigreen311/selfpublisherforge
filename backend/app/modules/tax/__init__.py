"""Tax dashboard module.

Aggregates gross income from royalty entries, tracks deductible expenses,
and computes quarterly estimated tax payments.

NOT a tax advisor. All outputs are estimates. Frontend MUST display the
TaxDisclaimer component on every tax page.
"""

from app.modules.tax.router import router

__all__ = ["router"]
