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
`scripts/deploy_test_release.py` and `azure-pipelines-test-cd.yml`.
See [automated Test deployment](test_cd.md) for first-run setup, preflight,
artifact selection and rollback. The remaining operational checks below still
apply; code availability alone does not verify the service principal.

1. Merge the existing CI branch through the required build policy.
2. Add the new helper tests to CI; the original five-file allowlist does not include them.
3. Pin validated dependencies for reproducible releases.
4. Prepare environment-specific definitions from the checked-out commit and publish
   them with the source commit, build ID, config checksum, Gold run and file inventory.
5. In the deployment job, download that exact artifact and verify the inventory.
6. Use an authenticated deployment identity with Test access; configure its service
   connection and Fabric permissions before enabling unattended execution.
7. Update existing items, wait for API operations and refresh, then run health checks.
8. Retain previous artifacts and referenced Gold runs for rollback.

## Alerts

Current state: health-check failures are recorded locally; outbound notifications
are not configured or tested. Choose a recipient or Teams channel and provision
its connection before enabling messages.

Alert on pipeline failure, failed Gold validation, refresh failure, incorrect target
binding and KPI mismatch. Include workspace, commit/build, run ID, failed step and
evidence URL. After configuring notifications, trigger a controlled failure in Test
and verify delivery. A successful logging script alone is not an alert-delivery test.
