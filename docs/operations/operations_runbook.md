# EV Analytics Test operations

## Routine check

Use an Azure CLI identity with access to the Test workspace:

```powershell
python scripts/check_test_health.py --output output/phase8/health_latest.json
```

The command checks report/model binding, latest refresh completion and live KPI.
It writes JSON evidence and exits nonzero on failure. It does not validate source
table integrity, model partition state through XMLA, report rendering, or send notifications.
KPI checks alone cannot prove the model's source workspace; inspect its definition
after every deployment.

The fixed snapshot does not require a daily data-processing schedule.

## Local DAX authentication — 29 October 2026

The existing Azure CLI **user** identity passed the full health check with the
JSON `executeQueries` backend on 29 October 2026 (07:57, Asia/Bangkok). Report
binding, latest refresh completion and all three KPI matched the pinned snapshot:
668665 respondents, 116779 Yes and 551886 No. The latest refresh was completed on
22 October; this probe did not start a new refresh or deploy definitions. See the
[dated evidence](../evidence/live_health_20261029.json).

Select the backend explicitly for local user checks, including in a shell previously
used for Arrow/CD:

```powershell
$env:EV_DAX_API = "json"
python scripts/check_test_health.py --output output/live-health-<new-run>/json.json
```

Using the **same cached token**, `EV_DAX_API=arrow` still returned HTTP 401.
Its decoded audience matched `https://analysis.windows.net/powerbi/api`, and
the token was not expired. This narrows the observed failure to the Arrow request
for this identity; it does not establish its root cause or prove an Arrow permission
fix. Successful JSON queries demonstrate current query access for that endpoint;
workspace role/Build ACLs were not independently enumerated.

The health checker uses the selected backend and fails on its error; it does not
fall back automatically. Keep the CD setting `EV_DAX_API=arrow` for the service
connection as documented in [Test deployment](../deployment/test_cd.md). This
local user check does not revalidate the service principal or supersede its
historical deployment evidence. Do not run deployment preflight to diagnose this
read-only health issue: preflight can change model ownership and connection mapping.

If a future JSON check also fails, inspect the selected Azure account/tenant and
Power BI token resource/expiry, then verify access for that identity. Record the
failure before renewing the login; do not change permissions or expected KPI to
force a pass. Keep separate evidence per backend and a fresh output path per run.
The raw probes, sanitized auth context and SHA-256 inputs for this run are retained
locally under ignored `output/live-health-20261029/`.

## Deployment and rollback tools

`scripts/fabric_test_api.py` uses the existing Azure CLI login and permits only the
named Test workspace. Tokens are held in memory. Mutating calls are not retried.
Every CLI operation saves its attempt and response to `--result`.

For a prepared, reviewed model definition:

```powershell
python scripts/fabric_test_api.py /semanticModels/a97a9cc1-eaac-4007-b8ad-c146ac1776c5/updateDefinition --method POST --body output/phase8/rollback_a.json --result output/phase8/rollback_attempt_2.json
```

Use a new journal for a genuinely new operation. If a request times out or returns
202, inspect the saved operation ID and poll `/v1/operations/<ID>`; never assume a
timeout means no change occurred. Wait for success before refresh or dependent steps.
The helper is a scoped API client, not a complete automatic release orchestrator.

After a model update, issue a full transactional refresh, wait for completion,
read the model definition back, and run the routine health check. Preserve model
and report IDs. Use `reports/<ID>/updateDefinition` for report updates after checking
that the prepared report binds to the intended model.

`prepare_test_data.py` is for first-time provisioning. It never overwrites existing
files; conflicting content fails. After item IDs are filled in the environment
config, do not rerun it blindly: its uploaded provisioning config differs from the
completed environment inventory. The restore notebook also refuses existing tables.

## Failure handling

| Failure | Response |
| --- | --- |
| Restore partially failed | Read the restore journal and inventory written tables. Do not delete or overwrite them as an automatic retry. |
| Missing script/default Lakehouse | Check notebook metadata, configure cell and Files/recovery/scripts in Test. |
| Wrong source or Gold run | Stop promotion; inspect expressions.tmdl and all six entityName/schemaName values. |
| Refresh failed | Inspect saved refresh details, access identity, source table registration and schema. |
| Report binding mismatch | Reapply the prepared Test report definition and verify Service datasetId/datasetWorkspaceId. |
| DAX mismatch | Keep the last verified run; compare Gold audit and expected snapshot before changing expected KPI. |
| API timeout/202 | Poll the saved operation or job; check item inventory before any new create. |
| Release defect | Apply the prior saved definition to existing items, refresh, then verify DAX and report. |
| Missing Gold data | Use the separately retained verified backup; code rollback does not restore data. |

## CI/CD integration

The implementation is in `scripts/build_test_release.py`,
`scripts/deploy_test_release.py` and `ci/azure_pipelines_test_cd.yml`.
See [automated Test deployment](../deployment/test_cd.md) for first-run setup, preflight,
artifact selection and rollback. The remaining operational checks below still
apply; code availability alone does not verify the service principal.

CI now discovers every top-level unit module and requires separate Spark and
Airflow jobs before packaging. It uses pinned runtime dependencies, builds from
the checked-out commit, and publishes the commit/build identity with a SHA-256
inventory. CD downloads the selected CI artifact with no checkout or rebuild,
verifies its identity, updates existing items, restores the connection, refreshes,
reads definitions back and checks binding/KPI. Retain the evidence artifact and
its sealed rollback package for every accepted deployment.

The Azure `main` build-validation policy and Test Exclusive lock were read back
on 17 October 2026. See [repository synchronization](repository_sync.md) for
GitHub protections and mirror handling. Complete [Service UAT](../deployment/service_uat.md)
after API gates pass, and record the accepted run in the
[portfolio acceptance record](../portfolio_acceptance.md).

## Alerts

Current state: health-check failures are recorded locally; outbound notifications
are not configured or tested. Choose a recipient or Teams channel and provision
its connection before enabling messages.

Alert on pipeline failure, failed Gold validation, refresh failure, incorrect target
binding and KPI mismatch. Include workspace, commit/build, run ID, failed step and
evidence URL. After configuring notifications, trigger a controlled failure in Test
and verify delivery. A successful logging script alone is not an alert-delivery test.
