#!/bin/bash
# =============================================================================
# before_install.sh — CodeDeploy BeforeInstall hook
# =============================================================================
# Installs/updates Docker and Docker Compose, pulls latest images, and
# creates the application directory if it does not already exist.
# =============================================================================

set -euo pipefail

LOG_TAG="[CodeDeploy:BeforeInstall]"
APP_DIR="/opt/selfpublisherforge"

echo "${LOG_TAG} Starting BeforeInstall hook..."

# ---------------------------------------------------------------------------
# 1. Install / update Docker
# ---------------------------------------------------------------------------
if ! command -v docker &> /dev/null; then
    echo "${LOG_TAG} Docker not found. Installing Docker..."
    yum update -y || apt-get update -y
    if command -v yum &> /dev/null; then
        yum install -y docker
        systemctl enable docker
    else
        apt-get install -y docker.io
        systemctl enable docker
    fi
    systemctl start docker
    echo "${LOG_TAG} Docker installed successfully."
else
    echo "${LOG_TAG} Docker is already installed: $(docker --version)"
fi

# Ensure Docker daemon is running
if ! systemctl is-active --quiet docker; then
    echo "${LOG_TAG} Starting Docker daemon..."
    systemctl start docker
fi

# ---------------------------------------------------------------------------
# 2. Install / update Docker Compose
# ---------------------------------------------------------------------------
COMPOSE_VERSION="2.27.0"

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "${LOG_TAG} Docker Compose not found. Installing Docker Compose v${COMPOSE_VERSION}..."
    ARCH=$(uname -m)
    if [ "${ARCH}" = "x86_64" ]; then
        ARCH="x86_64"
    elif [ "${ARCH}" = "aarch64" ]; then
        ARCH="aarch64"
    fi
    curl -SL "https://github.com/docker/compose/releases/download/v${COMPOSE_VERSION}/docker-compose-linux-${ARCH}" \
        -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    echo "${LOG_TAG} Docker Compose installed successfully."
else
    echo "${LOG_TAG} Docker Compose is already installed."
fi

# ---------------------------------------------------------------------------
# 3. Create application directory if needed
# ---------------------------------------------------------------------------
if [ ! -d "${APP_DIR}" ]; then
    echo "${LOG_TAG} Creating application directory: ${APP_DIR}"
    mkdir -p "${APP_DIR}"
fi

# ---------------------------------------------------------------------------
# 4. Clean up old deployment artifacts
# ---------------------------------------------------------------------------
echo "${LOG_TAG} Cleaning up previous deployment artifacts..."
if [ -d "${APP_DIR}/backend" ] || [ -d "${APP_DIR}/frontend" ]; then
    # Preserve docker volumes and env files, but remove stale code
    find "${APP_DIR}" -maxdepth 1 \
        -not -name "." \
        -not -name ".env" \
        -not -name ".env.*" \
        -not -name "docker-compose*.yml" \
        -type f -delete 2>/dev/null || true
fi

# ---------------------------------------------------------------------------
# 5. Pull latest base images to speed up builds
# ---------------------------------------------------------------------------
echo "${LOG_TAG} Pulling latest base images..."
docker pull postgres:16-alpine || true
docker pull redis:7-alpine || true
docker pull elasticsearch:8.15.0 || true

# ---------------------------------------------------------------------------
# 6. Prune dangling images to free disk space
# ---------------------------------------------------------------------------
echo "${LOG_TAG} Pruning dangling Docker images..."
docker image prune -f || true

echo "${LOG_TAG} BeforeInstall hook completed successfully."
exit 0
