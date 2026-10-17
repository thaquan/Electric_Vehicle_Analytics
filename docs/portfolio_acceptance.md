# Portfolio acceptance — 17 October 2026

This record covers delivery and final review items 3–7. It distinguishes the
previous deployed source from the presentation/readback changes currently under
verification. Playwright is excluded by the user's instruction.

| Item | Current evidence | Acceptance |
| --- | --- | --- |
| 3. CI/CD and Service UAT | Previous CI #63 / CD #64 inspected; PBIR schema validation passed with zero errors/warnings. New artifact and Windows-native Service interaction checks are in progress. | Pending current release and required UAT cases. |
| 4. Documentation | Deployment/runbook boundaries corrected; [UAT matrix](deployment/service_uat.md), [mirror procedure](operations/repository_sync.md) and [clean rehearsal](operations/clean_rehearsal.md) added. Current README screenshots remain the labeled 15 October Desktop captures. | Pending final run identities and evidence. |
| 5. GitHub/Azure | Both fetched main refs shared tree `62e219fcd5873adbeacf5de55342dcfe7e497112`. Azure required CI policy and Test Exclusive lock verified. GitHub main protection applied and read back: PR required, admins included, zero external approvals, no force-push/deletion. | Controls passed; synchronize this change after review. |
| 6. Reproduce and reduce | Fresh Python 3.13 environment installed from combined requirements/constraints; `pip check` passed; 117 baseline unit tests passed with zero skips. Four raw source checksums matched. A frozen source snapshot completed all six stages with exact Silver reconstruction, eight Gold tables, 35 segment groups, zero orphans and expected KPI. | Reconciliation and final frozen-source suites in progress. |
| 7. Final review | GitHub open issues and Azure non-closed work items both returned empty on 17 October. Local findings and unverified UAT remain tracked here. | Pending the remaining gates; no full acceptance claimed yet. |

## Previous deployed artifact

Azure CI [#63](https://dev.azure.com/thaquan081006/Electric_Vehicle_Analytics/_build/results?buildId=63)
and CD [#64](https://dev.azure.com/thaquan081006/Electric_Vehicle_Analytics/_build/results?buildId=64)
used commit `fa9e0fa701951ef73f07c88c29ffb864c604c622` on 14 October.
Downloaded CD evidence identifies CI build 63, successful refresh and KPI
668,665 / 116,779 / 551,886. These runs precede the pending presentation fixes
and report readback gate. Their success is historical evidence, not proof that
the current source was deployed.

## Rehearsal record

The isolated source inventory is under ignored
`output/acceptance-20261017/rehearsal/source-manifest.json`; full data output is
under `output/acceptance-20261017/full-pipeline/runs/acceptance_20261017/`.
Its run report and publication marker passed, with respondents / Yes / No of
668,665 / 116,779 / 551,886 and dimension sizes 45 / 4 / 16 / 2 / 30.
The sandbox process emitted a post-run `Access denied` during child cleanup;
that wrapper exit is retained and will be rechecked outside the sandbox before
final command-level acceptance. An earlier Spark test run was invalidated by
concurrent source edits; its failed context gate is retained rather than counted
as a pass. Final suites must run against frozen source.

Historical files are retained with explicit roles in the
[retention table](operations/clean_rehearsal.md#retention-decisions). No remote
history, source snapshot or rollback artifact was deleted during this review.
