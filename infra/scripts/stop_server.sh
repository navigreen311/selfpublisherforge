#!/bin/bash
# =============================================================================
# stop_server.sh — CodeDeploy ApplicationStop hook
# =============================================================================
# Gracefully stops all running containers via docker-compose down.
# =============================================================================

set -euo pipefail

LOG_TAG="[CodeDeploy:ApplicationStop]"
APP_DIR="/opt/selfpublisherforge"
COMPOSE_FILE="${APP_DIR}/infra/docker/docker-compose.prod.yml"

echo "${LOG_TAG} Starting ApplicationStop hook..."

# ---------------------------------------------------------------------------
# 1. Check if the application directory exists (first deploy scenario)
# ---------------------------------------------------------------------------
if [ ! -d "${APP_DIR}" ]; then
    echo "${LOG_TAG} Application directory does not exist. Nothing to stop (first deployment)."
    exit 0
fi

cd "${APP_DIR}"

# ---------------------------------------------------------------------------
# 2. Determine the compose file to use
# ---------------------------------------------------------------------------
if [ -f "${COMPOSE_FILE}" ]; then
    COMPOSE_CMD="docker compose -f ${COMPOSE_FILE}"
    echo "${LOG_TAG} Using production compose file: ${COMPOSE_FILE}"
elif [ -f "${APP_DIR}/docker-compose.yml" ]; then
    COMPOSE_CMD="docker compose -f ${APP_DIR}/docker-compose.yml"
    echo "${LOG_TAG} Using root compose file: ${APP_DIR}/docker-compose.yml"
else
    echo "${LOG_TAG} No docker-compose file found. Attempting to stop containers directly..."
    # Fallback: stop any containers with the project name
    docker ps -q --filter "name=selfpublisherforge" | xargs -r docker stop --time 30 || true
    docker ps -aq --filter "name=selfpublisherforge" | xargs -r docker rm -f || true
    echo "${LOG_TAG} ApplicationStop hook completed (fallback)."
    exit 0
fi

# ---------------------------------------------------------------------------
# 3. Show current running containers
# ---------------------------------------------------------------------------
echo "${LOG_TAG} Current running containers:"
${COMPOSE_CMD} ps || true

# ---------------------------------------------------------------------------
# 4. Gracefully stop all services
# ---------------------------------------------------------------------------
echo "${LOG_TAG} Gracefully stopping all services (30s timeout)..."
${COMPOSE_CMD} down --timeout 30 || {
    echo "${LOG_TAG} WARNING: Graceful shutdown failed. Force-stopping containers..."
    ${COMPOSE_CMD} kill || true
    ${COMPOSE_CMD} down --remove-orphans || true
}

# ---------------------------------------------------------------------------
# 5. Verify all containers are stopped
# ---------------------------------------------------------------------------
REMAINING=$(docker ps -q --filter "name=selfpublisherforge" 2>/dev/null | wc -l)
if [ "${REMAINING}" -gt 0 ]; then
    echo "${LOG_TAG} WARNING: ${REMAINING} containers still running. Force-stopping..."
    docker ps -q --filter "name=selfpublisherforge" | xargs -r docker stop --time 10 || true
    docker ps -aq --filter "name=selfpublisherforge" | xargs -r docker rm -f || true
fi

echo "${LOG_TAG} All containers stopped."
echo "${LOG_TAG} ApplicationStop hook completed successfully."
exit 0
