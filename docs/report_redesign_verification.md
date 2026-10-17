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
| Desktop rendering | The three [committed screenshots](screenshots/README.md) are the reviewed 17 October captures in `output/acceptance-20261017/desktop-cards`. They show the local preview backed by the exported Gold snapshot and the same visible report definitions as CI #67. |
| Narrative DAX | Local `output/redesign/dax-evidence.json`, dated 13 October 2026, records read-only `DEFINE MEASURE` queries against Fabric. Cases include baseline, age/income, charging/subsidy, Urban, empty selection and anxiety ordering. Query-scoped definitions do not establish that measures were persisted in Service. |
| Release guard | All 12 core names are required; extra measures are allowed. Missing core measures fail even when replaced by the same number of other measures. |
| Archived CI, 13 October | 110 local unit tests passed without skips; Azure builds 54 and 55 succeeded and PR #13 completed. Current CI #67 separately records 129 passed across Unit/Spark/Airflow. See [CI evidence](cicd_evidence.md). |
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

## Test acceptance completed on 17 October 2026

The current Test report comes from `295e26d`, CI #67 and CD #70. Packaging includes
the referenced shared base theme and the Service-canonical report binding, so
the new CD gate compares every returned report part, allowing only JSON formatting
and Service `.platform` metadata differences. CD refreshed the model and passed
the pinned KPI checks; the rollback package remains retained.

Windows-native Service UAT found and corrected clipped KPI callouts and the
context page's missing top-level `type: Tooltip`. Full-width callouts with zero
internal padding render complete values. Actual heatmap hovers now display the
six context metrics; the 65+/100k+ tooltip returned 19,832 / 5,299 / 26.72%,
2.97% population share, 32.6 km commute and 1.71 cars owned.

Seventeen value/filter/tooltip observations, reset on all three pages, six
directed navigation paths, active-page buttons, representative matrix/chart/bubble
selections and independent page slicers passed. Native captures and UI snapshots
support the [sanitized UAT record](evidence/service_uat_20261017.json).
All 180 atomic slicer combinations per page have data, so an empty selection
cannot be manufactured from the offered slicers; the older disposable Desktop
empty-filter check remains historical. These checks cover representative paths,
not every possible user selection. Playwright was excluded by the user.

See the [report guide](architecture/powerbi_report.md) for rebuild and preview
commands, and [Test deployment](deployment/test_cd.md) for release handling.
