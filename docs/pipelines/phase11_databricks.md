# Databricks serverless pipeline

Run these commands from the repository root using an authenticated Databricks
CLI profile with access to the target workspace and Volume.

## 1. Package the source and data

```powershell
python scripts/phase11_package.py --output output/databricks-release/project
```

Choose a new output directory for each release. Use `--raw <csv-directory>`
when inputs are outside `data/raw/kaggle/`. Packaging checks source sizes and
SHA-256 against the manifest before copying files.

Package v2 contains the four source CSVs, six metadata files, three script
modules and nine `src` modules. Local, Airflow and Databricks share processing,
validation and publication logic. `package_manifest.json` identifies the source
and checksum of every packaged file. Keep the package outside Git.

The notebook verifies the package before calling
`execute_pipeline(..., runtime='databricks-serverless')` with the platform Spark
session. This runtime does not cache/unpersist tables, select a local Spark
master or stop the platform session. Input validation requires pandas/numpy and
uses driver memory for the approximately 73 MB CSV snapshot. Import the current
notebook with a v2 package; older overlay packages are rejected.

## 2. Upload and submit

Choose an existing catalog/schema/Volume and a new release name. Replace the
Volume placeholder below before running the commands. The submit template uses
serverless compute and requires workspace support for it.

```powershell
$release = "release_" + (Get-Date -Format "yyyyMMdd_HHmmss")
$volumeRoot = "/Volumes/<catalog>/<schema>/<volume>" # replace with your Volume
$projectRoot = "$volumeRoot/releases/$release/project"
$notebookFolder = "/Shared/ev_analytics/$release"
$notebookPath = "$notebookFolder/phase11_runner"
New-Item -ItemType Directory -Force config/local | Out-Null
$submit = Get-Content config/examples/databricks_submit.json -Raw | ConvertFrom-Json
$submit.tasks[0].notebook_task.notebook_path = $notebookPath
$submit.tasks[0].notebook_task.base_parameters.project_root = $projectRoot
$submitJson = $submit | ConvertTo-Json -Depth 10
[IO.File]::WriteAllText((Join-Path (Get-Location) "config/local/databricks_submit.json"), $submitJson, (New-Object Text.UTF8Encoding($false)))

databricks fs cp output/databricks-release/project "dbfs:$projectRoot" --recursive
databricks workspace mkdirs $notebookFolder
databricks workspace import $notebookPath --file databricks/notebooks/phase11_runner.py --format SOURCE --language PYTHON
databricks jobs submit --json @config/local/databricks_submit.json --no-wait
```

Concrete submission paths stay in ignored `config/local/`. Do not submit the
example with unresolved `<...>` placeholders. Keep existing releases unchanged;
create a new package and notebook whenever code or metadata changes. Upload the
package rather than the entire repository.

`databricks/jobs/phase11_job_serverless.json` is the historical job definition.
This guide submits a separate run and does not update that existing job.

Read the returned run ID:

```powershell
databricks jobs get-run <run_id> --output json
```

Require `state.result_state: SUCCESS`. For a failed task, use its `tasks[].run_id`
with `databricks jobs get-run-output <task_run_id>`. Data runs are written under
`<project_root>/output/phase11/runs/phase11_<UTC timestamp>/`. Check for
`run_report.json` with `status: passed` and `published.json` with
`status: published`. Local tests alone do not establish a successful serverless run.

## 3. Download and reconcile

Use the same `$projectRoot` as the submitted run and replace both placeholders:

```powershell
python -m pip install -r requirements/requirements_phase11.txt
databricks fs cp "dbfs:$projectRoot/output/phase11/runs/<pipeline_run_id>" output/phase11_reconciliation/<pipeline_run_id> --recursive
python scripts/phase11_reconcile.py --reference-gold <verified-local-gold-directory> --candidate-gold output/phase11_reconciliation/<pipeline_run_id>/gold --output output/databricks-reconciliation.json
```

Reconciliation requires all eight Gold tables. It compares column names, types,
order and row counts, then uses `EXCEPT ALL` in both directions to preserve
record multiplicity. It ignores only three run-specific lineage values; their
column names and types are still checked. Reader-inferred Parquet nullability
is not treated as a physical schema contract. Missing tables, schema errors,
read failures or different rows return `status: failed` and exit code 1.
Success returns exit code 0. Downloaded data and results stay in `output/`.
