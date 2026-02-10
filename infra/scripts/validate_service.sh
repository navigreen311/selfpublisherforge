#!/bin/bash
# =============================================================================
# validate_service.sh — CodeDeploy ValidateService hook
# =============================================================================
# Validates that the backend (port 8000) and frontend (port 3000) are
# responding correctly after deployment.
# =============================================================================

set -euo pipefail

LOG_TAG="[CodeDeploy:ValidateService]"

echo "${LOG_TAG} Starting ValidateService hook..."

VALIDATION_PASSED=true

# ---------------------------------------------------------------------------
# 1. Validate backend health endpoint (port 8000)
# ---------------------------------------------------------------------------
echo "${LOG_TAG} Checking backend health endpoint on port 8000..."

BACKEND_MAX_RETRIES=10
BACKEND_RETRY_INTERVAL=5
BACKEND_HEALTHY=false

for i in $(seq 1 "${BACKEND_MAX_RETRIES}"); do
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 http://localhost:8000/health 2>/dev/null || echo "000")
    if [ "${HTTP_STATUS}" = "200" ]; then
        BACKEND_HEALTHY=true
        echo "${LOG_TAG} Backend health check PASSED (HTTP ${HTTP_STATUS}) on attempt ${i}."
        break
    fi
    echo "${LOG_TAG} Backend health check attempt ${i}/${BACKEND_MAX_RETRIES}: HTTP ${HTTP_STATUS}"
    sleep "${BACKEND_RETRY_INTERVAL}"
done

if [ "${BACKEND_HEALTHY}" = "false" ]; then
    echo "${LOG_TAG} ERROR: Backend health check FAILED after ${BACKEND_MAX_RETRIES} attempts."
    VALIDATION_PASSED=false
fi

# ---------------------------------------------------------------------------
# 2. Validate backend API response
# ---------------------------------------------------------------------------
echo "${LOG_TAG} Checking backend API response body..."

HEALTH_RESPONSE=$(curl -s --max-time 10 http://localhost:8000/health 2>/dev/null || echo "")
if [ -n "${HEALTH_RESPONSE}" ]; then
    echo "${LOG_TAG} Backend health response: ${HEALTH_RESPONSE}"
else
    echo "${LOG_TAG} WARNING: Backend returned empty health response."
fi

# ---------------------------------------------------------------------------
# 3. Validate frontend responds on port 3000
# ---------------------------------------------------------------------------
echo "${LOG_TAG} Checking frontend on port 3000..."

FRONTEND_MAX_RETRIES=10
FRONTEND_RETRY_INTERVAL=5
FRONTEND_HEALTHY=false

for i in $(seq 1 "${FRONTEND_MAX_RETRIES}"); do
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 http://localhost:3000/ 2>/dev/null || echo "000")
    if [ "${HTTP_STATUS}" = "200" ] || [ "${HTTP_STATUS}" = "304" ]; then
        FRONTEND_HEALTHY=true
        echo "${LOG_TAG} Frontend health check PASSED (HTTP ${HTTP_STATUS}) on attempt ${i}."
        break
    fi
    echo "${LOG_TAG} Frontend health check attempt ${i}/${FRONTEND_MAX_RETRIES}: HTTP ${HTTP_STATUS}"
    sleep "${FRONTEND_RETRY_INTERVAL}"
done

if [ "${FRONTEND_HEALTHY}" = "false" ]; then
    echo "${LOG_TAG} ERROR: Frontend health check FAILED after ${FRONTEND_MAX_RETRIES} attempts."
    VALIDATION_PASSED=false
fi

# ---------------------------------------------------------------------------
# 4. Validate supporting services
# ---------------------------------------------------------------------------
echo "${LOG_TAG} Checking supporting services..."

# Check PostgreSQL
PG_STATUS=$(docker exec $(docker ps -q --filter "name=postgres" | head -1) pg_isready -U postgres 2>/dev/null && echo "healthy" || echo "unhealthy")
echo "${LOG_TAG} PostgreSQL: ${PG_STATUS}"
if [ "${PG_STATUS}" != "healthy" ]; then
    echo "${LOG_TAG} WARNING: PostgreSQL is not healthy."
fi

# Check Redis
REDIS_STATUS=$(docker exec $(docker ps -q --filter "name=redis" | head -1) redis-cli ping 2>/dev/null || echo "unhealthy")
echo "${LOG_TAG} Redis: ${REDIS_STATUS}"
if [ "${REDIS_STATUS}" != "PONG" ]; then
    echo "${LOG_TAG} WARNING: Redis is not responding to PING."
fi

# ---------------------------------------------------------------------------
# 5. Check Docker container status
# ---------------------------------------------------------------------------
echo "${LOG_TAG} Docker container status:"
docker ps --filter "name=selfpublisherforge" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || true

# ---------------------------------------------------------------------------
# 6. Final validation result
# ---------------------------------------------------------------------------
if [ "${VALIDATION_PASSED}" = "true" ]; then
    echo "${LOG_TAG} =========================================="
    echo "${LOG_TAG} All validation checks PASSED."
    echo "${LOG_TAG} =========================================="
    exit 0
else
    echo "${LOG_TAG} =========================================="
    echo "${LOG_TAG} Validation FAILED. Deployment will be rolled back."
    echo "${LOG_TAG} =========================================="
    exit 1
fi
