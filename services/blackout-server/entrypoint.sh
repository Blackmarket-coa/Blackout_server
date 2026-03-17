#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH="/data/homeserver.yaml"
TEMPLATE_PATH="/templates/homeserver.yaml.template"

: "${SERVER_NAME:?SERVER_NAME is required}"
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
