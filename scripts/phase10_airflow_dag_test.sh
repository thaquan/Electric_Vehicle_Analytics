#!/usr/bin/env bash
set -euo pipefail

airflow db migrate >/tmp/airflow_migrate.log
airflow dags test ev_analytics_phase10 2026-10-03 -c '{"run_id":"airflow_dag_test_20261003"}'
