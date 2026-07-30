#!/usr/bin/env bash
# Deploys the latest built images. Run automatically by .github/workflows/ci-cd.yml over SSH after every
# push to main (once CI and the image build both pass), or manually for a re-deploy with no code change.
set -euo pipefail
cd "$(dirname "$0")/../.."

echo "==> Pulling latest images"
docker compose -f docker-compose.prod.yml pull backend frontend

echo "==> Applying database migrations"
docker compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

echo "==> Recreating services with the new images"
docker compose -f docker-compose.prod.yml up -d --remove-orphans backend frontend nginx

echo "==> Pruning now-unused images"
docker image prune -f

echo "==> Deploy complete"
