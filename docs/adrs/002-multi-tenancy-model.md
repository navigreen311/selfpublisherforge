# ADR-002: Multi-Tenancy Model

**Date**: 2025-06-15
**Status**: Accepted

## Context

SelfPublisherForge serves multiple distinct customer segments -- independent authors, small publishers, and publishing agencies -- each operating within their own organizational boundary. The platform must:

- **Isolate tenant data**: One organization must never see another organization's books, campaigns, analytics, or billing data. Data leakage between tenants is a critical security and trust violation.
- **Support team collaboration**: Within a single organization, multiple users need shared access to projects, books, and campaigns with role-based permissions (owner, admin, editor, viewer).
- **Scale to thousands of tenants**: The platform targets a broad market of self-publishers. The tenancy model must not impose per-tenant infrastructure overhead that limits growth.
- **Keep operational complexity low**: A small engineering team must be able to maintain, migrate, and back up the database without per-tenant operational procedures.
- **Support cross-tenant analytics (admin)**: Platform administrators need aggregate analytics (total users, revenue by tier, feature usage) without querying each tenant separately.

Three multi-tenancy strategies were evaluated:

### Option A: Row-Level Isolation (org_id column)

Every tenant-scoped table includes an `org_id` foreign key column. All queries filter by `org_id`, enforced at the ORM/middleware layer.

- **Pros**: Single database, single schema, simple migrations, efficient cross-tenant admin queries, no per-tenant provisioning.
- **Cons**: Requires disciplined query filtering (risk of missing `org_id` WHERE clause), shared indexes and connection pool, noisy-neighbor risk on large tables.

### Option B: Schema-Per-Tenant

Each tenant gets a dedicated PostgreSQL schema within the same database. Application sets `search_path` per request.

- **Pros**: Stronger logical isolation, per-tenant backup/restore possible, `search_path` prevents accidental cross-tenant queries.
- **Cons**: Schema migrations must be applied N times (once per tenant), connection pooling complexity (schema switching), cross-tenant analytics require `UNION ALL` across schemas, operational burden grows linearly with tenants.

### Option C: Database-Per-Tenant

Each tenant gets a dedicated PostgreSQL database (or separate RDS instance).

- **Pros**: Strongest isolation, independent scaling, per-tenant backup/restore, no noisy-neighbor risk.
- **Cons**: Extremely high infrastructure cost (RDS instance per tenant is prohibitive), migrations must run against every database, no straightforward cross-tenant queries, connection management complexity, operational burden is unsustainable for a small team.

## Decision

We will use **row-level multi-tenancy with an `org_id` column** (Option A) on all tenant-scoped database tables, enforced at multiple layers:

### 1. Database schema

Every tenant-scoped model includes a non-nullable `org_id` column with a foreign key to the `organizations` table and an index for query performance:

```python
class Book(Base):
    __tablename__ = "books"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500))
    # ...
```

### 2. ORM-level enforcement

A base query mixin automatically applies `org_id` filtering to all queries. Service methods receive `org_id` from the authenticated request context, and all CRUD operations include it:

```python
async def get_books(db: AsyncSession, org_id: uuid.UUID) -> list[Book]:
    result = await db.execute(
        select(Book).where(Book.org_id == org_id)
    )
    return result.scalars().all()
```

### 3. API middleware

The authentication middleware extracts `org_id` from the JWT token and injects it into the request state. Route handlers and dependency injection functions use this value for all database operations, ensuring no endpoint can operate outside the user's organization scope.

### 4. Testing

Integration tests verify tenant isolation by creating test data for two organizations and asserting that queries scoped to org A never return org B's data.

## Consequences

### Positive

- **Simple operations**: A single PostgreSQL database with a single schema means one Alembic migration run applies changes for all tenants simultaneously. Backup, restore, and monitoring are standard single-database operations.
- **Efficient cross-tenant queries**: Platform admin analytics (total users, revenue by tier, module usage) are simple aggregation queries on the same tables without `UNION ALL` or cross-database joins.
- **No per-tenant provisioning**: Onboarding a new organization requires only inserting a row in the `organizations` table. No schema creation, no database provisioning, no connection reconfiguration.
- **Straightforward connection pooling**: All requests share the same database connection pool. There is no need to manage per-schema or per-database connection routing.
- **Lower infrastructure cost**: One RDS instance (multi-AZ in production) serves all tenants. Cost scales with overall data volume, not tenant count.
- **Compatible with Alembic autogenerate**: SQLAlchemy 2.0 models with `org_id` columns work seamlessly with Alembic's autogenerate, which only needs to inspect one schema.

### Negative

- **Risk of missing org_id filter**: If a developer writes a query without filtering by `org_id`, it could return data from all tenants. This is mitigated by:
  - Enforcing `org_id` in base service methods and ORM mixins.
  - Code review checklists that specifically check for tenant scoping.
  - Integration tests that assert cross-tenant isolation.
  - Linting rules that flag direct `select()` calls without `org_id` in WHERE clauses.
- **Noisy-neighbor risk**: A single tenant with unusually high data volume or query complexity could degrade performance for other tenants. This is mitigated by:
  - Rate limiting per user and per organization at the API layer (Redis sliding window).
  - Database connection pool limits per request.
  - Monitoring and alerting on slow queries (Datadog APM).
  - Potential future migration to PostgreSQL Row-Level Security (RLS) policies for database-enforced isolation.
- **No per-tenant backup/restore**: Restoring data for a single tenant requires filtering from a full database backup rather than restoring an isolated schema or database. For the current scale and customer base, this tradeoff is acceptable.
- **Index size**: Composite indexes that include `org_id` (e.g., `org_id + created_at`, `org_id + status`) will be larger than single-column indexes. This is standard practice and PostgreSQL handles it efficiently with its B-tree implementation.
- **Future migration difficulty**: If the platform ever needs to move to schema-per-tenant (e.g., for regulatory data residency requirements), the migration would require significant refactoring. However, this is unlikely for the current target market and can be addressed with a new ADR if circumstances change.
