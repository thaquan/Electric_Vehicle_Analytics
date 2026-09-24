# Electric Vehicle Analytics

EV purchase analytics in Microsoft Fabric, versioned in Azure DevOps.

| Artifact | Name |
| --- | --- |
| Workspace | WS_EV_Analytics |
| Raw Lakehouse | LH_EV_Bronze |
| Validated Lakehouse | LH_EV_Silver |
| Transformation notebook | NB_EV_Bronze_To_Silver |

Foundation profiling and local data-quality checks are complete. Four source
CSVs are uploaded to Bronze. Silver notebook code is ready for the user to
sync from Git and run; successful execution in Fabric is not yet confirmed.

Start with [the Bronze/Silver runbook](docs/bronze_silver.md).
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
