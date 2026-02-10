# W24: Tests for Product Page Lab DB Queries

## Files to create/modify
- `backend/tests/unit/test_product_page_lab_service.py` — NEW or update

## Task

### 1. Read current product page lab service and tests

Read `backend/app/modules/product_page_lab/service.py` and any existing tests.

### 2. Write comprehensive unit tests

Test all service methods:
- A/B test creation
- A/B test listing (by org)
- A/B test status updates (start, stop, complete)
- Variant management (add, update, remove variants)
- Results retrieval and statistical significance calculation
- Blurb generation/optimization

```python
class TestCreateABTest:
    @pytest.mark.asyncio
    async def test_creates_test_in_db(self):
        """create_test should persist an ABTest record."""
        ...

    @pytest.mark.asyncio
    async def test_creates_with_variants(self):
        """Should create test with specified variants."""
        ...

class TestGetTestResults:
    @pytest.mark.asyncio
    async def test_returns_metrics_for_completed_test(self):
        """get_results should return conversion metrics for each variant."""
        ...

    @pytest.mark.asyncio
    async def test_returns_none_for_nonexistent(self):
        """get_results for missing test should raise 404."""
        ...

class TestUpdateTestStatus:
    @pytest.mark.asyncio
    async def test_start_test(self):
        """Starting a test should set status to 'running'."""
        ...

    @pytest.mark.asyncio
    async def test_stop_test(self):
        """Stopping a test should set status to 'stopped'."""
        ...
```

Write at least 8 tests covering the full CRUD lifecycle and edge cases.
