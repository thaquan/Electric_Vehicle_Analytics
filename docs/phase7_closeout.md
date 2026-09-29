# Phase 7 ? Handoff results

Closeout date: 2026-09-29. Phase 8 has not started.

## Results

| Item | Result and evidence |
| --- | --- |
| Export | 8 Parquet files, Gold run `20260925T152721965637Z`; `metadata/gold_export_manifest.json` |
| Transfer | 29/29 downloaded files match their SHA-256; `metadata/recovery_upload_verification.json` |
| Restore | 8/8 Delta tables match Parquet; `metadata/restore_data_20260929T012932575742Z.json` |
| Model | 6 Ready partitions, 6 tables, 5 relationships, 12 measures; `metadata/recovery_model_dax_verification.json` |
| DAX KPI | 668665 / 116779 / 551886; rate 0.17464500160768098 |
| Report | Service API confirmed the report and target model; `metadata/recovery_report_service_verification.json` |
| Report KPI | The user confirmed all checks were complete. No screenshot was supplied; this is not automated visual verification. |

Recovery workspace: `d9e8b78a-5c35-4267-b558-1780029a951c`.
Lakehouse: `48ebc295-3cc7-4f2e-bdcd-c6e15260d9ac`.
Model: `a0835af9-0dde-42d8-ab16-8439d3a63f09`.

[Open the recovery report](https://app.powerbi.com/groups/d9e8b78a-5c35-4267-b558-1780029a951c/reports/61e38b4a-e9a1-4a0f-9411-112d86c18eb2).

The pipeline was not rerun for recovery. The recovery workspace does not need Git integration.
The remaining navigation/reset, chart cross-filter, and Service rendering checks remain
`skipped_by_user_request`; they are not marked as passed.

## Package used for the recovery drill

- ZIP: `output/releases/20260927T152509Z/EV_Analytics_Recovery_20260925T152721965637Z.zip`.
- ZIP SHA-256: `f0afddb74d18cc094419de05f8941ac1279a7aed3dda90f9c70fcabfbaa44070`.
- Manifest SHA-256: `0da1b98e56c024261d247e3cfe94efaddb594cd52cce4eee89f6a8955cf1ad9f`.
- Source OneLake snapshot: `Files/exports/gold_v2/20260925T152721965637Z/20260927T130004568586Z`.
- Copy in the recovery lakehouse: `Files/recovery/snapshot`.

Keep the original ZIP unchanged. Its `not_started` statuses describe its release on
2026-09-27. Current acceptance results are recorded in the repository.
Parquet files, ZIP archives, and source data are excluded from Git.

## Issues addressed

1. Model creation returned HTTP 202 with a regional Location. The original helper
   accepted only `api.fabric.microsoft.com`, so it stopped after the server accepted
   the request. The fix uses `x-ms-operation-id` to build a polling URL on the public
   endpoint and saves the accepted response identifiers before validating the URL.
   Do not repeat POST while the creation result is unknown.
2. Fabric Git can export a database definition without a name or ID. The preparation
   helper supports both this format and local exports with a database name and ID.
3. The UI reported that an expression source was marked for deletion. A direct
   MCP/XMLA refresh succeeded, all six partitions became Ready, and DAX matched
   without changing the model. The UI editing error's root cause remains unconfirmed;
   this is not evidence of a fix to the Fabric product.

## Starting from the repository on another machine

The repository does not contain the data snapshot. To run all recovery tests,
retrieve the backup, verify its checksum, and extract the snapshot to the location
in the runbook. `tests/test_recovery_package.py` uses that location or the `snapshot/`
folder next to `project/` in an extracted package. A missing snapshot on a fresh
clone does not indicate a failed recovery.

See the [recovery runbook](recovery_runbook.md) and [export guide](gold_export.md).

## Updated handoff package

The archive `output/releases/20260929_phase7_closeout/EV_Analytics_Recovery_20260925T152721965637Z.zip`
contains the corrected helper and closeout evidence. SHA-256:
`a595f3c0cfd3eff7c91c2ce7e2b61257a4fbd73e974879012912ef107d7b78b5`.
The 230-file inventory and 10 recovery tests in the extracted package passed;
the complete project suite passed 41 tests. This revised package was not used for
a second Spark recovery drill. Its `release.json` values of `not_started` apply
to a new recovery attempt; historical results are in `recovery_verification.json`.
