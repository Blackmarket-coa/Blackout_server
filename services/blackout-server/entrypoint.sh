#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH="/data/homeserver.yaml"
TEMPLATE_PATH="/templates/homeserver.yaml.template"

# Prefer an explicit SERVER_NAME, then Railway-style SYNAPSE_SERVER_NAME, and
# finally a localhost default so container boot doesn't immediately crash-loop
# when only DB/redis secrets are wired.
SERVER_NAME="${SERVER_NAME:-${SYNAPSE_SERVER_NAME:-localhost}}"
export SERVER_NAME

: "${DATABASE_HOST:?DATABASE_HOST is required}"
: "${DATABASE_PASSWORD:?DATABASE_PASSWORD is required}"
: "${REDIS_HOST:?REDIS_HOST is required}"
: "${REGISTRATION_SHARED_SECRET:?REGISTRATION_SHARED_SECRET is required}"

mkdir -p /data

if [[ ! -f "$CONFIG_PATH" ]]; then
  envsubst < "$TEMPLATE_PATH" > "$CONFIG_PATH"
fi

if [[ ! -f "/data/${SERVER_NAME}.signing.key" ]]; then
  python -m synapse.app.homeserver \
    --config-path "$CONFIG_PATH" \
    --generate-keys
fi

python -m synapse.app.homeserver --config-path "$CONFIG_PATH"
