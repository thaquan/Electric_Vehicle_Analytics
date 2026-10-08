# Validation and limitations

## Implemented checks

- Source files: SHA-256, size, header, types, allowed categories and separation of labeled/unlabeled records.
- Gold: 668665 fact rows, 116779 Yes, 551886 No, five dimensions, zero orphan keys and 35 segment groups. Quality checks reconstruct Gold from Silver and compare schema and row multisets.
- Power BI: 12 measures and combined-filter calculations checked against reference metrics; saved Desktop screenshots cover all three pages. The Urban slicer check returned 289305 respondents and a 16.11% intent rate.
- Orchestration: publication follows quality validation; retries verify source, code and artifact integrity before reusing completed stages.
- Databricks: all eight Gold tables reconciled with standalone processing, accounting only for permitted run-specific lineage values.
- Delivery: CI runs regression tests and verifies release packaging. Test CD checks model/report binding, refresh and live KPI; rollback tooling preserves the previous definitions.
- Recovery: checksum-verified snapshot restoration has been demonstrated. Data and backup archives are stored separately from source code.

The [test suites](../tests/README.md) and [CI configuration](../ci/azure_pipelines.yml) show reproducible checks. Historical successful cloud runs include [CI #30](https://dev.azure.com/thaquan081006/Electric_Vehicle_Analytics/_build/results?buildId=30) and [Test CD #31](https://dev.azure.com/thaquan081006/Electric_Vehicle_Analytics/_build/results?buildId=31). These results describe recorded runs, not continuous service monitoring.

## Scope and limitations

- Synthetic data measures stated intent. There are no transactions, revenue, brands, business dates or precise locations; findings are descriptive and non-causal.
- Full navigation/reset, chart cross-filter and Service rendering acceptance, plus separate SQL endpoint execution, remain unverified. Structural validation and API KPI checks do not replace these tests.
- Power BI depends on the configured Fabric model. The Databricks pipeline is an alternative implementation, not the report's source.
- Direct source-file comparison with a Kaggle download remains unverified; provenance and hashes identify the acquired snapshot.
- This is a portfolio project, not a production service with agreed uptime, cost limits, automated alerting or completed recipient handoff. An independent backup copy outside the development machine remains unverified.
- Old run IDs cannot be reused after source/code/metadata changes: start a new run. Sealed backups retain their original manifests and layout.
