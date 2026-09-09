"""Kindle Unlimited (KU) vs. Wide Distribution Revenue Calculator.

Compares two scenarios:
1. KU Exclusive (KDP Select): revenue from KU page reads + Amazon paid sales
2. Wide Distribution: revenue from sales across multiple platforms (no KU reads)

Helps authors decide whether to enroll in KDP Select or go wide.
"""

from __future__ import annotations

from app.modules.pricing_automation.schemas import (
    KUCalculatorRequest,
    KUCalculatorResponse,
    RevenueBreakdown,
)


def calculate_ku_vs_wide(request: KUCalculatorRequest) -> KUCalculatorResponse:
    """Calculate and compare KU-exclusive vs. wide distribution revenue.

    KU Exclusive scenario:
        - KU page reads: pages * reads_per_month * page_rate
        - Amazon paid sales: amazon_price * amazon_monthly_sales * amazon_royalty_rate
        - Total = page reads + paid sales

    Wide Distribution scenario:
        - Wide sales: wide_price * wide_monthly_sales * wide_royalty_rate
        - No KU reads (not enrolled in KDP Select)
        - Amazon paid sales may still happen but typically fewer due to lack of KU exposure
    """

    # ── KU Exclusive Revenue ──
    ku_page_revenue = request.book_page_count * request.estimated_ku_reads_per_month * request.ku_page_rate
    ku_paid_sales_revenue = request.amazon_price * request.amazon_monthly_sales
    ku_paid_royalties = ku_paid_sales_revenue * request.amazon_royalty_rate
    ku_total_monthly_royalties = ku_page_revenue + ku_paid_royalties
    ku_total_monthly_revenue = ku_page_revenue + ku_paid_sales_revenue

    ku_breakdown = RevenueBreakdown(
        source="KU Exclusive (KDP Select)",
        monthly_revenue=round(ku_total_monthly_revenue, 2),
        monthly_royalties=round(ku_total_monthly_royalties, 2),
        annual_revenue=round(ku_total_monthly_revenue * 12, 2),
        annual_royalties=round(ku_total_monthly_royalties * 12, 2),
    )

    # ── Wide Distribution Revenue ──
    wide_sales_revenue = request.wide_price * request.wide_monthly_sales
    wide_royalties = wide_sales_revenue * request.wide_royalty_rate
    wide_total_monthly_revenue = wide_sales_revenue
    wide_total_monthly_royalties = wide_royalties

    wide_breakdown = RevenueBreakdown(
        source="Wide Distribution",
        monthly_revenue=round(wide_total_monthly_revenue, 2),
        monthly_royalties=round(wide_total_monthly_royalties, 2),
        annual_revenue=round(wide_total_monthly_revenue * 12, 2),
        annual_royalties=round(wide_total_monthly_royalties * 12, 2),
    )

    # ── Comparison ──
    diff_monthly = round(ku_total_monthly_royalties - wide_total_monthly_royalties, 2)
    diff_annual = round(diff_monthly * 12, 2)

    # ── Recommendation ──
    if diff_monthly > 0:
        margin_pct = (diff_monthly / wide_total_monthly_royalties * 100) if wide_total_monthly_royalties > 0 else 100.0
        if margin_pct > 50:
            recommendation = (
                f"Strongly recommend KU Exclusive. KU earns ${diff_monthly:.2f}/mo "
                f"({margin_pct:.0f}%) more in royalties."
            )
        elif margin_pct > 10:
            recommendation = (
                f"KU Exclusive is moderately better, earning ${diff_monthly:.2f}/mo "
                f"({margin_pct:.0f}%) more. Consider KU if you value discoverability."
            )
        else:
            recommendation = (
                f"KU Exclusive is slightly better by ${diff_monthly:.2f}/mo "
                f"({margin_pct:.0f}%). The difference is small; consider other "
                f"factors like catalog control and platform diversification."
            )
    elif diff_monthly < 0:
        abs_diff = abs(diff_monthly)
        margin_pct = (abs_diff / ku_total_monthly_royalties * 100) if ku_total_monthly_royalties > 0 else 100.0
        if margin_pct > 50:
            recommendation = (
                f"Strongly recommend Wide Distribution. Wide earns ${abs_diff:.2f}/mo "
                f"({margin_pct:.0f}%) more in royalties."
            )
        elif margin_pct > 10:
            recommendation = (
                f"Wide Distribution is moderately better, earning ${abs_diff:.2f}/mo "
                f"({margin_pct:.0f}%) more. Consider platform diversification benefits."
            )
        else:
            recommendation = (
                f"Wide Distribution is slightly better by ${abs_diff:.2f}/mo "
                f"({margin_pct:.0f}%). Consider KU's discoverability benefits "
                f"before deciding."
            )
    else:
        recommendation = (
            "Both options yield roughly equal royalties. Consider non-financial "
            "factors: KU offers discoverability; wide offers platform independence."
        )

    # ── Detailed breakdown ──
    details = {
        "ku_page_reads_revenue": round(ku_page_revenue, 2),
        "ku_paid_sales_revenue": round(ku_paid_sales_revenue, 2),
        "ku_paid_royalties": round(ku_paid_royalties, 2),
        "ku_pages_per_read": request.book_page_count,
        "ku_reads_per_month": request.estimated_ku_reads_per_month,
        "ku_page_rate": request.ku_page_rate,
        "wide_sales_revenue": round(wide_sales_revenue, 2),
        "wide_royalties": round(wide_royalties, 2),
        "wide_price": request.wide_price,
        "wide_monthly_sales": request.wide_monthly_sales,
        "wide_royalty_rate": request.wide_royalty_rate,
        "breakeven_ku_reads": _breakeven_ku_reads(
            wide_total_monthly_royalties,
            ku_paid_royalties,
            request.book_page_count,
            request.ku_page_rate,
        ),
    }

    return KUCalculatorResponse(
        ku_exclusive=ku_breakdown,
        wide_distribution=wide_breakdown,
        difference_monthly=diff_monthly,
        difference_annual=diff_annual,
        recommendation=recommendation,
        details=details,
    )


def _breakeven_ku_reads(
    wide_royalties: float,
    ku_paid_royalties: float,
    page_count: int,
    page_rate: float,
) -> int:
    """Calculate how many monthly KU reads needed to match wide royalties.

    Solves: page_count * reads * page_rate + ku_paid_royalties >= wide_royalties
    => reads >= (wide_royalties - ku_paid_royalties) / (page_count * page_rate)
    """
    revenue_gap = wide_royalties - ku_paid_royalties
    if revenue_gap <= 0:
        return 0
    per_read_revenue = page_count * page_rate
    if per_read_revenue <= 0:
        return 0
    import math

    return math.ceil(revenue_gap / per_read_revenue)
