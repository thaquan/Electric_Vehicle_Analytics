# Electric Vehicle Purchase Intent Analytics

An end-to-end data project that turns **668,665 customer records** into a three-page Power BI report explaining how EV purchase intent varies with income, charging access and incentives.

**Microsoft Fabric · Power BI · SQL · Python · PySpark · Airflow · Databricks · Azure DevOps**

## Business problem

Which customer groups express interest in an EV, and which conditions are associated with that interest? The project helps a manufacturer or dealership explore segments and form hypotheses for customer research and marketing.

The outcome is a descriptive analytics tool: **purchase intent, not actual sales or a prediction model**. The source is synthetic competition data, so the findings do not estimate real-world demand or establish causality.

## Dashboard

### Executive Overview

Summarize overall EV purchase intent, segment opportunity, and the largest observed intent gaps.

![Executive Overview](docs/screenshots/executive_overview.png)

### Charging & Incentives

Compare charging access, subsidies, range anxiety and nearby infrastructure as descriptive associations with EV purchase intent.

![Charging and Incentives](docs/screenshots/charging_incentives.png)

### Customer Segments

Explore which age and income segments combine scale with higher EV purchase intent, with supporting mobility context.

![Customer Segments](docs/screenshots/customer_segments.png)

[Open the published report](https://app.powerbi.com/groups/5fe78794-25c3-41ee-b35e-bc56542d2cea/reports/ae4d7c59-759e-4462-afed-1717475ae012) with workspace access, or inspect the [Power BI project](RPT_EV_Analytics.pbip). On 14 October 2026 the Dev Service items were updated in place from source commit `edf7114`: the live semantic model was verified with 29 measures and the expected KPI counts, and the live report definition was verified with three visible pages plus the hidden `Segment context` tooltip page and 68 visuals. The committed screenshots remain Desktop captures rather than Service UI evidence, so browser rendering and interactions still require separate acceptance. See the [report guide](docs/architecture/powerbi_report.md) for interactions, rebuild steps and model requirements.

## Key findings

**116,779 of 668,665 respondents express purchase intent: 17.46%.**

| Pattern in the dataset | Result | Business implication to investigate |
| --- | --- | --- |
| Annual income | 29.18% intent at USD 100,000+ vs 4.35% below USD 50,000 | Test affordability and total-cost-of-ownership messaging. |
| Subsidy availability | 27.47% with subsidies vs 0.58% without | Include incentive eligibility in customer research. |
| Home charging | 19.58% with access vs 12.71% without | Investigate charging feasibility and installation support. |
| Segment size vs rate | Rural intent is 19.34% vs 16.11% urban, but urban has 46,595 interested respondents vs 23,977 rural | Consider both interested-record count and rate when comparing segments. |

Figures come from the [reference segment metrics](metadata/star_expected_metrics.json). These are unadjusted associations; no campaign uplift, sales conversion or ROI has been measured.

## Architecture and technical work

```mermaid
flowchart LR
    A[Source CSVs] --> B[Bronze: immutable snapshots]
    B --> C[Silver: typed and validated data]
    C --> D[Gold: star schema]
    D --> E[Power BI semantic model]
    E --> F[Three report pages]
```

| Area | Implementation |
| --- | --- |
| Data engineering | Fabric/OneLake Bronze–Silver–Gold pipeline, schema and checksum validation, lineage and quality gates. |
| Data modeling | One respondent-level fact and five dimensions; 29 DAX measures (12 core + 17 narrative). Two Gold audit aggregates remain outside the model. |
| Analytics | Segment comparisons for income, demographics, mobility, charging and incentives. |
| Orchestration | Standalone PySpark with an Airflow DAG, controlled retries and integrity checks before publication. |
| Cross-platform execution | Databricks serverless runtime with eight-table Gold reconciliation against the standalone output. |
| Delivery | Azure CI tests and package verification; Test deployment with refresh, binding and KPI checks. |

Power BI uses the Fabric model. Databricks demonstrates an alternative data-processing path. See [validation and limitations](docs/validation.md), [star schema](docs/architecture/star_schema.md) and [semantic model](docs/architecture/semantic_model.md).

## Data

Source: Kaggle Playground Series S6E9, *Predicting Electric Vehicle Purchases*, and its original reference dataset. [Provenance and SHA-256](metadata/source_manifest.json) identify the acquired files; direct comparison with a Kaggle download remains unverified.

| File | Rows | Purpose |
| --- | ---: | --- |
| `train.csv` | 668,665 | Labeled analytical population; target `Will_Buy_EV`. |
| `test.csv` | 286,571 | Unlabeled competition data, excluded from intent rates. |
| `EV_Adoption_and_Range_Anxiety_Dataset.csv` | 10,000 | Separate reference data, not combined with training records. |
| `sample_submission.csv` | 286,571 | Competition template, excluded from analytical outcomes. |

[Data dictionary](docs/architecture/data_dictionary.md). Raw data is obtained separately and is not stored in Git.

## Run locally

Place the four source CSVs in `data/raw/kaggle/`, matching the manifest. Prepare Python, Java 17 and the [PySpark runtime](docs/pipelines/standalone_pipeline.md#runtime-windows), then run:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements/requirements_dev.txt -c requirements/constraints-local-py313.txt
.venv/Scripts/python.exe -m pip check
.venv/Scripts/python.exe scripts/verify_source_download.py --directory data/raw/kaggle
. ./scripts/phase10_env.ps1 -PythonExecutable .venv/Scripts/python.exe
.venv/Scripts/python.exe -m src.run_pipeline --raw data/raw/kaggle --output-root output/local
```

Use Python 3.13 for this Windows recipe. See the [runtime matrix and troubleshooting](requirements/README.md) for dependency scopes and other runtimes. The helper accepts custom Java/Hadoop paths; Java and Windows native helpers are installed separately. If PowerShell blocks the helper script, the runtime guide documents a process-only execution-policy setting.

Each run writes to `output/local/runs/<run_id>/`. Inspect `run_report.json` and `published.json`; publication requires passing quality and integrity checks. Opening the live Power BI report requires access to the configured Fabric model. Cloning the repo does not provision cloud resources.

## Explore the code

| Location | What to review |
| --- | --- |
| `src/`, `dags/`, `docker/` | Transformations, quality rules and Airflow orchestration. |
| `databricks/` | Serverless runtime, notebook and job configurations. |
| Fabric item folders, `notebooks/` | Lakehouse, notebook and pipeline definitions. |
| Power BI item folders, `models/` | Current report/model definitions and a historical model export; see the [model guide](docs/architecture/semantic_model.md). |
| `sql/`, `metadata/`, `config/` | Reconciliation queries, runtime contracts and environment mappings. |
| `scripts/`, `tests/`, `ci/` | Reusable utilities, automated regression tests and CI/CD. |
| `docs/` | Data model, screenshots and technical runbooks. |

Technical guides: [Fabric](docs/pipelines/pipeline_runbook.md) · [PySpark/Airflow](docs/pipelines/standalone_pipeline.md) · [Databricks](docs/pipelines/phase11_databricks.md) · [CI/CD](docs/deployment/test_cd.md) · [integration CI](docs/testing_ci.md) · [tests](tests/README.md) · [recovery](docs/recovery/recovery_runbook.md).

## CI/CD evidence

Dashboard redesign CI builds **54 and 55 succeeded on 13 October 2026**, and Azure DevOps PR #13 was merged. The release guard requires the 12 core measures by name while allowing additional measures. See the [CI/CD evidence](docs/cicd_evidence.md) for these runs and the separate archived Test deployment checks from 2 October. Separately, on 14 October 2026 the existing Dev semantic model and report were updated in place and verified through Fabric/Power BI APIs: 29 live measures, KPI counts of 668,665 respondents / 116,779 Yes / 551,886 No, and a 68-visual report definition bound to the same Dev model. This proves the deployed definitions and model health, not browser-level rendering or interaction acceptance.

## Reproducing the project

Follow [data acquisition and checksum verification](docs/data_access.md) before running locally. The four CSVs are obtained separately, and the source manifest's direct-Kaggle verification limitation remains explicit. For cloud adaptation, see [configuration templates and deployment constraints](config/README.md); the existing environment mappings identify the pinned demonstration deployment.
