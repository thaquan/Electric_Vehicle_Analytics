# EV Analytics design brief

## Scope

Apply the user's automotive references to the existing survey report. Keep all
report text in English and use **EV purchase intent** consistently. The model
has no transaction dates, purchase prices, brands, models or geographic locations;
those analyses are outside this report's data scope.

## Layout and palette

- Canvas: 1600 × 900, 16:9.
- Left rail: brand, page navigation, four slicers, Reset slicers, snapshot date.
- Main area: title, context line, four KPI callouts, three charts and source note.
- Navy canvas `#0B1220`; card surfaces `#131E2F`; borders `#26354B`.
- Mint `#34D399` for rates; blue `#38BDF8` for respondent counts.
- Text `#F8FAFC`; secondary text `#94A3B8`; Segoe UI.
- Executive Overview is the portfolio cover page. All five age groups must be
  visible without scrolling. Keep income and commute groups in model sort order.

## Verification

PBIR schema validation passes. Desktop screenshots confirm live data on all
three pages, visible English labels and full category lists. The baseline KPI
remain 668,665 respondents / 116,779 intending / 551,886 not intending / 17.46%.
Navigation and Reset slicers have native Power BI actions configured; clicking
them and chart cross-filter checks are still pending. The Urban slicer check and
clearing its selection pass. Publication was confirmed in the Fabric catalog on
2026-09-27 (report ID `ae4d7c59-759e-4462-afed-1717475ae012`).

Rebuild with `node scripts/build_report.cjs` then `node scripts/style_report.cjs`.
