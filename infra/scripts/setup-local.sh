#!/bin/bash
set -e

echo "=== SelfPublisherForge Local Setup ==="

# Start Docker services
echo "Starting Docker services..."
docker compose up -d postgres redis elasticsearch

# Wait for services
echo "Waiting for PostgreSQL..."
until docker compose exec postgres pg_isready -U postgres; do sleep 1; done

echo "Waiting for Redis..."
until docker compose exec redis redis-cli ping; do sleep 1; done

# Backend setup
echo "Setting up backend..."
cd backend
python -m venv .venv
source .venv/bin/activate || .venv/Scripts/activate
pip install -r requirements.txt
cp -n .env.example .env 2>/dev/null || true

# Run migrations
alembic upgrade head

cd ..

# Frontend setup
echo "Setting up frontend..."
cd frontend
npm install
cp -n .env.example .env.local 2>/dev/null || true
cd ..

echo "=== Setup complete! ==="
echo "Run 'docker compose up' to start all services"
echo "Or run backend/frontend manually:"
echo "  Backend: cd backend && uvicorn app.main:app --reload"
echo "  Frontend: cd frontend && npm run dev"
