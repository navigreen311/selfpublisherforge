#!/bin/bash
# Quick load testing script for SelfPublisherForge
# Usage: ./run-load-test.sh [profile] [mode]
#   profile: smoke, normal, stress, spike, soak (default: smoke)
#   mode: web, headless (default: web)

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
PROFILE=${1:-smoke}
MODE=${2:-web}
BACKEND_URL=${BACKEND_URL:-http://localhost:8000}
TEST_USER_EMAIL=${LOAD_TEST_USER_EMAIL:-loadtest@example.com}
TEST_USER_PASSWORD=${LOAD_TEST_USER_PASSWORD:-LoadTest123!}

# Load profile configurations
declare -A USERS=(
    [smoke]=5
    [normal]=50
    [stress]=200
    [spike]=500
    [soak]=100
)

declare -A SPAWN_RATES=(
    [smoke]=1
    [normal]=5
    [stress]=20
    [spike]=100
    [soak]=10
)

declare -A DURATIONS=(
    [smoke]=1m
    [normal]=5m
    [stress]=10m
    [spike]=2m
    [soak]=30m
)

# Validate profile
if [[ ! ${USERS[$PROFILE]} ]]; then
    echo -e "${RED}Error: Invalid profile '$PROFILE'${NC}"
    echo "Valid profiles: smoke, normal, stress, spike, soak"
    exit 1
fi

# Validate mode
if [[ "$MODE" != "web" && "$MODE" != "headless" ]]; then
    echo -e "${RED}Error: Invalid mode '$MODE'${NC}"
    echo "Valid modes: web, headless"
    exit 1
fi

echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  SelfPublisherForge Load Testing${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Profile:${NC}      $PROFILE"
echo -e "${GREEN}Mode:${NC}         $MODE"
echo -e "${GREEN}Backend URL:${NC}  $BACKEND_URL"
echo -e "${GREEN}Users:${NC}        ${USERS[$PROFILE]}"
echo -e "${GREEN}Spawn Rate:${NC}   ${SPAWN_RATES[$PROFILE]}/sec"
echo -e "${GREEN}Duration:${NC}     ${DURATIONS[$PROFILE]}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""

# Test backend connectivity
echo -e "${YELLOW}Checking backend connectivity...${NC}"
if curl -s -f -o /dev/null "$BACKEND_URL/health"; then
    echo -e "${GREEN}✓ Backend is reachable${NC}"
else
    echo -e "${RED}✗ Backend is not reachable at $BACKEND_URL${NC}"
    echo "Please ensure the backend is running."
    exit 1
fi

# Test authentication
echo -e "${YELLOW}Verifying test user authentication...${NC}"
AUTH_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_USER_EMAIL\",\"password\":\"$TEST_USER_PASSWORD\"}")

if echo "$AUTH_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✓ Test user authenticated successfully${NC}"
elif echo "$AUTH_RESPONSE" | grep -q "mfa_required"; then
    echo -e "${RED}✗ MFA is enabled for test user${NC}"
    echo "Please disable MFA for the load testing user."
    exit 1
else
    echo -e "${RED}✗ Authentication failed${NC}"
    echo "Response: $AUTH_RESPONSE"
    echo "Please verify test user credentials."
    exit 1
fi

echo ""

# Export environment variables
export LOAD_PROFILE=$PROFILE
export BACKEND_URL=$BACKEND_URL
export LOAD_TEST_USER_EMAIL=$TEST_USER_EMAIL
export LOAD_TEST_USER_PASSWORD=$TEST_USER_PASSWORD

# Run load test
if [[ "$MODE" == "web" ]]; then
    echo -e "${GREEN}Starting load test with web UI...${NC}"
    echo -e "${BLUE}Web UI will be available at: http://localhost:8089${NC}"
    echo ""

    locust -f locustfile.py --host="$BACKEND_URL"

elif [[ "$MODE" == "headless" ]]; then
    # Create reports directory
    mkdir -p reports

    TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    REPORT_FILE="reports/${PROFILE}-${TIMESTAMP}.html"

    echo -e "${GREEN}Starting headless load test...${NC}"
    echo -e "${BLUE}Report will be saved to: $REPORT_FILE${NC}"
    echo ""

    locust -f locustfile.py \
        --host="$BACKEND_URL" \
        --headless \
        --users "${USERS[$PROFILE]}" \
        --spawn-rate "${SPAWN_RATES[$PROFILE]}" \
        --run-time "${DURATIONS[$PROFILE]}" \
        --html "$REPORT_FILE" \
        --csv "reports/${PROFILE}-${TIMESTAMP}"

    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Load test completed!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}HTML Report:${NC} $REPORT_FILE"
    echo -e "${BLUE}CSV Stats:${NC}   reports/${PROFILE}-${TIMESTAMP}_stats.csv"
    echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
fi
