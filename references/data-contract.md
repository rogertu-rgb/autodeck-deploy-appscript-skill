# AutoDeck Data Contract

## Raw Tabs

`raw_dws_shop`

- Grain: GGP x shop x site x L1 x L2 x L3 x year_month x price_range.
- Used for seller KPI, category, fulfillment, traffic, subsidy, price band, and AMS sections.

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

`raw_dws_item`

- Grain: item x shop x site x month.
- Used for listing gain/loss and item-level diagnosis.

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
sec_root_cause
sec_text
sec_config
```

Future Architecture references a 38-section target. Preserve the script boundary: if the builder changes from 15 to 38 sections, the skill should call the new builder rather than hard-coding new pivots.

## Seller-Facing Naming

Do not show internal names such as `B_12M_ADG_BY_SITE`, `G1A`, `N0_HIST`, or raw SQL/task IDs in visible report copy.
