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
