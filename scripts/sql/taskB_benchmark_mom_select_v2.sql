-- ═══════════════════════════════════════════════════════════════
-- Task B SELECT v2: Read from cncbbi_general.autodeck__site_bu_benchmark_rpt
-- ═══════════════════════════════════════════════════════════════
-- autodeck__site_bu_benchmark_rpt 只有 MoM% — 无任何绝对值.
-- 本 SELECT: 去重透出. 不做任何计算.
-- ═══════════════════════════════════════════════════════════════

WITH dedup AS (
  SELECT
    site, l1, l2, l3, seller_type, price_band, year_month,

    MAX(mom_mkt_adg_pct) * 100        AS mkt_adg_mom,
    MAX(mom_mkt_ado_pct) * 100        AS mkt_ado_mom,
    MAX(mom_mkt_mall_adg_pct) * 100   AS mkt_mall_adg_mom,
    MAX(mom_mkt_mall_ado_pct) * 100   AS mkt_mall_ado_mom,
    MAX(mom_mkt_cb_adg_pct) * 100     AS mkt_cb_adg_mom,
    MAX(mom_mkt_local_adg_pct) * 100  AS mkt_local_adg_mom,

    MAX(mom_price_share_pp)           AS mom_price_share_pp,
    CAST(NULL AS DOUBLE)              AS mkt_price_share,
    CAST(NULL AS DOUBLE)              AS seller_cnt,
    CAST(NULL AS DOUBLE)              AS p10_growth,
    CAST(NULL AS DOUBLE)              AS p25_growth,
    CAST(NULL AS DOUBLE)              AS p50_growth

  FROM cncbbi_general.autodeck__site_bu_benchmark_rpt
  GROUP BY site, l1, l2, l3, seller_type, price_band, year_month
)
SELECT
  site, l1, l2, l3, seller_type, price_band,

  mkt_adg_mom,
  mkt_ado_mom,
  mkt_mall_adg_mom,
  mkt_mall_ado_mom,
  mkt_cb_adg_mom,
  mkt_local_adg_mom,

  mom_price_share_pp,
  mkt_price_share,
  seller_cnt,

  p10_growth,
  p25_growth,
  p50_growth,

  year_month

FROM dedup
;
