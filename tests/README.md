# Automated tests

These are reusable regression tests for the project, not local test logs or agent work files. CI selects its suites explicitly in `ci/azure_pipelines.yml`.

- Data rules: Bronze/Silver typing, categories, target leakage, Gold metrics and star-schema keys.
- Orchestration: stage dependencies, input integrity, retry behavior and publication gates.
- Delivery: API/DAX errors, release manifests, target binding and rollback packaging.
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

Seven Spark tests require `EV_RUN_SPARK_TESTS=1` and Java/Spark setup, including comparison of cached and uncached shared transformations. One Airflow test requires Linux with Airflow installed. Skips are reported separately from passes; see the [runtime guide](../docs/pipelines/standalone_pipeline.md).

`test_pipeline_entrypoints.py` checks invalid input rejection before Spark across
CLI/staged/serverless entry points, startup failure reports, preservation of the
original exception during cleanup, platform session ownership, and cache lifecycle.

Machine-specific snapshot rehearsals are kept locally, outside this suite. Test reports, coverage, browser traces, downloaded data and temporary fixtures must not be committed. The `Test` name in deployment helpers refers to the cloud deployment environment, not disposable local experiments.
