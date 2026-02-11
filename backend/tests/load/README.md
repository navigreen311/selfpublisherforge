# Load Testing with Locust

Comprehensive load testing setup for SelfPublisherForge API using [Locust](https://locust.io/).

## Overview

This load testing suite simulates realistic user behavior patterns across the SelfPublisherForge platform:

- **ReaderUser (60%)**: Read-heavy users browsing projects, analytics, and market data
- **WriterUser (30%)**: Content creators working on manuscripts and chapters
- **PowerUser (10%)**: Advanced users executing complete publishing workflows

## Quick Start

### Prerequisites

```bash
# Install Locust
pip install locust

# Or use the requirements file (if added to main requirements)
pip install -r ../requirements.txt
```

### Setup Test User

Before running load tests, create a test user account:

```bash
# 1. Start your backend server
cd backend
uvicorn app.main:app --reload

# 2. Create test user via API or directly in database
# Email: loadtest@example.com
# Password: LoadTest123!

# 3. Disable MFA for the test user (important!)
```

### Run Load Tests

```bash
# Navigate to load test directory
cd backend/tests/load

# Smoke test (5 users, 1 minute)
LOAD_PROFILE=smoke locust -f locustfile.py --host=http://localhost:8000

# Normal load (50 users, 5 minutes)
LOAD_PROFILE=normal locust -f locustfile.py --host=http://localhost:8000

# Stress test (200 users, 10 minutes)
LOAD_PROFILE=stress locust -f locustfile.py --host=http://localhost:8000

# Spike test (500 users, 2 minutes)
LOAD_PROFILE=spike locust -f locustfile.py --host=http://localhost:8000

# Soak test (100 users, 30 minutes)
LOAD_PROFILE=soak locust -f locustfile.py --host=http://localhost:8000
```

Then open http://localhost:8089 to access the Locust web UI.

### Headless Mode

Run tests without the web UI:

```bash
# Run normal profile headless
LOAD_PROFILE=normal locust -f locustfile.py \
  --host=http://localhost:8000 \
  --headless \
  --users 50 \
  --spawn-rate 5 \
  --run-time 5m \
  --html report.html

# This will generate an HTML report when complete
```

## Load Profiles

| Profile | Users | Spawn Rate | Duration | Purpose |
|---------|-------|------------|----------|---------|
| **smoke** | 5 | 1/sec | 1m | Verify basic functionality |
| **normal** | 50 | 5/sec | 5m | Typical operational load |
| **stress** | 200 | 20/sec | 10m | Find performance limits |
| **spike** | 500 | 100/sec | 2m | Test elasticity under sudden load |
| **soak** | 100 | 10/sec | 30m | Find memory leaks and stability issues |

## User Patterns

### ReaderUser (60% weight)

**Behavior**: Browse and view content without making changes

**Key Actions**:
- View analytics dashboard
- List and view projects
- Browse books in portfolio
- Search market categories
- View revenue and metrics
- Search knowledge vault
- Check notifications

**Wait Time**: 1-3 seconds between requests

### WriterUser (30% weight)

**Behavior**: Create and edit content

**Key Actions**:
- Work on manuscripts and chapters
- Create new chapters
- Update existing chapters
- Generate AI content
- Analyze manuscript readability
- Generate outlines
- Record writing sessions
- Search knowledge vault for research

**Wait Time**: 2-5 seconds between requests

### PowerUser (10% weight)

**Behavior**: Execute complete publishing workflows

**Workflow Sequence**:
1. Create project
2. Research market opportunities
3. Create book
4. Write manuscript with chapters
5. Validate content (KDP validation, readability)
6. Create marketing plan
7. Set up advertising campaigns
8. Review analytics

**Additional Tasks**:
- Manage multiple projects
- Review portfolio performance
- Optimize advertising campaigns
- Use AI agent system
- Manage knowledge vault
- Analyze competitive intelligence

**Wait Time**: 1-2 seconds between requests

## Distributed Load Testing with Docker

For higher load testing, use Docker Compose to run distributed Locust with 1 master and 4 workers:

```bash
# Start distributed load test
docker-compose -f docker-compose.load.yml up

# Access web UI
open http://localhost:8089

# Scale workers if needed
docker-compose -f docker-compose.load.yml up --scale locust-worker=8

# Stop load test
docker-compose -f docker-compose.load.yml down
```

### Docker Environment Variables

Create a `.env` file in the `backend/tests/load` directory:

```bash
# Backend URL (use host.docker.internal for local testing)
BACKEND_URL=http://host.docker.internal:8000

# Load profile
LOAD_PROFILE=normal

# Test user credentials
LOAD_TEST_USER_EMAIL=loadtest@example.com
LOAD_TEST_USER_PASSWORD=LoadTest123!
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_URL` | `http://localhost:8000` | Backend API URL |
| `LOAD_PROFILE` | `smoke` | Load profile (smoke, normal, stress, spike, soak) |
| `LOAD_TEST_USER_EMAIL` | `loadtest@example.com` | Test user email |
| `LOAD_TEST_USER_PASSWORD` | `LoadTest123!` | Test user password |

### Customizing Profiles

Edit `config.py` to add or modify load profiles:

```python
LOAD_PROFILES = {
    "custom": LoadProfile(
        users=100,
        spawn_rate=10,
        duration="15m",
        description="Custom load profile",
    ),
}
```

### Adjusting User Distribution

Modify weights in user classes to change traffic distribution:

```python
class ReaderUser(AuthenticatedUser):
    weight = 60  # Change this to adjust percentage

class WriterUser(AuthenticatedUser):
    weight = 30

class PowerUser(AuthenticatedUser):
    weight = 10
```

## Monitoring and Metrics

### Key Metrics to Monitor

**Response Times**:
- Median response time
- 95th percentile
- 99th percentile
- Average response time

**Throughput**:
- Requests per second (RPS)
- Total requests
- Failed requests

**Error Rates**:
- HTTP error codes (4xx, 5xx)
- Failure percentage
- Exception types

### Backend Monitoring

While running load tests, monitor your backend:

```bash
# Check backend logs
docker-compose logs -f backend

# Monitor resource usage
docker stats

# Check database connections
docker-compose exec postgres psql -U postgres -d selfpublisherforge \
  -c "SELECT count(*) FROM pg_stat_activity;"

# Monitor Redis
docker-compose exec redis redis-cli INFO stats
```

## Best Practices

### Before Load Testing

1. **Create dedicated test user** with representative permissions
2. **Disable MFA** for test user to avoid authentication issues
3. **Use separate environment** (staging, not production)
4. **Warm up the system** with a smoke test first
5. **Monitor backend resources** (CPU, memory, database connections)
6. **Clear test data** periodically to avoid database bloat

### During Load Testing

1. **Start with smoke test** to verify everything works
2. **Gradually increase load** (smoke → normal → stress)
3. **Monitor error rates** - stop if errors exceed 5%
4. **Watch database connections** - ensure pool isn't exhausted
5. **Check Redis memory** - ensure cache isn't overflowing
6. **Monitor response times** - identify slow endpoints

### After Load Testing

1. **Review HTML reports** for detailed analysis
2. **Identify bottlenecks** from response time percentiles
3. **Analyze failed requests** for patterns
4. **Check backend logs** for errors and warnings
5. **Clean up test data** created during load testing
6. **Document findings** and performance baselines

## Analyzing Results

### Response Time Targets

| Percentile | Target | Action if Exceeded |
|------------|--------|-------------------|
| Median | < 200ms | Investigate most common requests |
| 95th | < 500ms | Check slow queries and external API calls |
| 99th | < 1000ms | Identify outliers and edge cases |

### Error Rate Targets

| Error Rate | Status | Action |
|------------|--------|--------|
| < 0.1% | ✅ Excellent | Continue testing |
| 0.1% - 1% | ⚠️ Warning | Investigate errors |
| 1% - 5% | 🔶 Critical | Reduce load, fix issues |
| > 5% | ❌ Failure | Stop test, fix critical issues |

### Throughput Targets

| Profile | Target RPS | Notes |
|---------|-----------|-------|
| smoke | ~10 RPS | Baseline functionality |
| normal | ~100-200 RPS | Typical operational load |
| stress | ~500+ RPS | Maximum sustainable throughput |

## Troubleshooting

### Test User Authentication Fails

```bash
# Verify test user exists
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"loadtest@example.com","password":"LoadTest123!"}'

# Check if MFA is enabled (disable it for load testing)
# Ensure user account is active and verified
```

### High Error Rates

- Check backend logs for specific error messages
- Verify database connection pool size is adequate
- Ensure Redis is running and not out of memory
- Check for rate limiting or throttling

### Slow Response Times

- Use backend profiling tools to identify slow queries
- Check database indexes for frequently queried fields
- Review Redis cache hit rates
- Monitor external API call latency

### Docker Issues

```bash
# Check Docker logs
docker-compose -f docker-compose.load.yml logs -f

# Restart services
docker-compose -f docker-compose.load.yml restart

# Clean up and rebuild
docker-compose -f docker-compose.load.yml down -v
docker-compose -f docker-compose.load.yml up --build
```

## Example Load Test Session

```bash
# 1. Start backend services
cd backend
docker-compose up -d

# 2. Create and verify test user
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"loadtest@example.com","password":"LoadTest123!"}'

# 3. Run smoke test first
cd tests/load
LOAD_PROFILE=smoke locust -f locustfile.py --host=http://localhost:8000 \
  --headless --users 5 --spawn-rate 1 --run-time 1m

# 4. If smoke test passes, run normal load
LOAD_PROFILE=normal locust -f locustfile.py --host=http://localhost:8000 \
  --headless --users 50 --spawn-rate 5 --run-time 5m \
  --html reports/normal-$(date +%Y%m%d-%H%M%S).html

# 5. Review results
open reports/normal-*.html

# 6. Run stress test
LOAD_PROFILE=stress locust -f locustfile.py --host=http://localhost:8000 \
  --headless --users 200 --spawn-rate 20 --run-time 10m \
  --html reports/stress-$(date +%Y%m%d-%H%M%S).html
```

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Load Testing

on:
  schedule:
    - cron: '0 2 * * 1'  # Weekly on Monday at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Start services
        run: docker-compose up -d

      - name: Wait for services
        run: sleep 30

      - name: Install Locust
        run: pip install locust

      - name: Run load test
        working-directory: backend/tests/load
        run: |
          LOAD_PROFILE=normal locust -f locustfile.py \
            --host=http://localhost:8000 \
            --headless --users 50 --spawn-rate 5 --run-time 5m \
            --html report.html

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: load-test-report
          path: backend/tests/load/report.html
```

## Additional Resources

- [Locust Documentation](https://docs.locust.io/)
- [Load Testing Best Practices](https://docs.locust.io/en/stable/best-practices.html)
- [Writing Good Load Tests](https://docs.locust.io/en/stable/writing-a-locustfile.html)

## Support

For issues or questions:
1. Check backend logs: `docker-compose logs -f backend`
2. Review Locust logs in the web UI or console output
3. Verify test user authentication manually
4. Ensure all backend services are running and healthy
