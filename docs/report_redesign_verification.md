# Dashboard redesign verification

## Current source

The report has three visible pages: Executive Overview, Charging & Incentives,
and Customer Segments. Segment context is a hidden tooltip page. The PBIR
contains 68 visuals across all four pages. The current semantic model contains
29 measures: 12 core measures and 17 measures in `Narrative analysis`.

The model source is `SM_EV_Analytics.SemanticModel/definition/`; the older
`models/SM_EV_Analytics/` export contains only the 12 core measures. Keep the
current report and model definitions together when building a release.

## Recorded checks

| Check | Evidence and scope |
| --- | --- |
| Report structure | Local `output/redesign/validation-final.json` records `succeeded`, zero errors and zero warnings. This is a recorded validator result, not a new validation run. |
| Desktop rendering | The three [committed screenshots](screenshots/README.md) match the corresponding captures in `output/redesign/screenshots`. They show the local preview backed by the exported Gold snapshot. |
| Narrative DAX | Local `output/redesign/dax-evidence.json`, dated 13 October 2026, records read-only `DEFINE MEASURE` queries against Fabric. Cases include baseline, age/income, charging/subsidy, Urban, empty selection and anxiety ordering. Query-scoped definitions do not establish that measures were persisted in Service. |
| Release guard | All 12 core names are required; extra measures are allowed. Missing core measures fail even when replaced by the same number of other measures. |
| CI | 110 local unit tests passed without skips; Azure builds 54 and 55 succeeded and PR #13 completed. See [CI evidence](cicd_evidence.md). |

The recorded baseline is 668,665 respondents, 116,779 interested respondents
and a 17.4645% purchase intent rate. Observed gaps are 6.87 percentage points
for home charging, 26.89 for subsidy availability and 24.83 for income
(100k+ versus under 50k). These are unadjusted associations in synthetic data.

Local evidence files are excluded from Git. The DAX record predates final SVG
rendering adjustments, so it supports the recorded calculations and filter
cases rather than byte-for-byte validation of the final SVG expressions.

## Remaining acceptance

Full navigation/reset and chart-selection behavior, tooltip interactions and
Power BI Service rendering still need explicit acceptance. Static screenshots,
structural validation and API calculations do not establish these outcomes.
CI success and PR completion also do not prove a deployment to the Service
report linked from the README. Verify the deployed model/report versions and
repeat visual acceptance after publishing.

See the [report guide](architecture/powerbi_report.md) for rebuild and preview
commands, and [Test deployment](deployment/test_cd.md) for release handling.
