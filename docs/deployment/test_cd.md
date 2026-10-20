# Automated Test deployment

## Scope

CI now builds `ev-test-release` without `output/` or a Parquet snapshot. It contains
the target model/report definitions, fixed Test configuration, execution helpers,
commit/build identity, and a SHA-256 inventory. The release is restricted to the
already verified Gold run `20260925T152721965637Z` and existing Test item IDs.
This does not provision data or run the Bronze/Silver pipeline.

The redesigned report requires its matching 29-measure model (12 core plus 17
narrative measures). Package both current PBIP item folders together. The
release guard requires all 12 core names in `EV Respondents` and allows extra
measures; it no longer requires an exact total of 12. It also resolves structured
PBIR Column/Measure references against the packaged TMDL table declarations,
including narrative measures, filters, sorting and formatting expressions.
Unknown tables, missing fields, wrong field kinds and unresolved query-local
aliases fail before network access. Hierarchy expressions are currently unsupported
and fail closed. This is a reference check, not a DAX compiler or rendering test.
Every declared report resource must also be packaged. The referenced shared base
theme is included explicitly, and Test binding omits the optional `access mode`
property that Service strips on readback. This makes the artifact and returned
definition comparable without ignoring added themes or connection changes.
The historical export
under `models/SM_EV_Analytics` is not the source for this release.

`ci/azure_pipelines_test_cd.yml` consumes artifacts from `EV-Analytics-CI`. Successful
main builds trigger CD; a manual run can select another successful CI run for a
controlled test. The pipeline does not check out or rebuild from a newer branch.

## Prerequisites

Azure DevOps pipeline definitions use these repository paths (default branch: `refs/heads/main`):

| Pipeline | ID | YAML path |
| --- | --- | --- |
| EV-Analytics-CI | 1 | `ci/azure_pipelines.yml` |
| EV-Analytics-Test-CD | 2 | `ci/azure_pipelines_test_cd.yml` |

Update the pipeline definition as well as repository references whenever a YAML file moves.

- Azure DevOps service connection `sc-fabric-ev-test` (Azure Resource Manager).
- Deployment identity permitted by Fabric tenant settings and granted Test access.
- The identity must read the current model with the modern `executeDaxQueries`
  API. CD explicitly selects the Arrow response backend (`EV_DAX_API=arrow`).
  The older JSON `executeQueries` API returned HTTP 401 for this service principal.
  Arrow error rowsets are checked even when HTTP is 200. Preflight fails before
  updates if the deployment identity cannot query KPI; no user-login fallback.
- Environment `EV-Analytics-Test`, with an **Exclusive lock** check. The YAML sets
  sequential lock behavior, but the environment check must also exist to serialize
  deployments. Stop a failed/uncertain operation before starting another release.
- Authorize this pipeline to use the service connection and environment.
- Share `CONN_EV_Gold_Test_Fixed` with the deployment identity as a connection User.
  Its ID is recorded in `config/environments/test.json`. The semantic model owner
  must be able to bind it. Preflight applies and verifies this mapping before any
  definition changes, including when `preflightOnly=true`.
  CD first uses `Default.TakeOver` on the existing Test model so the deployment
  identity becomes its owner, as required by `bindConnection`. Preflight therefore
  changes ownership and applies the connection mapping even though it does not
  update definitions or refresh. CD run 13 confirmed the `BindNotModelOwner` guard.

## First run

1. Run CI on the implementation branch; confirm `ev-test-release` is published.
2. Register `ci/azure_pipelines_test_cd.yml` as `EV-Analytics-Test-CD`.
3. Run CD manually, select that CI run under Resources, and set `preflightOnly=true`.
4. Confirm it reads both existing items, checks live KPI, and captures both definitions.
5. Run the same CI artifact again with `preflightOnly=false` to exercise deployment.
6. Inspect `test-deployment-evidence/deployment.json` and `health_after.json`.
7. Merge the implementation through PR/CI. Change the CD pipeline's default branch
   from `refs/heads/feature/phase8-cd` to `refs/heads/main` after merge. Future
   successful main runs can deploy automatically.

When selecting a pipeline resource through the Runs REST API, its `version` is
the **run number**, not the numeric build ID: for CI build ID 67 use
`20261017.3`. The downloaded manifest and `resources.pipeline.verifiedCI.runID`
still identify build `67`; CD verifies that ID and its full commit SHA. An attempt
using `version: "67"` was rejected during pipeline validation as CD #69 before
any deployment job ran. The corrected request is retained with CD #70.

## Verified deployment

The current accepted release is **CI #67 -> CD #70**, source
`295e26da7aa1ea3c0cbe629ff83230f6ccafdbd2`, on 17 October 2026. The selected
artifact, complete report readback, refresh, binding and KPI passed. Windows-native
Service UAT exercised the same report definitions. See the
[acceptance evidence](../evidence/acceptance_20261017.json) and
[UAT observations](../evidence/service_uat_20261017.json).

Public readers can inspect the [archived evidence summary](../cicd_evidence.md) and its sanitized JSON without Azure DevOps access.

The later main release was CI #63 -> CD #64 on 14 October 2026, source
`fa9e0fa701951ef73f07c88c29ffb864c604c622`. On 17 October its downloaded release
inventory and retained deployment evidence were inspected: the manifest identifies
build 63, CD recorded `passed`, refresh completed and KPI matched the pinned
snapshot. That older deployment predates the new report-readback gate and the
15 October presentation fixes; it does not establish deployment of this working
tree. Use the [portfolio acceptance record](../portfolio_acceptance.md) for the
new verification and [Service UAT cases](service_uat.md) for interaction acceptance.

CI build 14 and CD build 15 succeeded on 2026-10-02. CD used source commit
`8e8e4f74a03efb91fbd2c6211fd2809ca532b851` and service principal
`sp-ev-analytics-test-deploy`. The Test model's ownership was transferred to
this deployment identity. Both existing items were updated, the configured
connection was restored, refresh completed, and the final KPI matched
668665 / 116779 / 551886. Build 15 retains `test-deployment-evidence`, including
the captured rollback package. See `metadata/phase8_cd_verification.json` (local output; excluded from Git).

## Deployment sequence

1. Verify exact file inventory, checksum, CI commit/build identity, target IDs,
   report model binding, model structure and all six Gold partitions.
2. Verify live item identity and current health using the deployment identity.
3. Capture current model/report definitions into a separately sealed `rollback/` package.
4. Update the existing model; poll the Fabric operation with a bounded timeout.
   Reapply the configured cloud connection and verify its ID and OneLake path.
   `updateDefinition` can clear the mapping; CD run 11 demonstrated this with
   `DMTS_MonikerWithUnboundDataSources`. Restore the mapping before refresh.
5. Read the model definition back and verify Test source and Gold run.
6. Start full transactional refresh; poll that exact refresh ID.
7. Check DAX KPI before updating the report.
8. Update the existing report and wait for completion.
9. Read the report definition back with `getDefinition` (including asynchronous
   operation results). Save `report_readback.json`, validate its references against
   the model read back in step 5, and compare every part with the release. JSON key
   order/whitespace and service `.platform` metadata are ignored; missing, extra or
   changed parts fail the gate. A service normalization beyond those exceptions
   also fails and needs investigation rather than a silent bypass.
10. Write `report_binding.json` only after readback passes, then check final
    report/model binding, refresh and DAX. Publish evidence even on failure.

A failed readback leaves deployment status `failed` and retains captured rollback;
it does not retry the report update or roll back automatically. The offline suite
`python -m unittest discover -s tests -p test_test_release.py` covers invalid fields,
missing narrative measures, stale/wrong report readback, read errors and successful
deployment ordering. These mocks do not establish that a live deployment passed.

The pipeline never creates replacement items, writes Gold tables, retries POST
requests automatically, or assumes a timeout means the operation failed remotely.
There is no cross-item transaction: model update may complete before report update
fails. Check `operations.json` and retain the captured rollback in this case.

## Local preflight

Use a fresh output/evidence path for every run:

```powershell
$commit = git rev-parse HEAD
python scripts/build_test_release.py --output output/test-release --commit $commit --build-id local --branch local
python -m pip install -r requirements/requirements_cd.txt
$env:EV_DAX_API = "arrow"
python scripts/deploy_test_release.py --release output/test-release --evidence output/test-preflight --preflight-only
```

Local tests use your Azure CLI identity; they are not evidence that the service
principal works. CI provenance only applies to a package actually built by CI.

## Rollback

Download the evidence artifact for the affected deployment. Its `rollback/`
directory is an executable release of the definitions captured before changes.
After checking that no API operation or refresh is still pending:

```powershell
python -m pip install -r rollback/requirements/requirements_cd.txt
$env:EV_DAX_API = "arrow"
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

- Deploys packaged report definitions, including visual changes, but does not verify rendering or interactions.
- Does not send notifications; subscribe to failed Azure DevOps builds separately.
- Does not change the selected Gold run or support Prod.
- SHA-256 detects corruption; trust in the release origin comes from Azure DevOps
  artifact permissions and the selected successful CI run, not from self-signed hashes.
