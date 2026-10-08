# Phase 7 ? Parquet export and manifest

## Scope

Parts 1?2 export the verified Gold v2 snapshot `20260925T152721965637Z`.
The export did not rerun the pipeline or transformation notebooks, refresh the model,
or modify source tables. Parts 3?4 cover packaging and the recovery procedure;
see the [recovery runbook](../recovery/recovery_runbook.md) and
`metadata/gold_recovery_package_status.json`. Isolated recovery had not run at the
export date; subsequent results are in the [project acceptance summary](../project_summary.md).
Remaining dashboard checks stay **skipped by user request**, not passed.

## Export details

- Export ID: `20260927T130004568586Z`.
- Source workspace: `5fe78794-25c3-41ee-b35e-bc56542d2cea`.
- Source lakehouse: `32e99e91-38e9-4428-8fd2-6bcff6573088` (`LH_EV_Gold`).
- Local: `output/exports/gold_v2/20260925T152721965637Z/20260927T130004568586Z/`.
- OneLake: `Files/exports/gold_v2/20260925T152721965637Z/20260927T130004568586Z/`.
- Transfer status and evidence: `metadata/gold_export_status.json`.
- Verified source: `metadata/e2e_star_verified_run.json`; do not use the stale Gold v1 marker.

| Table | Rows |
| --- | ---: |
| fact_ev_purchase_intent | 668665 |
| dim_demographics | 45 |
| dim_income | 4 |
| dim_mobility | 16 |
| dim_charging | 2 |
| dim_attitude_incentive | 30 |
| agg_ev_kpi | 1 |
| agg_ev_segments | 35 |

## Export method

1. Download Delta version 0 logs for the eight exact tables through the Fabric OneLake connector.
2. Read each log's `add` actions. Download only active data files for this version;
   do not scan the entire directory or include statistics in `_delta_log/_stats`.
3. Require reader protocol v1, no partitions, column mapping, deletion vectors,
   or remove actions. The script stops if these conditions change.
4. Download 49 source files (14,311,522 bytes), recording ETags, sizes, request IDs, and checksums.
5. Read and serialize with PyArrow into eight Snappy Parquet files totaling 11,721,983 bytes.
   Preserve `decimal(18,4)` and store timestamps as UTC microseconds.
6. Compare exact data before and after writing; verify schema, counts, lineage,
   PK/FK, dimension SHA-256 keys, band ordering, KPI, and 35 audit groups.
7. Finalize the manifest only after every check passes. Download the OneLake copy
   and compare its SHA-256 with the local copy before marking the transfer verified.

This export preserves verified snapshot data rather than the full Delta history.
To recover a Direct Lake model, load the Parquet files into Delta tables in the new lakehouse.

## Manifest contents

`manifest.json` records Gold/Silver/pipeline run IDs, source identifiers, Delta version,
column schemas, row counts, file SHA-256 values, source checksums and ETags,
primary keys, five many-to-one relationships with dimension-to-fact filtering,
validation results, and evidence file checksums.

`manifest.sha256` verifies manifest integrity; it is not a digital signature.
Source evidence and reconciliation settings are retained in `evidence/`.
The two aggregate tables are for audit only and are not added to the semantic model.

## Verify on another machine

Keep the export directory and the `export_gold_snapshot.py` and `star_schema.py`
scripts. From the project directory:

```powershell
python -m pip install -r requirements/requirements_export.txt
python scripts/export_gold_snapshot.py verify --output <export-directory>
```

The verifier checks the manifest, checksums, and schemas, then recomputes KPI and
keys from Parquet. No Fabric access is needed to verify a downloaded export.

To retrieve source files and build a new export with the connector:

```powershell
python scripts/export_gold_snapshot.py plan --staging output/gold_export_staging
# Use the connector to download the exact download_plan.json files and save receipts.
python scripts/export_gold_snapshot.py build --staging output/gold_export_staging --output <new-export-directory>
```

`build` refuses to overwrite an existing export directory. The local PyArrow runtime
used for this export is in `.tools/parquet-runtime`, outside the exported data.

## Acceptance scope

Parquet KPI: **668665 / 116779 / 551886**, rate `0.17464500160768098`.
There are zero orphan foreign keys; all 35 audit groups match the fact joined to dimensions.
These checks establish export and transfer integrity. Evidence of semantic model
and report recovery is recorded separately in the closeout.

References: [Delta protocol](https://github.com/delta-io/delta/blob/master/PROTOCOL.md),
[Apache Arrow Parquet](https://arrow.apache.org/docs/python/parquet.html).
