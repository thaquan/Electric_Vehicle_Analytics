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

Foundation, Bronze, Silver and the original Gold v1 are complete. E2E pipeline run
`17d02413-970d-4220-b110-cf05484ff3bb` completed successfully; its final audit
was verified directly on OneLake. Its Gold run `20260925T080132680916Z` is a
legacy wide-table snapshot, not the new star schema.

Gold v2 now builds one fact, five dimensions and two audit aggregates. Full
local reconstruction and SQL reconciliation pass for all 668665 train rows;
Fabric deployment and a new E2E run are pending.
The semantic model definition is authored and locally reloaded successfully
(6 tables, 5 relationships, 12 measures). It deliberately uses `pending_star_v2`
source names until a verified v2 audit is available; do not deploy it yet.
See [Star Schema design and rollout](docs/star_schema.md).
See [semantic model instructions](docs/semantic_model.md).

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
