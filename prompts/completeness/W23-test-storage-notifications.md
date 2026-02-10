# W23: Tests for Storage + Notifications Changes

## Files to create/modify
- `backend/tests/unit/test_storage_service.py` — NEW or update
- `backend/tests/unit/test_notification_email.py` — NEW

## Task

### 1. Storage service tests

Read `backend/app/modules/storage/service.py` and write tests for:
- File upload initiation (presigned URL generation)
- Upload completion handler
- trigger_processing (if implemented by W11)
- File listing and deletion
- Access control (org_id checks)

```python
class TestStorageTriggerProcessing:
    @pytest.mark.asyncio
    async def test_updates_status_to_processing(self):
        """trigger_processing should set status to 'processing' then 'completed'."""
        ...

    @pytest.mark.asyncio
    async def test_asset_not_found_raises_404(self):
        """trigger_processing for non-existent asset should raise 404."""
        ...
```

### 2. Notification email channel tests

Read the notifications module and write tests for email dispatch:

```python
class TestEmailChannel:
    def test_send_email_returns_false_when_not_configured(self):
        """If SMTP_HOST is None, send_email should log warning and return False."""
        ...

    @patch('smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        """With valid SMTP config, send_email should send and return True."""
        ...

    @patch('smtplib.SMTP')
    def test_send_email_handles_smtp_error(self, mock_smtp):
        """SMTP errors should be caught and return False."""
        mock_smtp.side_effect = Exception("Connection refused")
        ...
```

Write at least 8 tests total (4 storage + 4 notifications).
