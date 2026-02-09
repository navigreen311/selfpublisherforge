#!/usr/bin/env bash
# =============================================================================
# deploy.sh — Deployment script with rollback capability
# =============================================================================
# Usage:
#   ./deploy.sh <environment> <version>
#   ./deploy.sh staging v1.2.3
#   ./deploy.sh production v1.2.3
#   ./deploy.sh rollback <environment>
#
# Environment variables required:
#   AWS_REGION           — AWS region (default: us-east-1)
#   AWS_ACCOUNT_ID       — AWS account ID
#   SLACK_WEBHOOK_URL    — Slack webhook for notifications (optional)
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROJECT_NAME="selfpublisherforge"
AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------
log_info()  { echo -e "${BLUE}[INFO]${NC}  $(date '+%Y-%m-%d %H:%M:%S') $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $(date '+%Y-%m-%d %H:%M:%S') $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $(date '+%Y-%m-%d %H:%M:%S') $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') $*"; }

notify_slack() {
    local message="$1"
    local color="${2:-good}"
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        curl -s -X POST "$SLACK_WEBHOOK_URL" \
            -H 'Content-type: application/json' \
            -d "{\"attachments\":[{\"color\":\"${color}\",\"text\":\"${message}\"}]}" \
            > /dev/null 2>&1 || true
    fi
}

check_prerequisites() {
    local missing=()
    for cmd in aws docker jq curl; do
        if ! command -v "$cmd" &> /dev/null; then
            missing+=("$cmd")
        fi
    done
    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing[*]}"
        exit 1
    fi
}

get_current_task_def() {
    local service_name="$1"
    local cluster="$2"
    aws ecs describe-services \
        --cluster "$cluster" \
        --services "$service_name" \
        --query 'services[0].taskDefinition' \
        --output text \
        --region "$AWS_REGION"
}

wait_for_service_stable() {
    local cluster="$1"
    local service="$2"
    local timeout="${3:-600}"

    log_info "Waiting for ${service} to stabilize (timeout: ${timeout}s)..."
    if aws ecs wait services-stable \
        --cluster "$cluster" \
        --services "$service" \
        --region "$AWS_REGION" 2>/dev/null; then
        log_ok "${service} is stable"
        return 0
    else
        log_error "${service} failed to stabilize within timeout"
        return 1
    fi
}

health_check() {
    local url="$1"
    local max_retries="${2:-10}"
    local retry_interval="${3:-10}"

    log_info "Running health check against ${url}..."
    for i in $(seq 1 "$max_retries"); do
        HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" 2>/dev/null || echo "000")
        if [[ "$HTTP_STATUS" == "200" ]]; then
            log_ok "Health check passed (attempt ${i}/${max_retries})"
            return 0
        fi
        log_warn "Health check attempt ${i}/${max_retries}: HTTP ${HTTP_STATUS}"
        sleep "$retry_interval"
    done
    log_error "Health check failed after ${max_retries} attempts"
    return 1
}

# ---------------------------------------------------------------------------
# Deploy Function
# ---------------------------------------------------------------------------
deploy() {
    local environment="$1"
    local version="$2"
    local cluster="${PROJECT_NAME}-${environment}"
    local image_tag="${version}"

    log_info "=========================================="
    log_info "Deploying ${PROJECT_NAME} ${version} to ${environment}"
    log_info "=========================================="

    # Save current task definitions for rollback
    log_info "Saving current task definitions for rollback..."
    local api_prev_task frontend_prev_task
    api_prev_task=$(get_current_task_def "${PROJECT_NAME}-api-${environment}" "$cluster")
    frontend_prev_task=$(get_current_task_def "${PROJECT_NAME}-frontend-${environment}" "$cluster")
    log_info "Previous API task: ${api_prev_task}"
    log_info "Previous Frontend task: ${frontend_prev_task}"

    # Store rollback info
    echo "${api_prev_task}" > "/tmp/${PROJECT_NAME}-${environment}-api-rollback.txt"
    echo "${frontend_prev_task}" > "/tmp/${PROJECT_NAME}-${environment}-frontend-rollback.txt"

    # Login to ECR
    log_info "Logging in to ECR..."
    aws ecr get-login-password --region "$AWS_REGION" | \
        docker login --username AWS --password-stdin "$ECR_REGISTRY"

    # Build and push images
    log_info "Building and pushing API image..."
    docker build -t "${ECR_REGISTRY}/${PROJECT_NAME}-api:${image_tag}" \
        -t "${ECR_REGISTRY}/${PROJECT_NAME}-api:${environment}-latest" \
        ./backend
    docker push "${ECR_REGISTRY}/${PROJECT_NAME}-api:${image_tag}"
    docker push "${ECR_REGISTRY}/${PROJECT_NAME}-api:${environment}-latest"

    log_info "Building and pushing Frontend image..."
    docker build -t "${ECR_REGISTRY}/${PROJECT_NAME}-frontend:${image_tag}" \
        -t "${ECR_REGISTRY}/${PROJECT_NAME}-frontend:${environment}-latest" \
        ./frontend
    docker push "${ECR_REGISTRY}/${PROJECT_NAME}-frontend:${image_tag}"
    docker push "${ECR_REGISTRY}/${PROJECT_NAME}-frontend:${environment}-latest"

    # Update ECS services
    log_info "Updating ECS services..."
    local services=("api" "frontend" "worker" "beat")
    for svc in "${services[@]}"; do
        log_info "Forcing new deployment for ${svc}..."
        aws ecs update-service \
            --cluster "$cluster" \
            --service "${PROJECT_NAME}-${svc}-${environment}" \
            --force-new-deployment \
            --region "$AWS_REGION" \
            > /dev/null
    done

    # Wait for stability
    local deploy_failed=false
    for svc in "${services[@]}"; do
        if ! wait_for_service_stable "$cluster" "${PROJECT_NAME}-${svc}-${environment}" 600; then
            deploy_failed=true
            break
        fi
    done

    if [[ "$deploy_failed" == "true" ]]; then
        log_error "Deployment failed! Initiating rollback..."
        notify_slack "FAILED: ${PROJECT_NAME} ${version} deployment to ${environment} failed. Initiating rollback." "danger"
        rollback "$environment"
        exit 1
    fi

    # Health check
    if [[ -n "${HEALTH_CHECK_URL:-}" ]]; then
        if ! health_check "$HEALTH_CHECK_URL"; then
            log_error "Post-deploy health check failed! Initiating rollback..."
            notify_slack "FAILED: ${PROJECT_NAME} ${version} health check failed on ${environment}. Rolling back." "danger"
            rollback "$environment"
            exit 1
        fi
    fi

    log_ok "=========================================="
    log_ok "Deployment of ${version} to ${environment} SUCCESSFUL"
    log_ok "=========================================="
    notify_slack "SUCCESS: ${PROJECT_NAME} ${version} deployed to ${environment}" "good"
}

# ---------------------------------------------------------------------------
# Rollback Function
# ---------------------------------------------------------------------------
rollback() {
    local environment="$1"
    local cluster="${PROJECT_NAME}-${environment}"

    log_warn "=========================================="
    log_warn "Rolling back ${PROJECT_NAME} on ${environment}"
    log_warn "=========================================="

    # Read saved rollback task definitions
    local api_rollback_file="/tmp/${PROJECT_NAME}-${environment}-api-rollback.txt"
    local frontend_rollback_file="/tmp/${PROJECT_NAME}-${environment}-frontend-rollback.txt"

    if [[ -f "$api_rollback_file" ]] && [[ -f "$frontend_rollback_file" ]]; then
        local api_prev_task frontend_prev_task
        api_prev_task=$(cat "$api_rollback_file")
        frontend_prev_task=$(cat "$frontend_rollback_file")

        log_info "Rolling API back to: ${api_prev_task}"
        aws ecs update-service \
            --cluster "$cluster" \
            --service "${PROJECT_NAME}-api-${environment}" \
            --task-definition "$api_prev_task" \
            --force-new-deployment \
            --region "$AWS_REGION" > /dev/null

        log_info "Rolling Frontend back to: ${frontend_prev_task}"
        aws ecs update-service \
            --cluster "$cluster" \
            --service "${PROJECT_NAME}-frontend-${environment}" \
            --task-definition "$frontend_prev_task" \
            --force-new-deployment \
            --region "$AWS_REGION" > /dev/null

        log_info "Rolling Worker and Beat back..."
        aws ecs update-service \
            --cluster "$cluster" \
            --service "${PROJECT_NAME}-worker-${environment}" \
            --force-new-deployment \
            --region "$AWS_REGION" > /dev/null
        aws ecs update-service \
            --cluster "$cluster" \
            --service "${PROJECT_NAME}-beat-${environment}" \
            --force-new-deployment \
            --region "$AWS_REGION" > /dev/null

        # Wait for rollback stability
        wait_for_service_stable "$cluster" "${PROJECT_NAME}-api-${environment}" 600
        wait_for_service_stable "$cluster" "${PROJECT_NAME}-frontend-${environment}" 600

        log_ok "Rollback complete"
        notify_slack "ROLLBACK: ${PROJECT_NAME} rolled back on ${environment}" "warning"
    else
        log_error "No rollback task definitions found. Manual intervention required."
        log_error "Check ECS console for previous task definitions."
        exit 1
    fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    check_prerequisites

    local command="${1:-}"
    local arg2="${2:-}"
    local arg3="${3:-}"

    case "$command" in
        staging|production)
            if [[ -z "$arg2" ]]; then
                log_error "Usage: $0 <environment> <version>"
                log_error "Example: $0 staging v1.2.3"
                exit 1
            fi
            deploy "$command" "$arg2"
            ;;
        rollback)
            if [[ -z "$arg2" ]]; then
                log_error "Usage: $0 rollback <environment>"
                exit 1
            fi
            rollback "$arg2"
            ;;
        *)
            echo "Usage:"
            echo "  $0 <staging|production> <version>  — Deploy a version"
            echo "  $0 rollback <staging|production>    — Rollback to previous version"
            echo ""
            echo "Examples:"
            echo "  $0 staging v1.2.3"
            echo "  $0 production v1.2.3"
            echo "  $0 rollback staging"
            exit 1
            ;;
    esac
}

main "$@"
