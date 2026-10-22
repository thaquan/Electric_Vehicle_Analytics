# Test release acceptance - 17 October 2026

This record describes source `295e26da7aa1ea3c0cbe629ff83230f6ccafdbd2`
and the Test deployment produced by CI #67 and CD #70. Its results apply to
that release; later source changes require their own validation.

| Check | Recorded result |
| --- | --- |
| Regression tests | 118 unit, 8 Spark and 3 Airflow tests passed, with zero skips. |
| Test deployment | Refresh completed; model binding and report-definition readback matched the packaged release. |
| KPI | 668,665 respondents: 116,779 with purchase intent and 551,886 without. |
| Service interactions | Representative slicer, reset, navigation, tooltip and cross-filter cases passed using Windows UI Automation. |
| Local reproduction | All six processing stages completed and published eight Gold tables. Schema, key, 35-group reconciliation and Silver reconstruction checks passed. |
| Rollback package | Captured definitions passed package verification. A live rollback drill was not performed. |

Azure CI [#67](https://dev.azure.com/thaquan081006/Electric_Vehicle_Analytics/_build/results?buildId=67),
run `20261017.3`, produced the artifact deployed by
[CD #70](https://dev.azure.com/thaquan081006/Electric_Vehicle_Analytics/_build/results?buildId=70).
The [release evidence](evidence/acceptance_20261017.json) records the artifact
identity, checksums and reproduction results. The
[Service UAT evidence](evidence/service_uat_20261017.json) records observed
interactions; the [UAT guide](deployment/service_uat.md) defines repeatable cases.

The [dashboard images](screenshots/README.md) distinguish Desktop previews
from the Service capture. Interaction checks cover representative paths rather
than every possible selection. These records are author-maintained summaries,
not independent attestations.

For a new verification, follow the [clean rehearsal guide](operations/clean_rehearsal.md)
and [repository synchronization procedure](operations/repository_sync.md).
