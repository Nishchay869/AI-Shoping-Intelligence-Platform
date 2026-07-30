#!/usr/bin/env bash
# Renews the Let's Encrypt certificate if it's due (certbot only actually renews inside its last 30 days of
# validity, so this is safe to run frequently/on a schedule) and reloads nginx so it picks up the new cert
# without dropping connections. Intended to run from cron - see the crontab line init-tls.sh prints at the end.
set -euo pipefail
cd "$(dirname "$0")/../.."

docker compose -f docker-compose.prod.yml run --rm certbot renew --webroot --webroot-path=/var/www/certbot
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
