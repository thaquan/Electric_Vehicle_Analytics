# Evidence scope and chronology

These records describe specific releases or checks. Read their timestamp, source
commit and limitations before applying a result to another deployment.

| Record | Scope |
| --- | --- |
| [Acceptance, 17 October](acceptance_20261017.json) | Test release and repository controls observed at that review. Its public mirror field records local preparation at that time. |
| [Service UAT, 17 October](service_uat_20261017.json) | Representative interactions with the deployed Test report. |
| [Repository publication and snapshot integrity, 21 October](repository_publication_20261021.json) | GitHub PR #4 and #5, Azure PR #19, required build policy #76, matching main trees after the documentation merges, and the subsequent manifest byte repair. |

The 21 October record supplements the earlier acceptance record. It does not
rewrite the 17 October publication status or claim a new Fabric deployment,
refresh, KPI check, Service UAT or recovery exercise. Build #76's approval was
read through the Azure policy API; its detailed test logs were not inspected
during this check.

The recorded tree equality applies to the listed commits. Subsequent changes
require another fetch and repository comparison. These are author-maintained
evidence summaries, not independent attestations.

The manifest integrity check found that the Git copy used LF line endings,
while the existing checksum described the retained export's CRLF bytes. The
follow-up restores the original export bytes: JSON values, recovery status and
the checksum sidecar are unchanged. The restored file matches the existing
SHA-256 `0da1b98e56c024261d247e3cfe94efaddb594cd52cce4eee89f6a8955cf1ad9f`.
This repair follows the repository comparison; the recorded matching main trees
do not yet include it.

The [metadata guide](../../metadata/README.md) explains the older Phase 7 and
September recovery references, including skipped checks and manual KPI
confirmation. Those outcomes remain attached to their original snapshots.
