#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH="/data/homeserver.yaml"
TEMPLATE_PATH="/templates/homeserver.yaml.template"

# Prefer an explicit SERVER_NAME, then Railway-style SYNAPSE_SERVER_NAME, and
# finally a localhost default so container boot doesn't immediately crash-loop
# when only DB/redis secrets are wired.
SERVER_NAME="${SERVER_NAME:-${SYNAPSE_SERVER_NAME:-localhost}}"
export SERVER_NAME

HAS_EXTERNAL_BACKING_SERVICES=true
for required_var in DATABASE_HOST DATABASE_PASSWORD REDIS_HOST REGISTRATION_SHARED_SECRET; do
  if [[ -z "${!required_var:-}" ]]; then
    HAS_EXTERNAL_BACKING_SERVICES=false
    break
  fi
done

mkdir -p /data

if [[ ! -f "$CONFIG_PATH" ]]; then
  if [[ "$HAS_EXTERNAL_BACKING_SERVICES" == "true" ]]; then
    envsubst < "$TEMPLATE_PATH" > "$CONFIG_PATH"
  else
    echo "[entrypoint] DATABASE_HOST / DATABASE_PASSWORD / REDIS_HOST / REGISTRATION_SHARED_SECRET not fully set; generating standalone sqlite config"
    python -m synapse.app.homeserver \
      --generate-config \
      -H "$SERVER_NAME" \
      -c "$CONFIG_PATH" \
      --report-stats=no
  fi
fi

if [[ ! -f "/data/${SERVER_NAME}.signing.key" ]]; then
  python -m synapse.app.homeserver \
    --config-path "$CONFIG_PATH" \
    --generate-keys
fi

python -m synapse.app.homeserver --config-path "$CONFIG_PATH"
