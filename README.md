# Electric Vehicle Analytics

EV purchase analytics in Microsoft Fabric, versioned in Azure DevOps.

| Artifact | Name |
| --- | --- |
| Workspace | WS_EV_Analytics |
| Raw Lakehouse | LH_EV_Bronze |
| Validated Lakehouse | LH_EV_Silver |
| Analytics Lakehouse | LH_EV_Gold |
| Transformation notebook | NB_EV_Bronze_To_Silver |
| Analytics notebook | NB_EV_Silver_To_Gold |
| On-demand pipeline | PL_EV_E2E |

Gold v2 Star Schema is verified on Fabric. E2E run
`78f9cdfe-1e19-4624-bede-042310ec9bb9` produced Gold snapshot
`20260925T152721965637Z`: one fact, five dimensions and two audit aggregates.
All 668665 respondent rows reconstruct Silver exactly, with zero orphan keys;
Spark SQL reconciles KPI and all 35 segment groups.

`SM_EV_Analytics` contains 6 tables, 5 relationships and 12 measures. All source
partitions now target this verified snapshot; their columns match the published
schemas. The model is deployed and fully refreshed on Fabric; all 12 measures, 35
segment groups and 24 combined-filter groups pass live DAX reconciliation.
Separate SQL analytics endpoint execution remains pending. See [semantic model instructions](docs/semantic_model.md) and
[Star Schema design and rollout](docs/star_schema.md).

`RPT_EV_Analytics.pbip` now contains three pages: Executive Overview, Charging & Incentives,
and Customer Profile, bound to the existing `SM_EV_Analytics`. PBIR validation
passes with zero errors and warnings. All three pages render in English with
live data in Desktop; baseline KPI match and screenshots are saved.
[RPT_EV_Analytics is published](https://app.powerbi.com/groups/5fe78794-25c3-41ee-b35e-bc56542d2cea/reports/ae4d7c59-759e-4462-afed-1717475ae012),
confirmed in the Fabric catalog on 2026-09-27. The Urban slicer check passes;
navigation/reset, chart cross-filter and Service rendering checks were skipped at
the user's request, not marked as passed. SQL endpoint execution was also skipped.
Phase 7 parts 1â€“2 have a verified local and OneLake export: eight Parquet tables and a manifest,
with KPI 668665 / 116779 / 551886, zero orphan keys and 35 reconciled segment groups.
See [export instructions and evidence](docs/gold_export.md) and
`metadata/gold_export_status.json` for OneLake transfer verification.
The recovery package includes scripts, notebooks, SQL, TMDL, PBIP and target configuration.
See [the recovery runbook](docs/recovery_runbook.md) and
`metadata/gold_recovery_package_status.json` for the ZIP and verification results.
Isolated Fabric recovery is complete. Eight restored Delta tables match the snapshot;
all six model partitions are Ready and live DAX matches 668665 / 116779 / 551886.
The recovery report exists and its target model binding was verified through the Service API;
the user confirmed the published report KPI checks. No recovery report screenshot was supplied.
See [phase 7 closeout](docs/phase7_closeout.md) and `metadata/recovery_verification.json`.
Phase 8 covers Fabric CI/CD and operations. Automated CI build 14 and CD build 15
succeeded on 2026-10-02; see [automated Test deployment](docs/test_cd.md).
The roadmap accepts the user's update that the remaining phase 8 work is complete;
this documentation update does not re-audit the live services.
See [initial Test deployment evidence](docs/phase8_test_deployment.md) and
[operations runbook](docs/operations_runbook.md) for historical scope and procedures.

Next: [the updated phases 9–12 roadmap](docs/roadmap_phase9_12.md).
Phase 9 backs up source data, Bronze/Silver/Gold, code and configuration outside
Fabric, then restores them in a clean independent environment without reading
OneLake. This independent recovery has not yet been accepted. Phase 10 moves the
full flow to PySpark/Airflow; phase 11 integrates Snowflake or Databricks; phase 12
covers final acceptance and handoff. Phase 7 recovery inside Fabric does not prove
independent recovery, and a downloaded ZIP alone does not complete phase 9.
See [Power BI report status and checks](docs/powerbi_report.md).

Start with [the Bronze/Silver runbook](docs/bronze_silver.md).
Next: [Gold definitions and run instructions](docs/gold_runbook.md).
Run the full flow using [PL_EV_E2E instructions](docs/pipeline_runbook.md).
Source schema and checksums are in `metadata/`; raw/generated data is excluded
from Git. The original reference remains separate from competition train/test.

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/bronze_silver.py --stage-bronze
python scripts/build_fabric_notebook.py
```

The notebook is maintained in `scripts/fabric_silver.py` and generated into both
`NB_EV_Bronze_To_Silver.Notebook/` (Fabric Git) and `notebooks/` (manual import).
Its validation module is `scripts/bronze_silver.py`, deployed to Silver
`Files/code/bronze_silver.py`. Changes to that module must be uploaded to
OneLake as well as pushed to this repository.

This is synthetic competition data. Results describe this dataset, not causal
effects or population-level EV demand.

Live model: [SM_EV_Analytics](https://app.powerbi.com/groups/5fe78794-25c3-41ee-b35e-bc56542d2cea/datasets/8e7e37b7-7bab-4122-84fb-3ae7b2121cd7/details).
The exported live TMDL snapshot is in `models/SM_EV_Analytics/`.
