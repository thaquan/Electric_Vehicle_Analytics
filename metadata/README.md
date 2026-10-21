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

Profiles retain aggregate counts and category domains needed for validation. `Buyer_ID` retains its distinct/null counts but omits individual identifier values. Both profiling scripts preserve this rule; key uniqueness is checked against the input data at runtime. See [data acquisition and verification](../docs/data_access.md).

## Historical status and current verification

`fabric_workspace.json` supplies identifiers to the notebook and pipeline
generators. Its deployment flags, `pending` text and `phase_7_evidence` describe
the earlier Phase 7 record, including the statement that Phase 8 had not started.
They are not a live status feed. The referenced local recovery evidence is not
included in this repository. Consult the [17 October release evidence](../docs/evidence/acceptance_20261017.json)
for the later Test deployment and [evidence guide](../docs/evidence/README.md)
for the scope of subsequent repository checks. Neither record revalidates the
original workspace identifiers for a new deployment.

`gold_export_status.json` and `gold_export_manifest.json` describe the pinned
September export and recovery snapshot. `completed_with_user_attested_report_kpi`
records a KPI confirmed by the report reviewer; it does not assert an automated
UI check. `skipped_by_user_request` records checks omitted from that recovery
exercise, not passing results. Later Service UAT concerns a different release
and does not change those historical outcomes.

Preserve the manifest bytes and `gold_export_manifest.sha256` together. The
recovery verification example and export/package/restore scripts retain these
status values for compatibility. For a new run, record actual results and their
evidence as described in the [recovery runbook](../docs/recovery/recovery_runbook.md).
