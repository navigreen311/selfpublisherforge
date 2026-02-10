#!/bin/bash
# =============================================================================
# start_server.sh — CodeDeploy ApplicationStart hook
# =============================================================================
# Starts all services with docker-compose and waits for health checks to pass.
# =============================================================================

set -euo pipefail

LOG_TAG="[CodeDeploy:ApplicationStart]"
APP_DIR="/opt/selfpublisherforge"
COMPOSE_FILE="${APP_DIR}/infra/docker/docker-compose.prod.yml"

echo "${LOG_TAG} Starting ApplicationStart hook..."

cd "${APP_DIR}"

# ---------------------------------------------------------------------------
# 1. Determine the compose file to use
# ---------------------------------------------------------------------------
if [ -f "${COMPOSE_FILE}" ]; then
    COMPOSE_CMD="docker compose -f ${COMPOSE_FILE}"
    echo "${LOG_TAG} Using production compose file: ${COMPOSE_FILE}"
else
    COMPOSE_FILE="${APP_DIR}/docker-compose.yml"
    COMPOSE_CMD="docker compose -f ${COMPOSE_FILE}"
    echo "${LOG_TAG} Using root compose file: ${COMPOSE_FILE}"
fi

# ---------------------------------------------------------------------------
# 2. Start all services
# ---------------------------------------------------------------------------
echo "${LOG_TAG} Starting all services..."
${COMPOSE_CMD} up -d

echo "${LOG_TAG} Containers started. Current status:"
${COMPOSE_CMD} ps

# ---------------------------------------------------------------------------
# 3. Wait for backend health check (port 8000)
# ---------------------------------------------------------------------------
echo "${LOG_TAG} Waiting for backend to become healthy..."

BACKEND_MAX_RETRIES=30
BACKEND_RETRY_INTERVAL=5
BACKEND_HEALTHY=false

for i in $(seq 1 "${BACKEND_MAX_RETRIES}"); do
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8000/health 2>/dev/null || echo "000")
    if [ "${HTTP_STATUS}" = "200" ]; then
        BACKEND_HEALTHY=true
        echo "${LOG_TAG} Backend is healthy (attempt ${i}/${BACKEND_MAX_RETRIES})."
        break
    fi
    echo "${LOG_TAG} Backend not ready yet (HTTP ${HTTP_STATUS}). Retrying in ${BACKEND_RETRY_INTERVAL}s... (${i}/${BACKEND_MAX_RETRIES})"
    sleep "${BACKEND_RETRY_INTERVAL}"
done

if [ "${BACKEND_HEALTHY}" = "false" ]; then
    echo "${LOG_TAG} ERROR: Backend failed to become healthy after ${BACKEND_MAX_RETRIES} attempts."
    echo "${LOG_TAG} Backend container logs:"
    ${COMPOSE_CMD} logs --tail=50 backend
    exit 1
fi

# ---------------------------------------------------------------------------
# 4. Wait for frontend health check (port 3000)
# ---------------------------------------------------------------------------
echo "${LOG_TAG} Waiting for frontend to become healthy..."

FRONTEND_MAX_RETRIES=30
FRONTEND_RETRY_INTERVAL=5
FRONTEND_HEALTHY=false

for i in $(seq 1 "${FRONTEND_MAX_RETRIES}"); do
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:3000/ 2>/dev/null || echo "000")
    if [ "${HTTP_STATUS}" = "200" ] || [ "${HTTP_STATUS}" = "304" ]; then
        FRONTEND_HEALTHY=true
        echo "${LOG_TAG} Frontend is healthy (attempt ${i}/${FRONTEND_MAX_RETRIES})."
        break
    fi
    echo "${LOG_TAG} Frontend not ready yet (HTTP ${HTTP_STATUS}). Retrying in ${FRONTEND_RETRY_INTERVAL}s... (${i}/${FRONTEND_MAX_RETRIES})"
    sleep "${FRONTEND_RETRY_INTERVAL}"
done

if [ "${FRONTEND_HEALTHY}" = "false" ]; then
    echo "${LOG_TAG} ERROR: Frontend failed to become healthy after ${FRONTEND_MAX_RETRIES} attempts."
    echo "${LOG_TAG} Frontend container logs:"
    ${COMPOSE_CMD} logs --tail=50 frontend
    exit 1
fi

# ---------------------------------------------------------------------------
# 5. Final status
# ---------------------------------------------------------------------------
echo "${LOG_TAG} All services are up and healthy."
${COMPOSE_CMD} ps
echo "${LOG_TAG} ApplicationStart hook completed successfully."
exit 0
