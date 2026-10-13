# Runtime and dependency setup

Run commands from the repository root. Use a virtual environment, not the system
Python installation. `requirements_dev.txt` combines all local test dependencies;
CD and export both pin PyArrow 25.0.1. The CD file remains self-contained because
release/rollback packages copy it without other requirement files.

| Purpose | Runtime | Requirements | Verification boundary |
| --- | --- | --- | --- |
| Local regression, DAX parsing, export/reconciliation | Python 3.13, Windows x64 | `requirements_dev.txt` + `constraints-local-py313.txt` | No cloud credentials required; real Spark/Airflow tests are opt-in. |
| Standalone Spark pipeline | Same Python environment, Java 17, Spark 3.5.9 | `requirements_phase10.txt` + local constraints | Windows additionally needs `winutils.exe` and `hadoop.dll`; see runtime guide. |
| CI unit tests | Ubuntu, Python 3.13 | `requirements_dev.txt` + local constraints | Cloud CI must run to establish Linux acceptance; a local Windows pass is not CI evidence. |
| CI Spark integration | Ubuntu 24.04, Python 3.11, Java 17 | `requirements_phase10.txt` | Real Parquet and full synthetic pipeline; required, zero skips. |
| Test CD release | Pipeline Python 3.13, existing Azure identity | `requirements_cd.txt` | Local Arrow tests do not establish live deployment success. |
| Airflow | Linux container, Python 3.11, Java 17 | `docker/phase10_airflow/Dockerfile` | Separate runtime; do not install Airflow into the Windows local environment. |
| Databricks serverless | Platform-provided Python/Spark | Runtime notebook/package | Do not install local PySpark into serverless. `requirements_phase11.txt` is for local reconciliation only. |

## Clean local install

```powershell
python --version
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements/requirements_dev.txt -c requirements/constraints-local-py313.txt
.venv/Scripts/python.exe -m pip check
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

Use Python 3.13 for this verified local recipe. The constraints record the resolved
package versions, including transitive dependencies; they are not a wheel archive
or an artifact hash lock. Installation needs access to PyPI. Linux uses
`.venv/bin/python`. Activation is optional when invoking the environment's Python
explicitly. If `.venv` already exists, select a new directory for a clean rehearsal.

For a lighter pipeline-only environment, install `requirements_phase10.txt` with
the same constraints. For all tests, use `requirements_dev.txt`; the base
`requirements.txt` alone does not include Arrow, Spark or DuckDB.

## Spark on Windows

Follow [the standalone runtime guide](../docs/pipelines/standalone_pipeline.md).
The environment helper accepts `-JavaHome`, `-HadoopHome`, and `-PythonExecutable`,
or existing JAVA_HOME/HADOOP_HOME values. It validates Java 17 and the two helper
files before setting session variables, including the Python used by Spark workers.
It does not download or install Java/native binaries.

## Troubleshooting

- `No module named pyarrow`: install the dev requirements using the same Python
  executable that runs tests. Do not copy libraries from `.tools` into the environment.
- Resolver conflict: use the combined requirements and constraints together;
  remove old commands pinning Arrow 23.0.1 alongside 25.0.1.
- PyPI connection denied: fix network access before retrying. An empty package
  listing after a connection error is not proof the package version does not exist.
- Java/helper errors: pass the installed paths to the PowerShell helper; on a
  machine without the documented Windows helpers, use the separate Linux runtime.
- Spark/Airflow skipped: default unit success does not mean these integration
  checks ran. Follow `tests/README.md` and the standalone guide explicitly.

The existing [PyArrow 25.0.1 release](https://pypi.org/project/pyarrow/25.0.1/)
is retained for export compatibility; the local Arrow/DAX tests validate the same
version for CD parsing. Historical deployments/backups keep their original version
records and are not represented as rerun.
