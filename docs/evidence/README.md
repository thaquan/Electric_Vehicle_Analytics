# Release evidence

These records identify the source release, checks performed and limitations.
Results apply to the recorded deployment, not to subsequent source changes.

| Record | Scope |
| --- | --- |
| [CI/CD verification, 2 October](cicd_verification.json) | Archived deployment results and artifact identity. |
| [Acceptance, 17 October](acceptance_20261017.json) | CI #67, CD #70, refresh, KPI, report readback and local reproduction. Repository controls describe that review date. |
| [Service UAT, 17 October](service_uat_20261017.json) | Representative interactions with the deployed Test report. |

These are author-maintained evidence summaries, not independent attestations.
Raw API responses, traces, maintenance journals and intermediate test output
belong in ignored `output/` or CI/CD artifacts.

Use the [repository synchronization procedure](../operations/repository_sync.md)
to compare current remote source trees. Use the
[metadata guide](../../metadata/README.md) for pinned snapshot provenance,
manifest checksums and historical recovery statuses.
