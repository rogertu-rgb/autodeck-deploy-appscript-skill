# Report Interaction and Analysis Contract

This contract turns AutoDeck section tabs into a seller-facing diagnosis report, not a raw-data viewer.

## Formatting

- Use a sticky top header with seller name, report month, source Sheet link, and section search.
- Use a left section rail on desktop and a stacked flow on mobile.
- Start the report body with a compact summary grid that surfaces the first evidence-linked signals.
- Immediately expose storyline gate decisions in the executive area:
  - Site Anomaly
  - Category Dynamics
  - Subsidy Health
  - Market Position
- Each section should use this order:
  1. title and source-row status
  2. primary chart or visual table driven by `sec_config.chart_type`
  3. visible filterable important-row table
  4. compact evidence cards generated from section rows
  5. generated key takeaways
  6. collapsible source table
- Metric cards and tables alone are never sufficient for a section. Every section must expose a chart-like primary visual before analysis: bar/line, stacked bar, matrix/heatmap, scatter, tile/treemap, diagnostic card grid, or gated route visual for no-row drill sections.
- Section 1 / `sec_12m_history` is an exception to generic bar/line fallback: render it as a screenshot-style stacked monthly bar chart where each month stacks site-level `adg`, labels the monthly `total_adg` above the bar, uses `M/1/YYYY` x-axis labels, and shows a site legend. Do not render a dual-axis bar/line chart for this section.
- Keep typography dense and operational. Avoid marketing-page hero treatment, decorative gradients, or long explanatory UI copy.

## Interaction Components

- The report is generated as standalone HTML/JS, but it should behave like a composed component UI: shell, nav rail, section accordion, chart module, important-row table, evidence chips, analysis block, and source table each have a clear role.
- Do not remove `bindInteractions()`, `focusEvidence(...)`, `#section-search`, `data-target-section`, or `data-toggle-section` when changing visuals.
- ECharts modules must initialize after the DOM has measurable width, dispose stale instances before re-render, and resize via `ResizeObserver`.
- The page must render from embedded `AUTODECK_LOCAL_DATA` for local preview and still attempt `google.script.run.loadAutodeckData()` for deployed Apps Script data refresh.
- Use the project golden report artifact as the behavioral baseline, not just a screenshot style sample.

## Gate Decisions

- If the Sheet has a `Gate Config` tab, use it for thresholds and gate names.
- If `Gate Config` is absent, derive gates from section rows:
  - Site Anomaly: site `adg_share > 10` and absolute `seller_adg_mom > 5`
  - Category Dynamics: absolute L1 `adg_mom > 10`
  - Subsidy Health: `subsidy_share > 40`
  - Market Position: absolute `adg_gap_pp > 5`
- Show triggered and reference gates; do not omit untriggered gates.
- Gate cards should include a short reason and evidence action when source rows exist.

## Analysis Generation

- Do not show raw `sec_text` placeholder templates as analysis.
- Treat `sec_text` as historical framework notes only. The visible analysis must come from computed section analyzers in `render/engine.py`.
- Follow `section-analysis-harness.md` for per-section diagnostic rules and thresholds.
- Prefer specific signal rules when columns are available:
  - site benchmark: current ADG, seller MoM, benchmark gap pp, ADG/ADO share
  - L1 overview: top L1 share/ADG, strongest decline/growth, benchmark gap pp
  - site x L1 matrix: largest site-category cell, concentration, largest gap
  - 12-month history: latest total ADG, total trend, latest top-site share
  - fulfillment: dominant fulfillment mode and mix shift
  - traffic and AMS: channel share, spend, ROAS, ads reliance
  - subsidy: subsidy/ADG load, seller-funded mix, total subsidy
  - price band: seller share, share shift, price bias
  - shop impact: contribution and ADG delta
- If a section has rows but no known metric columns, generate conservative generic bullets from scale, share, movement, and efficiency columns.
- If a section has no rows, show a clear data-gap takeaway.

## Evidence Links

- Every numeric claim in a generated bullet must include an evidence chip.
- Evidence chips must show the row label, metric label, and formatted value.
- Clicking an evidence chip must open the section source table, scroll to the row, and highlight the exact cell when possible.
- Section analysis may only link to evidence from the same section.

## Data Handling

- Format month serials as `YYYY-MM`.
- For the Section 1 screenshot-style chart only, format month serials as `M/1/YYYY` on the x-axis to match the visit-report reference.
- Format large values compactly (`K`, `M`, `B`) and percentages/gap columns with `%` or `pp`.
- Convert technical column names into seller-readable labels in tables and evidence chips.
- Use `sec_config.chart_type` to select chart type when present. Supported fallbacks include bar/line, stacked bar, heatmap, scatter, tile/treemap, and table.
- If a section tab is missing but a `<section_id>_meta` tab exists, use the meta tab as the section data surface.
- Meta tabs must be parsed into charts where possible, not rendered as raw key/value tables in the primary visual.
- Missing/no-row drill sections should render a gated route visual rather than a blank or raw-data panel.
- Filterable important-row tables should rank rows by scale, concentration, movement/gap, efficiency, and spend/subsidy signals.
- Preserve the full source table for auditability, but keep it collapsed by default.
