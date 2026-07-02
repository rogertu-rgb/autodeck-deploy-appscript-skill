# Content Guardrails

Use these rules for the generated seller-facing HTML.

## Section Structure

Every section follows:

```text
Title
Subtitle / trigger status
Data display: compact evidence cards, chart, table, or expandable full data
Analysis block with generated takeaways
Expandable source table when raw rows are available
```

Data must appear before analysis. If the raw table is collapsed, a compact evidence snapshot can satisfy the data-first rule as long as every analysis claim links to same-section source rows. If a section has no data, show a visible empty-state note before analysis.

Metric cards or raw/filterable tables alone do not satisfy the data display requirement. Each section must show a chart-like primary visual before the analysis block, then a filterable important-row table as supporting evidence when rows exist.

Section 1 (`sec_12m_history`) must expose two questions separately: site mix and market outperformance. Use a split diagnostic visual where the left panel defaults to 100% stacked monthly site share, includes total ADG labels and a toggle to absolute stacked ADG, and the right panel shows GGP MoM%, Shopee overall MoM%, and Seller - Shopee gap pp. Do not collapse these into one crowded dual-axis chart.

For Section 1, do not show the generic `All 站点` row-filter dropdown above the source table. It duplicates the site chart and looks inactive; keep the source table as a simple collapsible audit surface.

Section 1.1 (`sec_site_benchmark`) must be titled `各站点增速对标大盘` and must expose current-month site attribution. Use an equal-dot dumbbell for Seller ADG MoM vs Market ADG MoM, sorted by `abs(adg_gap_pp) * adg_share`. Share may drive sorting and labels, but not dot size. Use thin connectors and light row tinting only; avoid thick orange/red boxes or borders that visually merge when highlighted rows are adjacent.

Section 1.2 (`sec_l1_overview`) should be a site x L1 diagnostic matrix. Color = seller-market gap pp, in-cell bar = L1 share within that site, and circular 1/2/3 markers = priority cells ranked by `abs(gap_pp) * share_in_site`. This matrix replaces the old site filter + heatmap + Top5-table pattern.

Section 1.4 (`sec_l2_drill`) should be four attribution lanes: high-share underperformers, absolute scale leaders, fastest growers, and large-share decliners. This keeps L2 tied to the L1 drilldown story and avoids an unreadable wall of heatmap cells.

Section 1.4 data must be aggregated at `site × L1 × L2` grain. Do not aggregate directly by L2 leaf, and do not restrict the section tab to one selected L1. `share_in_l1` must divide the L2 current ADG by the total current ADG of the same `site × L1`; if a site/L1 has multiple active L2 rows, those rows should not all show 100%.

Section 1.5 (`sec_l3_granular`) should be a visual proof table with share bars, ADG bars, seller MoM, P50 growth, seller-P50 gap, and action tags. If P50 is missing, show `缺P50` / seller-side evidence and avoid claiming market outperformance or underperformance.

Category drill labels must preserve hierarchy. In Section 1.4, each visible L2 row/card/bullet must identify `site + L1 > L2`, not only the L2 leaf. In Section 1.5, each visible L3 row/card/bullet must identify `site + L1 > L2 > L3`, not only the L3 leaf. This is required because generic names such as `Other` and even normal L2/L3 names can appear under multiple parent categories.

Section 1.5 data must be aggregated at `site × L1 × L2 × L3` grain. Do not aggregate directly by L3 leaf, and do not collapse all `Other` / `Others` rows across parents. A generic leaf can be displayed only with its full parent path, for example `Computers & Accessories > Desktop & Laptop Components > Others`.

Section 1.6 (`sec_volatility`) should be titled `类目站点异常信号扫描` and shown as an anomaly workbench rather than raw signal cards. Use a summary strip, seller-vs-market MoM quadrant scatter, right-side priority queue, selected-signal detail card, and linked Key Highlights. Default-hide low-confidence noise: low ADG, extreme benchmark gap, and generic Other/Others paths. The visible priority should be ranked by `abs(gap_pp) * log(ADG+2) * confidence`, and the circular `1/2/3` markers must match the same Chinese computed-analysis bullets.

Section 1.5 (`sec_l3_granular`) must not show numbered Chinese analysis bullets unless the same `1/2/3` markers are visible in the primary proof table. If the visual cannot render the marker cleanly, render a normal bullet without the orange numbered circle.

Section 1.7 (`sec_shop_impact`) should be titled `店铺贡献分析`. It should not try to fill Top3 slots when a site has fewer real loss/gain shops. The primary path is: identify each site's key driver shop(s) by absolute ADG delta, then dive those shops into L3 x price_range combinations, and show traffic funnel diagnostics: `adimp` = average daily impression, `adclick` = average daily clicks, `CTR = adclick/adimp`, and `CR = ADO/adclick`. Use shop names when `raw_dws_item` can map them; otherwise show shop ID. Do not reduce this section to one concentration card, one waterfall chart, or one raw table.

Section 1.8 (`sec_listing_change`) must show actionable item-level evidence, not only a raw Top listing table. Use `raw_dws_item` from `cncbbi_general.autodeck__dws_item_rpt_mi`; show best sellers, biggest growth listings, and biggest-loss listings. For item funnel, use `mtd_adimp` as average daily impression, `mtd_adpv` as average daily view, `CTR = mtd_adpv/mtd_adimp`, and `CR = mtd_ado/mtd_adpv`. Do not describe item CTR with shop-level `adclicks`, and do not invent missing M-1 item traffic.

Section 1.9 (`sec_fulfillment`) must push the local-fulfillment conversation. Define FBS as official warehouse/local fulfillment ADO, TPF as third-party warehouse/local fulfillment ADO, local fulfillment as `FBS + TPF`, and SLS as cross-border logistics ADO. Show current local fulfillment share and which sites are increasing local share MoM.

Sections 2.0 and 2.1 must treat order sources and promotion/subsidy levers as non-MECE. For `sec_traffic_channel`, expose site-level source drivers such as organic, ADS, livestream, campaign, seller/platform item rebates, platform/seller shipping rebates, and CFS. For `sec_subsidy`, focus on promotion effectiveness and seller/platform funding pressure; use it as a companion to order source instead of a disconnected subsidy table. Visible copy must explicitly say these shares cannot be summed to 100%.

Section 2.4 (`sec_ams`) should be titled `ADS出单效率审计`. It should evaluate site-level advertising efficiency using Ads ADO share, Ads ADG share, Ads Spend/GMV, ROAS, and HE1 Ads ADG%. If `ads_spend/total_adg > 100%`, preserve a data-quality warning rather than hiding it; it may indicate true low efficiency or currency/metric-scope mismatch.

For L1/L2/L3 category drill visuals, suppress no-data sites and categories. A row/cell needs seller-side evidence to appear in the primary visual: current ADG, previous ADG, seller share, or seller MoM. Rows that only contain benchmark values can remain in collapsed audit/source data, but should not be shown as seller-facing evidence.

## Evidence Rule

Every numeric claim in analysis should be traceable to visible data in the same section. Cross-section jumps are only allowed in the executive summary. Section analysis may mention another section as plain text, but should not call `jumpTo(...)`.

Do not render raw `{placeholder}` analysis templates from `sec_text` as seller-facing copy. Treat those templates as an analysis framework only; generated bullets must substitute real values from section rows.

Top highlight takeaways should use compact circular `1/2/3` markers when there are 2-3 priority findings. Reuse the same number on the chart/table evidence and in the Chinese computed-analysis bullet, so the marker is a trace link rather than decoration. If a chart renders numbered circles, the section's `数据诊断` text must include the same numbers and explain the same ranked rows; otherwise do not render the circles. If the takeaway and computed analysis say the same thing, merge them into computed analysis instead of showing a duplicate list.

## Gate Rule

Show all storyline gate decisions in the executive area. If explicit gate tabs are missing, derive gate state from approved section rows and show both triggered and reference gates with their reason.

## Highlighting

- Positive values use `.up`.
- Negative or risk values use `.dn` or `.warn`.
- Values referenced in analysis should have matching table emphasis where practical.

## Benchmark Rule

Never expose market benchmark absolute values in seller-facing HTML. Use relative values only: MoM%, share%, growth percentile, gap pp, or seller count.

## Visual V1

The renderer should feel like a working seller-visit diagnosis report: dense, scan-friendly, restrained, and tied to evidence. Use compact cards, clear section hierarchy, and table disclosure controls rather than long raw tables as the first thing users read.
