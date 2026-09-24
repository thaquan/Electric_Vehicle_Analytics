# PL_EV_E2E

## Deployment status

The pipeline definition and notebook updates are prepared in Azure DevOps.
The first pipeline run in Fabric is pending. Prior manual Silver and Gold
runs succeeded; their publication markers have been verified directly in OneLake.

The source-controlled pipeline is `PL_EV_E2E.DataPipeline/pipeline-content.json`.
It is created in Fabric by **Update from Git**, together with the notebook
updates. Do not create a separate empty pipeline with the same name.

## Activity sequence

| Activity | Notebook | Mode | Completion requirement |
| --- | --- | --- | --- |
| Check_Bronze | NB_EV_Bronze_To_Silver | validate_only | Four pinned CSV hashes/headers, schema, counts, keys, categories and target checks pass; no Silver tables written |
| Build_Silver | NB_EV_Bronze_To_Silver | publish | Revalidate input, write three new Delta tables, verify written counts, publish Silver marker |
| Validate_Silver | NB_EV_Silver_To_Gold | verify_silver | Read marker and all three Silver tables at Delta version 0; verify table set, row counts, keys, train target total and test target absence |
| Build_Gold | NB_EV_Silver_To_Gold | publish | Use the just-published Silver run; validate lineage, KPI totals and all segment aggregates; publish three Gold tables |
| Validate_Gold | NB_EV_Silver_To_Gold | verify_gold | Independently read Gold tables; check counts, lineage, fact keys/target, KPI and segment metrics; write final E2E audit |

Every dependency is **Succeeded**, never Completed. Exceptions and missing
output values fail the activity and skip downstream activities. A malformed or
missing marker, stale run, or wrong pipeline correlation also fails validation.

## Run propagation

All activities receive `pipeline_run_id = @pipeline().RunId`.
Silver writes this ID into its publication marker and returns compact JSON via
`notebookutils.notebook.exit()` in a separate final cell.

Gold and both verification steps receive the current Silver run using:

```text
@json(activity('Build_Silver').output.result.exitValue).run_id
```

Validate_Gold receives the current Gold run using:

```text
@json(activity('Build_Gold').output.result.exitValue).run_id
```

Parameter cells are generated as both Fabric `PARAMETERS CELL` sections and
ipynb `parameters` tags. Defaults are never reassigned after runtime injection.
A pipeline invocation without injected correlation or Silver run ID fails
instead of silently using the historical Silver run in the manual-run spec.

Gold constructs `silver_train_<supplied run>` and its physical Delta path
dynamically. It requires the Silver marker to belong to the same pipeline run.
The Gold marker and each Gold table also retain the selected Silver lineage.
This workflow still targets the **pinned CSV snapshot**; changing source files
requires an intentional update to the schema/profiles and reference metrics.

## First run in Fabric

1. Commit any intended local Fabric changes, then **Update from Git** for
   `PL_EV_E2E` and both notebooks. Use the updated notebooks as a set.
2. Verify default Lakehouses: `NB_EV_Bronze_To_Silver` → **LH_EV_Silver**;
   `NB_EV_Silver_To_Gold` → **LH_EV_Gold**. Restart any active sessions if changed.
3. Open **PL_EV_E2E**. Confirm five Notebook activities and validate the pipeline.
   If Fabric asks for a Notebook connection, select your authorized connection
   for this workspace in the activity Settings, save, then commit that binding.
4. Select **Run** once. Inspect the activity Output/Monitor for all five stages.
5. Final activity output must contain `status: verified`, `stage: e2e`,
   the current `pipeline_run_id`, and the new Silver/Gold run IDs.
6. Verify the audit at
   `LH_EV_Gold/Files/pipeline_runs/<pipeline_run_id>.json`.

Only this final audit proves that the entire pipeline completed. Individual
Silver/Gold `published` markers prove only their respective publication stage.

No schedule is configured. Each activity has a one-hour timeout and retry = 0.
After investigating a failure, rerun the **whole pipeline** to obtain a fresh
correlated set. Do not manually retry isolated activities with old run parameters.
Partial tables from a failed run remain available for inspection and are never
selected by a later run or automatically deleted. Consumers use only table sets
from successful publication/audit markers; writes are not atomic across tables.

## Version control and validation

```powershell
python scripts/build_fabric_notebook.py
python scripts/build_gold_notebook.py
python scripts/build_pipeline.py
python -m unittest discover -s tests -v
```

Commit/push each completed change set to Azure DevOps. The pipeline currently
targets the actual existing Notebook IDs in `WS_EV_Analytics`, recorded in
`metadata/fabric_workspace.json`. Recreating notebooks or moving to another
workspace requires updating these IDs and Lakehouse configuration, rebuilding,
and validating again. Do not substitute logical IDs for physical IDs arbitrarily.

Local tests cover missing parameter injection, unsafe run IDs, stale/cross-run
markers, incomplete table sets, wrong Gold parent, success-only dependencies,
dynamic output expressions and generated parameter/exit cells. Fabric Spark
execution and connection binding still require the first real pipeline run.

References: [Fabric pipeline definition](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/datapipeline-definition),
[Notebook activity](https://learn.microsoft.com/en-us/fabric/data-factory/notebook-activity),
[Notebook exit and orchestration](https://learn.microsoft.com/en-us/fabric/data-engineering/notebookutils/notebookutils-notebook-run).
