# EV Analytics ? Handoff and recovery package

Gold v2 snapshot: **20260925T152721965637Z**. Expected KPI: **668665 / 116779 / 551886**.

The package contains eight Parquet files and a manifest, notebooks/scripts, SQL,
semantic model TMDL, report PBIP, visual resources, and configuration instructions.
Parts 3?4 prepared the package and procedure. Recovery had not run when the original
ZIP was released; see the repository's `docs/project_summary.md` for subsequent results.
Remaining dashboard tests are **skipped by user request**, not passed.

## Get started

1. Compare the ZIP SHA-256 with its `.zip.sha256` sidecar, then extract the archive.
2. Open a terminal in `EV_Analytics_Recovery` and run:

   ```powershell
   python verify_package.py .
   ```

   Run this before adding configuration, a Python environment, or result files.
   The verifier requires the exact original inventory. You can verify the unchanged
   ZIP at any time:

   ```powershell
   python verify_package.py <zip-path>
   ```

3. Read `project/docs/recovery/recovery_runbook.md` in the extracted package. In the source
   repository, use the [recovery runbook](recovery_runbook.md).
4. For a new recovery attempt, create a workspace/lakehouse, fill in
   `recovery.config.json`, load the snapshot, create the model, refresh it,
   and publish the report in the order described in the runbook.

## Layout

| Path | Contents |
| --- | --- |
| `snapshot/` | Eight Parquet files, manifest, and export evidence |
| `project/` | Original source code and artifacts for comparison |
| `project/notebooks/NB_EV_Restore_Gold.ipynb` | Notebook for the new lakehouse |
| `project/scripts/prepare_recovery.py` | Prepare model/report copies with target bindings |
| `project/scripts/create_recovery_item.py` | Create Fabric items during recovery |
| `recovery.example.json` | Configuration template with empty target IDs |
| `package_manifest.json` | Complete file inventory and SHA-256 values |
| `release.json` | Scope, snapshot, and tool versions |

PBIP/TMDL under `project/` preserve the source environment references. Use the
preparation script to create recovery artifacts under `generated/`, then open
that generated PBIP. Restoring the snapshot does not require rerunning the pipeline
or the Bronze/Silver/Gold transformation notebooks.

## Checks performed before the original release

- Directory and ZIP inventories and file checksums verified.
- Configuration guards and target TMDL/PBIP generation checked with offline test IDs.
- Rebound PBIR: zero errors and one warning for the unavailable Microsoft
  `visualContainer/2.12.0` schema. Visuals were byte-identical; the unavailable
  schema check was not marked as passed.
- Spark restore, model/report creation, refresh, and recovery dashboard checks
  had not run at the original release date.

Source screenshots and DAX evidence already in `project/` belong to the source
environment. Record fresh evidence for each recovery attempt using the runbook template.
