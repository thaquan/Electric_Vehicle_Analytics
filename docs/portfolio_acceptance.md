# Portfolio acceptance — 17 October 2026

The report release and representative Service interactions passed. This record
summarizes the release, documentation, repository checks and reproduction run
reviewed on 17 October 2026. Service interactions were tested with Windows UI
Automation.

| Area | Evidence at review | Result |
| --- | --- | --- |
| CI/CD and Service UAT | CI #67: 118 Unit, 8 real Spark and 3 Airflow tests passed, zero skips. CD #70 consumed that exact artifact, refreshed the model, checked Gold binding/KPI and compared every report part. Seventeen UI observations, navigation, resets and representative cross-filter paths passed. | Passed. |
| Documentation | README points to the verified Test report. Runbooks, release/source identity, a [Service capture](screenshots/service_charging.png), Desktop previews and sanitized evidence identify their actual sources. | Updated and reviewed. |
| Repository controls and mirror preparation | Azure main required CI and Test Exclusive lock verified. GitHub main requires PRs, includes admins, blocks force-push/deletion and needs zero external reviewers for this personal portfolio. The local mirror used the public history and matched accepted source content. | Controls and local content comparison passed. Remote publication was not verified in this record. |
| Reproduction | Fresh Python 3.13 environment from pinned requirements; `pip check` passed; four CSV checksums matched. Frozen-source execution returned Python exit 0 and published after all six stages, eight tables, 35 segment groups, zero orphans and exact Silver reconstruction. All eight Gold tables reconciled with the retained reference, including schema and duplicate-sensitive rows. | Passed; process-exit and data evidence retained. |
| Final review | Open GitHub issues and non-closed Azure work items were empty at the review. The clipped Service cards and inactive report-page tooltip were fixed and retested. Azure PR #17 passed required build validation #68 and merged as `0d09c51`. | Technical acceptance passed. |

## Accepted release and UAT

Source commit: `295e26da7aa1ea3c0cbe629ff83230f6ccafdbd2`.
Azure CI [#67](https://dev.azure.com/thaquan081006/Electric_Vehicle_Analytics/_build/results?buildId=67),
run number `20261017.3`, produced the release used by
[CD #70](https://dev.azure.com/thaquan081006/Electric_Vehicle_Analytics/_build/results?buildId=70).
Downloaded evidence identifies CI build 67, successful refresh, complete report
readback equality and KPI 668,665 / 116,779 / 551,886. Its sealed rollback was
verified locally; a live rollback drill was not performed.

Windows UI Automation exercised the authenticated Test report. The initial
report-only candidate came from a sealed archive of that commit, and every
report part matched both the downloaded CI #67 artifact and CD #70's later
readback. Hover checks confirmed the actual `Segment context` page and all six
metrics. Matrix, line-chart and bubble selections changed the other KPI/charts;
the page reset buttons and independent slicers behaved as documented.

Read the [sanitized release evidence](evidence/acceptance_20261017.json),
[UAT observations](evidence/service_uat_20261017.json) and
[repeatable UAT matrix](deployment/service_uat.md). The checks cover
representative paths, not every possible selection. Every one of the 180 atomic
slicer combinations per page has records, so the published slicers cannot produce
the manufactured empty state previously tested in a disposable Desktop copy.

## Rehearsal record

Raw evidence remains under ignored `output/acceptance-20261017/`. The frozen
source inventory is `final-rehearsal/source-manifest.json`; data runs and their
sealed publication markers are retained separately. Results include the expected
dimension sizes 45 / 4 / 16 / 2 / 30 and zero differences in all eight Gold tables
against the retained `review_fix_20261003_03` reference. Lineage values alone are
excluded from that row comparison; schemas remain checked.

Earlier attempts are preserved: a run was invalidated by concurrent source edits,
PowerShell stream redirection emitted a misleading post-run wrapper error, local
Arrow DAX returned 401 before updates, and CD #69 rejected a resource version
before creating a job. Frozen-source execution, direct subprocess exit capture,
the supported local JSON DAX path, and CD #70's correct run-number selection
provide the corresponding verification. These attempts are not counted as passes.

The unused 89,995-byte `customer_profile.png` was removed from the current tree
after checking references and verifying a local backup. Its checksum/blob/recovery
commit are in the [retirement inventory](evidence/retired_artifacts_20261017.json).
The older 12-measure export remains labeled as historical; data, rollback packages
and remote history remain preserved. See the [retention decisions](operations/clean_rehearsal.md#retention-decisions).

## Repository synchronization

Azure Repos is the source for required CI/CD; GitHub is the public portfolio
mirror with a separate history. At this review, the initially fetched main trees
matched despite different commit IDs, and the release mirror was prepared and
scanned locally. The publication procedure preserves both histories and merges
changes through a PR.

To verify synchronization after a mirror PR is merged, follow the
[mirror runbook](operations/repository_sync.md): fetch both remotes, then run
`scripts/check_repository_sync.py` to compare their trees.
