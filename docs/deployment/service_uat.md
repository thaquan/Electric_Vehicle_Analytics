# Power BI Service acceptance

Run these checks against the **Test report deployed from the selected successful
CI artifact**. Record the CI run, CD run, source commit, report/model IDs, UTC time,
tester, actual values and screenshot or other direct UI evidence for each case.
API readback, DAX and Desktop screenshots are supporting checks; they do not
establish that a Service button, hover or chart selection worked.

The 17 October run is recorded in [sanitized UAT evidence](../evidence/service_uat_20261017.json).
It exercised 17 KPI/filter/tooltip observations, the six directed page-navigation
paths, the active-page buttons and independent page slicers through Windows UI
Automation. Hover checks verified the actual `Segment context` page. The target
page needs top-level `"type": "Tooltip"`; `pageBinding.type` alone left Desktop
treating it as a Standard page. Native screenshots and UI snapshots established
the correction. Hard reload was needed after deployment because an ordinary
reload initially reused an older report definition.

Open the Test report using the report ID in `config/environments/test.json`.
Start in reading mode, use **Reset to default** to remove persistent filters,
and clear any chart selections before each independent case. A page's **Reset
slicers** button clears its slicers; clear chart selections separately.

| ID | Action | Expected result |
| --- | --- | --- |
| UAT-01 | Open each of the three visible pages with default filters. | No visual errors; baseline 668,665 respondents, 116,779 interested, 17.46% displayed intent. Hidden `Segment context` is absent from ordinary page navigation. |
| UAT-02 | On Executive, set City to Urban; repeat independently on Charging. | Both show 289,305 respondents, 46,595 interested, 16.11%; dependent charts/insight text update. |
| UAT-03 | On Customer Segments select Income 100k+, then Age 65+. | 19,832 respondents, 5,299 interested, 26.72%; bubbles remain inside the plot. |
| UAT-04 | Add Age 55-64 while retaining 65+ and Income 100k+. | 59,971 respondents, 17,085 interested, 28.49%; heatmap/profile/combo respond. |
| UAT-05 | With a non-default slicer selection, click the page's Reset slicers button; repeat on all three pages. | Slicers return to All and baseline KPIs return after chart selections are cleared. No navigation occurs. |
| UAT-06 | Use every page-navigation button from each visible page. | Correct destination and active-page styling; slicers remain independent per page. |
| UAT-07 | Hover a populated cell on each heatmap. | Report-page `Segment context` tooltip renders the selected cell's respondents, interested count, intent rate, population share, commute and cars owned; compare with an equivalent DAX filter. |
| UAT-08 | Select a matrix cell, bubble and native chart mark; clear each selection. | Other analytical visuals and cards filter to the selection, then return. Image-based SVG dumbbells/lollipops respond to filters but do not emit chart selections. |
| UAT-09 | Exercise a supported no-data filter combination, if available. | Blank charts and dash callouts, no visual error. If no such slicer combination exists, record not applicable with reason; do not alter the published report just to manufacture a case. |
| UAT-10 | Reopen the report and compare the accepted release identity and screenshots. | Same report/model IDs and accepted definition inventory; evidence clearly distinguishes Service captures from the 15 October Desktop captures. |

Statuses are `passed`, `failed`, `not_verified`, or `not_applicable` with a
reason. A failed or unverified required case blocks full portfolio acceptance.
Do not infer a report defect from an automation tool's inability to click a
control. Preserve the actual values and failed attempt before retrying.

For repeat runs, use Windows UI Automation or manual interaction with an
authenticated Service session. Keep raw captures and traces under ignored
`output/`; publish reviewed evidence with its source and checksums.
