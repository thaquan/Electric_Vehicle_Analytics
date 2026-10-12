# Regression and integration CI

`ci/azure_pipelines.yml` requires three independent test jobs. `Package` depends on
all three and preserves the existing `ev-test-release` and `ev-source` artifact
names consumed by Test CD. There is no optional integration flag or
`continueOnError` path.

| Job | Runtime | What actually executes |
| --- | --- | --- |
| Unit | Ubuntu 24.04, Python 3.13, dev requirements + existing constraints | Every top-level `test_*.py` except the two integration modules; validation, entrypoint lifecycle, export, release and reporting regressions. |
| Spark | Ubuntu 24.04, Python 3.11, Java 17, PySpark 3.5.9 | Real local Spark/Parquet corruption checks and the complete pipeline using synthetic inputs. |
| Airflow | Airflow slim 2.10.5 / Python 3.11 image, Java 17, PySpark 3.5.9 | Migrates a disposable SQLite DB, renders the real DAG, executes all six BashOperator tasks, and verifies that corrupt input blocks publication. |

Synthetic fixtures create four CSVs and matching metadata in temporary folders.
No Kaggle download, cloud identity, Fabric workspace or committed raw data is needed.
Expected Gold counts are specified independently of the transformation code.
The Airflow test appends temporary input/output paths to the production DAG's
commands; transformations, quality checks and publication are not mocked.
Retries are disabled only in the test instance so intentional failure finishes quickly.

## Results and gates

Run `python scripts/run_ci_tests.py --suite unit|spark|airflow` from the repository
root (choose one suite). Results go to ignored `test-results/<suite>.xml` and
`<suite>.json`; use `--output` to select another evidence folder.

- **Pass:** test body and lifecycle complete successfully.
- **Fail/error:** assertion, import, setup/teardown or runtime error; exit 1.
- **Skip:** unavailable runtime or explicit skip, recorded with its reason;
  exit 1 in required CI, even if unittest prints `OK (skipped=...)`.
- **Empty suite:** synthetic discovery error and exit 1.
- **Infrastructure failure before discovery:** job fails; missing JUnit is also
  rejected by `PublishTestResults@2`, never represented as a test pass.

`--allow-skips` is only for local inspection. It preserves skip counts and reasons;
it cannot permit failures or empty suites. Expected failures are recorded as skips;
unexpected successes fail. Reporter regressions cover these gate boundaries,
including failed subtests.

JUnit is published to the Azure Tests tab and XML/JSON are retained as separate
`test-results-unit`, `test-results-spark`, and `test-results-airflow` artifacts,
including failed runs. Source/release artifacts are withheld if any required job
fails, is cancelled or is skipped.

## Run Airflow locally on Linux

Docker must be running. Use a fresh container for each run so the metadata DB is
isolated. These commands match CI:

The slim image avoids unused Google/Snowflake providers from the full Airflow
image, whose pandas constraints conflict with this pipeline's pandas 2.3.3.
The Docker build and test run both require `pip check` to succeed.

```bash
docker build -t ev-airflow-ci docker/phase10_airflow
mkdir -p test-results
chmod a+w test-results
docker run --rm --entrypoint /bin/bash \
  -v "$PWD:/workspace" -w /workspace \
  -e AIRFLOW_HOME=/tmp/airflow-ci \
  -e AIRFLOW__CORE__LOAD_EXAMPLES=False \
  -e AIRFLOW__CORE__EXECUTOR=SequentialExecutor \
  -e AIRFLOW__CORE__DAGS_FOLDER=/workspace/dags \
  -e EV_PROJECT_ROOT=/workspace \
  -e SPARK_LOCAL_IP=127.0.0.1 \
  -e 'SPARK_MASTER=local[2]' -e SPARK_SHUFFLE_PARTITIONS=2 \
  ev-airflow-ci -euo pipefail -c \
  'export PYSPARK_PYTHON="$(command -v python)"; python -m pip check; airflow db migrate; python scripts/run_ci_tests.py --suite airflow'
```

Airflow uses [`dag.test()`](https://airflow.apache.org/docs/apache-airflow/2.10.5/core-concepts/debug.html)
with real task execution. This verifies DAG dependencies and Bash commands, but
does not establish production scheduler/executor, external service or cloud health.
JUnit publication follows Microsoft's
[`PublishTestResults@2` contract](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/publish-test-results-v2?view=azure-pipelines).

## Trigger and acceptance boundary

Pushes to `main` and `feature/*` trigger CI. For Azure Repos, configure a **required
Build validation branch policy** on `main` using `EV-Analytics-CI`; YAML `pr` is used
by supported GitHub/Bitbucket connections, not Azure Repos branch policies.
Local results do not prove that this policy or the hosted CI has run. Acceptance
requires a hosted run with all three test jobs and `Package` successful, JUnit
counts showing zero required skips, and the resulting artifact/build IDs.
