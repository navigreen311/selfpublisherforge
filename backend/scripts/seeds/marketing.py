"""Seed demo marketing campaigns and email templates."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketing import (
    EmailSequence,
    EmailSequenceStatus,
    EmailTemplate,
    EmailTemplateType,
    LaunchPlan,
    LaunchPlanStatus,
)
from app.modules.advertising.models import Campaign


async def seed_marketing(
    db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID, book_ids: dict[str, uuid.UUID]
) -> None:
    """Seed demo marketing campaigns and email templates.

    Args:
        db: Database session
        org_id: Organization ID
        user_id: User ID (creator)
        book_ids: Dict mapping book titles to book IDs
    """
    published_book = book_ids.get("The Dragon's Prophecy")
    if not published_book:
        print("⚠ No published book found, skipping marketing")
        return

    # Check if data already exists
    existing = await db.execute(
        select(LaunchPlan).where(LaunchPlan.org_id == org_id, LaunchPlan.book_id == published_book)
    )
    if existing.scalar_one_or_none():
        print("✓ Marketing data already exists, skipping")
        return

    # Create launch plan
    launch_plan = LaunchPlan(
        org_id=org_id,
        book_id=published_book,
        title="Dragon's Prophecy Launch Campaign",
        description="Complete launch campaign for epic fantasy debut novel",
        status=LaunchPlanStatus.COMPLETED,
        launch_date=datetime.now(UTC) - timedelta(days=180),
        genre="Epic Fantasy",
        target_audience="Adult fantasy readers aged 25-45 who enjoy epic quests and dragon lore",
        budget=500.0,
        goals={
            "first_week_sales": 200,
            "reviews_target": 50,
            "email_subscribers": 1000,
        },
        checklist={
            "cover_design": True,
            "manuscript_final": True,
            "blurb_written": True,
            "arc_sent": True,
        },
        ai_metadata={
            "generated_strategies": [
                "Focus on dragon enthusiast groups",
                "Partner with fantasy book bloggers",
                "Run targeted Facebook ads",
            ]
        },
        created_by=user_id,
    )
    db.add(launch_plan)
    await db.flush()

    # Create advertising campaign
    campaign = Campaign(
        org_id=org_id,
        book_id=published_book,
        name="Dragon's Prophecy - Amazon Ads",
        platform="amazon_ads",
        campaign_type="sponsored_products",
        status="active",
        total_budget=300.00,
        daily_budget=10.00,
        start_date=datetime.now(UTC) - timedelta(days=150),
        end_date=datetime.now(UTC) + timedelta(days=30),
        targeting_keywords=["epic fantasy", "dragon books", "fantasy adventure"],
        negative_keywords=["free", "pirated"],
    )
    db.add(campaign)

    # Create email sequence
    email_sequence = EmailSequence(
        org_id=org_id,
        launch_plan_id=launch_plan.id,
        name="Dragon's Prophecy - Launch Sequence",
        description="5-email launch announcement sequence",
        status=EmailSequenceStatus.COMPLETED,
        trigger_event="book_launch",
        subscriber_count=1247,
        recipient_count=1247,
        sent_count=1247,
        open_rate=0.42,
        click_rate=0.15,
        settings={
            "send_time": "09:00",
            "timezone": "America/New_York",
        },
        created_by=user_id,
    )
    db.add(email_sequence)
    await db.flush()

    # Create email templates
    email_templates = [
        {
            "type": EmailTemplateType.LAUNCH_ANNOUNCEMENT,
            "subject": "🐉 The Dragon's Prophecy is LIVE!",
            "body": """
<h1>The wait is over!</h1>
<p>Dear Reader,</p>
<p>I'm thrilled to announce that <strong>The Dragon's Prophecy</strong> is now available on Amazon!</p>
<p>Join Aria on her epic quest to fulfill an ancient prophecy and save the realm from darkness.</p>
<p><a href="https://amazon.com/dp/B08ABCD123">Get your copy now →</a></p>
<p>To celebrate the launch, the book is <strong>$0.99 for the first 48 hours only!</strong></p>
<p>Happy reading!<br>Jane Doe</p>
            """,
            "delay_days": 0,
        },
        {
            "type": EmailTemplateType.FOLLOW_UP,
            "subject": "Behind the Scenes: Creating The Dragon's Prophecy",
            "body": """
<h1>The Journey Behind the Book</h1>
<p>Hi there,</p>
<p>Thank you for your interest in The Dragon's Prophecy! I wanted to share some behind-the-scenes insights about how this book came to life...</p>
<p>The idea sparked from a dream about an ancient dragon...(continue story)</p>
<p>If you haven't grabbed your copy yet, <a href="https://amazon.com/dp/B08ABCD123">it's still on sale!</a></p>
            """,
            "delay_days": 2,
        },
        {
            "type": EmailTemplateType.REVIEW_REQUEST,
            "subject": "Would you leave a review? 🙏",
            "body": """
<h1>Your Review Matters</h1>
<p>Hi friend,</p>
<p>I hope you're enjoying The Dragon's Prophecy! If you've finished reading (or even if you're partway through), I'd be incredibly grateful if you could leave a quick review on Amazon.</p>
<p>Reviews help other readers discover the book and mean the world to authors like me.</p>
<p><a href="https://amazon.com/review/create-review?asin=B08ABCD123">Leave a review →</a></p>
<p>Thank you so much!<br>Jane</p>
            """,
            "delay_days": 7,
        },
        {
            "type": EmailTemplateType.FOLLOW_UP,
            "subject": "What's Next? Book 2 Sneak Peek",
            "body": """
<h1>Coming Soon: Book 2</h1>
<p>Hello loyal readers,</p>
<p>The adventure continues! I'm hard at work on Book 2 of the Fire Chronicles, and I wanted to give you an exclusive sneak peek...</p>
<p>(Excerpt from Chapter 1 of Book 2)</p>
<p>Expected release: Summer 2026</p>
            """,
            "delay_days": 14,
        },
        {
            "type": EmailTemplateType.CUSTOM,
            "subject": "Free Bonus Content: World Map & Character Guide",
            "body": """
<h1>Exclusive Reader Bonuses</h1>
<p>As a thank you for being part of this journey, I've created some bonus content just for you:</p>
<ul>
<li>Full color map of the Fire Realm</li>
<li>Character guide with backstories</li>
<li>Deleted scenes</li>
</ul>
<p><a href="https://example.com/bonuses">Download your bonuses →</a></p>
            """,
            "delay_days": 21,
        },
    ]

    for idx, template_data in enumerate(email_templates):
        template = EmailTemplate(
            sequence_id=email_sequence.id,
            template_type=template_data["type"],
            subject=template_data["subject"],
            body_html=template_data["body"],
            body_text=None,  # Could strip HTML for plain text version
            order_index=idx,
            delay_days=template_data["delay_days"],
            settings={
                "track_opens": True,
                "track_clicks": True,
            },
        )
        db.add(template)

    await db.commit()

    print(f"✓ Seeded launch plan, campaign, email sequence with {len(email_templates)} templates")
