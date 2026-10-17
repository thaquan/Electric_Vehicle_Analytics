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
| Desktop rendering | The three [committed screenshots](screenshots/README.md) match the reviewed 15 October captures in `output/remediation-20261015/after`. They show the local preview backed by the exported Gold snapshot. |
| Narrative DAX | Local `output/redesign/dax-evidence.json`, dated 13 October 2026, records read-only `DEFINE MEASURE` queries against Fabric. Cases include baseline, age/income, charging/subsidy, Urban, empty selection and anxiety ordering. Query-scoped definitions do not establish that measures were persisted in Service. |
| Release guard | All 12 core names are required; extra measures are allowed. Missing core measures fail even when replaced by the same number of other measures. |
| CI | 110 local unit tests passed without skips; Azure builds 54 and 55 succeeded and PR #13 completed. See [CI evidence](cicd_evidence.md). |
| Dev Service deployment | On 14 October 2026 the existing Dev semantic model `8e7e37b7-7bab-4122-84fb-3ae7b2121cd7` and report `ae4d7c59-759e-4462-afed-1717475ae012` in workspace `5fe78794-25c3-41ee-b35e-bc56542d2cea` were updated in place from source commit `edf7114`. The live model was read back with all 29 measures, its Automatic OneLake connection still targeted Dev Gold lakehouse `32e99e91-38e9-4428-8fd2-6bcff6573088`, and DAX returned 668,665 respondents / 116,779 Yes / 551,886 No. The live PBIR was read back with Executive Overview 19 visuals, Charging & Incentives 20, Customer Segments 22, hidden Segment context 7, for 68 total visuals, and remained bound to the same semantic model. Fabric Service normalized returned PBIR JSON and added its shared base-theme resource, so byte-for-byte payload equality is not used as the acceptance criterion. |

The recorded baseline is 668,665 respondents, 116,779 interested respondents
and a 17.4645% purchase intent rate. Observed gaps are 6.87 percentage points
for home charging, 26.89 for subsidy availability and 24.83 for income
(100k+ versus under 50k). These are unadjusted associations in synthetic data.

Local evidence files are excluded from Git. The DAX record predates final SVG
rendering adjustments, so it supports the recorded calculations and filter
cases rather than byte-for-byte validation of the final SVG expressions.

## Presentation fixes verified on 15 October 2026

The generator now enables scatter marker auto-fit on both bubble charts,
labels the charging heatmap's row and column dimensions explicitly, shortens
the anxiety Y-axis title, and assigns blue to the combo chart's Respondents
columns to match its legend. The intent line remains green.

The three committed screenshots were replaced with reviewed Desktop Import
preview captures. Baseline remains 668,665 respondents, 116,779 interested and
17.46% displayed intent. Full online PBIR validation passed with zero errors
and warnings; a second generator run produced identical bytes. The model,
report binding, page IDs and inventory (68 visuals, 29 measures) are unchanged.

Actual Desktop slicer checks covered City=Urban on Executive and Charging
(289,305 / 46,595 / 16.11%), Income=100k+ on Customer Segments, and that income
with Age=65+ (19,832 / 5,299 / 26.72%) and ages 55–64 plus 65+
(59,971 / 17,085 / 28.49%). Bubbles remained inside the plot area and the
profile, heatmap and combo responded. An impossible City page filter applied
only to the disposable preview exercised the empty state: blank charts and
dash callouts, with no visual error. This was a controlled render case, not
a value selected from the slicer. Baseline overlaps between nearby points
remain; auto-fit fixes clipping without moving data points or changing size
encoding. The city comparison and segment matrix provide readable values.

Local raw evidence is under `output/remediation-20261015/`; it is ignored by
Git. The temporary empty-case preview also encountered a schema-fetch warning
for a Desktop-upgraded 2.13.0 visual schema. That does not alter the zero-warning
validation of the committed source or its initial generated preview.
These checks do not establish Service rendering, reset-button behavior,
all chart-selection paths, or the custom report-page tooltip content.

## Remaining acceptance

Full navigation/reset and chart-selection behavior, tooltip interactions and
Power BI Service rendering still need explicit browser-level acceptance. Static
screenshots, structural validation and API calculations do not establish those
UI outcomes. The Dev deployment itself is now established by the 14 October 2026
read-back checks above; remaining acceptance is specifically visual rendering
and interaction behavior in the published Service report.

See the [report guide](architecture/powerbi_report.md) for rebuild and preview
commands, and [Test deployment](deployment/test_cd.md) for release handling.
