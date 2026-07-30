#!/usr/bin/env bash
# One-time HTTPS bootstrap. Run from /opt/pricewise on the EC2 host after DNS for DOMAIN_NAME already
# resolves to this instance (Let's Encrypt's HTTP-01 challenge validates ownership by fetching a file over
# real port 80 from the public internet - this will fail if DNS hasn't propagated yet).
#
# What it does: starts nginx with the HTTP-only bootstrap config, requests a certificate from Let's Encrypt
# via the webroot challenge, then swaps nginx over to the full HTTPS reverse-proxy config.
set -euo pipefail
cd "$(dirname "$0")/../.."

set -a; source .env; set +a
: "${DOMAIN_NAME:?Set DOMAIN_NAME in .env}"
: "${CERTBOT_EMAIL:?Set CERTBOT_EMAIL in .env}"

echo "==> Starting nginx with the HTTP-only bootstrap config"
cp deploy/nginx/available/bootstrap.conf.template deploy/nginx/templates/default.conf.template
docker compose -f docker-compose.prod.yml up -d nginx

echo "==> Requesting a certificate for $DOMAIN_NAME"
docker compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot --webroot-path=/var/www/certbot \
  --email "$CERTBOT_EMAIL" --agree-tos --no-eff-email \
  -d "$DOMAIN_NAME"

echo "==> Switching nginx to the full HTTPS config"
cp deploy/nginx/available/production.conf.template deploy/nginx/templates/default.conf.template
docker compose -f docker-compose.prod.yml up -d --force-recreate nginx

cat <<EOF

HTTPS is live at https://$DOMAIN_NAME

Certificates expire after 90 days. Add a cron entry (crontab -e) so renewal runs automatically, e.g.:
  0 3 * * * cd /opt/pricewise && ./deploy/scripts/renew-tls.sh >> /var/log/pricewise-renew.log 2>&1
EOF
