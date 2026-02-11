#!/usr/bin/env python3
"""Database seeding script for development and demo environments.

Usage:
    python -m scripts.seed                    # Seed all data
    python -m scripts.seed --reset            # Reset DB and seed
    python -m scripts.seed --module users     # Seed only users
    python -m scripts.seed --module projects  # Seed only projects
"""
import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.database import async_session, engine, Base
from scripts.seeds.users import seed_users
from scripts.seeds.projects import seed_projects
from scripts.seeds.content import seed_content
from scripts.seeds.analytics import seed_analytics
from scripts.seeds.market import seed_market
from scripts.seeds.marketing import seed_marketing


async def reset_database():
    """Drop all tables and recreate them."""
    print("⚠️  Resetting database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Database reset complete")


async def seed_all():
    """Run all seed modules in order."""
    async with async_session() as db:
        # 1. Seed users and orgs
        print("\n📦 Seeding users and organizations...")
        user_data = await seed_users(db)
        user_map = user_data["users"]
        org_map = user_data["orgs"]

        # Get Jane's IDs (our main demo user)
        jane_user_id = user_map.get("jane@example.com")
        jane_org_id = org_map.get("jane@example.com")

        if not jane_user_id or not jane_org_id:
            print("❌ Failed to create Jane's user/org")
            return

        # 2. Seed projects and books
        print("\n📚 Seeding projects and books...")
        project_data = await seed_projects(db, jane_org_id)
        book_ids = project_data["books"]

        # 3. Seed chapters and content
        print("\n📝 Seeding chapters and content...")
        await seed_content(db, book_ids)

        # 4. Seed analytics and revenue
        print("\n📊 Seeding analytics and revenue data...")
        await seed_analytics(db, jane_org_id, book_ids)

        # 5. Seed market intelligence
        print("\n🔍 Seeding market intelligence data...")
        await seed_market(db, jane_org_id)

        # 6. Seed marketing campaigns
        print("\n📧 Seeding marketing campaigns...")
        await seed_marketing(db, jane_org_id, jane_user_id, book_ids)

    print("\n✅ All seeding complete!")
    print("\n📋 Demo Credentials:")
    print("  Admin:   admin@selfpublisherforge.com / admin123")
    print("  Pro:     jane@example.com / demo123")
    print("  Starter: bob@example.com / demo123")
    print("  Free:    alice@example.com / demo123")


async def seed_module(module_name: str):
    """Seed a specific module only."""
    async with async_session() as db:
        if module_name == "users":
            print("📦 Seeding users...")
            await seed_users(db)

        elif module_name == "projects":
            # Need to get org_id first
            result = await db.execute(
                text("SELECT id FROM organizations WHERE slug = 'janes-publishing'")
            )
            row = result.first()
            if not row:
                print("❌ Jane's org not found. Run 'users' module first.")
                return
            jane_org_id = row[0]
            print("📚 Seeding projects...")
            await seed_projects(db, jane_org_id)

        elif module_name == "content":
            # Get book IDs
            result = await db.execute(
                text(
                    """
                SELECT b.title, b.id
                FROM books b
                JOIN projects p ON b.project_id = p.id
                JOIN organizations o ON p.org_id = o.id
                WHERE o.slug = 'janes-publishing'
                """
                )
            )
            book_ids = {row[0]: row[1] for row in result}
            if not book_ids:
                print("❌ No books found. Run 'projects' module first.")
                return
            print("📝 Seeding content...")
            await seed_content(db, book_ids)

        elif module_name == "analytics":
            # Get org and book IDs
            result = await db.execute(
                text("SELECT id FROM organizations WHERE slug = 'janes-publishing'")
            )
            row = result.first()
            if not row:
                print("❌ Jane's org not found.")
                return
            jane_org_id = row[0]

            result = await db.execute(
                text(
                    """
                SELECT b.title, b.id
                FROM books b
                JOIN projects p ON b.project_id = p.id
                WHERE p.org_id = :org_id
                """
                ),
                {"org_id": jane_org_id},
            )
            book_ids = {row[0]: row[1] for row in result}
            print("📊 Seeding analytics...")
            await seed_analytics(db, jane_org_id, book_ids)

        elif module_name == "market":
            result = await db.execute(
                text("SELECT id FROM organizations WHERE slug = 'janes-publishing'")
            )
            row = result.first()
            if not row:
                print("❌ Jane's org not found.")
                return
            jane_org_id = row[0]
            print("🔍 Seeding market data...")
            await seed_market(db, jane_org_id)

        elif module_name == "marketing":
            # Get org, user, and book IDs
            result = await db.execute(
                text(
                    """
                SELECT o.id, u.id
                FROM organizations o
                JOIN users u ON u.org_id = o.id
                WHERE o.slug = 'janes-publishing' AND u.email = 'jane@example.com'
                """
                )
            )
            row = result.first()
            if not row:
                print("❌ Jane's org/user not found.")
                return
            jane_org_id, jane_user_id = row[0], row[1]

            result = await db.execute(
                text(
                    """
                SELECT b.title, b.id
                FROM books b
                JOIN projects p ON b.project_id = p.id
                WHERE p.org_id = :org_id
                """
                ),
                {"org_id": jane_org_id},
            )
            book_ids = {row[0]: row[1] for row in result}
            print("📧 Seeding marketing...")
            await seed_marketing(db, jane_org_id, jane_user_id, book_ids)

        else:
            print(f"❌ Unknown module: {module_name}")
            print("Available modules: users, projects, content, analytics, market, marketing")
            return

    print("✅ Module seeding complete!")


async def main():
    """Main entrypoint."""
    parser = argparse.ArgumentParser(
        description="Seed database with demo data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m scripts.seed                    # Seed all data
  python -m scripts.seed --reset            # Reset DB and seed all
  python -m scripts.seed --module users     # Seed only users module
        """,
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop all tables and recreate before seeding",
    )
    parser.add_argument(
        "--module",
        type=str,
        choices=["users", "projects", "content", "analytics", "market", "marketing", "all"],
        help="Seed a specific module only",
    )

    args = parser.parse_args()

    try:
        if args.reset:
            await reset_database()

        if args.module and args.module != "all":
            await seed_module(args.module)
        else:
            await seed_all()

    except KeyboardInterrupt:
        print("\n\n⚠️  Seeding interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
