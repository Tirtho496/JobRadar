#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
[ -f .env ] || cp .env.example .env
docker compose up --build -d
echo "JobRadar is starting at http://localhost:8080"
