# Runtime contracts and pinned references

Only inputs needed to reproduce processing, validate results or package the pinned snapshot are versioned here.

| Files | Used for |
| --- | --- |
| `source_manifest.json`, `schema_contract.yaml` | Source provenance, checksums and schema. |
| `categorical_profile.json`, `profiling_summary.json` | Allowed values and source validation in Bronze/Silver. |
| `gold_spec.json`, `gold_expected_metrics.json`, `star_expected_metrics.json` | Transformation rules, expected KPIs and segment reconciliation. |
| `fabric_workspace.json` | Generate the Fabric notebook and pipeline definitions. |
| `e2e_star_verified_run.json` | Pinned source audit required by the Gold export tool and its regression tests. |
| `e2e_verified_run.json`, `gold_published_run.json`, `silver_published_run.json` | Versioned reference inputs used by pipeline/star-schema regression tests. |
| `gold_export_status.json`, `gold_export_manifest.json`, `gold_export_manifest.sha256` | Identity and provenance of the pinned recovery/export snapshot. |

Local test results, API responses, service probes, acceptance journals and generated diagnostics are not source inputs and are excluded from Git. New run output belongs in `output/` or CI artifacts. Use the [validation overview](../docs/validation.md) for the project scope.
