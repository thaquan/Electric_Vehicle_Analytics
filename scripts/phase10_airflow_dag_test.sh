#!/usr/bin/env bash
set -euo pipefail

airflow db migrate >/tmp/airflow_migrate.log
run_id="$(python -c 'import uuid; print("airflow_test_" + uuid.uuid4().hex)')"
logical_date="$(date -u +%Y-%m-%dT%H:%M:%S)"
printf 'Application run ID: %s\n' "$run_id"
airflow dags test ev_analytics_phase10 "$logical_date" -c "{\"run_id\":\"$run_id\"}"
