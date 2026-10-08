# Phase 8: first Test deployment

Historical bootstrap record for 2026-10-01. The pending items below describe that
deployment, not the current CI/CD status. See the [project summary](../project_summary.md)
and [Test CD guide](test_cd.md) for subsequent delivery and operational instructions.

## Verified on 2026-10-01

Workspace: `WS_EV_Analytics_Test` (`27873d0c-580a-4963-9e25-5846948f1c5d`).
Capacity assignment was completed before deployment. Dev and Recovery were not modified.

| Item | ID |
| --- | --- |
| LH_EV_Gold | `970801bb-ffc3-4c5a-b25d-a940a5fd697e` |
| NB_EV_Test_Restore_Gold | `2a7ea51b-8a82-4fe2-821e-39555ba2535f` |
| SM_EV_Analytics | `a97a9cc1-eaac-4007-b8ad-c146ac1776c5` |
| RPT_EV_Analytics | `b7d65039-0413-4ecc-9f7f-33f0098c9cc0` |

[Open the Test report](https://app.powerbi.com/groups/27873d0c-580a-4963-9e25-5846948f1c5d/reports/b7d65039-0413-4ecc-9f7f-33f0098c9cc0).

Azure DevOps build 1 succeeded for commit
`4a00626eba0a0dfe3335f73ae2719d22eef6b1b9` on `feature/phase8-ci`.
At inspection, `origin/main` remained at `2bfd3d1`; the CI YAML was on the feature branch.
This bootstrap deployment used an exact Git archive of the successful build's
commit. It was prepared locally, not downloaded as an artifact from Azure Pipelines.
The new operational helpers have local validation and are not part of that build.

## Results

- 29 uploaded files verified by downloading their bytes again; original snapshot checksums passed.
- Eight Delta tables restored, with exact row-multiset equality against Parquet.
- Fact count 668665, Yes 116779, No 551886; zero orphan keys; 35 segment groups reconciled.
- Service model definition confirmed Test OneLake IDs, six tables, five relationships and 12 measures.
- Initial and post-rollback full refresh completed for all six partitions.
- Live DAX matched the pinned snapshot before and after rollback.
- PBIR validation completed with zero errors and zero warnings after allowing schema downloads.
- Service report binding confirmed the Test model ID and Test workspace ID.

The restore notebook reuses recovery helpers, so its paths and some evidence field
names contain `recovery`. It ran entirely in the Test workspace. Its historical
dashboard-skip field is not evidence of any new Test visual checks.

## Rollback drill

1. Captured deployed definition A.
2. Prepared B by changing only the Respondents measure description.
3. Updated the existing Test model using `updateDefinition`.
4. Downloaded B and confirmed the description changed.
5. Reapplied A to the same model ID.
6. Downloaded the result and compared every non-`.platform` definition part: byte-identical to A.
7. Refreshed and ran the health check successfully.

B was a controlled local drill variant, not a separate CI release. The Gold run
remained `20260925T152721965637Z`. No data rollback was needed.

## Artifacts and evidence

- Target configuration: `config/environments/test.json`.
- Source reference: `config/environments/dev.json` (from historical repository metadata).
- Deployment summary: `metadata/phase8_test_deployment.json`.
- Automated CD evidence: `metadata/phase8_cd_verification.json`.
- Later JSON API health check: `metadata/phase12/fabric_test_health_json.json`.
- Intermediate upload, restore, PBIR, refresh, report binding and bootstrap CI responses are archived locally at `output/repository_cleanup_20261008/archive/metadata/`; the deployment summary retains the accepted results.
- Full request/response journals and prepared definitions: `output/phase8/`.
- Release A: `output/phase8/test_release_a.zip`; checksum in the deployment summary.

The archive and full journals are excluded from Git. Retain them in the backup or
release-artifact store before cleaning this computer.

## What is still pending

- Visual verification of the published report requires a signed-in browser.
- Bronze/Silver/E2E deployment is outside this first Gold/model/report deployment.
- CI artifact publication and automatic CD are not configured by this work.
- PR policy and merge status were not audited.
- Notification recipients and connections are not configured.
- Commit and run CI for the newly added helpers, configs, tests and documentation.

The user confirmed that the published Test report works correctly.
This is user-attested verification; no screenshot was supplied.
