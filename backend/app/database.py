import enum
import logging
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as _SAEnum, func, text
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import get_settings

# ---------------------------------------------------------------------------
# Patch: force SQLAlchemy Enum to use .value (lowercase) instead of .name
# (uppercase) for PEP-435 enums.  The Alembic migrations create PostgreSQL
# ENUM types with lowercase values, so the ORM must match.
# ---------------------------------------------------------------------------
_orig_enum_init = _SAEnum.__init__

def _patched_enum_init(self, *enums, **kw):
    if enums and len(enums) == 1 and isinstance(enums[0], type) and issubclass(enums[0], enum.Enum):
        kw.setdefault("values_callable", lambda cls: [e.value for e in cls])
    _orig_enum_init(self, *enums, **kw)

_SAEnum.__init__ = _patched_enum_init

logger = logging.getLogger(__name__)

settings = get_settings()
engine = create_async_engine(settings.DATABASE_URL, echo=settings.DATABASE_ECHO)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    """Project-wide declarative base.

    Automatically injects ``extend_existing=True`` into every concrete
    model's ``__table_args__`` so that duplicate table definitions
    (common after merging many feature branches) are merged instead of
    raising ``InvalidRequestError``.
    """

    def __init_subclass__(cls, **kw):
        # A class is concrete (needs a table) when it declares __tablename__
        # in its own __dict__ and does NOT declare __abstract__ = True itself.
        is_own_abstract = cls.__dict__.get("__abstract__", False)
        has_own_tablename = "__tablename__" in cls.__dict__
        if not is_own_abstract and has_own_tablename:
            ta = cls.__dict__.get("__table_args__")  # only this class, not inherited
            if ta is None:
                cls.__table_args__ = {"extend_existing": True}
            elif isinstance(ta, dict):
                ta.setdefault("extend_existing", True)
            elif isinstance(ta, tuple):
                if ta and isinstance(ta[-1], dict):
                    ta[-1].setdefault("extend_existing", True)
                else:
                    cls.__table_args__ = (*ta, {"extend_existing": True})
        super().__init_subclass__(**kw)

class BaseModel(Base):
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

class TenantModel(BaseModel):
    __abstract__ = True

    org_id: Mapped[uuid.UUID] = mapped_column(index=True)

async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except (SQLAlchemyError, DBAPIError):
            logger.error("Database session error, rolling back", exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Verify database connectivity.

    Schema creation is handled by Alembic migrations, so we only test
    the connection here rather than calling ``Base.metadata.create_all``.
    """
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
