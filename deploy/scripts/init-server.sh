#!/usr/bin/env bash
# One-time bootstrap for a fresh Ubuntu 22.04/24.04 EC2 instance. Run this manually over SSH after launching
# the instance and before the first deploy. Installs Docker Engine + the Compose plugin, and creates the
# directory the app will live in.
set -euo pipefail

sudo apt-get update -y
sudo apt-get install -y ca-certificates curl gnupg git

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo usermod -aG docker "$USER"

sudo mkdir -p /opt/pricewise
sudo chown "$USER":"$USER" /opt/pricewise

cat <<'EOF'

Docker is installed. Next steps:
  1. Log out and back in (or run `newgrp docker`) so your user's docker group membership takes effect.
  2. git clone <your-repo-url> /opt/pricewise
  3. cd /opt/pricewise && cp .env.production.example .env
  4. Fill in every value in .env.production.example, then save it as .env.
  5. Point DOMAIN_NAME's DNS A record at this instance's public IP, then run deploy/scripts/init-tls.sh.
EOF
