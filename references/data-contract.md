# AutoDeck Data Contract

## Raw Tabs

`raw_dws_shop`

- Grain: GGP x shop x site x L1 x L2 x L3 x year_month x price_range.
- Used for seller KPI, category, fulfillment, traffic, subsidy, price band, shop impact, and ADS sections.
- Fulfillment fields:
  - `fbs_ado`: official warehouse/local fulfillment average daily orders.
  - `tpf_ado`: third-party warehouse/local fulfillment average daily orders.
  - `sls_ado`: cross-border logistics average daily orders.
  - `local_ado = fbs_ado + tpf_ado`.
- Order-source and promotion levers are not MECE. A single order can be counted in multiple source/rebate/campaign fields, so seller-facing percentages are driver signals, not a 100% split.
- ADS efficiency fields:
  - `ads_ado_share = ads_ado / ado`.
  - `ads_adg_share = ads_adg / adg`.
  - `ads_spend_gmv = ads_spend / adg`.
  - `roas = ads_adg / ads_spend`.

`raw_benchmark`

- Grain: site x L1 x L2 x L3 x seller_type x price_band x year_month.
- Seller-facing output must not expose benchmark absolute values.
- Allowed benchmark fields are relative values:
  - `mkt_adg_mom`
  - `mkt_ado_mom`
  - `mkt_mall_adg_mom`
  - `mkt_mall_ado_mom`
  - `mkt_cb_adg_mom`
  - `mkt_local_adg_mom`
  - `p10_growth`
  - `p25_growth`
  - `p50_growth`
  - `mkt_price_share`
  - `seller_cnt`

`raw_benchmark_site`

- Grain: site x year_month for seller sites only.
- Source filter: `l1 = 'Total'`, `l2 = 'Total'`, `l3 = 'Total'`, `price_band = 'Total'`, `seller_type = 'CNCB'`.
- Used for `sec_site_benchmark` current-month site attribution. Do not compute this by averaging detailed L1/L2/L3/price rows.

`raw_dws_item`

- Grain: item x shop x site x month.
- Used for listing gain/loss and item-level diagnosis.
- Source table: `cncbbi_general.autodeck__dws_item_rpt_mi`.
- Item funnel:
  - `mtd_adimp` = month-to-date average daily impression.
  - `mtd_adpv` = month-to-date average daily view.
  - `CTR = mtd_adpv / mtd_adimp`.
  - `CR = mtd_ado / mtd_adpv`.
  - Use `m1_adg` and `m1_ado` for ADG/ADO movement; do not invent M-1 item traffic when it is absent.

## v_0602 Section Tabs

The current working builder writes these section tabs:

```text
sec_12m_history
sec_site_benchmark
sec_l1_overview
sec_l1_matrix
sec_l2_drill
sec_l3_granular
sec_volatility
sec_shop_impact
sec_listing_change
sec_fulfillment
sec_traffic_channel
sec_subsidy
sec_price_band
sec_ams
sec_data_quality_notes
sec_root_cause
sec_text
sec_config
```

Future Architecture references a 38-section target. Preserve the script boundary: if the builder changes from 15 to 38 sections, the skill should call the new builder rather than hard-coding new pivots.

## Seller-Facing Naming

Do not show internal names such as `B_12M_ADG_BY_SITE`, `G1A`, `N0_HIST`, or raw SQL/task IDs in visible report copy.
