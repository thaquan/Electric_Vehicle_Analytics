# Dashboard screenshots

The README uses these reviewed Desktop captures from 17 October 2026:

| Page | Current image |
| --- | --- |
| Executive Overview | [executive_overview.png](executive_overview.png) |
| Charging & Incentives | [charging_incentives.png](charging_incentives.png) |
| Customer Segments | [customer_segments.png](customer_segments.png) |

They show the disposable Desktop Import preview backed by the exported Gold
snapshot, including full-width KPI callouts and the presentation fixes. The
visible definitions match the report packaged by CI #67 from `295e26d`; the
tooltip-page type correction does not change these three visible pages. Raw
captures are retained under `output/acceptance-20261017/desktop-cards/`.

[service_charging.png](service_charging.png) is a direct Windows screenshot of
the authenticated **Power BI Service Test report**, captured after the report
deployment from `295e26d` and a hard browser reload. It is separate from the
Desktop README images. Service interaction snapshots, selected-state images
and tooltip captures are retained locally; their values/checksums are summarized
in the [Service UAT evidence](../evidence/service_uat_20261017.json).

The unused `customer_profile.png` was removed from the current tree after a
reference check and verified local backup. Its 89,995-byte content, SHA-256,
Git blob and recovery commit are recorded in the
[retirement inventory](../evidence/retired_artifacts_20261017.json).

`cicd_evidence.svg` illustrates the archived 2 October deployment evidence;
it is not an Azure DevOps UI screenshot or evidence of the redesigned report's
deployment. See [CI/CD evidence](../cicd_evidence.md) for the separate runs.
