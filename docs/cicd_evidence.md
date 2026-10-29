# CI/CD evidence

Records below distinguish deployment, Service interaction acceptance and later
read-only API probes. Each applies to its stated source, time and identity; these
records are not a live listing of the latest pipeline runs.

## Live API verification — 29 October 2026

- At 07:57 Asia/Bangkok (`2026-10-29T00:57:48Z`), the existing local Azure CLI user passed JSON `executeQueries`: report binding, latest-refresh completion and KPI **668,665 / 116,779 / 551,886**.
- The same client and cached token received HTTP 401 from Arrow `executeDaxQueries`. The decoded audience matched the requested Power BI resource and the token was not expired. The Arrow root cause remains unestablished; JSON success does not verify an Arrow fix.
- The latest refresh observed in this probe completed on 22 October. The probe did not deploy definitions, start a refresh, change permissions, repeat Service UAT or revalidate the CD service principal.
- Four health tests and five Arrow-decoder tests passed without skips. These are the focused local checks for this probe, not a new full Unit/Spark/Airflow acceptance run.

See the [sanitized live-health record](evidence/live_health_20261029.json) and
[local backend instructions](operations/operations_runbook.md). Raw probes and
the sanitized auth context are retained in ignored `output/live-health-20261029/`.
The 28 October failed Arrow probe below remains part of the history.

## Inspected Test release — 22 October 2026

- Source: `48fa1fe022f78b86dd9837a5a85bd8e9c74dd6c5`.
- [CI #84](https://dev.azure.com/thaquan081006/Electric_Vehicle_Analytics/_build/results?buildId=84): 118 unit, 8 Spark and 3 Airflow tests passed, with zero failures/errors/skips. Results were downloaded from Azure during the 28 October review.
- [CD #85](https://dev.azure.com/thaquan081006/Electric_Vehicle_Analytics/_build/results?buildId=85): deployed CI #84's release; `preflight_only=false`. Downloaded evidence records successful model/report deployment, binding, refresh and DAX KPI 668,665 / 116,779 / 551,886 at 08:51 UTC on 22 October.
- The 28 October local probe passed report binding and latest-refresh checks, but its Arrow DAX request returned HTTP 401. Do not report that probe as a full health pass or substitute it for Service UAT.

See the [sanitized release record](evidence/release_20261022.json). Raw downloaded
artifacts are retained locally under `output/review-20261028/ci84/` and `cd85/`.
Later uncommitted remediation has its own local test evidence and has not been
deployed by these builds. Representative Service interaction evidence remains
the separately scoped 17 October record below.

## Accepted Test release — 17 October 2026

- Source: `295e26da7aa1ea3c0cbe629ff83230f6ccafdbd2`.
- [CI #67](https://dev.azure.com/thaquan081006/Electric_Vehicle_Analytics/_build/results?buildId=67), run number `20261017.3`: succeeded. Downloaded results record 118 Unit, 8 real Spark and 3 Airflow tests passed, zero failures/errors/skips. Package succeeded after all three jobs.
- [PR validation #68](https://dev.azure.com/thaquan081006/Electric_Vehicle_Analytics/_build/results?buildId=68) approved the required build policy on [Azure PR #17](https://dev.azure.com/thaquan081006/Electric_Vehicle_Analytics/_git/Electric_Vehicle_Analytics/pullrequest/17).
- [Test CD #70](https://dev.azure.com/thaquan081006/Electric_Vehicle_Analytics/_build/results?buildId=70): succeeded using **CI build 67's artifact**, with no checkout or rebuild. Downloaded evidence records `definition_matches_release=true`, successful connection/Gold-run checks, completed refresh and KPI 668,665 / 116,779 / 551,886 using the service principal's Arrow DAX API. The sealed rollback package was retained and verified.
- [Service UAT](evidence/service_uat_20261017.json): 17 value/filter/tooltip observations passed through Windows UI Automation, plus six directed page-navigation paths, active-page buttons and page-slicer independence. Its report-only candidate came from a sealed archive of the same commit; every report part matched the downloaded CI artifact and the later CD readback.

See the [sanitized acceptance JSON](evidence/acceptance_20261017.json) for artifact
checksums and verification scope. Raw deployment evidence, rollback, snapshots
and screenshots remain under ignored `output/acceptance-20261017/`.

CD #69 failed pipeline resource resolution before any job or Service change:
REST `version` needed run number `20261017.3`, rather than build ID `67`.
A separate local report-preparation attempt received Arrow DAX HTTP 401 before
updates; the existing user identity passed the supported JSON API on the next
attempt. The unattended CD #70 passed with its configured Arrow/service-principal
path. Failed attempts are retained and are not counted as successful deployments.

## Dashboard redesign CI - 13 October 2026

- Fix commit: `45552d7509b78428dee64702ef64231ab8998f57`.
- Local unit suite: 110 passed, zero failures/errors/skips.
- [Branch CI #54](https://dev.azure.com/thaquan081006/Electric_Vehicle_Analytics/_build/results?buildId=54) and [PR validation #55](https://dev.azure.com/thaquan081006/Electric_Vehicle_Analytics/_build/results?buildId=55): succeeded, including Unit, Spark, Airflow and Package.
- [PR #13](https://dev.azure.com/thaquan081006/Electric_Vehicle_Analytics/_git/Electric_Vehicle_Analytics/pullrequest/13): completed after the Build policy approved #55. Merge commit: `5e0952ffd94d0617cea08c778a4eb2c940b5ad4b`, verified on `origin/main`.

The guard checks the 12 required measure names and permits additional measures.
These runs verify CI and packaging, not deployment or Service rendering of the
redesigned report. The older Test deployment evidence below remains separate.

## Archived Test deployment - 2 October 2026

![Archived CI/CD verification summary](screenshots/cicd_evidence.svg)

This image renders an **archived verification record**, not the Azure DevOps UI. It documents the run recorded on **2 October 2026**; it does not claim that the pipeline was rerun or that cloud resources are healthy today.

| Check | Recorded result |
| --- | --- |
| CI | Build 14 succeeded |
| Test deployment | Build 15 succeeded |
| Report-to-model binding | Passed |
| Semantic model refresh | Completed |
| DAX KPI reconciliation | Passed: 668,665 respondents / 116,779 yes / 551,886 no |
| Rollback capture | Captured during build 15 |

Read the [sanitized evidence JSON](evidence/cicd_verification.json) for timestamps, the original deployed commit, failed attempts preceding the successful run, and the source-record checksum. Workspace IDs, connection IDs, account details and private artifact paths have been omitted. The extract is maintained by the author and is not an independent attestation.

Original Azure DevOps source commit: `8e8e4f74a03efb91fbd2c6211fd2809ca532b851`. Historical source identities remain recorded as plain text; privacy cleanup of public Git history can change GitHub commit hashes.

The Azure DevOps project requires access. Public readers can inspect the [CI YAML](../ci/azure_pipelines.yml), [CD YAML](../ci/azure_pipelines_test_cd.yml), [deployment procedure](deployment/test_cd.md) and evidence above without an account. An original Azure DevOps UI screenshot is not included.
