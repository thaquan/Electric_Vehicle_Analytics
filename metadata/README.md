# Contracts and retained evidence

This directory contains inputs used by the project and selected historical acceptance evidence. JSON evidence records the run and date inside each file; it is not a live service-health guarantee.

Keep schema contracts, source manifests/checksums, Gold specifications, expected metrics, environment mappings and model/report validation files. Build, reconciliation and recovery tools rely on these files.

| Evidence | Purpose |
| --- | --- |
| `phase7_handoff_validation.json` | Historical recovery-package validation |
| `phase8_test_deployment.json`, `phase8_cd_verification.json` | Bootstrap deployment/rollback and subsequent automated CD evidence |
| `phase11/clean_package_manifest.json` | Source-package provenance |
| `phase11/clean_package_verification.json`, `phase11/clean_package_reconciliation.json` | Accepted Databricks artifact integrity and eight-table comparison |
| `phase12/acceptance.json`, `phase12/tests.json` | Technical acceptance scope, historical tests and pending handoff |
| `phase12/restore_report.json`, `phase12/restored_phase11_reconciliation.json` | Restore drill and restored Gold comparison |
| `phase12/package_report.json`, `phase12/final_archive_verification.json` | Final archive identity and verification method |
| `phase12/airflow_verification.json`, `phase12/airflow_reconciliation.json` | Airflow execution and comparison |
| `phase12/fabric_test_health_json.json` | Successful Fabric Test JSON API health check |
| `phase12/databricks_access.json`, `phase12/runtime_billing.json` | Scope of identity/access verification and DBU usage, not monetary cost |

Intermediate API responses, initial probes, failed attempts and superseded run reports are archived locally under `output/repository_cleanup_20261008/archive/metadata/`. The parent cleanup manifest records their original paths and SHA-256. They also remain in prior Git history. New diagnostic output belongs under `output/` or in CI artifacts; only deliberately selected acceptance evidence belongs here.

Historical JSON may reference local artifacts or files inside sealed packages. Those references describe the historical run and are preserved unchanged; do not rewrite checksummed packages to match the current repository layout. See the [project summary](../docs/project_summary.md) for current documentation and limits.
