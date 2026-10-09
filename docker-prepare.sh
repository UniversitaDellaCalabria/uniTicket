#!/bin/bash

# Prepares the examples-docker/ folder used as the Django project volume.
#
# Usage:
#   ./docker-prepare.sh [DOMAIN]
#
# DOMAIN can also be set via:
#   - .env file (recommended):  echo "DOMAIN=your.fqdn.example" >> .env
#   - environment variable:     export DOMAIN=your.fqdn.example
#
# Example:
#   cp .env.example .env && nano .env
#   ./docker-prepare.sh

# Load .env if present
[ -f .env ] && set -a && source .env && set +a

DOMAIN=${1:-${DOMAIN:-uniticket.hostname.url}}
EXPFOLDER="examples-docker"

echo "→ Preparing ${EXPFOLDER}/ for domain: ${DOMAIN}"

# Copy application and example config
cp -R uniticket $EXPFOLDER
cp -R uniticket/uni_ticket_project/settingslocal.py.example $EXPFOLDER/uni_ticket_project/settingslocal.py
cp -R dumps $EXPFOLDER

# Patch HOSTNAME / CSRF_TRUSTED_ORIGINS with the real domain
sed -i "s|uniticket.hostname.url|${DOMAIN}|g" $EXPFOLDER/uni_ticket_project/settingslocal.py

# Remove dev db
rm -f $EXPFOLDER/db.sqlite3

echo "✓ Done. Run: docker compose up --build"
echo "  For HTTPS: docker compose -f docker-compose.yml -f docker-compose.https.yml up --build -d"
