#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE=${COMPOSE_FILE:-contrib/docker_compose_workers/docker-compose-ha.yaml}
PROJECT_NAME=${PROJECT_NAME:-synapse-ha}

run() {
  echo "\n>>> $*"
  "$@"
}

run docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" up -d

# D1: Worker topology
run docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" ps synapse-generic-worker-1 synapse-federation-sender-1 synapse-background-worker-1 synapse-persister-1

# D2: Redis replication/cache coherence
run docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" exec -T redis-replica redis-cli -a redispassword INFO replication

# D3: PostgreSQL HA failover
run docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" exec -T postgres-proxy bash -lc "PGPASSWORD=postgres psql -h 127.0.0.1 -p 5432 -U synapse_user -d synapse -c 'select now()'"
run docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" stop postgres-primary
sleep 10
run docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" exec -T postgres-proxy bash -lc "PGPASSWORD=postgres psql -h 127.0.0.1 -p 5432 -U synapse_user -d synapse -c 'select now()'"

# D4 + D5: Reverse proxy/LB and readiness
run docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" exec -T reverse-proxy sh -lc "wget -q -O- http://127.0.0.1:8008/health"
run docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" ps

# D6: Rollback (illustrative flow)
CURRENT_IMAGE=$(docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" images -q synapse)

echo "Current synapse image digest: ${CURRENT_IMAGE}"
echo "To validate rollback, deploy a known bad image tag and restore the previous digest/tag if health checks fail."

echo "Validation flow completed."
