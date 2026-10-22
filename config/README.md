# Environment configuration

[`examples/`](examples/) contains templates for adapting the project. Copy the appropriate JSON into `config/local/`, which is excluded from Git, then populate your own resource IDs. Never place credentials in these files; use the platform credential store, Azure CLI identity or secret variables documented by the relevant pipeline.

The existing [`environments/`](environments/) files describe the project's pinned demonstration environment. Their resource IDs and hostnames are references, not credentials. The Test release builder checks these IDs against explicit allowlists to reject deployments to an unexpected target. They are retained to keep the recorded deployment and its regression tests reproducible.

**Fabric environment examples are not accepted as deployment configurations.** Zero IDs intentionally do not match the deployment allowlist. Changing a JSON file alone does not provision a workspace or adapt every Fabric/Power BI definition. To target your own environment, update the deployment allowlists, item definitions, bindings and regression fixtures together, then validate before running CD. The local data pipeline can run without any of these cloud IDs.

Do not overwrite the pinned Test configuration with a template or use cloud deployment commands merely to preview the portfolio.

## Databricks submit template

`examples/databricks_submit.json` is a reusable serverless job-submit payload.
Copy it to `config/local/`, replace the notebook and Volume path placeholders,
and follow the [Databricks guide](../docs/pipelines/phase11_databricks.md).
It is separate from the pinned Fabric deployment configurations and does not
provision a workspace, Volume or notebook.
