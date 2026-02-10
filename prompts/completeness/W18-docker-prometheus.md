# W18: Docker-Compose Prometheus Exporters + Fix Staging Workflow

## Files to modify
- `infra/docker-compose.yml` or `docker-compose.yml` — Add Prometheus exporters
- `.github/workflows/staging.yml` — Fix branch trigger

## Task

### 1. Read current docker-compose files

Find and read all docker-compose files in the project. Identify which services exist and what monitoring is configured.

### 2. Add Prometheus exporters

Add these services to the main docker-compose file:

```yaml
  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    environment:
      DATA_SOURCE_NAME: "postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}?sslmode=disable"
    ports:
      - "9187:9187"
    depends_on:
      - postgres
    networks:
      - app-network

  redis-exporter:
    image: oliver006/redis_exporter:latest
    environment:
      REDIS_ADDR: "redis://redis:6379"
    ports:
      - "9121:9121"
    depends_on:
      - redis
    networks:
      - app-network

  node-exporter:
    image: prom/node-exporter:latest
    ports:
      - "9100:9100"
    networks:
      - app-network
```

### 3. Update Prometheus config

If a prometheus.yml config exists, add scrape targets for the new exporters:
```yaml
scrape_configs:
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
```

### 4. Fix staging workflow

Read `.github/workflows/staging.yml` (or similar). If it triggers on `develop` branch but docs say `main`, update to be consistent. The typical pattern is:
- `main` branch → production deploy
- `develop` branch → staging deploy
- PR → run tests only

Ensure the workflow file matches the documented behavior.
