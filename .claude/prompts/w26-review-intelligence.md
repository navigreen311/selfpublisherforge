# W26: Review Intelligence & Reputation (Module #23)
**Branch:** `ai-feature/review-intelligence`
**Scope:** api

## Mission
Build the Review Intelligence system: review monitoring, sentiment analysis, review velocity tracking, reputation alerts, and review acquisition optimization.

## API Endpoints
- GET /api/v1/reviews — List reviews for org's books
- GET /api/v1/reviews/book/{book_id} — Reviews for a specific book with sentiment analysis
- GET /api/v1/reviews/sentiment/{book_id} — Sentiment breakdown (positive/neutral/negative, key themes)
- GET /api/v1/reviews/velocity/{book_id} — Review velocity over time
- GET /api/v1/reviews/alerts — Active review alerts (negative review, velocity drop, competitor surge)
- PATCH /api/v1/reviews/alerts/{id}/acknowledge — Acknowledge alert
- POST /api/v1/reviews/analyze — AI analyze a batch of reviews (themes, complaints, praise)
- GET /api/v1/reviews/reputation/{book_id} — Reputation score and health metrics
- POST /api/v1/reviews/acquisition/tips — AI tips for improving review acquisition

## What to Build

### Backend
1. **backend/app/modules/review_intelligence/__init__.py**
2. **backend/app/modules/review_intelligence/router.py** — All endpoints
3. **backend/app/modules/review_intelligence/schemas.py** — Review, SentimentAnalysis, VelocityReport, ReviewAlert, ReputationScore
4. **backend/app/modules/review_intelligence/service.py** — Review monitoring, alert management, reputation scoring
5. **backend/app/modules/review_intelligence/sentiment.py** — NLP sentiment analysis: positive/negative/neutral classification, theme extraction, complaint categorization (AI-powered via LLM)
6. **backend/app/modules/review_intelligence/velocity.py** — Review velocity tracking: daily/weekly/monthly rates, trend detection, anomaly detection
7. **backend/app/modules/review_intelligence/alerts.py** — Alert rules: negative review spike, velocity drop, star rating decline, competitor review surge
8. **backend/app/tasks/review_intelligence.py** — Celery: periodic review fetch, sentiment analysis batch, alert checking

### Tests
9. **backend/tests/unit/test_sentiment.py**
10. **backend/tests/unit/test_velocity.py**
11. **backend/tests/integration/test_review_api.py**

## Database Tables (from W02, read-only)
competitor_reviews (reused for own-book reviews tracking too)

## Commit Convention
`feat(reviews): implement review intelligence with sentiment analysis and reputation monitoring`
