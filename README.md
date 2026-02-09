# SelfPublisherForge

AI-powered, end-to-end self-publishing platform for independent authors, small publishers, and publishing agencies.

## Tech Stack

- **Frontend:** Next.js 14, React 18, Tailwind CSS, shadcn/ui
- **Backend:** FastAPI (Python 3.12+), SQLAlchemy, Celery
- **Database:** PostgreSQL 16, Redis 7, Elasticsearch 8
- **AI/ML:** Claude API (Anthropic), OpenAI fallback
- **Storage:** AWS S3 / Cloudflare R2
- **Payments:** Stripe

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+
- Python 3.12+
- Git

### Run with Docker Compose
```bash
docker-compose up -d
```

Services:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/api/v1/docs
- Flower (Celery monitor): http://localhost:5555
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- Elasticsearch: localhost:9200

### Manual Setup

#### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your values
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

### Run Tests
```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm test
```

## Project Structure
```
selfpublisherforge/
├── backend/          # FastAPI Python backend
│   ├── app/
│   │   ├── api/      # API route handlers
│   │   ├── core/     # Shared utilities (auth, config)
│   │   ├── models/   # SQLAlchemy models
│   │   ├── modules/  # Feature modules
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── services/ # Business logic
│   │   └── tasks/    # Celery async tasks
│   ├── migrations/   # Alembic DB migrations
│   └── tests/
├── frontend/         # Next.js React frontend
│   └── src/
│       ├── app/      # Next.js App Router pages
│       ├── components/
│       ├── hooks/
│       ├── lib/
│       ├── modules/
│       └── types/
├── shared/           # Shared type contracts
├── infra/            # Terraform, Docker configs
├── docs/             # Feature documentation
└── .claude/          # AI development commands
```

## Feature Modules

29 modules across 8 tiers — see `docs/architecture.md` for the full module registry and dependency map.

## License

Proprietary — Green Companies LLC
