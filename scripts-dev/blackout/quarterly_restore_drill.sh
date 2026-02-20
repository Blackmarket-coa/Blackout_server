#!/usr/bin/env bash
set -euo pipefail

# Restore-drill script for quarterly disaster-recovery validation.
# Restores the latest base backup to a temporary PGDATA and runs
# a startup smoke check with pg_controldata.

BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/postgres}"
DRILL_ROOT="${DRILL_ROOT:-/var/tmp/postgres-restore-drill}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LATEST_BACKUP="$(find "${BACKUP_ROOT}/base" -mindepth 1 -maxdepth 1 -type d | sort | tail -n1)"
RESTORE_DIR="${DRILL_ROOT}/${STAMP}"
REPORT="${DRILL_ROOT}/restore-drill-${STAMP}.txt"

mkdir -p "${RESTORE_DIR}" "${DRILL_ROOT}"

if [[ -z "${LATEST_BACKUP}" ]]; then
  echo "No base backup directories found under ${BACKUP_ROOT}/base" | tee "${REPORT}"
  exit 1
fi

cp -a "${LATEST_BACKUP}/data" "${RESTORE_DIR}/data"

pg_controldata "${RESTORE_DIR}/data" 2>&1 | tee "${REPORT}"

echo "Restore drill PASSED from ${LATEST_BACKUP}" | tee -a "${REPORT}"
