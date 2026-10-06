#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  printf 'Usage: %s <existing_application_run_id>\n' "$0" >&2
  exit 2
fi
export EV_RESUME_RUN_ID="$1"
conf="$(python -c 'import json, os; print(json.dumps({"run_id": os.environ["EV_RESUME_RUN_ID"]}))')"
airflow db migrate >/tmp/airflow_migrate.log
airflow dags test ev_analytics_phase10 "$(date -u +%Y-%m-%dT%H:%M:%S)" -c "$conf"
