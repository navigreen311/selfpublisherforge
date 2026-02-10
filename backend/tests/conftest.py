"""Shared test fixtures for the backend test suite."""
from __future__ import annotations

import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database import Base, get_db

# Ensure all models are imported so Base.metadata knows about them.
# IMPORTANT: must come BEFORE ``from app.main import create_app`` because
# importing main.py triggers ``create_app()`` which loads module routers.
# Some module routers define inline ORM models with ``extend_existing=True``
# that expect the canonical models to already be registered in the metadata.
import app.models  # noqa: F401, E402

from app.main import create_app  # noqa: E402

# ---------------------------------------------------------------------------
# In-memory SQLite for tests (async via aiosqlite)
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


# ---------------------------------------------------------------------------
# Strip PostgreSQL-only server_defaults before CREATE TABLE on SQLite
# ---------------------------------------------------------------------------

@event.listens_for(Base.metadata, "before_create")
def _strip_pg_server_defaults(target, connection, **kw):
    """Remove server_default values that use PostgreSQL-specific functions
    (e.g. gen_random_uuid()) when running against SQLite for tests.
    The Python-side ``default`` still handles value generation."""
    if connection.dialect.name == "sqlite":
        for table in target.tables.values():
            for column in table.columns:
                if column.server_default is not None:
                    sd = column.server_default
                    if hasattr(sd, "arg") and hasattr(sd.arg, "text"):
                        if "gen_random_uuid" in str(sd.arg.text):
                            column.server_default = None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a fresh database session with tables created/dropped per test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Yield an HTTP test client with the DB dependency overridden."""

    async def _override_get_db():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def org_id() -> uuid.UUID:
    """Return the placeholder org ID used by the routers."""
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


# ---------------------------------------------------------------------------
# Auth-specific fixtures
# ---------------------------------------------------------------------------

VALID_PASSWORD = "StrongP@ss1"


@pytest_asyncio.fixture(scope="function")
async def seed_user(db_session: AsyncSession):
    """Factory fixture that inserts a user + org into the test DB.

    Usage::

        user = await seed_user()
        user = await seed_user(email="other@test.com", mfa=True)
    """
    from app.core.security import hash_password
    from app.models.organization import Organization
    from app.models.user import User, UserRole
    from app.modules.auth.utils import generate_totp_secret

    async def _create(
        email: str = "user@test.com",
        password: str = VALID_PASSWORD,
        mfa: bool = False,
    ) -> User:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="TestOrg", slug=f"testorg-{str(org_id)[:8]}")
        db_session.add(org)

        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            org_id=org_id,
            email=email,
            name="Test User",
            password_hash=hash_password(password),
            role=UserRole.OWNER,
            email_verified=False,
            mfa_enabled=mfa,
            mfa_secret=generate_totp_secret() if mfa else None,
        )
        db_session.add(user)
        await db_session.flush()
        return user

    return _create


@pytest_asyncio.fixture(scope="function")
async def auth_headers(client: AsyncClient):
    """Factory fixture returning auth headers for a registered user.

    Usage::

        headers = await auth_headers()
        headers = await auth_headers(email="other@test.com")
    """
    from app.config import get_settings

    settings = get_settings()
    prefix = f"{settings.API_V1_PREFIX}/auth"

    async def _create(email: str = "auth-fixture@test.com") -> dict:
        resp = await client.post(
            f"{prefix}/register",
            json={
                "email": email,
                "password": VALID_PASSWORD,
                "name": "Fixture User",
                "org_name": "Fixture Org",
            },
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        token = data["tokens"]["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _create
