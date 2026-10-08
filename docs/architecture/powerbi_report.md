# Power BI report

Three pages connect to the Fabric semantic model and describe EV purchase intent.
The saved Desktop screenshots are in `docs/screenshots/`; see the [README](../../README.md#dashboard).
Structural validation and KPI comparisons have passed for the recorded report version.
Full navigation/reset, chart cross-filter and Service rendering acceptance remain unverified.

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

`metadata/report_create_payload.json` (local output; excluded from Git) was generated locally with CLI `pack --mode create`.
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

- Compare KPI and groups with `metadata/star_expected_metrics.json` and `metadata/gold_expected_metrics.json`.
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
