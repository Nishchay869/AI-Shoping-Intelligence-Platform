# Pricewise FastAPI Backend

This is a deployable **modular monolith**: one FastAPI service and one PostgreSQL database, internally separated into API routes, services, models, schemas, and infrastructure. It is simpler to deploy than microservices while preserving boundaries that can be extracted later.

## Run locally

```bash
cd backend
cp .env.example .env
docker compose up -d postgres redis
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` in development. The Next.js application signs shoppers in/up directly
against Supabase Auth, then attaches the resulting Supabase-issued JWT in `Authorization: Bearer <token>`
on every call to this backend.

## What each folder does

- `app/main.py`: composition root, CORS, request logging, exception translation, health check, and router registration.
- `app/api`: HTTP-only code. `deps.py` verifies Supabase-issued JWTs, authorizes roles, and rate-limits sensitive endpoints; routes validate input then call services.
- `app/services`: business rules such as `auth.py`'s JIT-provisioning of a local profile row for a verified Supabase identity, and ownership checks. They do not import FastAPI.
- `app/models`: SQLAlchemy table mappings; `schemas`: Pydantic API contracts that validate all input and prevent accidental field exposure.
- `app/core`: typed config, Supabase JWT verification helpers, logs, and framework-independent domain errors.
- `app/db`: database engine, declarative base, and a safely closed request session.
- `migrations`: Alembic versioned schema changes; always use migrations rather than `create_all` in deployment.

## REST API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v1/auth/me` | Current authenticated profile (sign-in/sign-up happen against Supabase directly, not this API) |
| GET | `/api/v1/products` | Search/paginate products |
| GET | `/api/v1/products/{id}` | Product detail |
| GET/POST | `/api/v1/wishlists` | Read/create private wishlists |
| POST | `/api/v1/wishlists/{id}/items` | Add tracked product |
| DELETE | `/api/v1/wishlists/{id}/items/{itemId}` | Remove owned item |
| GET/PATCH | `/api/v1/preferences` | Read/update alert rules, AI persona, and smart-rule settings |
| POST | `/api/v1/preferences/phone/verify` | Generate a phone verification code (no SMS provider configured yet - see `services/preferences.py`) |
| POST | `/api/v1/preferences/phone/confirm` | Confirm a phone verification code |
| GET | `/api/v1/webhooks/whatsapp` | Meta Cloud API subscription verification handshake |
| POST | `/api/v1/webhooks/whatsapp` | Meta Cloud API delivery-status callbacks and inbound `STOP` opt-out (HMAC-verified, no user auth) |

## Database

The full normalized commerce design, ER diagram, constraints, indexing strategy, and scaling guidance are in [docs/database-design.md](docs/database-design.md). Apply it after the base schema with `alembic upgrade head`.

## Security decisions

Passwords are never handled by this backend - Supabase Auth owns credentials entirely. Incoming bearer tokens are verified locally against Supabase's published JWKS (explicit algorithm/audience/issuer checks, no shared secret involved), then resolved to a local profile row, JIT-provisioned on first sight. Auth is always checked against the current database user, so disabled users immediately lose access. Query construction uses SQLAlchemy parameterization. Input limits prevent oversized payloads. Rate limiting on sensitive endpoints uses Redis and fails closed in production. Errors never include stack traces or credential details. Set a real `SUPABASE_URL`, TLS at the reverse proxy, and database/Redis credentials before production.
