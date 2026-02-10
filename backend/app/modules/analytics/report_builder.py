"""Report generation engine.

Generates PDF and XLSX reports for revenue summaries, book performance,
marketing ROI, and portfolio overviews.
"""

from __future__ import annotations

import io
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.modules.analytics.models import Report, RoyaltyRecord
from app.modules.analytics.schemas import OutputFormat, ReportStatus, ReportType


class ReportGenerationError(Exception):
    """Raised when report generation fails."""
    pass


async def generate_report(
    db: AsyncSession,
    report: Report,
) -> Report:
    """Generate a report based on its type and parameters.

    Updates the Report record with file path, size, and status.
    """
    try:
        report.status = ReportStatus.PROCESSING.value
        await db.flush()

        report_data = await _gather_report_data(
            db,
            org_id=report.org_id,
            report_type=ReportType(report.report_type),
            parameters=report.parameters or {},
        )

        output_format = OutputFormat(report.output_format)
        if output_format == OutputFormat.XLSX:
            file_bytes = _build_xlsx(report.title, report_data)
            extension = "xlsx"
        else:
            file_bytes = _build_pdf(report.title, report_data)
            extension = "pdf"

        # Store file to local disk (in production, upload to S3)
        reports_dir = os.path.join(os.getcwd(), "generated_reports")
        os.makedirs(reports_dir, exist_ok=True)
        file_name = f"{report.id}.{extension}"
        file_path = os.path.join(reports_dir, file_name)

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        report.file_path = file_path
        report.file_size = len(file_bytes)
        report.status = ReportStatus.COMPLETED.value
        report.generated_at = datetime.now(timezone.utc)
        await db.flush()

        return report

    except (ValueError, KeyError, OSError, SQLAlchemyError) as exc:
        logger.error("Report generation failed for report %s: %s", report.id, exc, exc_info=True)
        report.status = ReportStatus.FAILED.value
        report.error_message = str(exc)
        await db.flush()
        raise ReportGenerationError(str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error generating report %s", report.id, exc_info=True)
        report.status = ReportStatus.FAILED.value
        report.error_message = str(exc)
        await db.flush()
        raise ReportGenerationError(str(exc)) from exc


async def _gather_report_data(
    db: AsyncSession,
    org_id: uuid.UUID,
    report_type: ReportType,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    """Gather data needed for a specific report type."""
    if report_type == ReportType.REVENUE_SUMMARY:
        return await _gather_revenue_summary(db, org_id, parameters)
    elif report_type == ReportType.BOOK_PERFORMANCE:
        return await _gather_book_performance(db, org_id, parameters)
    elif report_type == ReportType.PORTFOLIO_OVERVIEW:
        return await _gather_portfolio_overview(db, org_id, parameters)
    elif report_type == ReportType.MARKETING_ROI:
        return await _gather_marketing_roi(db, org_id, parameters)
    else:
        return await _gather_revenue_summary(db, org_id, parameters)


async def _gather_revenue_summary(
    db: AsyncSession,
    org_id: uuid.UUID,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    """Gather data for a revenue summary report."""
    # Total revenue
    totals_query = (
        select(
            func.coalesce(func.sum(RoyaltyRecord.net_revenue), 0).label("total_revenue"),
            func.coalesce(func.sum(RoyaltyRecord.gross_revenue), 0).label("gross_revenue"),
            func.coalesce(func.sum(RoyaltyRecord.net_units), 0).label("total_units"),
            func.count(RoyaltyRecord.id).label("record_count"),
        )
        .where(
            and_(
                RoyaltyRecord.org_id == org_id,
                RoyaltyRecord.deleted_at.is_(None),
            )
        )
    )
    result = await db.execute(totals_query)
    totals = result.one()

    # Revenue by platform
    platform_query = (
        select(
            RoyaltyRecord.platform,
            func.coalesce(func.sum(RoyaltyRecord.net_revenue), 0).label("revenue"),
            func.coalesce(func.sum(RoyaltyRecord.net_units), 0).label("units"),
        )
        .where(
            and_(
                RoyaltyRecord.org_id == org_id,
                RoyaltyRecord.deleted_at.is_(None),
            )
        )
        .group_by(RoyaltyRecord.platform)
    )
    platform_result = await db.execute(platform_query)
    platforms = [
        {"platform": r.platform, "revenue": str(r.revenue), "units": r.units}
        for r in platform_result.all()
    ]

    return {
        "report_type": "Revenue Summary",
        "total_revenue": str(totals.total_revenue),
        "gross_revenue": str(totals.gross_revenue),
        "total_units": totals.total_units,
        "record_count": totals.record_count,
        "by_platform": platforms,
    }


async def _gather_book_performance(
    db: AsyncSession,
    org_id: uuid.UUID,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    """Gather data for a book performance report."""
    books_query = (
        select(
            RoyaltyRecord.title,
            func.coalesce(func.sum(RoyaltyRecord.net_revenue), 0).label("revenue"),
            func.coalesce(func.sum(RoyaltyRecord.net_units), 0).label("units"),
            func.count(RoyaltyRecord.id).label("records"),
        )
        .where(
            and_(
                RoyaltyRecord.org_id == org_id,
                RoyaltyRecord.deleted_at.is_(None),
            )
        )
        .group_by(RoyaltyRecord.title)
        .order_by(func.sum(RoyaltyRecord.net_revenue).desc())
        .limit(50)
    )
    result = await db.execute(books_query)
    books = [
        {"title": r.title, "revenue": str(r.revenue), "units": r.units, "records": r.records}
        for r in result.all()
    ]

    return {
        "report_type": "Book Performance",
        "books": books,
        "total_books": len(books),
    }


async def _gather_portfolio_overview(
    db: AsyncSession,
    org_id: uuid.UUID,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    """Gather data for a portfolio overview report."""
    revenue_data = await _gather_revenue_summary(db, org_id, parameters)
    book_data = await _gather_book_performance(db, org_id, parameters)
    return {
        "report_type": "Portfolio Overview",
        **revenue_data,
        **book_data,
    }


async def _gather_marketing_roi(
    db: AsyncSession,
    org_id: uuid.UUID,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    """Gather data for a marketing ROI report.

    Combines revenue data with advertising spend from the campaigns module
    to compute return on investment.
    """
    from app.modules.advertising.models import Campaign, CampaignPerformance

    revenue_data = await _gather_revenue_summary(db, org_id, parameters)

    # Compute total advertising spend
    spend_stmt = (
        select(func.coalesce(func.sum(CampaignPerformance.spend), 0.0))
        .join(Campaign, CampaignPerformance.campaign_id == Campaign.id)
        .where(
            Campaign.org_id == org_id,
            Campaign.deleted_at.is_(None),
            CampaignPerformance.deleted_at.is_(None),
        )
    )
    spend_result = await db.execute(spend_stmt)
    total_spend = float(spend_result.scalar() or 0.0)
    total_revenue = float(revenue_data.get("total_revenue", 0))
    roi = ((total_revenue - total_spend) / total_spend * 100) if total_spend > 0 else 0.0

    return {
        "report_type": "Marketing ROI",
        "total_ad_spend": round(total_spend, 2),
        "total_revenue": round(total_revenue, 2),
        "net_return": round(total_revenue - total_spend, 2),
        "roi_percent": round(roi, 1),
        **revenue_data,
    }


def _build_pdf(title: str, data: dict[str, Any]) -> bytes:
    """Build a simple PDF report.

    In production, this would use a library like ReportLab or WeasyPrint.
    For now, generates a simple text-based representation as bytes.
    """
    lines = [
        f"REPORT: {title}",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "=" * 60,
        "",
    ]

    report_type = data.get("report_type", "Report")
    lines.append(f"Type: {report_type}")
    lines.append("")

    if "total_revenue" in data:
        lines.append(f"Total Revenue: ${data['total_revenue']}")
    if "total_units" in data:
        lines.append(f"Total Units: {data['total_units']}")
    if "gross_revenue" in data:
        lines.append(f"Gross Revenue: ${data['gross_revenue']}")

    lines.append("")

    if "by_platform" in data:
        lines.append("Revenue by Platform:")
        for p in data["by_platform"]:
            lines.append(f"  {p['platform']}: ${p['revenue']} ({p['units']} units)")

    if "books" in data:
        lines.append("")
        lines.append("Top Books:")
        for b in data["books"][:10]:
            lines.append(f"  {b['title']}: ${b['revenue']} ({b['units']} units)")

    content = "\n".join(lines)
    return content.encode("utf-8")


def _build_xlsx(title: str, data: dict[str, Any]) -> bytes:
    """Build an XLSX report.

    In production, this would use openpyxl.
    For now, generates a CSV-like representation as bytes.
    """
    lines = [f"Title,{title}"]
    lines.append(f"Generated,{datetime.now(timezone.utc).isoformat()}")
    lines.append("")

    if "total_revenue" in data:
        lines.append(f"Total Revenue,{data['total_revenue']}")
    if "total_units" in data:
        lines.append(f"Total Units,{data['total_units']}")

    lines.append("")

    if "by_platform" in data:
        lines.append("Platform,Revenue,Units")
        for p in data["by_platform"]:
            lines.append(f"{p['platform']},{p['revenue']},{p['units']}")

    if "books" in data:
        lines.append("")
        lines.append("Book Title,Revenue,Units")
        for b in data["books"]:
            safe_title = b["title"].replace(",", " ")
            lines.append(f"{safe_title},{b['revenue']},{b['units']}")

    content = "\n".join(lines)
    return content.encode("utf-8")
