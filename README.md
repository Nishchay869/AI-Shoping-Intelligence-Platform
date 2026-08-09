# Pricewise — AI Shopping Intelligence Platform

A full-stack shopping platform with a real FastAPI + PostgreSQL/pgvector backend and a Next.js frontend,
covering the whole AI shopping-assistant surface: semantic product search, an LLM recommendation engine,
an AI review summarizer, a behavioral (embeddings-only) personalization engine, a RAG shopping chatbot, a
LangGraph tool-calling shopping assistant with voice, CLIP image search, an OCR receipt scanner, and the
security/testing/deployment infrastructure around all of it.

## Features

| Feature | What it does | Backend | Frontend |
|---|---|---|---|
| Product search | Filter/sort/paginate the catalog by name, category, brand, price, rating | `app/api/routes/products.py` | `/search` |
| AI recommendation engine | Budget/purpose/brand/features → LLM query understanding → embedding search → LLM ranking with explanations | `app/services/recommendations.py` | `/recommendations` |
| Personalized recommendations | Tracks search/wishlist/purchase/click, builds a taste vector purely from embeddings (no LLM), explains picks | `app/services/personalization.py` | `/for-you` |
| AI review summarizer | Map-reduce LLM pipeline over up to 5,000 reviews → pros/cons/complaints/sentiment/verdict | `app/services/review_summary.py` | `/reviews/[id]` |
| RAG shopping chat | Retriever + prompt template + LLM answer generation grounded in the catalog and reviews | `app/services/rag/` | `/chat` |
| AI shopping assistant | LangGraph tool-calling agent: compare products, explain specs, suggest alternatives, persistent memory | `app/services/assistant/` | `/assistant` |
| Voice shopping assistant | Gemini speech-to-text → the same assistant → Gemini text-to-speech | `app/services/assistant/voice.py` | `/assistant` |
| Image-based product search | Upload a photo, CLIP embeddings + pgvector cosine search find visually similar products | `app/infrastructure/clip_embeddings.py` | `/search` |
| AI receipt scanner | Tesseract OCR + LLM structured extraction → product/price/tax/date/store/warranty as JSON | `app/services/receipt_scanner.py` | `/receipts` |
| Wishlist | Private per-user product tracking with target prices | `app/services/wishlist.py` | `/wishlist` |
| Supabase Auth | Sign-in/sign-up via Supabase; backend verifies the resulting JWT locally against Supabase's JWKS and JIT-provisions a matching local profile row | `app/core/security.py`, `app/services/auth.py` | `/auth/sign-in`, `/auth/sign-up` |

Standalone research/teaching modules (not part of the live API, each with its own `requirements.txt`):
- `backend/ml/fake_review_detection` — TF-IDF/BERT/Sentence-Transformers + XGBoost/Random Forest classifiers
- `backend/ml/price_prediction` — Prophet + LSTM + XGBoost price forecasting
- `backend/vectordb_tutorial` — the same data indexed in ChromaDB, FAISS, Pinecone, and Qdrant side by side

## Tech stack

**Backend:** FastAPI, SQLAlchemy 2.0, PostgreSQL + pgvector, Redis, Alembic, Google Gemini (recommendations,
review summaries, RAG chat, receipt scanning, the LangGraph assistant's model, and voice STT/TTS), Voyage AI
(embeddings), CLIP (local), Tesseract OCR (local).
**Frontend:** Next.js 15 (App Router), React 19, Tailwind CSS, Zod.
**Infra:** Docker, nginx, GitHub Actions CI/CD, Prometheus metrics, structured JSON logging.

## Project structure

```
backend/app/          FastAPI application (routes, services, models, schemas, infrastructure)
backend/migrations/   Alembic schema history (10 migrations)
backend/tests/        pytest: unit, integration (real Postgres+pgvector), api, security, performance
backend/ml/           standalone ML research modules - own requirements.txt, not imported by the API
backend/vectordb_tutorial/  vector database comparison - own requirements.txt
src/app/(platform)/   the signed-in Next.js pages (one per feature above)
src/app/api/v1/       Next.js route handlers that proxy to the FastAPI backend
src/middleware.ts      nonce-based Content-Security-Policy
tests/                 vitest: unit, component (RTL), API route handlers, CSP middleware
deploy/                nginx configs + EC2 deploy/TLS scripts for the Docker Compose production stack
.github/workflows/     CI (test) + CD (build, push to GHCR, SSH deploy) pipeline
```

`contracts/`, `supabase/`, and `workers/` predate this build and are **not used** by anything above — see
[Leftover from the original scaffold](#leftover-from-the-original-scaffold-not-needed).

## Prerequisites

Install these once, locally:

| Tool | Why | macOS |
|---|---|---|
| Node.js 22+ | Frontend | `brew install node` |
| Python 3.13 | Backend | `brew install python@3.13` |
| PostgreSQL 16/17 + **pgvector** | Product/review embeddings | `brew install postgresql@17 pgvector` |
| Redis | Rate limiting, caching | `brew install redis` |
| Tesseract OCR | Receipt scanner | `brew install tesseract` |

(Debian/Ubuntu: `apt install postgresql postgresql-contrib redis-server tesseract-ocr`; pgvector may need
building from source on Linux distros whose package repos don't carry it.)

### API keys

| Key | Unlocks | Get it at |
|---|---|---|
| `GEMINI_API_KEY` | Recommendations, review summarizer, RAG chat, receipt-scanner extraction, the LangGraph shopping assistant, and voice (STT/TTS) | aistudio.google.com |
| `VOYAGE_API_KEY` | All embeddings (search/recommendation similarity, search-history logging) | voyageai.com |

None of these are required just to start the app - every AI endpoint fails closed with a clean `503` if its
key is missing, rather than crashing. CLIP image search and Tesseract OCR run **locally** and need no key.

## Setup

### 1. Start the data stores

```bash
brew services start postgresql@17
brew services start redis
createdb pricewise
psql -d pricewise -c "CREATE EXTENSION vector;"
```

### 2. Backend

```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env` - only these need real values, everything else already has a working default:

```
DATABASE_URL=postgresql+psycopg://YOUR_USERNAME@localhost:5432/pricewise
SUPABASE_URL=https://your-project.supabase.co
GEMINI_API_KEY=AIza...
VOYAGE_API_KEY=pa-...
```

```bash
alembic upgrade head
```

### 3. Frontend

```bash
cd ..                 # project root
npm install
```

`BACKEND_API_URL`/`NEXT_PUBLIC_APP_URL` already default correctly for `localhost`, but
`NEXT_PUBLIC_SUPABASE_URL`/`NEXT_PUBLIC_SUPABASE_ANON_KEY` are required - copy `.env.example` to `.env` at the
project root and fill in your Supabase project's URL and publishable key (Dashboard > Project Settings > API).

### 4. Run it

```bash
npm run dev
```

Runs the FastAPI backend (`backend/.venv/bin/uvicorn app.main:app --reload`, port 8000) and the Next.js
frontend (`next dev`, port 3000) together in one terminal, output prefixed `[backend]`/`[frontend]`. Requires
step 1's Postgres/Redis to already be running and step 2's `.venv` to already exist.

Open **http://localhost:3000**. Verify the API separately with `curl http://localhost:8000/health` →
`{"status":"ok",...}`; interactive API docs at `http://localhost:8000/docs`.

To run just one side, use `npm run dev:backend` or `npm run dev:frontend`.

### 5. Create an account

Sign up at **/auth/sign-up** - this calls Supabase Auth directly and stores a real session, which is what
unlocks wishlist, receipt history, and personalized recommendations. If your Supabase project has email
confirmation enabled (the default), you'll need to click the confirmation link before your first sign-in.

### 6. Populate the catalog (manual - there is no seed data or scraper)

By design, this app never scrapes retailers (see [Security & data policy](#security--data-policy)). Insert
a few products yourself to have something to search/recommend/wishlist:

```bash
cd backend && source .venv/bin/activate
python -c "
from app.db.session import SessionLocal
from app.models import Product
db = SessionLocal()
db.add(Product(title='Sony WH-1000XM5 Headphones', brand='Sony', category='Audio', currency='USD', current_price_minor=34999, retailer='Amazon'))
db.add(Product(title='Apple Watch SE', brand='Apple', category='Wearables', currency='USD', current_price_minor=24900, retailer='Amazon'))
db.commit()
"
python -m scripts.backfill_embeddings          # product/review text embeddings (needs VOYAGE_API_KEY)
python -m scripts.backfill_image_embeddings    # CLIP image embeddings, only for products with an image_url
python -m scripts.seed_reviews <product_id> --count 500   # sample reviews, to test the AI summarizer
```

## Environment variables reference

All of `backend/.env.example` and the root `.env.example` are documented inline in those files.
`NEXT_PUBLIC_SUPABASE_URL`/`NEXT_PUBLIC_SUPABASE_ANON_KEY` are required (this app's real Auth provider - see
[Setup](#setup)). The root `.env.example` also lists `SUPABASE_SERVICE_ROLE_KEY`, `INNGEST_*`,
`RESEND_API_KEY`, and `TWILIO_*` - these remain leftovers from the original scaffold (see below) and can be
ignored; nothing in the current app reads them.

## Testing

```bash
# Backend - uses a second, disposable database so tests never touch dev data
createdb pricewise_test && psql -d pricewise_test -c "CREATE EXTENSION vector;"
cd backend
DATABASE_URL="postgresql+psycopg://$(whoami)@localhost:5432/pricewise_test" SUPABASE_URL="https://test-project.supabase.co" REDIS_URL="redis://localhost:6379/1" \
  alembic upgrade head && pytest -q

# Frontend
npm test
```

`backend/tests/` also has a `security/` suite (SQL injection, XSS, JWT tampering, IDOR, rate limits) and a
`performance/` suite (`locustfile.py` for load testing, `benchmark.py` for quick concurrency/latency checks
against a running instance).

## Deployment

`deploy/` and `docker-compose.prod.yml` set up Docker + nginx (TLS via Let's Encrypt) + GitHub Actions
CI/CD on an AWS EC2 instance. See the scripts in `deploy/scripts/` (`init-server.sh` → point your domain's
DNS at the instance → `init-tls.sh` → push to `main` to trigger `.github/workflows/ci-cd.yml`).

## Security & data policy

Supabase-issued JWTs verified locally against the project's JWKS (explicit algorithm/audience/issuer
checks, no shared secret), Redis fixed-window rate limiting (fails closed in production), parameterized
queries throughout (no raw SQL string-building), a nonce-based Content-Security-Policy, structured JSON
logging, and a Prometheus `/metrics` endpoint. No scraper: retailer data is expected to enter through
approved APIs or affiliate feeds only.

## Leftover from the original scaffold (not needed)

This repository started from a Supabase-oriented scaffold before the FastAPI/Next.js platform above was
built on top of it. `contracts/openapi.yaml`, `supabase/migrations/`, and `workers/` (Inngest) describe a
different, disconnected `listings/resolve` + price-alert design that nothing in `backend/` or the feature
pages implements - they're harmless to leave in place, and you don't need Inngest, Resend, or Twilio for
anything documented above to work. Supabase itself is the one exception: it's no longer just scaffold -
it's the real, active Auth provider (see [Setup](#setup)), it just doesn't use `supabase/migrations/` or
any table in Supabase's own Postgres - the FastAPI backend's own database is still the only source of
truth for product/wishlist/review/recommendation data.
