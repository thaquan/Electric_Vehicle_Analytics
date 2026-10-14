# Power BI report

The report now has three distinct analytical pages, plus a hidden context tooltip.
The dark 1600 x 900 canvas remains; navigation and dropdown slicers run across the top.

| Page | Business question | Main visuals |
| --- | --- | --- |
| Executive Overview | Where do interest and scale meet? | Hero intent KPI, respondent/interested counts, city opportunity bubbles, ranked observed-gap lollipops, city comparison, dynamic insight |
| Charging & Incentives | Which conditions are associated with higher intent? | Charging/subsidy dumbbells, charging x subsidy heatmap, ordered anxiety trend, infrastructure comparison |
| Customer Segments | Which groups combine scale and intent? | Age x income heatmap, dynamic segment profile, age/income bubbles, age volume/rate combo, ownership trend |

Heatmap tooltips show respondents, interested respondents, intent rate, share of
population, average commute and cars owned. Selecting a matrix cell or chart point
filters the other analytical visuals and cards. Slicers are independent per page.
Reset slicers clears page slicers; clear chart selections separately. Desktop button
actions use Ctrl+click in edit mode.

## Measures and interpretation

The model contains 29 measures: 12 core measures plus 17 narrative measures in the
`Narrative analysis` display folder. All report values are data-bound.

- Opportunity map: X = interested respondents, Y = intent rate, bubble area = respondents.
- Segment bubbles: age and income jointly identify groups; X = respondents, Y = intent rate.
- Gaps: Yes minus No for charging/subsidy; 100k+ minus Under 50k for income.
  Each pair clears only its comparison attribute, retaining other filters.
  Gaps use percentage points, return blank when either endpoint lacks data,
  and are ranked by absolute magnitude with deterministic tie breaking.
- Dumbbells share a 0-100% scale. Their SVGs and the ranked lollipops are DAX
  ImageUrl measures rendered by native image visuals. They respond to filters,
  but do not themselves emit chart selections.
- Share of Population uses the full respondent population as denominator, subject
  to model security. It is not the share of the currently selected population.
- Heatmaps use one fixed 0-40% color scale; values above 40% saturate the color,
  while their numeric values remain visible. Blank cells remain blank.
- Anxiety uses the explicit Low -> Medium -> High order, never alphabetical order.
- The age/income bands come from the model; illustrative bands in the design
  proposal were not substituted for the actual data.

This is synthetic survey purchase intent, not sales or causal uplift.

## Rebuild

```powershell
node scripts/redesign_report.cjs
.tools/node_modules/.bin/powerbi-report-author.cmd validate RPT_EV_Analytics.Report --out output/redesign/validation-online.json
```

`build_report.cjs` and `style_report.cjs` are compatibility entry points for the same
generator, so the previous build commands cannot restore the old dashboard.
The generator preserves `definition.pbir`, report theme registration, page IDs and
model source bindings. It replaces visuals on the three managed pages, adds one
hidden tooltip page, and replaces only its marked measure block in the fact TMDL.
Preserve manual edits to those managed objects before rebuilding.

## Desktop verification copy

The committed semantic model remains Direct Lake. For local rendering from the
existing exported Gold parquet snapshot:

```powershell
node scripts/prepare_redesign_preview.cjs
# Open output/redesign/desktop/RPT_EV_Analytics.pbip, then refresh its local model.
```

This creates a disposable Import model under `output/redesign/desktop`; it does
not convert the committed model or update Fabric. The Gold export must already
exist under `output/gold_export_staging/source_parquet`.

See [redesign verification](../report_redesign_verification.md) for checks and
limitations. The three current Desktop captures are committed in
`docs/screenshots` as `executive_overview.png`, `charging_incentives.png` and
`customer_segments.png`. See the [screenshot inventory](../screenshots/README.md).
Additional local captures remain under `output/redesign/screenshots`.

## Publish

Deploy the updated semantic model measures together with the report. Publishing
only PBIR against a model that still has the original 12 measures will leave the
new narrative visuals without their required fields. CI validates the 12 core
measure names while permitting the 17 additions and future measures.

The Dev workspace was synchronized on 14 October 2026 by updating the existing
semantic model and report in place. API read-back verified 29 live measures,
the expected KPI counts, the existing Direct Lake/OneLake connection, and the
redesigned report structure with 68 visuals across three visible pages plus the
hidden `Segment context` tooltip page. The report remained bound to semantic
model `8e7e37b7-7bab-4122-84fb-3ae7b2121cd7`. Fabric may normalize returned PBIR
JSON and add a shared base-theme resource, so structural equivalence is the
relevant deployment check. Browser rendering and interaction behavior still
require explicit Service UI acceptance.
