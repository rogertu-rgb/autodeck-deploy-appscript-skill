# Section Analysis Harness

This harness is distilled from:

the local Obsidian storyline reference `auto_deck/storyline/v_0602/Section Design v_0602.md`

The renderer must treat `sec_text` as historical framework notes only. Do not render template directions or unfilled placeholders. Each analysis block must be computed from the section rows and meta tabs.

## Global Rules

- Every section renders `data-analysis-mode="computed"`.
- Generate seller-facing conclusions, not instructions such as "check X" without saying what X currently shows.
- Prefer 2-4 bullets per section.
- Each bullet should answer: what changed, where it happened, why it matters, and what diagnostic route it triggers.
- Evidence chips should point to same-section source rows when the row exists. Meta-only sections may summarize parsed meta JSON but must not show raw JSON.
- Never expose placeholder text such as `{top_l1}`, `待分析`, `待填充`, `from sec_*`, or raw `sec_text`.
- If a primary visual renders circular `1/2/3` markers, computed analysis must render matching `1/2/3` bullets with the same ranking logic and the same row identities. A marker without matching analysis text is invalid; suppress the marker instead of leaving it unexplained.

## Section Logic

- `sec_12m_history`: identify latest total ADG, previous comparable month change, peak/low month, latest top site, and concentration risk above 60%.
- `sec_site_benchmark`: identify largest site by ADG, largest benchmark gap, sites running more than 5pp ahead/behind market, same-direction rate versus market, and current-month attribution priority using `abs(adg_gap_pp) * adg_share`. The top 1-3 attribution findings should use matching circular callout numbers on the visual, important-row table, and Chinese computed-analysis bullets. Do not duplicate those bullets in a separate takeaway list.
- `sec_l1_overview`: identify Top1/Top3 L1 concentration, largest L1 MoM mover, count of L1s beyond 10% MoM, and largest market gap. Its primary visual should use `sec_l1_matrix` when available to expose site x L1 cells.
- `sec_l1_matrix`: identify largest site×L1 gap, important cells where `|gap_pp| > 5` and share is material, and whether anomalies cluster by site or by L1. Priority drilldown cells should be ranked by `abs(gap_pp) * share_in_site` and marked 1/2/3.
- `sec_l2_drill`: identify largest L2 ADG delta, largest `share_in_l1`, largest L2 benchmark gap, and whether L3 drill should be triggered. The input table must be aggregated at `site × L1 × L2` grain, not selected-L1-only and not `site × L2`; `share_in_l1` must use the same `site × L1` total as denominator. The visual route is four lanes: high-share underperformers, absolute scale leaders, fastest growers, and large-share decliners. Numbered visual markers must be ranked by `abs(gap_pp) * share_in_l1`, deduplicated across lanes, and mirrored by matching numbered computed-analysis bullets. Every L2 finding must name the full `site / L1 > L2` path, not only the L2 leaf.
- `sec_l3_granular`: identify exact L3 movement, compare seller growth with P50 when present, and route to listing verification when movement is concentrated. The input table must be aggregated at `site × L1 × L2 × L3` grain so repeated L3 leaf names such as `Other` are not collapsed across parents. If P50 is absent, state that the row is seller-side proof only and do not describe a market gap. Numbered table markers must be mirrored by matching numbered computed-analysis bullets. Every L3 finding must name the full `site / L1 > L2 > L3` path, not only the L3 leaf.
- For all category drill analysis and visuals, ignore no-data site/category rows unless they represent a real disappearance signal with previous ADG or seller MoM. Do not use benchmark-only rows as seller-facing evidence.
- `sec_volatility`: parse `sec_volatility_meta`; summarize total signals and then expose an actionable anomaly workbench. Enrich each signal with inferred market MoM (`seller_mom - gap_pp` when market is not explicit), low-confidence flags (low ADG, extreme benchmark gap, generic Other/Others path), red-alert flag (seller down while market up with negative gap), and route. Rank the visible queue by `abs(gap_pp) * log(ADG+2) * confidence`; the top 1-3 rows must use matching circular markers in the quadrant scatter, priority queue, Key Highlights, and Chinese computed-analysis bullets. Low-confidence signals should be hidden by default and summarized as audit-only, not treated as seller conclusions.
- `sec_shop_impact`: title as `店铺贡献分析`. Use the enriched shop table generated from `raw_dws_shop` after the standard builder. The diagnostic route is site -> key driver shop -> L3 x price range -> traffic funnel. Identify overall Top ADG/ADO shops only as context, then prioritize site key driver shops by absolute ADG delta. For those key shops, expose the L3 x price_range combinations where gain/loss happens and summarize whether the movement is driven by exposure (`adimp`), clicks (`adclick`), CTR (`adclick/adimp`), CR (`ADO/adclick`), or basket/order value. Do not force three loss shops when a site genuinely has fewer loss shops; use the L3 x price-range dive to add actionability instead.
- `sec_listing_change`: use the enriched `sec_listing_change` table built from `raw_dws_item` / `cncbbi_general.autodeck__dws_item_rpt_mi`. Identify the best-selling listing, the largest-growth listing, and the largest-loss listing. Show item funnel as `ADIMP -> ADPV -> ADO`, where `CTR = mtd_adpv / mtd_adimp` and `CR = mtd_ado / mtd_adpv`. Use item-level ADG/ADO movement and current CTR/CR to guide root-cause prompts; do not invent M-1 item traffic fields.
- `sec_fulfillment`: use the enriched `sec_fulfillment` table from `raw_dws_shop`. Define local fulfillment as `fbs_ado + tpf_ado`; SLS is cross-border. Identify the highest-local-share site, the fastest-growing local-share site, and the lowest-local-share site to prioritize seller push for FBS/TPF. Flag fulfillment coverage anomalies when `FBS + TPF + SLS` materially differs from total ADO.
- `sec_traffic_channel`: use the enriched long table of site x source levers from `raw_dws_shop`. Identify the largest current ADO source, the fastest-growing source, and the steepest-declining source by site. Always state that sources are not MECE and shares must not be summed.
- `sec_subsidy`: treat this as a promotion-effectiveness companion to order source. Identify which promo/rebate/CFS/Campaign/LPP lever generates the most ADO/ADG, which lever is growing, and which site has the highest seller-funded pressure. Always state that promo/subsidy levers are not MECE.
- `sec_price_band`: identify largest price-band bias, largest share migration, strongest seller price-band concentration, and whether it implies over-concentration or under-coverage.
- `sec_ams`: title as `ADS出单效率审计`. Use site-level enriched ADS rows from `raw_dws_shop`. Compute `ads_ado_share`, `ads_adg_share`, `ads_spend_gmv`, `ROAS = ads_adg / ads_spend`, and `HE1 Ads ADG % = ads_adg / total_adg` unless a dedicated HE1 field exists. Identify highest ROAS, highest ads-dependence, highest spend/GMV, low-ROAS risk, and spend cuts that may explain ADG declines.
- `sec_root_cause`: synthesize benchmark gap, volatility signals, subsidy load, fulfillment shift, and price bias by site. Cards must contain hypothesis, confidence, recommendation, and evidence chain with real findings.

## End-to-End Skill Goal

The standard user flow is:

```text
OAuth file + GGP name/query + YYYY-MM
  -> resolve/search the correct GGP account name
  -> extract raw data through the DataService SDK
  -> build all section tabs
  -> render all 15 seller-report sections
  -> validate computed analysis, visual shell, and Apps Script files
  -> publish the Apps Script HTML report
```

If the GGP name is ambiguous, resolve it before running the expensive build/deploy steps. If the data source cannot search names directly, use the closest SDK-supported account lookup or stop with the candidate list needed from the user.
