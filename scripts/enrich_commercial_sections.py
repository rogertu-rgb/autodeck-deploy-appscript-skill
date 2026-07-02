#!/usr/bin/env python3
"""Enrich commercial diagnosis sections from raw AutoDeck tabs."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Tuple

from googleapiclient.discovery import build

from enrich_shop_impact import (
    cell,
    idx,
    month_serial,
    num,
    pct,
    prev_month_serial,
    rate,
    read_tab,
    shop_name_map,
    write_tab,
)
from oauth_check import build_credentials


LISTING_HEADER = [
    "rank_type",
    "rank",
    "site",
    "shop_id",
    "shop_name",
    "item_id",
    "item_name",
    "item_link",
    "l1",
    "l2",
    "l3",
    "price_range",
    "mtd_adg",
    "m1_adg",
    "adg_delta",
    "adg_mom",
    "mtd_ado",
    "m1_ado",
    "ado_delta",
    "ado_mom",
    "adg_per_order_mtd",
    "adg_per_order_delta",
    "mtd_adimp",
    "mtd_adpv",
    "ctr",
    "cr",
    "mtd_ads_adg",
    "mtd_ads_ado",
    "ads_adg_share",
    "is_new",
    "avg_adg_30d",
    "primary_driver",
    "data_note",
]

FULFILLMENT_HEADER = [
    "site",
    "total_ado",
    "fulfillment_ado",
    "fbs_ado",
    "tpf_ado",
    "local_ado",
    "sls_ado",
    "fbs_share",
    "tpf_share",
    "local_share",
    "sls_share",
    "local_share_m1",
    "local_shift_pp",
    "local_ado_delta",
    "local_ado_mom",
    "fbs_shift_pp",
    "tpf_shift_pp",
    "sls_shift_pp",
    "fulfillment_coverage",
    "main_mode",
    "localization_status",
]

TRAFFIC_HEADER = [
    "site",
    "source_key",
    "source_label",
    "source_group",
    "ado_mtd",
    "ado_m1",
    "ado_delta",
    "ado_mom",
    "ado_share",
    "adg_mtd",
    "adg_m1",
    "adg_delta",
    "adg_mom",
    "adg_share",
    "total_ado",
    "total_adg",
    "rank_type",
    "non_mece_note",
]

SUBSIDY_HEADER = [
    "site",
    "source_key",
    "source_label",
    "source_group",
    "ado_mtd",
    "ado_m1",
    "ado_delta",
    "ado_mom",
    "ado_share",
    "adg_mtd",
    "adg_m1",
    "adg_delta",
    "adg_mom",
    "adg_share",
    "total_ado",
    "total_adg",
    "total_subsidy_adg",
    "subsidy_share",
    "seller_funded_share",
    "platform_funded_share",
    "rank_type",
    "non_mece_note",
]

ADS_HEADER = [
    "site",
    "total_ado",
    "total_adg",
    "ads_ado",
    "ads_adg",
    "ads_spend",
    "ads_ado_share",
    "ads_adg_share",
    "he1_ads_adg_pct",
    "ads_spend_gmv",
    "roas",
    "ads_ado_m1",
    "ads_adg_m1",
    "ads_spend_m1",
    "ads_ado_delta",
    "ads_adg_delta",
    "ads_spend_delta",
    "ads_ado_mom",
    "ads_adg_mom",
    "ads_spend_mom",
    "efficiency_status",
]

QUALITY_HEADER = ["section", "severity", "check", "result", "detail"]

SHOP_FIELDS = [
    "ado",
    "adg",
    "adimp",
    "adpv",
    "adclicks",
    "ads_ado",
    "ads_adg",
    "ads_spend",
    "organic_ado",
    "organic_adg",
    "livestream_ado",
    "livestream_adg",
    "campaign_ado",
    "campaign_adg",
    "seller_item_rebated_ado",
    "seller_item_rebated_adg",
    "platform_item_rebated_ado",
    "platform_item_rebated_adg",
    "seller_shipping_rebated_ado",
    "seller_shipping_rebated_adg",
    "platform_shipping_rebated_ado",
    "platform_shipping_rebated_adg",
    "cfs_ado",
    "cfs_adg",
    "lpp_adg",
    "total_subsidy_adg",
    "fbs_ado",
    "tpf_ado",
    "sls_ado",
]

SOURCE_DEFS = [
    ("organic", "自然/Organic", "baseline", "organic_ado", "organic_adg"),
    ("ads", "ADS广告", "paid", "ads_ado", "ads_adg"),
    ("livestream", "Livestream", "content", "livestream_ado", "livestream_adg"),
    ("campaign", "Campaign活动", "platform", "campaign_ado", "campaign_adg"),
    ("seller_item_rebate", "卖家商品补贴", "promotion", "seller_item_rebated_ado", "seller_item_rebated_adg"),
    ("platform_item_rebate", "平台商品补贴", "promotion", "platform_item_rebated_ado", "platform_item_rebated_adg"),
    ("platform_shipping_rebate", "平台运费补贴", "promotion", "platform_shipping_rebated_ado", "platform_shipping_rebated_adg"),
    ("seller_shipping_rebate", "卖家运费补贴", "promotion", "seller_shipping_rebated_ado", "seller_shipping_rebated_adg"),
    ("cfs", "CFS闪购", "promotion", "cfs_ado", "cfs_adg"),
]

PROMO_DEFS = [
    ("seller_item_rebate", "卖家商品补贴", "seller_funded", "seller_item_rebated_ado", "seller_item_rebated_adg"),
    ("seller_shipping_rebate", "卖家运费补贴", "seller_funded", "seller_shipping_rebated_ado", "seller_shipping_rebated_adg"),
    ("platform_item_rebate", "平台商品补贴", "platform_funded", "platform_item_rebated_ado", "platform_item_rebated_adg"),
    ("platform_shipping_rebate", "平台运费补贴", "platform_funded", "platform_shipping_rebated_ado", "platform_shipping_rebated_adg"),
    ("cfs", "CFS闪购", "platform_mechanic", "cfs_ado", "cfs_adg"),
    ("campaign", "Campaign活动", "platform_mechanic", "campaign_ado", "campaign_adg"),
    ("lpp", "LPP低价秒杀", "platform_mechanic", "", "lpp_adg"),
]


def resolve_target_month(raw_rows: List[List[Any]], index: Dict[str, int], month: str) -> Tuple[int, int, List[int]]:
    target = month_serial(month)
    previous = prev_month_serial(month)
    available = sorted(
        {
            int(num(cell(row, index, "year_month", 0), 0))
            for row in raw_rows[1:]
            if num(cell(row, index, "year_month", 0), 0)
        }
    )
    if target not in available and available:
        target = available[-1]
        prior = [m for m in available if m < target]
        previous = prior[-1] if prior else previous
    return target, previous, available


def safe_share(numerator: float, denominator: float) -> Any:
    if not denominator:
        return ""
    return numerator / denominator * 100


def delta_pp(current: Any, previous: Any) -> Any:
    if current == "" or previous == "":
        return ""
    return float(current) - float(previous)


def item_driver(row: Dict[str, Any]) -> str:
    direction = -1 if row["adg_delta"] < 0 else 1
    ado_delta = row["ado_delta"]
    aov_delta = row["adg_per_order_delta"]
    ctr = row.get("ctr", "")
    cr = row.get("cr", "")
    if direction < 0:
        if ado_delta < 0:
            return "订单下滑"
        if aov_delta != "" and aov_delta < 0:
            return "客单下降"
        if ctr != "" and ctr < 0.03:
            return "CTR承接弱"
        if cr != "" and cr < 0.01:
            return "下单转化弱"
        return "需排查流量"
    if ado_delta > 0:
        return "订单增长"
    if aov_delta != "" and aov_delta > 0:
        return "客单提升"
    if ctr != "" and ctr >= 0.08:
        return "流量承接好"
    return "爆品维护"


def source_rank_type(rows: List[Dict[str, Any]]) -> None:
    by_site: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_site[row["site"]].append(row)
    for site_rows in by_site.values():
        primary = sorted(site_rows, key=lambda r: r["ado_mtd"], reverse=True)[:1]
        gainer = sorted([r for r in site_rows if r["ado_delta"] > 0], key=lambda r: r["ado_delta"], reverse=True)[:1]
        decliner = sorted([r for r in site_rows if r["ado_delta"] < 0], key=lambda r: r["ado_delta"])[:1]
        for row in primary:
            row["rank_type"] = "primary_driver"
        for row in gainer:
            row["rank_type"] = "growth_driver" if row.get("rank_type") != "primary_driver" else "primary_growth_driver"
        for row in decliner:
            row["rank_type"] = "loss_driver" if row.get("rank_type") != "primary_driver" else "primary_loss_driver"


def build_listing_rows(raw_item_rows: List[List[Any]], month: str, quality: List[List[Any]]) -> List[List[Any]]:
    if len(raw_item_rows) <= 1:
        quality.append(["sec_listing_change", "warn", "raw_dws_item", "missing", "raw_dws_item missing or empty"])
        return [LISTING_HEADER]
    index = idx(raw_item_rows[0])
    target, _previous, _available = resolve_target_month(raw_item_rows, index, month)

    rows: List[Dict[str, Any]] = []
    for raw in raw_item_rows[1:]:
        serial = int(num(cell(raw, index, "year_month", target), target))
        if serial != target:
            continue
        mtd_adg = num(cell(raw, index, "mtd_adg", 0))
        m1_adg = num(cell(raw, index, "m1_adg", 0))
        mtd_ado = num(cell(raw, index, "mtd_ado", 0))
        m1_ado = num(cell(raw, index, "m1_ado", 0))
        mtd_adimp = num(cell(raw, index, "mtd_adimp", 0))
        mtd_adpv = num(cell(raw, index, "mtd_adpv", 0))
        if not any([mtd_adg, m1_adg, mtd_ado, m1_ado, mtd_adimp, mtd_adpv]):
            continue
        adg_per_order = rate(mtd_adg, mtd_ado)
        adg_per_order_m1 = rate(m1_adg, m1_ado)
        row = {
            "rank_type": "",
            "site": str(cell(raw, index, "site", "")).strip(),
            "shop_id": str(cell(raw, index, "shop_id", "")).strip(),
            "shop_name": str(cell(raw, index, "shop_name", "")).strip(),
            "item_id": str(cell(raw, index, "item_id", "")).strip(),
            "item_name": str(cell(raw, index, "item_name", "")).strip(),
            "item_link": str(cell(raw, index, "item_link", "")).strip(),
            "l1": str(cell(raw, index, "l1", "")).strip(),
            "l2": str(cell(raw, index, "l2", "")).strip(),
            "l3": str(cell(raw, index, "l3", "")).strip(),
            "price_range": str(cell(raw, index, "price_range", "")).strip(),
            "mtd_adg": mtd_adg,
            "m1_adg": m1_adg,
            "adg_delta": mtd_adg - m1_adg,
            "adg_mom": pct(mtd_adg, m1_adg),
            "mtd_ado": mtd_ado,
            "m1_ado": m1_ado,
            "ado_delta": mtd_ado - m1_ado,
            "ado_mom": pct(mtd_ado, m1_ado),
            "adg_per_order_mtd": adg_per_order,
            "adg_per_order_delta": "" if adg_per_order == "" or adg_per_order_m1 == "" else adg_per_order - adg_per_order_m1,
            "mtd_adimp": mtd_adimp,
            "mtd_adpv": mtd_adpv,
            "ctr": rate(mtd_adpv, mtd_adimp),
            "cr": rate(mtd_ado, mtd_adpv),
            "mtd_ads_adg": num(cell(raw, index, "mtd_ads_adg", 0)),
            "mtd_ads_ado": num(cell(raw, index, "mtd_ads_ado", 0)),
            "is_new": int(num(cell(raw, index, "is_new", 0), 0)),
            "avg_adg_30d": num(cell(raw, index, "avg_adg_30d", 0)),
            "data_note": "item funnel uses ADIMP->ADPV->ADO; CTR=ADPV/ADIMP, CR=ADO/ADPV",
        }
        row["ads_adg_share"] = safe_share(row["mtd_ads_adg"], row["mtd_adg"])
        row["primary_driver"] = item_driver(row)
        rows.append(row)

    quality.append(["sec_listing_change", "info", "item traffic fields", "ok", "raw_dws_item uses mtd_adpv as average daily view; CTR=mtd_adpv/mtd_adimp and CR=mtd_ado/mtd_adpv"])
    output: List[List[Any]] = [LISTING_HEADER]

    def append_ranked(selected: Iterable[Dict[str, Any]], rank_type: str, limit: int) -> None:
        for rank, row in enumerate(list(selected)[:limit], 1):
            output.append([
                rank_type,
                rank,
                row["site"],
                row["shop_id"],
                row["shop_name"],
                row["item_id"],
                row["item_name"],
                row["item_link"],
                row["l1"],
                row["l2"],
                row["l3"],
                row["price_range"],
                row["mtd_adg"],
                row["m1_adg"],
                row["adg_delta"],
                row["adg_mom"],
                row["mtd_ado"],
                row["m1_ado"],
                row["ado_delta"],
                row["ado_mom"],
                row["adg_per_order_mtd"],
                row["adg_per_order_delta"],
                row["mtd_adimp"],
                row["mtd_adpv"],
                row["ctr"],
                row["cr"],
                row["mtd_ads_adg"],
                row["mtd_ads_ado"],
                row["ads_adg_share"],
                row["is_new"],
                row["avg_adg_30d"],
                row["primary_driver"],
                row["data_note"],
            ])

    append_ranked(sorted(rows, key=lambda r: r["mtd_adg"], reverse=True), "top_adg", 20)
    append_ranked([r for r in sorted(rows, key=lambda r: r["adg_delta"], reverse=True) if r["adg_delta"] > 0], "top_growth", 20)
    append_ranked([r for r in sorted(rows, key=lambda r: r["adg_delta"]) if r["adg_delta"] < 0], "top_loss", 20)
    for site in sorted({r["site"] for r in rows if r["site"]}):
        site_rows = [r for r in rows if r["site"] == site]
        append_ranked(sorted(site_rows, key=lambda r: r["mtd_adg"], reverse=True), "site_top_adg", 5)
        append_ranked([r for r in sorted(site_rows, key=lambda r: r["adg_delta"], reverse=True) if r["adg_delta"] > 0], "site_growth", 5)
        append_ranked([r for r in sorted(site_rows, key=lambda r: r["adg_delta"]) if r["adg_delta"] < 0], "site_loss", 5)
    return output


def build_shop_buckets(raw_shop_rows: List[List[Any]], month: str, quality: List[List[Any]]) -> Dict[str, Dict[str, float]]:
    if len(raw_shop_rows) <= 1:
        quality.append(["all_shop_sections", "warn", "raw_dws_shop", "missing", "raw_dws_shop missing or empty"])
        return {}
    index = idx(raw_shop_rows[0])
    target, previous, available = resolve_target_month(raw_shop_rows, index, month)
    if target not in available:
        quality.append(["all_shop_sections", "warn", "target month", "fallback", f"requested month not found; using serial {target}"])
    missing = [name for name in SHOP_FIELDS if name not in index]
    if missing:
        quality.append(["all_shop_sections", "warn", "raw_dws_shop columns", "partial", "missing columns: " + ", ".join(missing)])

    def empty_bucket() -> Dict[str, float]:
        bucket: Dict[str, float] = {}
        for field in SHOP_FIELDS:
            bucket[f"{field}_mtd"] = 0.0
            bucket[f"{field}_m1"] = 0.0
        return bucket

    buckets: Dict[str, Dict[str, float]] = defaultdict(empty_bucket)
    for raw in raw_shop_rows[1:]:
        serial = int(num(cell(raw, index, "year_month", 0), 0))
        if serial == target:
            suffix = "mtd"
        elif serial == previous:
            suffix = "m1"
        else:
            continue
        site = str(cell(raw, index, "site", "")).strip()
        if not site:
            continue
        bucket = buckets[site]
        for field in SHOP_FIELDS:
            bucket[f"{field}_{suffix}"] += num(cell(raw, index, field, 0))
    return buckets


def build_fulfillment_rows(buckets: Dict[str, Dict[str, float]], quality: List[List[Any]]) -> List[List[Any]]:
    output = [FULFILLMENT_HEADER]
    for site, b in sorted(buckets.items(), key=lambda kv: kv[1]["ado_mtd"], reverse=True):
        total_ado = b["ado_mtd"]
        fbs = b["fbs_ado_mtd"]
        tpf = b["tpf_ado_mtd"]
        sls = b["sls_ado_mtd"]
        local = fbs + tpf
        tracked = local + sls
        fbs_m1 = b["fbs_ado_m1"]
        tpf_m1 = b["tpf_ado_m1"]
        sls_m1 = b["sls_ado_m1"]
        local_m1 = fbs_m1 + tpf_m1
        tracked_m1 = local_m1 + sls_m1
        local_share = safe_share(local, tracked)
        local_share_m1 = safe_share(local_m1, tracked_m1)
        coverage = safe_share(tracked, total_ado)
        if coverage != "" and (coverage < 95 or coverage > 105) and total_ado > 1:
            quality.append(["sec_fulfillment", "warn", "fulfillment coverage", "check", f"{site}: FBS+TPF+SLS is {coverage:.1f}% of total ADO"])
        shares = {
            "FBS": safe_share(fbs, tracked) or 0,
            "TPF": safe_share(tpf, tracked) or 0,
            "SLS": safe_share(sls, tracked) or 0,
        }
        main_mode = max(shares, key=shares.get) if tracked else "No fulfillment data"
        status = "本地履约提升" if local_share != "" and local_share_m1 != "" and local_share > local_share_m1 else "本地履约待推进"
        output.append([
            site,
            total_ado,
            tracked,
            fbs,
            tpf,
            local,
            sls,
            safe_share(fbs, tracked),
            safe_share(tpf, tracked),
            local_share,
            safe_share(sls, tracked),
            local_share_m1,
            delta_pp(local_share, local_share_m1),
            local - local_m1,
            pct(local, local_m1),
            delta_pp(safe_share(fbs, tracked), safe_share(fbs_m1, tracked_m1)),
            delta_pp(safe_share(tpf, tracked), safe_share(tpf_m1, tracked_m1)),
            delta_pp(safe_share(sls, tracked), safe_share(sls_m1, tracked_m1)),
            coverage,
            main_mode,
            status,
        ])
    return output


def build_traffic_rows(buckets: Dict[str, Dict[str, float]]) -> List[List[Any]]:
    rows: List[Dict[str, Any]] = []
    for site, b in buckets.items():
        total_ado = b["ado_mtd"]
        total_adg = b["adg_mtd"]
        for key, label, group, ado_col, adg_col in SOURCE_DEFS:
            ado = b[f"{ado_col}_mtd"]
            ado_m1 = b[f"{ado_col}_m1"]
            adg = b[f"{adg_col}_mtd"]
            adg_m1 = b[f"{adg_col}_m1"]
            if not any([ado, ado_m1, adg, adg_m1]):
                continue
            rows.append({
                "site": site,
                "source_key": key,
                "source_label": label,
                "source_group": group,
                "ado_mtd": ado,
                "ado_m1": ado_m1,
                "ado_delta": ado - ado_m1,
                "ado_mom": pct(ado, ado_m1),
                "ado_share": safe_share(ado, total_ado),
                "adg_mtd": adg,
                "adg_m1": adg_m1,
                "adg_delta": adg - adg_m1,
                "adg_mom": pct(adg, adg_m1),
                "adg_share": safe_share(adg, total_adg),
                "total_ado": total_ado,
                "total_adg": total_adg,
                "rank_type": "source",
                "non_mece_note": "not MECE; source shares can overlap and should not be summed",
            })
    source_rank_type(rows)
    output = [TRAFFIC_HEADER]
    for row in sorted(rows, key=lambda r: (r["site"], -r["ado_mtd"], r["source_label"])):
        output.append([row[col] for col in TRAFFIC_HEADER])
    return output


def build_subsidy_rows(buckets: Dict[str, Dict[str, float]], quality: List[List[Any]]) -> List[List[Any]]:
    output = [SUBSIDY_HEADER]
    for site, b in sorted(buckets.items(), key=lambda kv: kv[1]["adg_mtd"], reverse=True):
        total_ado = b["ado_mtd"]
        total_adg = b["adg_mtd"]
        total_subsidy = b["total_subsidy_adg_mtd"]
        seller_funded = b["seller_item_rebated_adg_mtd"] + b["seller_shipping_rebated_adg_mtd"]
        platform_funded = b["platform_item_rebated_adg_mtd"] + b["platform_shipping_rebated_adg_mtd"]
        funding_base = seller_funded + platform_funded
        rows: List[Dict[str, Any]] = []
        for key, label, group, ado_col, adg_col in PROMO_DEFS:
            ado = b[f"{ado_col}_mtd"] if ado_col else 0.0
            ado_m1 = b[f"{ado_col}_m1"] if ado_col else 0.0
            adg = b[f"{adg_col}_mtd"] if adg_col else 0.0
            adg_m1 = b[f"{adg_col}_m1"] if adg_col else 0.0
            if not any([ado, ado_m1, adg, adg_m1]):
                continue
            rows.append({
                "site": site,
                "source_key": key,
                "source_label": label,
                "source_group": group,
                "ado_mtd": ado,
                "ado_m1": ado_m1,
                "ado_delta": ado - ado_m1,
                "ado_mom": pct(ado, ado_m1),
                "ado_share": safe_share(ado, total_ado),
                "adg_mtd": adg,
                "adg_m1": adg_m1,
                "adg_delta": adg - adg_m1,
                "adg_mom": pct(adg, adg_m1),
                "adg_share": safe_share(adg, total_adg),
                "total_ado": total_ado,
                "total_adg": total_adg,
                "total_subsidy_adg": total_subsidy,
                "subsidy_share": safe_share(total_subsidy, total_adg),
                "seller_funded_share": safe_share(seller_funded, funding_base),
                "platform_funded_share": safe_share(platform_funded, funding_base),
                "rank_type": "promo_lever",
                "non_mece_note": "not MECE; rebate, campaign, CFS and LPP can overlap",
            })
        source_rank_type(rows)
        for row in sorted(rows, key=lambda r: -max(r["ado_mtd"], r["adg_mtd"])):
            output.append([row[col] for col in SUBSIDY_HEADER])
        promo_ado_share_sum = sum((row["ado_share"] or 0) for row in rows if row["ado_share"] != "")
        if promo_ado_share_sum > 120:
            quality.append(["sec_subsidy", "info", "non-MECE source coverage", "expected", f"{site}: promo ADO shares sum to {promo_ado_share_sum:.1f}% because levers overlap"])
    return output


def build_ads_rows(buckets: Dict[str, Dict[str, float]], quality: List[List[Any]]) -> List[List[Any]]:
    output = [ADS_HEADER]
    quality.append(["sec_ams", "info", "HE1 ads adg %", "computed", "raw_dws_shop has no dedicated he1_ads_adg_pct field; using ads_adg / total_adg"])
    for site, b in sorted(buckets.items(), key=lambda kv: kv[1]["adg_mtd"], reverse=True):
        total_ado = b["ado_mtd"]
        total_adg = b["adg_mtd"]
        ads_ado = b["ads_ado_mtd"]
        ads_adg = b["ads_adg_mtd"]
        spend = b["ads_spend_mtd"]
        ads_ado_m1 = b["ads_ado_m1"]
        ads_adg_m1 = b["ads_adg_m1"]
        spend_m1 = b["ads_spend_m1"]
        roas = rate(ads_adg, spend)
        spend_gmv = safe_share(spend, total_adg)
        ads_adg_share = safe_share(ads_adg, total_adg)
        if spend_gmv != "" and spend_gmv > 100 and total_adg > 0:
            quality.append(["sec_ams", "warn", "ads spend/gmv", "check", f"{site}: ads_spend / total_adg = {spend_gmv:.1f}%; confirm spend and GMV currency/metric scope"])
        if roas != "" and spend_gmv != "" and spend_gmv > 8 and roas < 2:
            status = "高投入低回报"
        elif ads_adg_share != "" and ads_adg_share >= 25 and roas != "" and roas >= 5:
            status = "广告有效可扩量"
        elif ads_adg_share == "" or ads_adg_share < 5:
            status = "低广告依赖"
        else:
            status = "效率待监控"
        output.append([
            site,
            total_ado,
            total_adg,
            ads_ado,
            ads_adg,
            spend,
            safe_share(ads_ado, total_ado),
            ads_adg_share,
            ads_adg_share,
            spend_gmv,
            roas,
            ads_ado_m1,
            ads_adg_m1,
            spend_m1,
            ads_ado - ads_ado_m1,
            ads_adg - ads_adg_m1,
            spend - spend_m1,
            pct(ads_ado, ads_ado_m1),
            pct(ads_adg, ads_adg_m1),
            pct(spend, spend_m1),
            status,
        ])
    return output


def enrich_commercial_sections(oauth: str, sheet_id: str, month: str) -> Dict[str, Any]:
    service = build("sheets", "v4", credentials=build_credentials(oauth))
    raw_shop = read_tab(service, sheet_id, "raw_dws_shop")
    raw_item = read_tab(service, sheet_id, "raw_dws_item")
    quality: List[List[Any]] = [QUALITY_HEADER]

    listing_rows = build_listing_rows(raw_item, month, quality)
    buckets = build_shop_buckets(raw_shop, month, quality)
    fulfillment_rows = build_fulfillment_rows(buckets, quality)
    traffic_rows = build_traffic_rows(buckets)
    subsidy_rows = build_subsidy_rows(buckets, quality)
    ads_rows = build_ads_rows(buckets, quality)

    outputs = {
        "sec_listing_change": listing_rows,
        "sec_fulfillment": fulfillment_rows,
        "sec_traffic_channel": traffic_rows,
        "sec_subsidy": subsidy_rows,
        "sec_ams": ads_rows,
        "sec_data_quality_notes": quality,
    }
    for tab, rows in outputs.items():
        write_tab(service, sheet_id, tab, rows)

    return {
        "ok": True,
        "sections": {tab: len(rows) - 1 for tab, rows in outputs.items()},
        "quality_notes": len(quality) - 1,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Enrich commercial AutoDeck sections from raw tabs.")
    parser.add_argument("--oauth", required=True)
    parser.add_argument("--sheet-id", required=True)
    parser.add_argument("--month", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = enrich_commercial_sections(args.oauth, args.sheet_id, args.month)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result)
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
