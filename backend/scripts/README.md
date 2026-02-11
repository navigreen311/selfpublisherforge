# Database Seeding Scripts

Comprehensive database seeding system for development and demo environments.

## Quick Start

```bash
# Seed all data
python -m scripts.seed

# Reset database and seed
python -m scripts.seed --reset

# Seed specific module only
python -m scripts.seed --module users
python -m scripts.seed --module projects
```

## Available Modules

- **users** - Demo users (admin, pro, starter, free) with organizations
- **projects** - 3 demo books for Jane (Fantasy, Cookbook, Romance)
- **content** - Chapters and manuscripts for each book
- **analytics** - 12 months of royalty and revenue data
- **market** - Competitor books and keyword data
- **marketing** - Launch plans, campaigns, and email sequences

## Demo Credentials

```
Admin:   admin@selfpublisherforge.com / admin123
Pro:     jane@example.com / demo123
Starter: bob@example.com / demo123
Free:    alice@example.com / demo123
```

## Data Generated

- 4 users across 4 subscription tiers
- 3 books in various states (published, writing, draft)
- 15 chapters (5 per book)
- ~180 royalty records (12 months)
- 10 competitor books
- 10 market keywords
- 1 launch campaign
- 5 email templates

## Features

- **Idempotent**: Safe to run multiple times
- **Modular**: Seed only what you need
- **Realistic**: Production-like demo data
- **Tested**: Full test coverage

## Running Tests

```bash
pytest backend/tests/unit/test_seed_scripts.py -v
```
