# Automated tests

These are reusable regression tests for the project, not local test logs or agent work files. CI selects its suites explicitly in `ci/azure_pipelines.yml`.

- Data rules: Bronze/Silver typing, categories, target leakage, Gold metrics and star-schema keys.
- Orchestration: stage dependencies, input integrity, retry behavior and publication gates.
- Delivery: API/DAX errors, release manifests, target binding and rollback packaging.
- Recovery: archive integrity and unsafe path rejection using temporary fixtures.
- Integration: real Spark Parquet checks and Airflow template rendering, enabled only in their required runtimes.

```bash
python -m pip install -r requirements.txt -r requirements/requirements_cd.txt -r requirements/requirements_export.txt -r requirements/requirements_phase10.txt -r requirements/requirements_phase11.txt
python -m unittest discover -s tests -v
```

Six Spark tests require `EV_RUN_SPARK_TESTS=1` and Java/Spark setup. One Airflow test requires Linux with Airflow installed. Skips are reported separately from passes; see the [runtime guide](../docs/pipelines/standalone_pipeline.md).

Machine-specific snapshot rehearsals are kept locally, outside this suite. Test reports, coverage, browser traces, downloaded data and temporary fixtures must not be committed. The `Test` name in deployment helpers refers to the cloud deployment environment, not disposable local experiments.
