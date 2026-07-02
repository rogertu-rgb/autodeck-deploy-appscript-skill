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
- Section 1 / `sec_12m_history` is an exception to generic bar/line fallback: render it as a split diagnostic visual. The left panel defaults to a 100% stacked monthly site-share chart, labels monthly `total_adg` above each bar, uses `M/1/YYYY` x-axis labels, shows a site legend, and provides a toggle to absolute stacked ADG. The right panel separates GGP MoM%, Shopee overall MoM%, and Seller - Shopee gap pp so benchmark comparison text does not overlap the site-mix bars.
- For Section 1 / `sec_12m_history`, omit the generic row-filter dropdown above the source table. The chart already exposes site mix by color and tooltip; the source rows should remain a plain collapsible audit table.
- Section 1.1 / `sec_site_benchmark` must be titled `各站点增速对标大盘`, without the old L2 qualifier. It must answer current-month site attribution: sort sites by `abs(adg_gap_pp) * adg_share`, render a dumbbell comparison of Seller ADG MoM vs Market ADG MoM, keep Market/Seller dots equal size, and use only a thin gap connector. Do not encode share as bubble size, and do not use heavy orange/red row boxes that stack into thick borders.
- Section 1.2 / `sec_l1_overview` must answer "which site-category cells deserve drilldown". Use a site x L1 diagnostic matrix. Cell color encodes seller-market gap pp, the in-cell bar encodes `share_in_site`, and circular 1/2/3 markers identify the highest-priority cells by `abs(gap_pp) * share_in_site`. Do not reintroduce the old generic site filter or make Top5 tables the primary visual.
- Section 1.4 / `sec_l2_drill` must continue the L1 route with four attribution lanes: high-share underperformers, absolute scale leaders, fastest growers, and large-share decliners. This section should not rely on a crowded site x L2 heatmap as the primary view.
- Section 1.5 / `sec_l3_granular` must be a proof table, not a broad heatmap. Show share bars, ADG bars, seller MoM, P50 growth, seller-P50 gap, and an action tag. When P50 is missing, explicitly label the row as seller-side evidence and avoid benchmark-overclaiming.
- L2/L3 category identities must include the full available hierarchy everywhere they appear. L2 should read as `site / L1 > L2`; L3 should read as `site / L1 > L2 > L3`. Do not show only the leaf category in cards, proof tables, source-facing labels, or computed analysis because leaf names can be duplicated under different parents.
- Section 1.6 / `sec_volatility` must be titled `类目站点异常信号扫描` and rendered as an anomaly workbench. Parse `sec_volatility_meta` into a summary strip, seller-vs-market MoM quadrant scatter, priority queue, selected detail card, and linked Key Highlights. Rank actionability by `abs(gap_pp) * log(ADG+2) * confidence`; confidence should penalize low ADG, extreme benchmark gaps, and generic Other/Others paths. Default-hide low-confidence and low-volume noise but provide toggles for audit.
- Section 1.7 / `sec_shop_impact` must be titled `店铺贡献分析` and answer a site-root-cause workflow: first identify each site's key driver shops by absolute shop ADG delta, then dive those shops into `L3 × price_range` combinations, and show whether the movement is traffic-volume driven or conversion driven. After the standard builder, enrich `sec_shop_impact` from `raw_dws_shop` at shop x site grain and map shop names from `raw_dws_item` when available. The visual must show overall Top ADG/ADO shops, site key driver shops, L3×price-range gain/loss rows for those key shops, and traffic funnel diagnostics using `adimp`, `adclick`, `CTR = adclick/adimp`, and `CR = ADO/adclick`.
- Section 1.8 / `sec_listing_change` must be enriched from `raw_dws_item` / `cncbbi_general.autodeck__dws_item_rpt_mi`. The visual must expose best-selling listings, largest-growth listings, largest-loss listings, and item-level funnel fields. Use `CTR = mtd_adpv / mtd_adimp` and `CR = mtd_ado / mtd_adpv`.
- Section 1.9 / `sec_fulfillment` must show local fulfillment penetration by site. Use `fbs_ado` and `tpf_ado` as local fulfillment, `sls_ado` as cross-border, and show current local share plus MoM local-share movement.
- Section 2.0 / `sec_traffic_channel` and Section 2.1 / `sec_subsidy` must expose source and promotion levers as non-MECE driver signals. Do not draw a 100% stacked source split. Use heatmap/table views that make it clear that ADS, livestream, campaign, rebate, shipping rebate, CFS, and LPP can overlap.
- Section 2.4 / `sec_ams` must be titled `ADS出单效率审计`. Use site-level ADS efficiency metrics: Ads ADO%, Ads ADG%, Ads Spend/GMV, ROAS, and HE1 Ads ADG% (`ads_adg / total_adg` when no dedicated field exists). Use equal-size scatter points when plotting sites to avoid misleading bubble-size emphasis.
- Category drill visuals must not show no-data sites or categories. For `sec_l1_overview`, `sec_l2_drill`, and `sec_l3_granular`, include a row/cell only when seller-side current ADG, previous ADG, seller share, or seller MoM is present. Benchmark-only rows are allowed in collapsed audit data but must not appear in the seller-facing primary visual.
- Keep typography dense and operational. Avoid marketing-page hero treatment, decorative gradients, or long explanatory UI copy.

## Interaction Components

- The report is generated as standalone HTML/JS, but it should behave like a composed component UI: shell, nav rail, section accordion, chart module, important-row table, evidence chips, analysis block, and source table each have a clear role.
- Do not remove `bindInteractions()`, `focusEvidence(...)`, `#section-search`, `data-target-section`, or `data-toggle-section` when changing visuals.
- ECharts modules must initialize after the DOM has measurable width, dispose stale instances before re-render, and resize via `ResizeObserver`.
- The page must render from embedded `AUTODECK_LOCAL_DATA` for local preview and still attempt `google.script.run.loadAutodeckData()` for deployed Apps Script data refresh.
- Use the bundled golden contract or a user-provided `sections_review.html` artifact as the behavioral baseline, not just a screenshot style sample.

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
  - L2 lanes: high-share underperforming L2, absolute-scale L2, fastest-growing L2, and high-share declining L2
  - L3 proof: largest L3 scale, strongest growth/decline, P50 availability, and action route
  - volatility: actionable signal count after low-confidence filtering, top 1-3 anomaly paths ranked by `abs(gap_pp) * log(ADG+2) * confidence`, seller MoM vs market MoM, gap pp, ADG, and diagnostic route
  - 12-month history: latest total ADG, total trend, latest top-site share, and GGP MoM% versus Shopee overall MoM% when `shopee_adg_mom` is available
  - fulfillment: FBS/TPF/SLS mix, local fulfillment share, local-share MoM movement, and fulfillment coverage
  - traffic: non-MECE source driver ADO/ADG share and source gain/loss by site
  - subsidy: non-MECE promo/rebate/CFS/Campaign/LPP effectiveness and seller-funded pressure
  - ADS audit: ads ADO share, ads ADG share, spend/GMV, ROAS, and ads dependence
  - price band: seller share, share shift, price bias
  - shop impact: site key driver shops by absolute ADG delta, each key shop's traffic funnel movement, and the L3×price-range combinations where gain/loss happens
- If a section has rows but no known metric columns, generate conservative generic bullets from scale, share, movement, and efficiency columns.
- If a section has no rows, show a clear data-gap takeaway.

## Evidence Links

- Every numeric claim in a generated bullet must include an evidence chip.
- Evidence chips must show the row label, metric label, and formatted value.
- Clicking an evidence chip must open the section source table, scroll to the row, and highlight the exact cell when possible.
- Section analysis may only link to evidence from the same section.
- For top highlight takeaways, prefer compact circular `1/2/3` callouts. The same number must appear on the primary visual data point, the important-row table where practical, and the matching Chinese computed-analysis bullet so the reader can trace the claim without hunting. If a chart/table renders a numbered circle, the corresponding `数据诊断` text must include that same number and describe the same row/ranking logic; if the analysis cannot be generated, suppress the numbered circle. Do not add a second standalone takeaway list when it duplicates computed analysis.

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
