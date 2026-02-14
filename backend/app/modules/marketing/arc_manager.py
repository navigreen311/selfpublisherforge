"""ARC (Advance Review Copy) campaign manager.

Handles:
- Recipient management
- Delivery tracking
- Review follow-up scheduling
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.marketing import (
    ARCCampaign,
    ARCRecipient,
    ARCRecipientStatus,
)

logger = logging.getLogger(__name__)


class ARCManager:
    """Manages ARC campaign operations: delivery, tracking, follow-up."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_recipients(
        self,
        campaign_id: UUID,
        org_id: UUID,
        recipients: list[dict[str, str]],
    ) -> list[ARCRecipient]:
        """Add recipients to an existing ARC campaign."""
        campaign = await self._get_campaign(campaign_id, org_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        new_recipients = []
        for r in recipients:
            recipient = ARCRecipient(
                campaign_id=campaign_id,
                name=r["name"],
                email=r["email"],
                notes=r.get("notes"),
                status=ARCRecipientStatus.PENDING,
            )
            self.db.add(recipient)
            new_recipients.append(recipient)

        campaign.total_copies += len(new_recipients)
        await self.db.flush()

        return new_recipients

    async def remove_recipient(
        self,
        campaign_id: UUID,
        org_id: UUID,
        recipient_id: UUID,
    ) -> bool:
        """Remove a recipient from an ARC campaign (only if pending)."""
        campaign = await self._get_campaign(campaign_id, org_id)
        if not campaign:
            return False

        stmt = select(ARCRecipient).where(
            and_(
                ARCRecipient.id == recipient_id,
                ARCRecipient.campaign_id == campaign_id,
            )
        )
        result = await self.db.execute(stmt)
        recipient = result.scalar_one_or_none()

        if not recipient or recipient.status != ARCRecipientStatus.PENDING:
            return False

        await self.db.delete(recipient)
        campaign.total_copies = max(0, campaign.total_copies - 1)
        await self.db.flush()
        return True

    async def mark_delivered(
        self,
        campaign_id: UUID,
        org_id: UUID,
        recipient_id: UUID,
    ) -> ARCRecipient | None:
        """Mark an ARC copy as delivered to a recipient."""
        recipient = await self._get_recipient(campaign_id, org_id, recipient_id)
        if not recipient:
            return None

        recipient.status = ARCRecipientStatus.DELIVERED
        recipient.delivered_at = datetime.now(tz=UTC)
        await self.db.flush()
        return recipient

    async def mark_reviewed(
        self,
        campaign_id: UUID,
        org_id: UUID,
        recipient_id: UUID,
        review_url: str | None = None,
    ) -> ARCRecipient | None:
        """Mark a recipient as having submitted a review."""
        recipient = await self._get_recipient(campaign_id, org_id, recipient_id)
        if not recipient:
            return None

        recipient.status = ARCRecipientStatus.REVIEWED
        recipient.review_received_at = datetime.now(tz=UTC)
        if review_url:
            recipient.review_url = review_url

        # Update campaign stats
        campaign = await self._get_campaign(campaign_id, org_id)
        if campaign:
            campaign.reviews_received += 1

        await self.db.flush()
        return recipient

    async def get_pending_follow_ups(
        self,
        org_id: UUID,
        days_since_send: int = 7,
    ) -> list[dict[str, Any]]:
        """Get recipients who were sent ARC copies but have not reviewed.

        Returns recipients whose copies were sent more than `days_since_send`
        days ago and who have not yet submitted a review.
        """
        cutoff = datetime.now(tz=UTC) - timedelta(days=days_since_send)

        stmt = (
            select(ARCRecipient)
            .join(ARCCampaign, ARCRecipient.campaign_id == ARCCampaign.id)
            .where(
                and_(
                    ARCCampaign.org_id == org_id,
                    ARCCampaign.deleted_at.is_(None),
                    ARCRecipient.status.in_([
                        ARCRecipientStatus.SENT,
                        ARCRecipientStatus.DELIVERED,
                    ]),
                    ARCRecipient.sent_at <= cutoff,
                )
            )
        )
        result = await self.db.execute(stmt)
        recipients = list(result.scalars().all())

        return [
            {
                "recipient_id": str(r.id),
                "campaign_id": str(r.campaign_id),
                "name": r.name,
                "email": r.email,
                "sent_at": r.sent_at.isoformat() if r.sent_at else None,
                "days_since_send": (datetime.now(tz=UTC) - r.sent_at).days if r.sent_at else 0,
            }
            for r in recipients
        ]

    async def get_campaign_stats(
        self,
        campaign_id: UUID,
        org_id: UUID,
    ) -> dict[str, Any] | None:
        """Get detailed statistics for an ARC campaign."""
        campaign = await self._get_campaign(campaign_id, org_id)
        if not campaign:
            return None

        status_counts: dict[str, int] = {}
        for recipient in campaign.recipients:
            status = recipient.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "campaign_id": str(campaign.id),
            "campaign_name": campaign.name,
            "status": campaign.status.value,
            "total_copies": campaign.total_copies,
            "sent_copies": campaign.sent_copies,
            "reviews_received": campaign.reviews_received,
            "review_rate": (
                campaign.reviews_received / campaign.sent_copies * 100
                if campaign.sent_copies > 0
                else 0.0
            ),
            "recipient_status_breakdown": status_counts,
            "deadline": campaign.deadline.isoformat() if campaign.deadline else None,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _get_campaign(
        self, campaign_id: UUID, org_id: UUID
    ) -> ARCCampaign | None:
        stmt = (
            select(ARCCampaign)
            .options(selectinload(ARCCampaign.recipients))
            .where(
                and_(
                    ARCCampaign.id == campaign_id,
                    ARCCampaign.org_id == org_id,
                    ARCCampaign.deleted_at.is_(None),
                )
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_recipient(
        self, campaign_id: UUID, org_id: UUID, recipient_id: UUID
    ) -> ARCRecipient | None:
        stmt = (
            select(ARCRecipient)
            .join(ARCCampaign, ARCRecipient.campaign_id == ARCCampaign.id)
            .where(
                and_(
                    ARCRecipient.id == recipient_id,
                    ARCRecipient.campaign_id == campaign_id,
                    ARCCampaign.org_id == org_id,
                    ARCCampaign.deleted_at.is_(None),
                )
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def export_campaign_csv(
        self, campaign_id: UUID, org_id: UUID,
    ) -> str:
        """Export campaign recipients as CSV string."""
        import csv
        import io

        stmt = select(ARCCampaign).where(
            ARCCampaign.id == campaign_id,
            ARCCampaign.org_id == org_id,
        )
        result = await self.db.execute(stmt)
        campaign = result.scalar_one_or_none()
        if not campaign:
            return ""

        recipients_stmt = select(ARCRecipient).where(
            ARCRecipient.campaign_id == campaign_id,
        )
        recipients_result = await self.db.execute(recipients_stmt)
        recipients = list(recipients_result.scalars().all())

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Name", "Email", "Status", "Sent At", "Review URL"])
        for r in recipients:
            writer.writerow([
                r.name,
                r.email,
                str(r.status),
                r.sent_at.isoformat() if r.sent_at else "",
                r.review_url or "",
            ])
        return output.getvalue()
