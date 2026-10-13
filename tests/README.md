# Automated tests

These are reusable regression tests for the project, not local test logs or agent work files. CI discovers unit tests automatically and requires separate Spark and Airflow jobs in `ci/azure_pipelines.yml`.

- Data rules: Bronze/Silver typing, categories, target leakage, Gold metrics and star-schema keys.
- Orchestration: stage dependencies, input integrity, retry behavior and publication gates.
- Delivery: API/DAX errors, release manifests, target binding and rollback packaging. The measure guard requires all 12 core names while allowing additional dashboard measures; tests reject missing/replaced core names even when the total count is unchanged.
- Recovery: archive integrity and unsafe path rejection using temporary fixtures.
- Integration: real Spark Parquet checks and Airflow template rendering, enabled only in their required runtimes.

Create an isolated Python 3.13 environment from the repository root. The combined
requirements include local Spark, Arrow (DAX/export), and DuckDB. Java is not needed
for the default suite because real Spark tests are opt-in.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements/requirements_dev.txt -c requirements/constraints-local-py313.txt
.venv/Scripts/python.exe -m pip check
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

On Linux use `.venv/bin/python` instead of `.venv/Scripts/python.exe`.
See the [runtime matrix](../requirements/README.md) for separate cloud/runtime environments.

Eight Spark tests require `EV_RUN_SPARK_TESTS=1` and Java/Spark setup. They cover
Gold corruption, cached/uncached equivalence, and a complete synthetic CSV -> Bronze
-> Silver -> Gold -> quality -> publish run, including decimal precision, preserved
nulls, target leakage and rejection of modified published artifacts. Three Airflow
tests require Linux with Airflow installed: shell-substitution rejection, actual
six-task DAG execution, and failed input blocking downstream publication.

The shared runner writes JUnit XML and JSON with separate pass/fail/error/skip counts:

```powershell
.venv/Scripts/python.exe scripts/run_ci_tests.py --suite unit
# After configuring Java/Hadoop with scripts/phase10_env.ps1:
$env:EV_RUN_SPARK_TESTS = '1'
$env:SPARK_MASTER = 'local[2]'
$env:SPARK_SHUFFLE_PARTITIONS = '2'
.venv/Scripts/python.exe scripts/run_ci_tests.py --suite spark
# Local inventory only: explicitly permit unavailable integration runtimes.
.venv/Scripts/python.exe scripts/run_ci_tests.py --suite all --allow-skips
```

Without `--allow-skips`, any skip makes the process exit nonzero. Import errors,
test failures and empty discovery also fail. Missing runtime is never a pass.
CI never uses `--allow-skips`, publishes results even on failure, and releases
artifacts only after all three jobs succeed. See the [CI guide](../docs/testing_ci.md)
for Airflow commands, runtime boundaries and Azure Repos PR setup.

`test_pipeline_entrypoints.py` checks invalid input rejection before Spark across
CLI/staged/serverless entry points, startup failure reports, preservation of the
original exception during cleanup, platform session ownership, and cache lifecycle.

Machine-specific snapshot rehearsals are kept locally, outside this suite. Test reports, coverage, browser traces, downloaded data and temporary fixtures must not be committed. The `Test` name in deployment helpers refers to the cloud deployment environment, not disposable local experiments.
