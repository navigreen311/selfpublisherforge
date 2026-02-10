# W04: Fix Silent Exception Swallowing in Agent System

## Branch: `fix/w04-agent-system-exceptions`

## Files YOU Own (only modify these):
- `backend/app/modules/agent_system/governance.py`
- `backend/app/modules/agent_system/audit.py`
- `backend/app/modules/agent_system/service.py`

## Task

Three files in the agent_system module have dangerous `except Exception: pass` blocks that silently swallow errors.

### Fix 1: governance.py (line ~93) — SECURITY CRITICAL
This is a permission check. Silent failure means permissions could be bypassed.

```python
# BEFORE (bad):
except Exception:
    pass

# AFTER (good):
except Exception:
    logger.exception("Permission check failed for action — denying by default")
    return False  # Fail closed: deny permission on error
```

Make sure `logger` is defined at the top: `logger = logging.getLogger(__name__)`. Add `import logging` if missing.

**IMPORTANT**: The fix must fail closed (return False / deny) on exception, not fail open.

### Fix 2: audit.py (line ~95)
Audit logging should not silently fail — it's important for compliance.

```python
# BEFORE (bad):
except Exception:
    pass

# AFTER (good):
except Exception:
    logger.exception("Failed to write audit log entry")
```

### Fix 3: service.py (lines ~258, ~481)
Two `except ValueError: pass` blocks for status parsing.

```python
# BEFORE:
except ValueError:
    pass

# AFTER:
except ValueError:
    logger.warning("Invalid status value encountered: %s", <the_value_variable>)
```

Find the actual variable being parsed in each location and include it in the warning message.

## Verification
```bash
cd backend && python -c "from app.modules.agent_system import governance, audit, service; print('imports OK')"
cd backend && grep -rn "except.*pass" app/modules/agent_system/ || echo "No silent exceptions remaining"
```
