# Gold: EV purchase-intent analytics

## Gold v2 update

Gold v2 is now verified on Fabric: E2E run
`78f9cdfe-1e19-4624-bede-042310ec9bb9`, Gold run `20260925T152721965637Z`.
All 8 tables, exact Silver reconstruction, zero orphan keys and 35-group Spark
SQL reconciliation passed. See `metadata/e2e_star_verified_run.json` and
[Star Schema design](../architecture/star_schema.md). Semantic Model is deployed/refreshed and live DAX matches the verified Gold.
Separate SQL analytics endpoint execution remains pending.
The older executions below remain historical reference.

## Current status

- `WS_EV_Analytics`: `5fe78794-25c3-41ee-b35e-bc56542d2cea`.
- `LH_EV_Gold` created: `32e99e91-38e9-4428-8fd2-6bcff6573088`.
- Silver success marker and quality report downloaded from OneLake into
  `metadata/silver_published_run.json` and `metadata/silver_fabric_quality_report.json`.
- Gold run `20260924T131322687853Z` published successfully; its OneLake marker
  is saved as `metadata/gold_published_run.json`.
- The updated notebook supports the E2E pipeline. See [pipeline instructions](pipeline_runbook.md).

## Input and scope

For a manual run with no override, the notebook pins Silver run `20260924T031507399976Z`, table
`silver_train_20260924t031507399976z`, Delta version **0**. The verified physical
path is `LH_EV_Silver/Tables/silver_train_20260924t031507399976z` (no `dbo`
folder). It checks the source publication marker, row counts, unique IDs,
source checksum lineage and exact Yes/No-to-flag mapping before writing Gold.
In pipeline mode, `silver_run_id` must be supplied from `Build_Silver`; source
table and path are derived from that run, and its marker must belong to the
same pipeline execution. The historical run is never a pipeline fallback.

Only labeled competition **train** enters Gold. Test is unlabeled;
original_reference is a separate population and must not inflate train KPIs.
The outcome is **purchase intent**, not realized vehicle sales or revenue.
These synthetic observations do not establish causal effects.

## Output tables

Each run appends its unique run ID to these table prefixes:

| Prefix | Grain | Expected rows |
| --- | --- | ---: |
| `fact_ev_purchase_intent` | One train respondent, numeric observations, target, lineage and five dimension keys | 668,665 |
| `dim_demographics` | Age band, gender, city type | 45 |
| `dim_income` | Income band | 4 |
| `dim_mobility` | Commute band, current car type | 16 |
| `dim_charging` | Home charging availability | 2 |
| `dim_attitude_incentive` | Environmental concern, subsidy, range anxiety | 30 |
| `agg_ev_kpi` | One overall train snapshot | 1 |
| `agg_ev_segments` | One dimension/value pair | 35 |

KPI columns are `respondent_count`, `yes_count`, `no_count`, and
`purchase_intent_rate = yes_count / respondent_count` (0 to 1, formatted as a
percentage in Power BI). Expected totals: **668,665 / 116,779 / 551,886**;
purchase-intent rate **17.464500160768098%**.

Each of the 10 segment dimensions reconciles separately to the train totals.
Never sum across `segment_dimension`: each respondent appears once per
dimension, so summing all segment rows would multiply totals by 10. Use the
fact table for interactive multi-dimension filters; the segment summary is
for single-dimension summaries and reconciliation, not a join to the fact.
Do not average subgroup percentages; recompute `SUM(yes_count) / SUM(respondent_count)`
within one dimension, or compute counts directly from the filtered fact table.

Bands are descriptive choices, recorded in `metadata/gold_spec.json`:

| Attribute | Band boundaries |
| --- | --- |
| Age | <35; 35-44; 45-54; 55-64; >=65 |
| Annual income (USD) | <50,000; 50,000-<75,000; 75,000-<100,000; >=100,000 |
| Daily commute (km) | <10; 10-<25; 25-<50; >=50 |

The other dimensions are Gender, City_Type, Current_Car_Type,
Home_Charging_Possible, Subsidy_Available, Range_Anxiety_Level and
Environmental_Concern_Level. Environmental concern remains its original
categorical string, including values such as `1.0`; no new scale is inferred.

## Run in Fabric

1. Open `WS_EV_Analytics` > Source control. Commit the new `LH_EV_Gold`
   item if it appears in Changes, preserving its existing item ID.
2. Select **Update from Git** to load `NB_EV_Silver_To_Gold`.
3. Open the notebook. Attach/pin **LH_EV_Gold** as default Lakehouse; if you
   change the default in an existing Spark session, restart the session.
4. **Run all**. No separate helper-module or metadata upload is needed: all
   code, configuration and expected aggregates are embedded in the notebook.
5. Confirm `status: published`, matching counts, and all output table
   names (8 tables in v2). Save the output for the Power BI semantic-model step.
6. The authoritative completion marker is
   `LH_EV_Gold/Files/quality/<gold_run_id>_published.json`.

The first execution check stops on the wrong or missing default Lakehouse.
The notebook also tests band boundaries on Spark, checks all 35 segment
counts against the local reference, and verifies data read back from Delta.
It never replaces existing output tables. A failed run may leave partial
tables; use only table sets referenced by a final success marker. Transactions
are per table, so there is no claim of a single transaction across all tables.

## Maintain and validate

```powershell
python scripts/profile_gold.py
python scripts/profile_star.py
python -m unittest discover -s tests -v
python scripts/build_gold_notebook.py
```

Edit `scripts/fabric_gold.py`, `scripts/gold_rules.py`, or the spec, then rebuild.
The builder produces both `NB_EV_Silver_To_Gold.Notebook/` for Fabric Git and
`notebooks/NB_EV_Silver_To_Gold.ipynb` for manual import. Preserve the `.platform`
logical ID. Commit/push every completed change set to Azure DevOps.

Local tests exercise threshold boundaries, SQL CASE equivalence using SQLite,
wrong-Lakehouse rejection and reference-total reconciliation. They are not
a substitute for a successful Fabric Spark run; those checks also execute
inside the notebook. The reference script reads the pinned raw train snapshot,
verifies its SHA-256, and writes only aggregate metadata into Git.

Runtime-context reference: [Microsoft NotebookUtils runtime context](https://learn.microsoft.com/en-us/fabric/data-engineering/notebookutils/notebookutils-runtime).
