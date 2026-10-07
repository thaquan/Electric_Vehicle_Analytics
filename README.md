# Electric Vehicle Purchase Intent Analytics

An end-to-end analytics project that turns EV purchase-intent data into customer insights and Power BI dashboards, supported by a validated data pipeline, automated deployment, and recoverable data snapshots.

**Microsoft Fabric · Power BI · PySpark · Apache Airflow · Databricks · Azure DevOps**

## Business problem

For an EV manufacturer or dealership, understanding who is considering an electric vehicle is a starting point for customer research, marketing, and sales conversations. A single overall interest rate does not explain how interest varies with affordability, charging access, incentives, or everyday travel needs.

This project addresses three questions:

- **Who expresses purchase intent?** Compare customer groups by income, age, city type, and mobility profile.
- **Which conditions are associated with higher or lower interest?** Examine home charging, subsidy availability, and range anxiety.
- **How can teams explore these patterns consistently?** Provide a shared set of validated metrics and dashboards instead of separate spreadsheet calculations.

The business output is a descriptive decision-support tool for identifying segments and forming hypotheses to test with real customers. It measures **stated purchase intent, not completed purchases, revenue, or future sales**.

## Data sources and scope

The project uses the **Kaggle Playground Series S6E9: Predicting Electric Vehicle Purchases** dataset and its original reference dataset. The local files were acquired from the public repository linked by the reference analysis; their provenance and SHA-256 checksums are recorded in the [source manifest](metadata/source_manifest.json). A direct Kaggle download comparison remains unverified.

| Input | Rows | Use in this project |
| --- | ---: | --- |
| `train.csv` | 668,665 | Labeled records used for dashboard metrics and segment analysis. |
| `test.csv` | 286,571 | Unlabeled competition records; validated separately and excluded from purchase-intent rates. |
| `EV_Adoption_and_Range_Anxiety_Dataset.csv` | 10,000 | Original reference data; retained separately rather than combined with training records. |
| `sample_submission.csv` | 286,571 | Competition submission template; excluded from analytical outcomes. |

The target is `Will_Buy_EV`. Inputs cover demographics, annual income, city type, commuting distance, vehicle ownership, charging availability, environmental concern, subsidies, and range anxiety. See the [data dictionary](docs/data_dictionary.md) for field definitions.

> This is synthetic competition data. The findings describe this dataset and are not estimates of real-world EV demand or evidence that any factor causes a purchase. There are no transaction dates, purchase prices, brands, or precise geographic locations for sales trends, revenue analysis, or charging-site selection.

## Solution

The solution preserves the source data, validates it, and produces a reusable analytical model for Power BI.

```mermaid
flowchart LR
    A[Source CSV files] --> B[Bronze: source snapshots]
    B --> C[Silver: typed and validated records]
    C --> D[Gold: fact, dimensions and audit aggregates]
    D --> E[Power BI semantic model]
    E --> F[Three business dashboards]
```

| Component | Purpose |
| --- | --- |
| **Fabric and OneLake** | Store the Bronze, Silver, and Gold layers; run notebooks through an orchestrated pipeline. |
| **Gold star schema** | One respondent-level fact table and five dimensions for demographics, income, mobility, charging, and attitudes/incentives; two additional aggregates support reconciliation. |
| **Power BI** | A semantic model with 12 measures and three report pages for business exploration. |
| **PySpark and Airflow** | Run the transformation pipeline independently, with quality gates, artifact integrity checks, and controlled retries. |
| **Databricks** | Execute the data pipeline on serverless compute and reconcile all eight Gold tables against the standalone baseline. |
| **Azure DevOps and GitHub** | Version the project; Azure Pipelines validates changes and deploys the model/report to the Test workspace. |
| **Backup and recovery** | Preserve data, code, definitions, and manifests in checksum-verified packages for offline recovery. |

The Power BI report uses the Fabric model. Databricks demonstrates an alternative execution path for the data pipeline; it is not the report's current data source.

## Dashboard walkthrough

The screenshots below show the saved, unfiltered Power BI Desktop report. [Open the published report](https://app.powerbi.com/groups/5fe78794-25c3-41ee-b35e-bc56542d2cea/reports/ae4d7c59-759e-4462-afed-1717475ae012) if you have workspace access.

### Executive Overview

Establish the overall purchase-intent baseline, compare age and income groups, and see how the sample is distributed across city types.

![Executive Overview dashboard showing purchase-intent KPIs and age, income, and city segments](docs/screenshots/Executive%20Overview.png)

### Charging & Incentives

Explore the relationship between purchase intent, home charging, subsidy availability, and range anxiety. Supporting KPIs summarize charging access and nearby charging infrastructure.

![Charging and Incentives dashboard comparing purchase intent by home charging, subsidies, and range anxiety](docs/screenshots/Charging%20%26%20Incentives.png)

### Customer Profile

Understand the composition of the sample through income, age, vehicle ownership, and commuting patterns. Compare segment size with intent rate before prioritizing further research.

![Customer Profile dashboard showing demographics, income distribution, and purchase intent by commute distance](docs/screenshots/Customer%20Profile.png)

## Key findings and business recommendations

All figures below describe the **668,665 labeled training records**, with no dashboard filters applied. Purchase-intent rate is the number of `Yes` records divided by the number of records in the relevant group.

| Labeled records | Intending to buy an EV | Not intending to buy an EV | Overall intent rate |
| ---: | ---: | ---: | ---: |
| 668,665 | 116,779 | 551,886 | **17.46%** |

| Finding in the dataset | Evidence | Suggested next step |
| --- | --- | --- |
| **Intent differs substantially by income.** | **29.18%** for annual income of USD 100,000+ versus **4.35%** below USD 50,000. | Test affordability and total-cost-of-ownership messaging across income groups. Assess segment size alongside interest rate. |
| **Subsidy availability has a large observed association with intent.** | **27.47%** with subsidies versus **0.58%** without. | Make incentive eligibility clear in customer research and test whether better information changes expressed interest. Do not interpret the difference as the causal effect of a subsidy. |
| **Home charging access is associated with higher intent.** | **19.58%** where home charging is possible versus **12.71%** where it is not. | Include charging feasibility in customer discovery and test whether installation guidance addresses practical concerns. |
| **Longer commutes do not correspond to higher intent in this sample.** | **21.20%** for commutes of 10–<25 km versus **14.67%** for 50+ km. | Investigate range and charging concerns among long-distance commuters; tailor demonstrations to daily travel needs. |
| **A higher rate does not necessarily mean a larger opportunity pool.** | Rural records have a **19.34%** intent rate versus **16.11%** for urban records, but urban records contain **46,595 Yes responses**, compared with **23,977** for rural records. | Evaluate both intent rate and interested-record count. Avoid ranking segments by percentage alone. |

These are unadjusted comparisons, not independent driver effects. Income, incentives, charging access, and other attributes may overlap. The recommendations are hypotheses for validation with representative customer data or controlled experiments, not proven campaign results.

Figures are traceable to the [verified segment metrics](metadata/star_expected_metrics.json); [live DAX checks](metadata/semantic_model_live_dax.json) reconcile the model's analytical results. No revenue uplift, conversion improvement, or marketing ROI has been measured.

## Project outcomes

- **A business-facing report:** three dashboard pages provide a consistent view of purchase intent, charging conditions, and customer profiles.
- **A validated analytical foundation:** 668,665 fact rows, zero orphan dimension keys, and reconciliation of 35 segment groups. The semantic model's 12 measures and 24 combined-filter groups have also been checked.
- **Reproducible processing:** Fabric, standalone PySpark/Airflow, and Databricks implementations are supported by quality checks and cross-platform Gold reconciliation.
- **Verified delivery:** [Azure CI #30](https://dev.azure.com/thaquan081006/Electric_Vehicle_Analytics/_build/results?buildId=30) passed 86 configured unit tests, and [Test CD #31](https://dev.azure.com/thaquan081006/Electric_Vehicle_Analytics/_build/results?buildId=31) passed deployment, refresh, report/model binding, and KPI checks on 7 October 2026.
- **Recoverable artifacts:** offline baseline recovery and snapshot reconciliation have been demonstrated. An independently stored backup copy and final recipient handoff remain pending.

Saved report screenshots and the verified Urban slicer check do not constitute full UI acceptance. Remaining navigation/reset, chart cross-filter, Service rendering, and separate SQL endpoint checks were explicitly deferred; see [report validation details](docs/powerbi_report.md).

## Explore or run the project

### View the report

Start with the screenshots above, or open [RPT_EV_Analytics.pbip](RPT_EV_Analytics.pbip) in Power BI Desktop. Access to the configured Fabric model is required to query live data; cloning the repository does not provision the cloud resources.

### Run the standalone data pipeline

1. Obtain the four source CSVs listed above and place them in `data/raw/kaggle/`. Use the recorded snapshot checksums; raw data is not included in Git.
2. Prepare Python and Java for the pinned PySpark runtime. The verified Windows setup uses Python 3.13, Java 17, and Hadoop compatibility helpers; see the [standalone runtime guide](docs/phase10_closeout.md#7-runtime-windows).
3. From the repository root, install the pipeline dependencies and run:

```bash
python -m pip install -r requirements.txt -r requirements-phase10.txt
python -m src.run_pipeline --raw data/raw/kaggle --output-root output/local
```

Each run uses a new run directory. Inspect `run_report.json` and `published.json` under `output/local/runs/<run_id>/`; publication requires the quality and integrity checks to pass. This command builds local data artifacts, not a cloud deployment or a dashboard refresh.

For other execution paths, use the [Fabric pipeline guide](docs/pipeline_runbook.md), [Databricks guide](docs/phase11_databricks.md), or [recovery guide](docs/phase12_operations.md). Cloning the repository alone is not a data backup: large datasets, runtime artifacts, and recovery ZIPs are intentionally excluded from Git.

## Repository guide

| Location | Contents |
| --- | --- |
| `src/`, `dags/`, `docker/` | Standalone transformations, Airflow orchestration, and container setup. |
| `databricks/` | Serverless runtime modules, notebooks, and job definitions. |
| `*.Lakehouse/`, `*.Notebook/`, `*.DataPipeline/`, `notebooks/` | Fabric item definitions and importable notebooks. |
| `RPT_EV_Analytics.Report/`, `SM_EV_Analytics.SemanticModel/`, `models/` | Power BI report, semantic model, and exported model snapshot. |
| `scripts/`, `sql/`, `tests/` | Build/deployment utilities, reconciliation queries, and validation tests. |
| `config/`, `metadata/` | Environment mappings, schema contracts, source checksums, and verification evidence. |
| `docs/` | Architecture, analytical definitions, screenshots, and operational runbooks. |

Further reading: [data dictionary](docs/data_dictionary.md) · [star schema](docs/star_schema.md) · [semantic model](docs/semantic_model.md) · [CI/CD](docs/test_cd.md) · [operations](docs/operations_runbook.md).
