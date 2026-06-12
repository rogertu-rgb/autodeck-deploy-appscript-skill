# Section Analysis Harness

This harness is distilled from AutoDeck storyline section design v_0602.

The renderer must treat `sec_text` as historical framework notes only. Do not render template directions or unfilled placeholders. Each analysis block must be computed from the section rows and meta tabs.

## Global Rules

- Every section renders `data-analysis-mode="computed"`.
- Generate seller-facing conclusions, not instructions such as "check X" without saying what X currently shows.
- Prefer 2-4 bullets per section.
- Each bullet should answer: what changed, where it happened, why it matters, and what diagnostic route it triggers.
- Evidence chips should point to same-section source rows when the row exists. Meta-only sections may summarize parsed meta JSON but must not show raw JSON.
- Never expose placeholder text such as `{top_l1}`, `待分析`, `待填充`, `from sec_*`, or raw `sec_text`.

## Section Logic

- `sec_12m_history`: identify latest total ADG, previous comparable month change, peak/low month, latest top site, and concentration risk above 60%.
- `sec_site_benchmark`: identify largest site by ADG, largest benchmark gap, sites running more than 5pp ahead/behind market, and same-direction rate versus market.
- `sec_l1_overview`: identify Top1/Top3 L1 concentration, largest L1 MoM mover, count of L1s beyond 10% MoM, and largest market gap.
- `sec_l1_matrix`: identify largest site×L1 gap, important cells where `|gap_pp| > 5` and share is material, and whether anomalies cluster by site or by L1.
- `sec_l2_drill`: identify largest L2 ADG delta, largest `share_in_l1`, largest L2 benchmark gap, and whether L3 drill should be triggered.
- `sec_l3_granular`: identify exact L3 movement, compare seller growth with P50 when present, and route to listing verification when movement is concentrated.
- `sec_volatility`: parse `sec_volatility_meta`; summarize total signals, high-priority signal types, top path, and site/category clustering.
- `sec_shop_impact`: identify top positive/negative shop contribution, Top1 shop share, and single-shop dependency risk above 40%.
- `sec_listing_change`: parse `sec_listing_change_meta`; identify top listing, new item count, cross-site repeated items, and dominant top-listing price band.
- `sec_fulfillment`: compute total FBS/TPF/SLS mix, identify dominant mode and largest share shift, and flag FBS>60%, TPF>40%, or major fulfillment migration.
- `sec_traffic_channel`: compute channel share mix, identify the channel with steepest MoM decline, assess paid traffic dependence, and include ROAS when present.
- `sec_subsidy`: compute total subsidy load, highest subsidy site, seller/platform funding split, and flag >40% subsidy dependence.
- `sec_price_band`: identify largest price-band bias, largest share migration, strongest seller price-band concentration, and whether it implies over-concentration or under-coverage.
- `sec_ams`: compute weighted ROAS, identify highest ROAS expansion candidate, highest ads-share risk, and spend cuts that may explain ADG declines.
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
