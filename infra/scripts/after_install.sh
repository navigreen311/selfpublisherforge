#!/bin/bash
# =============================================================================
# after_install.sh — CodeDeploy AfterInstall hook
# =============================================================================
# Copies environment files, runs database migrations, and builds/pulls
# Docker images required by the application.
# =============================================================================

set -euo pipefail

LOG_TAG="[CodeDeploy:AfterInstall]"
APP_DIR="/opt/selfpublisherforge"
COMPOSE_FILE="${APP_DIR}/infra/docker/docker-compose.prod.yml"

echo "${LOG_TAG} Starting AfterInstall hook..."

cd "${APP_DIR}"

# ---------------------------------------------------------------------------
# 1. Copy environment files from SSM Parameter Store / Secrets Manager
# ---------------------------------------------------------------------------
echo "${LOG_TAG} Setting up environment files..."

# Fetch environment from instance tag or default to production
ENVIRONMENT="${DEPLOYMENT_GROUP_NAME:-production}"
if echo "${ENVIRONMENT}" | grep -qi "staging"; then
    ENVIRONMENT="staging"
else
    ENVIRONMENT="production"
fi

echo "${LOG_TAG} Detected environment: ${ENVIRONMENT}"

# Backend .env file
if command -v aws &> /dev/null; then
    echo "${LOG_TAG} Fetching backend environment variables from SSM..."

    # Build backend .env from SSM parameters
    {
        echo "ENVIRONMENT=${ENVIRONMENT}"
        echo "DEBUG=false"
        echo "PORT=8000"

        # Fetch secrets from SSM Parameter Store
        DATABASE_URL=$(aws ssm get-parameter \
            --name "/selfpublisherforge/${ENVIRONMENT}/database-url" \
            --with-decryption --query 'Parameter.Value' --output text 2>/dev/null) && \
            echo "DATABASE_URL=${DATABASE_URL}" || \
            echo "${LOG_TAG} WARNING: Could not fetch DATABASE_URL from SSM"

        SECRET_KEY=$(aws ssm get-parameter \
            --name "/selfpublisherforge/${ENVIRONMENT}/secret-key" \
            --with-decryption --query 'Parameter.Value' --output text 2>/dev/null) && \
            echo "SECRET_KEY=${SECRET_KEY}" || \
            echo "${LOG_TAG} WARNING: Could not fetch SECRET_KEY from SSM"

        REDIS_URL=$(aws ssm get-parameter \
            --name "/selfpublisherforge/${ENVIRONMENT}/redis-url" \
            --query 'Parameter.Value' --output text 2>/dev/null) && \
            echo "REDIS_URL=${REDIS_URL}" || \
            echo "REDIS_URL=redis://redis:6379/0"

        echo "CELERY_BROKER_URL=redis://redis:6379/1"
        echo "CELERY_RESULT_BACKEND=redis://redis:6379/2"
        echo "ELASTICSEARCH_URL=http://elasticsearch:9200"
    } > "${APP_DIR}/backend/.env"

    echo "${LOG_TAG} Backend .env file created."

    # Frontend .env.local file
    {
        echo "NODE_ENV=production"
        NEXT_PUBLIC_API_URL=$(aws ssm get-parameter \
            --name "/selfpublisherforge/${ENVIRONMENT}/api-url" \
            --query 'Parameter.Value' --output text 2>/dev/null) && \
            echo "NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}" || \
            echo "NEXT_PUBLIC_API_URL=http://backend:8000"
    } > "${APP_DIR}/frontend/.env.local"

    echo "${LOG_TAG} Frontend .env.local file created."
else
    echo "${LOG_TAG} WARNING: AWS CLI not available. Using existing environment files."
fi

# ---------------------------------------------------------------------------
# 2. Build / pull Docker images
# ---------------------------------------------------------------------------
echo "${LOG_TAG} Building Docker images..."

if [ -f "${COMPOSE_FILE}" ]; then
    # Use the production compose file with correct context paths
    docker compose -f "${COMPOSE_FILE}" build --no-cache backend frontend
    echo "${LOG_TAG} Docker images built successfully."
else
    echo "${LOG_TAG} Production compose file not found at ${COMPOSE_FILE}."
    echo "${LOG_TAG} Attempting to build from root docker-compose.yml..."
    if [ -f "${APP_DIR}/docker-compose.yml" ]; then
        docker compose -f "${APP_DIR}/docker-compose.yml" build --no-cache backend frontend
        echo "${LOG_TAG} Docker images built successfully."
    else
        echo "${LOG_TAG} ERROR: No docker-compose file found."
        exit 1
    fi
fi

# ---------------------------------------------------------------------------
# 3. Run database migrations
# ---------------------------------------------------------------------------
echo "${LOG_TAG} Running database migrations..."

if [ -f "${COMPOSE_FILE}" ]; then
    COMPOSE_CMD="docker compose -f ${COMPOSE_FILE}"
else
    COMPOSE_CMD="docker compose -f ${APP_DIR}/docker-compose.yml"
fi

# Start only the database service for migrations
${COMPOSE_CMD} up -d postgres

# Wait for PostgreSQL to be healthy
echo "${LOG_TAG} Waiting for PostgreSQL to be ready..."
RETRIES=30
until ${COMPOSE_CMD} exec -T postgres pg_isready -U postgres -d selfpublisherforge 2>/dev/null; do
    RETRIES=$((RETRIES - 1))
    if [ "${RETRIES}" -le 0 ]; then
        echo "${LOG_TAG} ERROR: PostgreSQL did not become ready in time."
        exit 1
    fi
    echo "${LOG_TAG} Waiting for PostgreSQL... (${RETRIES} retries remaining)"
    sleep 2
done

echo "${LOG_TAG} PostgreSQL is ready. Running Alembic migrations..."
${COMPOSE_CMD} run --rm --no-deps backend alembic upgrade head || {
    echo "${LOG_TAG} WARNING: Alembic migration failed or alembic not configured. Continuing..."
}

echo "${LOG_TAG} AfterInstall hook completed successfully."
exit 0
