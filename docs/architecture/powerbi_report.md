# RPT_EV_Analytics ? Phase 6

## Status on 2026-09-27

- Created `RPT_EV_Analytics.pbip` and `RPT_EV_Analytics.Report`.
- The report connects to the existing `SM_EV_Analytics`
  (`8e7e37b7-7bab-4122-84fb-3ae7b2121cd7`) in `WS_EV_Analytics`.
- No pipeline rerun, model refresh, or model modification was performed for this report work.
- SQL analytics endpoint execution was skipped by user request, not passed.
- PBIR CLI validation: **zero errors and zero warnings**; see `metadata/report_validation.json`.
- Opened the report in Power BI Desktop and checked live data and screenshots of all
  three pages. Overview matches 668,665 / 116,779 / 551,886 / 17.46%; the other eight
  KPI match the DAX evidence after rounding. Screenshots are in `docs/screenshots/`.
- All report text is in English and uses **EV purchase intent**. Reloaded and checked
  for visual errors and clipped text.
- Published to `WS_EV_Analytics`; the Fabric catalog confirmed report ID
  `ae4d7c59-759e-4462-afed-1717475ae012` on 2026-09-27.
  [Open report](https://app.powerbi.com/groups/5fe78794-25c3-41ee-b35e-bc56542d2cea/reports/ae4d7c59-759e-4462-afed-1717475ae012).
- Tested City type = Urban using Windows UI Automation: 289,305 respondents,
  46,595 intending, 242,710 not intending, and a 16.11% rate; all match the reference.
  Clearing the slicer restores 668,665. Evidence: `docs/screenshots/overview_urban_filter.png`.
- Navigation/reset, chart cross-filter, and remaining Service rendering tests are
  **skipped by user request**, not passed. Playwright was not used.
- Phase 7 export and manifest evidence is in the [export guide](../pipelines/gold_export.md).
  For subsequent isolated recovery results, see the [project acceptance summary](../project_summary.md).

## Contents

| Page | KPI | Charts and slicers |
| --- | --- | --- |
| Executive Overview | Respondents; intending/not intending to buy EV; purchase intent rate | City type distribution; rates by age and income. Slicers: city type, gender, age, income. |
| Charging & Incentives | Home charging access; subsidy availability; average chargers near home/work | Purchase intent by home charging, subsidy, range anxiety. Slicers: home charging, subsidy, range anxiety, city type. |
| Customer Profile | Average annual income USD, age, commute km, cars owned | Income and age distributions; purchase intent by commute. Slicers: income, age, city type, commute. |

Each page has one card with four KPI, three charts, four slicers, seven text boxes,
and four buttons: 57 visuals in total. Slicers operate independently on each page
and allow multiple selections.

The automotive dark design uses a 1600 x 900 canvas (16:9), navy `#0B1220`,
card surfaces `#131E2F`, mint `#34D399` for rates, and blue `#38BDF8` for counts.
The sidebar contains three navigation buttons and **Reset slicers**, which clears
slicers on the current page, not every filter or chart selection. In Desktop edit
mode, use Ctrl+click to run button actions. Live button and chart cross-filter
behavior has not been accepted as passed.

**Survey snapshot** shows the verified Gold snapshot date, not the live refresh time.
Slicer/chart interactions with KPI and other charts use `DataFilter`.
Age, income, and commute bands follow semantic model sort order. All KPI use
explicit measures; the two Gold aggregate tables are not summed in the report.

The dashboard describes **EV purchase intent** in synthetic data. It does not
represent actual sales, conversion rates, or causal effects.

## Open and publish

1. Open `RPT_EV_Analytics.pbip` in Power BI Desktop with PBIP/PBIR support.
2. Sign in with access to `SM_EV_Analytics` in `WS_EV_Analytics`.
3. Check all three pages with live data using the checklist below as applicable.
4. Publish to `WS_EV_Analytics` as `RPT_EV_Analytics`.
5. Save the report URL/ID and screenshots with the acceptance evidence.

`metadata/report_create_payload.json` was generated locally with CLI `pack --mode create`.
Its Fabric API request body is `data.body`, not the whole envelope. This generated
file is excluded from Git and is not evidence of publication to the Service.

## Checks in Power BI

The following values come from saved DAX evidence and were compared with all
12 KPI in Desktop screenshots after rounding.

| KPI with all filters cleared | Expected value |
| --- | ---: |
| Respondents | 668,665 |
| Intending to buy EV | 116,779 |
| Not intending to buy EV | 551,886 |
| Purchase intent rate | 17.46% |
| Home charging access | 69.19% |
| Subsidy availability | 62.80% |
| Average age | 47.0 |
| Average annual income USD | 84,769.27 |
| Average daily commute km | 32.2 |
| Average cars owned | 1.71 |
| Average chargers near home | 4.96 |
| Average chargers near work | 7.18 |

The following checklist describes expected behavior; it does not override skipped tests:

- Compare KPI and groups with `metadata/semantic_model_live_dax.json`,
  `metadata/semantic_model_profile_dax.json`, and `metadata/star_expected_metrics.json`.
- Select an age/income band: KPI and charts should update together; the rate should
  equal intending respondents divided by respondents in the current filter context.
- Combine city type, home charging, and subsidy in the Filter pane and compare
  with the groups in the DAX evidence.
- Select a chart bar: target visuals should filter. Clearing selections and filters
  should restore the original totals.
- Check multiple selections, clearing filters, and empty results (blank rate).
- Check titles, KPI labels, percentages, group order, and visual/text clipping errors.
- Capture all three unfiltered pages and at least one filtered state.

## Rebuild and validate structure

```powershell
node scripts/build_report.cjs
node scripts/style_report.cjs
.tools/node_modules/.bin/powerbi-report-author.cmd validate RPT_EV_Analytics.Report --out metadata/report_validation.json
.tools/node_modules/.bin/powerbi-report-author.cmd pack RPT_EV_Analytics.Report --mode create --display-name RPT_EV_Analytics --out metadata/report_create_payload.json
```

The scripts use the existing report structure and generate deterministic content
with stable IDs. Rerunning them overwrites script-managed visuals; preserve manual
edits first. Recheck structure and rendering after changes. PBIR validation does
not replace opening the report, querying live data, or testing interactions.
