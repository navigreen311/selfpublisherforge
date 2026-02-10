# W20: Tests for Publishing Ops DB Service

## Files to create/modify
- `backend/tests/unit/test_publishing_ops_service.py` — NEW or update

## Context
Publishing ops is being migrated from in-memory dicts to DB (by W02). Write tests using mocked AsyncSession.

## Task

### 1. Find and read existing tests

Check `backend/tests/` for any publishing ops tests. Read the current service interface.

### 2. Write comprehensive unit tests

Cover all service functions:
- `list_accounts(db, org_id)` — returns accounts for org
- `create_account(db, org_id, data)` — creates publishing account
- `delete_account(db, account_id)` — soft-deletes account
- `generate_export(db, org_id, request)` — generates EPUB/PDF export
- `list_templates(db, org_id)` — returns built-in + custom templates
- `create_template(db, org_id, data)` — creates custom template
- `get_metadata(db, book_id)` — gets book metadata
- `update_metadata(db, book_id, data)` — creates/updates metadata
- `list_listings(db, org_id)` — returns all listings
- `sync_listing(db, listing_id)` — queues sync

Test patterns:
```python
@pytest.mark.asyncio
async def test_create_account_persists(self):
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    from app.modules.publishing_ops.schemas import PublishingAccountCreate
    data = PublishingAccountCreate(
        platform="kdp",
        account_name="My KDP",
        account_email="test@example.com",
    )
    result = await create_account(db, uuid.uuid4(), data)
    db.add.assert_called_once()
    assert result.platform == "kdp"
```

Write at least 10 tests covering CRUD operations, edge cases (not found, duplicate), and export generation.
