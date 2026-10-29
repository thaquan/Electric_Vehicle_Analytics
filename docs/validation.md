# Validation and limitations

## Implemented checks

- Source files: SHA-256, size, header, types, allowed categories and separation of labeled/unlabeled records.
- Gold: 668665 fact rows, 116779 Yes, 551886 No, five dimensions, zero orphan keys and 35 segment groups. Quality checks reconstruct Gold from Silver and compare schema and row multisets.
- Power BI baseline: the 12 core measures and combined-filter calculations were checked against reference metrics. The Urban slicer check returned 289305 respondents and a 16.11% intent rate.
- Dashboard redesign: 29 measures, three visible pages and one hidden tooltip page. Recorded report validation returned zero errors/warnings; committed Desktop captures cover all three visible pages. Read-only DAX evidence covers narrative metrics and selected filter cases; see [verification scope](report_redesign_verification.md).
- Orchestration: publication follows quality validation; retries verify source, code and artifact integrity before reusing completed stages.
- Databricks: all eight Gold tables reconciled with standalone processing, accounting only for permitted run-specific lineage values.
- Delivery: CI runs regression tests and verifies release packaging. Test CD checks model/report binding, refresh and live KPI; rollback tooling preserves the previous definitions.
- Recovery: checksum-verified snapshot restoration has been demonstrated. Data and backup archives are stored separately from source code.

## Verification dates and release scope

| Record | Verified scope | Limits |
| --- | --- | --- |
| [17 October acceptance](portfolio_acceptance.md) | CI #67/CD #70; representative Service slicer/reset/navigation/tooltip/cross-filter cases passed on source `295e26d`. | Not exhaustive interaction coverage or a new UAT of later source changes. |
| [22 October release, inspected 28 October](evidence/release_20261022.json) | CI #84: 118 unit, 8 Spark, 3 Airflow passed, zero skips. CD #85: model/report update, binding, refresh and KPI passed on `48fa1fe`. | This cloud release predates the uncommitted portfolio remediation. |
| [28 October live API probe](evidence/release_20261022.json) | Report binding passed; latest refresh was Completed on 22 October. | Arrow DAX query returned HTTP 401 with the current local identity. Live KPI was not reverified in that probe; this does not invalidate the successful service-connection query in CD #85. |
| [29 October live API probes](evidence/live_health_20261029.json), 07:57 Asia/Bangkok | Local Azure CLI user: JSON binding, latest-refresh status and KPI passed (668665 / 116779 / 551886). | Same cached token: Arrow HTTP 401 remains unresolved. No deployment, new refresh, Service UAT or service-principal revalidation; latest refresh observed by this probe was 22 October. |

The [test suites](../tests/README.md) and [CI configuration](../ci/azure_pipelines.yml)
define the required checks. See the [CI/CD history](cicd_evidence.md) for earlier
runs. Recorded successful builds are evidence for their source commits, not
continuous monitoring or acceptance of subsequent working-tree changes.
The 29 October source identity describes the checked health helpers/config; a
successful KPI query alone does not identify the deployed source commit. Deployment
provenance comes from its selected CI artifact and CD/readback evidence.

## Scope and limitations

- Synthetic data measures stated intent. There are no transactions, revenue, brands, business dates or precise locations; findings are descriptive and non-causal.
- Representative Service navigation/reset, slicer, tooltip and cross-filter cases passed for the 17 October release. Every possible selection, rendering after later source changes and separate SQL analytics endpoint execution remain unverified. Structural validation and API KPI checks do not replace interaction tests.
- Power BI depends on the configured Fabric model. The Databricks pipeline is an alternative implementation, not the report's source.
- Direct source-file comparison with a Kaggle download remains unverified; provenance and hashes identify the acquired snapshot.
- This is a portfolio project, not a production service with agreed uptime, cost limits, automated alerting or completed recipient handoff. An independent backup copy outside the development machine remains unverified.
- Old run IDs cannot be reused after source/code/metadata changes: start a new run. Sealed backups retain their original manifests and layout.
