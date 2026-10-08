# EV Analytics recovery runbook

> Updated 2026-09-29: the recovery drill is complete; see the
> [closeout results](../project_summary.md). Historical statements about work not yet
> performed refer to the original ZIP release. Verify every step for each new
> recovery attempt; historical results are not evidence for a new attempt.

## 1. Scope and status

This runbook restores the exported Gold v2 snapshot without rerunning the pipeline.
Parts 3?4 prepared the package, notebooks/scripts, and procedure. Creating the
workspace, loading tables, deploying and refreshing the model, and publishing the
report belong to **part 5** and had not run at the original package release date.

| Component | Reference value |
| --- | --- |
| Gold run ID | `20260925T152721965637Z` |
| Export ID | `20260927T130004568586Z` |
| Snapshot manifest SHA-256 | `0da1b98e56c024261d247e3cfe94efaddb594cd52cce4eee89f6a8955cf1ad9f` |
| Fact | 668665 rows |
| Dimensions | 45 / 4 / 16 / 2 / 30 rows |
| Audit aggregates | 1 / 35 rows |
| KPI | 668665 / 116779 / 551886 |
| Purchase intent rate | 0.17464500160768098 |
| Semantic model | 6 tables, 5 relationships, 12 measures |
| Report | 3 pages, 57 visuals |

The KPI describe EV purchase intent in synthetic data. The two aggregate tables
are for audit only. Remaining navigation/reset, chart cross-filter, and dashboard
rendering tests stay **skipped by user request**, not passed. Verifying the recovery
report KPI below provides separate evidence for part 5.

## 2. Tools and access

- Python 3.11 or later; the handoff was tested with Python 3.13.
- For local Parquet validation, install `project/requirements/requirements_export.txt`
  (PyArrow 25.0.1, pandas, and numpy).
- An active Fabric capacity for the target workspace and permission to create
  lakehouses, notebooks, semantic models, and reports.
- Read access to all Delta tables in the new lakehouse and Build permission on the
  model for DAX/report checks. Grant read access to the model's fixed identity if used.
- Power BI Desktop with PBIP, TMDL, and Direct Lake support.
- Azure CLI for the item creation helper; sign in as a user with Contributor or higher access.
- Node.js 20+ for PBIR validation after changing report bindings.

The recovery notebook uses PySpark, PyArrow, and pandas from the Fabric runtime.
If a dependency is missing or the runtime cannot read the Parquet schema, stop at
preflight and configure the environment. Keep checksum and schema checks enabled.

## 3. Verify the package

Example ZIP: `EV_Analytics_Recovery_20260925T152721965637Z.zip`.
In PowerShell, before extraction:

```powershell
$recoveryZip = '.\EV_Analytics_Recovery_20260925T152721965637Z.zip'
$expectedHash = ((Get-Content -LiteralPath ($recoveryZip + '.sha256') -Raw).Trim() -split '\s+')[0]
$actualHash = (Get-FileHash -LiteralPath $recoveryZip -Algorithm SHA256).Hash
if ($actualHash -ne $expectedHash) { throw 'ZIP checksum mismatch' }
Expand-Archive -LiteralPath $recoveryZip -DestinationPath '.\recovery_work'
Set-Location '.\recovery_work\EV_Analytics_Recovery'
python verify_package.py .
```

Require `status: passed` and `parquet_tables: 8`. The verifier checks the exact
inventory, so run it before adding local files. Keep the original ZIP and checksum;
you can verify them again with `verify_package.py <zip>`. Checksums detect changed
files but do not replace digital signatures.

To recompute KPI and PK/FK checks locally, create an environment and run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r project/requirements/requirements_export.txt
.\.venv\Scripts\python.exe project/scripts/export_gold_snapshot.py verify --output snapshot
```

Require the reference KPI, `orphan_keys: 0`, and `segment_groups: 35`.

## 4. Create a new workspace and lakehouse

In Fabric:

1. Create `WS_EV_Analytics_Recovery` and assign a suitable capacity.
2. Create `LH_EV_Gold_Recovery`. Use `dbo` if schemas are enabled.
3. Record workspace and lakehouse IDs from their URLs/properties.
4. Load independent physical data; do not use a shortcut to the source lakehouse.

From the package root:

```powershell
Copy-Item recovery.example.json recovery.config.json
```

Fill in the configuration:

| Field | Value |
| --- | --- |
| `workspace_id` | New workspace GUID |
| `workspace_name` | New workspace name; default `WS_EV_Analytics_Recovery` |
| `lakehouse_id` | New lakehouse GUID |
| `lakehouse_name` | New lakehouse name |
| `lakehouse_schema` | `dbo` with schemas enabled; empty string for a legacy lakehouse |
| `semantic_model_name` | `SM_EV_Analytics_Recovery` |
| `semantic_model_id` | Keep `null` until model creation succeeds |
| `report_name` | `RPT_EV_Analytics_Recovery` |
| `gold_run_id`, `snapshot_manifest_sha256` | Keep unchanged |
| `snapshot_relative_path` | Keep `Files/recovery/snapshot` |

Helper names use letters, digits, and underscores. The script rejects source IDs
and requires a different workspace. Configuration contains no tokens or passwords.

## 5. Upload the snapshot and recovery code

Use Lakehouse explorer or OneLake File Explorer to upload into the new lakehouse:

```text
LH_EV_Gold_Recovery/Files/recovery/
??? recovery.config.json
??? snapshot/
?   ??? manifest.json
?   ??? manifest.sha256
?   ??? parquet/                  # 8 .parquet files
?   ??? evidence/                 # preserve all export evidence
??? scripts/
    ??? recovery_common.py
    ??? fabric_restore_gold.py
    ??? export_gold_snapshot.py
    ??? star_schema.py
```

Take the scripts from `project/scripts/`. Avoid an extra `snapshot/snapshot/`
level; the manifest must be directly under `Files/recovery/snapshot`.

Import `project/notebooks/NB_EV_Restore_Gold.ipynb` as a new notebook in the recovery
workspace. Attach the **new lakehouse as default** and start a fresh session after
changing it. The notebook has no source lakehouse binding. It checks
`currentWorkspaceId`, `defaultLakehouseWorkspaceId`, and `defaultLakehouseId` before writing.
[Runtime context documentation](https://learn.microsoft.com/en-us/fabric/data-engineering/notebookutils/notebookutils-runtime).

## 6. Load Parquet into Delta

1. Keep `MODE = "preflight"` and run the notebook.
2. Require `preflight_passed_no_tables_written`. This checks checksums, Parquet
   KPI/PK/FK, Spark schemas, and the absence of destination tables.
3. Change to `MODE = "restore"` and run again.
4. Require `data_restored_and_verified` and all eight `verified_tables`.

The notebook preserves snapshot-suffixed table names and original Gold/Silver
lineage. It writes Delta, reads every table through the catalog, and compares both
directions with `exceptAll`. Fabric supports loading files with Spark and `saveAsTable`.
[Data loading guide](https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-notebook-load-data).

Evidence is saved to:

```text
Files/recovery/results/restore_data_<recovery_run_id>.json
```

Download it to local `results/`. A passing data restore does not mark model refresh,
report publication, or the overall recovery complete. The output can therefore
contain `isolated_recovery_complete: false` after a successful data restore.

## 7. Prepare and create the semantic model

Run from the package root:

```powershell
python project/scripts/prepare_recovery.py model --config recovery.config.json --snapshot snapshot --output generated/model
```

The script creates:

- `generated/model/SM_EV_Analytics_Recovery.SemanticModel/`.
- `create_semantic_model.json`: request body containing Base64 TMDL parts.
- `recovery_gold_checks.sql`: Gold-only SQL for the recovery lakehouse.
- `prepared.json`: endpoint and **prepared_not_deployed** status.

The copy uses the target OneLake URL, the appropriate `schemaName`, and a new
logical ID; the source database ID is removed when present. All six entity names
point to the restored snapshot. Measures, relationships, formats, and sort columns
are preserved.

To create the model through the API:

```powershell
az login --tenant <TENANT_ID> --allow-no-subscriptions
python project/scripts/create_recovery_item.py model --config recovery.config.json --prepared generated/model --result results/model_created.json
```

The helper holds the Azure CLI token in memory, calls `POST /semanticModels`, polls
an operation for HTTP 202, and saves the ID to `results/model_created.json`. The
updated helper uses `x-ms-operation-id` to poll the public endpoint when Location
is regional. TMDL is supported by the semantic model API. The caller needs suitable
permissions and `SemanticModel.ReadWrite.All` or `Item.ReadWrite.All` scope.
[Create semantic model](https://learn.microsoft.com/en-us/rest/api/fabric/semanticmodel/items/create-semantic-model),
[TMDL definition](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/semantic-model-definition).

Copy the returned `item.id` into `semantic_model_id` in `recovery.config.json`.
The helper creates new items only; it does not update or delete existing items.
If a name already exists or the request times out, inspect the result and workspace
before retrying.

## 8. Configure the connection and refresh

In the recovery workspace:

1. Open settings for `SM_EV_Analytics_Recovery`.
2. Configure the gateway/cloud connection or OneLake identity as appropriate for the tenant.
3. Verify the connection targets the new workspace/lakehouse and the executing
   identity has read access.
4. Run **Refresh now**, wait for success, and save refresh evidence.
5. Verify six tables, five active many-to-one relationships filtering from dimensions
   to fact, and 12 measures. Keep the two audit aggregates outside the model.

Direct Lake uses Delta tables and a model hosted on Fabric. Opening the source
PBIP report does not create an independent model. You can live-edit the recovery
model in Power BI Desktop to inspect expressions and partitions.
[Direct Lake in Desktop](https://learn.microsoft.com/en-us/fabric/fundamentals/direct-lake-power-bi-desktop).

Run this against the **recovery model** in a connected DAX query view:

```dax
EVALUATE
ROW(
    "respondent_count", [Respondents],
    "yes_count", [Intending to Buy EV],
    "no_count", [Not Intending to Buy EV],
    "purchase_intent_rate", [Purchase Intent Rate]
)
```

Require 668665 / 116779 / 551886 and rate 0.17464500160768098. Save fresh DAX
results. Additional queries in `project/tests/semantic_model_validation.dax`
check 35 groups and combined filters.

`generated/model/recovery_gold_checks.sql` is an optional SQL endpoint check.
The earlier skipped SQL endpoint test retains its status. Do not run source SQL
that compares against `LH_EV_Silver` when the recovery environment contains Gold only.

## 9. Prepare and publish the report

After a successful model refresh and updating the model ID in configuration:

```powershell
python project/scripts/prepare_recovery.py report --config recovery.config.json --output generated/report
npx --yes @microsoft/powerbi-report-authoring-cli@0.4.0 validate generated/report/RPT_EV_Analytics_Recovery.Report --out results/report_validation.json
```

The script updates `definition.pbir` to the new model, generates a new logical ID,
and preserves visuals and resources. CLI validation does not verify live model
access or data. PBIR uses `byConnection` to reference the Service model.
[PBIR structure](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report).

Choose one publication method:

**Power BI Desktop:** open `generated/report/RPT_EV_Analytics_Recovery.pbip`, sign in,
verify the recovery model connection, and publish to `WS_EV_Analytics_Recovery`.

**API:**

```powershell
python project/scripts/create_recovery_item.py report --config recovery.config.json --prepared generated/report --result results/report_created.json
```

The request includes PBIR and resources. The API requires report creation permission
and `Report.ReadWrite.All` or `Item.ReadWrite.All` scope.
[Create report](https://learn.microsoft.com/en-us/rest/api/fabric/report/items/create-report).

Open the new report, clear filters, compare **668,665 / 116,779 / 551,886**, and
save the URL and KPI screenshot. Source workspace screenshots or DAX results are
not evidence of recovery.

## 10. Record part 5 results

Copy `project/config/recovery_verification.example.json` to
`results/recovery_verification.json`; fill in actual IDs and evidence links.
Mark overall recovery `passed` only when:

- Package/snapshot checksums match; eight Delta tables have correct schemas/counts and valid PK/FK.
- Delta data matches Parquet and is stored physically in the new lakehouse.
- The model uses the new lakehouse, refresh succeeds, and DAX returns the three expected KPI.
- The published report uses the new model and displays matching KPI.
- Workspace, lakehouse, model, and report IDs are recorded.

Keep skipped dashboard tests as `skipped_by_user_request`. Payload preparation,
unit tests, or checksum verification alone do not prove recovery succeeded.
Distinguish user-attested checks from checks directly verified by a tool.

## 11. Troubleshooting and reruns

| Issue | Action |
| --- | --- |
| Hash mismatch or missing file | Retrieve the correct ZIP/snapshot and verify it before loading |
| Wrong notebook context | Attach the recovery lakehouse as default and start a new session |
| Destination tables already exist | The script stops before writing. Inspect tables and prior logs; use a new recovery lakehouse or deliberately clean test tables after checking the target |
| Partial write followed by failure | Inspect `written_tables`/`verified_tables`; do not append or overwrite to hide the error. Fix the cause and retry on a clean target |
| Schema/decimal/timestamp error | Check runtime, `lakehouse_schema`, and UTC timezone; preserve the manifest schema |
| API 401/403 | Sign in to the correct tenant and check license, workspace role, and API scope |
| API 202 pending or timeout | Poll the saved `operation_url` and `/result`; do not repeat the creation POST while its outcome is unknown |
| Model refresh permission error | Check connection identity and read access to the target OneLake data |
| Report still uses source | Inspect `generated/report/.../definition.pbir` and model ID; prepare again in a new output directory |
| Incorrect KPI | Stop acceptance and inspect filters, snapshot, six partitions, and relationships |

Writes target the recovery workspace; source data remains unchanged. Keep logs
and the ZIP when stopping an attempt. Deleting the test workspace is a separate
operation and is not part of the packaging script or notebook.

## 12. Checks performed during parts 3?4

- Offline target configuration, model/report generation with test IDs, and package integrity.
- All 57 visuals remained byte-identical after changing report bindings.
- PBIR: **zero errors, one warning** because Microsoft `visualContainer/2.12.0`
  could not be downloaded. Its schema version was not changed to hide the warning.
  Evidence: `project/metadata/recovery_report_preflight.json`.
- Notebook syntax was checked; Spark recovery had not run at the original package release.
- API creation, refresh, and report publication had not run at that release date.
  Subsequent live results are in the closeout document.

Additional references: [Fabric API authentication](https://learn.microsoft.com/en-us/rest/api/fabric/articles/get-started/fabric-api-quickstart),
[Long-running operations](https://learn.microsoft.com/en-us/rest/api/fabric/articles/long-running-operation).
