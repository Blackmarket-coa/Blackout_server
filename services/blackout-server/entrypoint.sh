#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH="/data/homeserver.yaml"
TEMPLATE_PATH="/templates/homeserver.yaml.template"
PORT="${PORT:-8008}"

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
    python - <<'PY' "$CONFIG_PATH" "$PORT" "${SYNAPSE_PUBLIC_BASEURL:-}"
from pathlib import Path
import sys

import yaml

config_path = Path(sys.argv[1])
port = int(sys.argv[2])
public_baseurl = sys.argv[3]
with config_path.open("r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

listeners = config.setdefault("listeners", [])
if listeners:
    listener = listeners[0]
else:
    listener = {}
    listeners.append(listener)

listener["port"] = port
listener["bind_addresses"] = ["0.0.0.0"]
listener["tls"] = False
listener["type"] = "http"
listener["x_forwarded"] = True
listener.setdefault("resources", [{"names": ["client", "federation"], "compress": False}])

if public_baseurl:
    config["public_baseurl"] = public_baseurl

config.setdefault("suppress_key_server_warning", True)

with config_path.open("w", encoding="utf-8") as f:
    yaml.safe_dump(config, f, sort_keys=False)
PY
  fi
fi

if [[ ! -f "/data/${SERVER_NAME}.signing.key" ]]; then
  python -m synapse.app.homeserver \
    --config-path "$CONFIG_PATH" \
    --generate-keys
fi

python -m synapse.app.homeserver --config-path "$CONFIG_PATH"
