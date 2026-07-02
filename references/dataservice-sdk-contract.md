# DataService SDK Contract

Source reference:

the local Obsidian tech reference `auto_deck/tech design/v_0602/Tech Reference.md`, section 11 "SDK — DataService API (Skill 专用数据通道)".

## Contract

- Skills must use the DataService SDK for standard AutoDeck raw data extraction.
- Do not use the DataSuite Chrome bridge as the default path.
- The raw tab contract is unchanged:
  - `raw_dws_shop`
  - `raw_benchmark`
  - `raw_benchmark_total_site` for Shopee overall MoM% in `sec_12m_history`
  - `raw_dws_item`
- The SDK runs SQL through the authorized AutoDeck DataService API and returns structured row dictionaries.
- Before raw extraction, the SDK path resolves `--ggp` to an exact `ggp_account_name` from `cncbbi_general.autodeck__dws_shop_rpt_mi` using the current and prior report month:
  - exact case-insensitive match wins
  - one partial-name candidate is accepted
  - multiple candidates block the run and must be resolved by the user
  - no lookup match preserves the input so legacy exact-name runs are not broken
- The query helper writes the same local CSV artifacts as before, then `create_report_sheet.py` writes those CSVs into Google Sheet raw tabs.
- `raw_benchmark_site` must use the same Total-dimension MoM logic as `raw_benchmark_total_site`, except it keeps each seller site instead of filtering to `site = 'Total Site'`. Query `cncbbi_general.autodeck__site_bu_benchmark_rpt` directly with `l1 = 'Total'`, `l2 = 'Total'`, `l3 = 'Total'`, `price_band = 'Total'`, `seller_type = 'CNCB'`, and seller-site filtering from `raw_dws_shop`; do not average site benchmark across L1/L2/L3/price_band detail rows.
- SDK raw pulls must not rely on a single OLAP response when the response reaches the DataService row cap. Treat `20,000` returned rows as a cap signal, not as proof of completeness.
- Capped raw pulls must be refetched with deterministic site-first slices and merged locally:
  - `raw_dws_shop`: `site` first, then `year_month`, `l1`, `l2`, `l3` only if a site slice still reaches the cap.
  - `raw_benchmark_price`: `site` first, then `year_month`, `l1`, `l2`, `l3`, `price_band` only if a site slice still reaches the cap.
  - other capped `raw_benchmark_*` tabs use site-first splitting with the dimensions present in the tab.
- `query_summary.json` must expose `api_cap_hit`, `split_strategy`, and `max_split_rows` when splitting occurs so row completeness can be audited before Sheet publish.

## Benchmark RPT Normalization

The SDK allowlist exposes `cncbbi_general.autodeck__site_bu_benchmark_rpt` rather than the legacy benchmark source table. This table currently has MoM fields plus `mom_price_share_pp`, but not absolute market share, seller count, or p10/p25/p50 distribution fields.

`scripts/sql/taskB_benchmark_mom_select_v2.sql` must normalize the live RPT schema into the section-builder contract:

- multiply `mom_mkt_*_pct` by `100` and expose the results as `mkt_*_mom`
- expose `mom_price_share_pp` for price-band movement evidence
- keep unavailable market-share, seller-count, and growth-distribution fields as nullable columns, not fake zeroes

When reading raw tabs back from Google Sheets, pad short rows to the header width before creating DataFrames. Google Sheets omits trailing empty cells, and benchmark tabs with nullable trailing columns otherwise fail to load.

## Default SDK Settings

- API name: `cncbbi_general.autodeck__rpt_table_list`
- API version: `n4rfgou3k5r5mhu7`
- Base URL: `https://open-api.datasuite.shopee.io`
- Queue: `cncbbi-scheduled`
- System name: `autodeck_skill`

Credentials are resolved in this order:

1. CLI args such as `--dataservice-app-key` and `--dataservice-app-secret`
2. environment variables such as `AUTODECK_DATASERVICE_APP_KEY` and `AUTODECK_DATASERVICE_APP_SECRET`
3. optional JSON passed by `--dataservice-config`
4. the local Tech Reference values

## Fallback

`--data-mode bridge` remains available only for debugging or emergency fallback. New skill runs should default to `--data-mode sdk`.
