# Automated Test deployment

## Scope

CI now builds `ev-test-release` without `output/` or a Parquet snapshot. It contains
the target model/report definitions, fixed Test configuration, execution helpers,
commit/build identity, and a SHA-256 inventory. The release is restricted to the
already verified Gold run `20260925T152721965637Z` and existing Test item IDs.
This does not provision data or run the Bronze/Silver pipeline.

`azure-pipelines-test-cd.yml` consumes artifacts from `EV-Analytics-CI`. Successful
main builds trigger CD; a manual run can select another successful CI run for a
controlled test. The pipeline does not check out or rebuild from a newer branch.

## Prerequisites

- Azure DevOps service connection `sc-fabric-ev-test` (Azure Resource Manager).
- Deployment identity permitted by Fabric tenant settings and granted Test access.
- The identity must read the current model with Execute Queries. Models using SSO
  or RLS can restrict service-principal Execute Queries. Preflight fails before
  updates if this identity cannot run the KPI query; do not replace the check with
  a user login or silently skip it.
- Environment `EV-Analytics-Test`, with an **Exclusive lock** check. The YAML sets
  sequential lock behavior, but the environment check must also exist to serialize
  deployments. Stop a failed/uncertain operation before starting another release.
- Authorize this pipeline to use the service connection and environment.

## First run

1. Run CI on the implementation branch; confirm `ev-test-release` is published.
2. Register `azure-pipelines-test-cd.yml` as `EV-Analytics-Test-CD`.
3. Run CD manually, select that CI run under Resources, and set `preflightOnly=true`.
4. Confirm it reads both existing items, checks live KPI, and captures both definitions.
5. Run the same CI artifact again with `preflightOnly=false` to exercise deployment.
6. Inspect `test-deployment-evidence/deployment.json` and `health_after.json`.
7. Merge the implementation through PR/CI. Future successful main runs can deploy automatically.

## Deployment sequence

1. Verify exact file inventory, checksum, CI commit/build identity, target IDs,
   report model binding, model structure and all six Gold partitions.
2. Verify live item identity and current health using the deployment identity.
3. Capture current model/report definitions into a separately sealed `rollback/` package.
4. Update the existing model; poll the Fabric operation with a bounded timeout.
5. Read the model definition back and verify Test source and Gold run.
6. Start full transactional refresh; poll that exact refresh ID.
7. Check DAX KPI before updating the report.
8. Update the existing report and wait for completion.
9. Check final report/model binding, refresh and DAX, and publish evidence even on failure.

The pipeline never creates replacement items, writes Gold tables, retries POST
requests automatically, or assumes a timeout means the operation failed remotely.
There is no cross-item transaction: model update may complete before report update
fails. Check `operations.json` and retain the captured rollback in this case.

## Local preflight

Use a fresh output/evidence path for every run:

```powershell
$commit = git rev-parse HEAD
python scripts/build_test_release.py --output output/test-release --commit $commit --build-id local --branch local
python scripts/deploy_test_release.py --release output/test-release --evidence output/test-preflight --preflight-only
```

Local tests use your Azure CLI identity; they are not evidence that the service
principal works. CI provenance only applies to a package actually built by CI.

## Rollback

Download the evidence artifact for the affected deployment. Its `rollback/`
directory is an executable release of the definitions captured before changes.
After checking that no API operation or refresh is still pending:

```powershell
python -B rollback/scripts/deploy_test_release.py --release rollback --evidence output/rollback-attempt
```

This uses the same source checks, refresh and KPI validation. The pinned snapshot
must still exist. The capture manifest identifies the tooling/build that captured
the previous definitions; it does not assert that the previous definitions came
from that source commit.

Preflight deliberately requires a healthy baseline. If a failed release left an
unhealthy model, stop and inspect the captured payloads and operation IDs; use the
scoped API helper for supervised restoration rather than bypassing checks in CI.

## Limitations

- Does not verify rendering or alter report visuals.
- Does not send notifications; subscribe to failed Azure DevOps builds separately.
- Does not change the selected Gold run or support Prod.
- SHA-256 detects corruption; trust in the release origin comes from Azure DevOps
  artifact permissions and the selected successful CI run, not from self-signed hashes.
