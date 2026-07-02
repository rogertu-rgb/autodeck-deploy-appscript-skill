#!/usr/bin/env python3
"""Build a richer sec_shop_impact tab from raw shop and item tabs."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import date
from typing import Any, Dict, Iterable, List, Optional, Tuple

from googleapiclient.discovery import build

from oauth_check import build_credentials


HEADER = [
    "scope",
    "rank_type",
    "rank",
    "site",
    "top_site",
    "shop_id",
    "shop_name",
    "l3",
    "price_range",
    "adg_mtd",
    "ado_mtd",
    "adimp_mtd",
    "adclick_mtd",
    "ctr_mtd",
    "cr_mtd",
    "adg_per_order_mtd",
    "adg_m1",
    "ado_m1",
    "adimp_m1",
    "adclick_m1",
    "ctr_m1",
    "cr_m1",
    "adg_per_order_m1",
    "adg_delta",
    "ado_delta",
    "adimp_delta",
    "adclick_delta",
    "ctr_delta_pp",
    "cr_delta_pp",
    "adg_per_order_delta",
    "adg_mom",
    "ado_mom",
    "adimp_mom",
    "adclick_mom",
    "site_adg_share",
    "site_delta_contribution_pct",
    "primary_driver",
    "is_official_shop",
    "days_cnt",
]


def month_serial(month: str) -> int:
    year_s, month_s = month.split("-", 1)
    current = date(int(year_s), int(month_s), 1)
    return (current - date(1899, 12, 30)).days


def prev_month_serial(month: str) -> int:
    year_s, month_s = month.split("-", 1)
    year, mon = int(year_s), int(month_s)
    if mon == 1:
        year -= 1
        mon = 12
    else:
        mon -= 1
    return month_serial(f"{year:04d}-{mon:02d}")


def idx(header: List[Any]) -> Dict[str, int]:
    return {str(name).strip().lower(): i for i, name in enumerate(header)}


def cell(row: List[Any], index: Dict[str, int], name: str, default: Any = "") -> Any:
    pos = index.get(name)
    if pos is None or pos >= len(row):
        return default
    return row[pos]


def num(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def pct(current: float, previous: float) -> Any:
    if not previous:
        return ""
    return (current - previous) / previous * 100


def rate(numerator: float, denominator: float) -> Any:
    if not denominator:
        return ""
    return numerator / denominator


def delta_pp(current: Any, previous: Any) -> Any:
    if current == "" or previous == "":
        return ""
    return (float(current) - float(previous)) * 100


def primary_driver(row: Dict[str, Any]) -> str:
    direction = -1 if row.get("adg_delta", 0) < 0 else 1
    checks = [
        ("曝光", row.get("adimp_mom", "")),
        ("点击", row.get("adclick_mom", "")),
        ("CTR", row.get("ctr_delta_pp", "")),
        ("CR", row.get("cr_delta_pp", "")),
        ("客单", row.get("adg_per_order_delta", "")),
    ]
    aligned: List[Tuple[str, float]] = []
    for label, value in checks:
        if value == "" or value is None:
            continue
        v = float(value)
        if direction < 0 and v < 0:
            aligned.append((label, abs(v)))
        elif direction > 0 and v > 0:
            aligned.append((label, abs(v)))
    if aligned:
        label = sorted(aligned, key=lambda item: item[1], reverse=True)[0][0]
        return label + ("下降" if direction < 0 else "提升")
    return "结构变化"


def read_tab(service, sheet_id: str, name: str) -> List[List[Any]]:
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"'{name}'",
            valueRenderOption="UNFORMATTED_VALUE",
        ).execute()
    except Exception:
        return []
    return result.get("values", [])


def write_tab(service, sheet_id: str, name: str, rows: List[List[Any]]) -> None:
    meta = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    existing = {s["properties"]["title"] for s in meta.get("sheets", [])}
    if name not in existing:
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={"requests": [{"addSheet": {"properties": {"title": name}}}]},
        ).execute()
    service.spreadsheets().values().clear(spreadsheetId=sheet_id, range=f"'{name}'").execute()
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"'{name}'!A1",
        valueInputOption="USER_ENTERED",
        body={"values": rows},
    ).execute()


def shop_name_map(item_rows: List[List[Any]], latest_serial: int) -> Dict[str, str]:
    if not item_rows:
        return {}
    header = item_rows[0]
    index = idx(header)
    names: Dict[str, Tuple[int, str]] = {}
    for row in item_rows[1:]:
        shop_id = str(cell(row, index, "shop_id", "")).strip()
        name = str(cell(row, index, "shop_name", "")).strip()
        if not shop_id or not name:
            continue
        serial = int(num(cell(row, index, "year_month", latest_serial), latest_serial))
        current = names.get(shop_id)
        if current is None or abs(serial - latest_serial) < abs(current[0] - latest_serial):
            names[shop_id] = (serial, name)
    return {shop_id: name for shop_id, (_serial, name) in names.items()}


def enrich_rows(raw_shop_rows: List[List[Any]], raw_item_rows: List[List[Any]], month: str) -> List[List[Any]]:
    if len(raw_shop_rows) <= 1:
        return [HEADER]

    header = raw_shop_rows[0]
    index = idx(header)
    target = month_serial(month)
    previous = prev_month_serial(month)
    available_months = sorted({
        int(num(cell(row, index, "year_month", 0), 0))
        for row in raw_shop_rows[1:]
        if num(cell(row, index, "year_month", 0), 0)
    })
    if target not in available_months and available_months:
        target = available_months[-1]
        previous_candidates = [m for m in available_months if m < target]
        previous = previous_candidates[-1] if previous_candidates else previous

    names = shop_name_map(raw_item_rows, target)
    def empty_bucket() -> Dict[str, Any]:
        return {
        "adg_mtd": 0.0,
        "ado_mtd": 0.0,
        "adimp_mtd": 0.0,
        "adclick_mtd": 0.0,
        "adg_m1": 0.0,
        "ado_m1": 0.0,
        "adimp_m1": 0.0,
        "adclick_m1": 0.0,
        "is_official_shop": 0,
        "days_cnt": 0,
        }

    grouped: Dict[Tuple[str, str], Dict[str, Any]] = defaultdict(empty_bucket)
    l3_price_grouped: Dict[Tuple[str, str, str, str], Dict[str, Any]] = defaultdict(empty_bucket)

    def add_raw_to_bucket(bucket: Dict[str, Any], row: List[Any], serial: int) -> None:
        if serial == target:
            suffix = "mtd"
        elif serial == previous:
            suffix = "m1"
        else:
            return
        bucket[f"adg_{suffix}"] += num(cell(row, index, "adg", 0))
        bucket[f"ado_{suffix}"] += num(cell(row, index, "ado", 0))
        bucket[f"adimp_{suffix}"] += num(cell(row, index, "adimp", 0))
        bucket[f"adclick_{suffix}"] += num(cell(row, index, "adclicks", cell(row, index, "adclick", 0)))
        if serial == target:
            bucket["is_official_shop"] = max(bucket["is_official_shop"], int(num(cell(row, index, "is_official_shop", 0), 0)))
            bucket["days_cnt"] = max(bucket["days_cnt"], int(num(cell(row, index, "days_cnt", 0), 0)))

    for row in raw_shop_rows[1:]:
        serial = int(num(cell(row, index, "year_month", 0), 0))
        if serial not in (target, previous):
            continue
        site = str(cell(row, index, "site", "")).strip()
        shop_id = str(cell(row, index, "shop_id", "")).strip()
        if not site or not shop_id:
            continue
        bucket = grouped[(site, shop_id)]
        add_raw_to_bucket(bucket, row, serial)
        l3 = str(cell(row, index, "l3", "")).strip() or "Unknown L3"
        price_range = str(cell(row, index, "price_range", "")).strip() or "Unknown Price"
        driver_bucket = l3_price_grouped[(site, shop_id, l3, price_range)]
        add_raw_to_bucket(driver_bucket, row, serial)

    site_rows: List[Dict[str, Any]] = []

    def finalize_row(base: Dict[str, Any]) -> Dict[str, Any]:
        row = dict(base)
        row["adg_delta"] = row["adg_mtd"] - row["adg_m1"]
        row["ado_delta"] = row["ado_mtd"] - row["ado_m1"]
        row["adimp_delta"] = row["adimp_mtd"] - row["adimp_m1"]
        row["adclick_delta"] = row["adclick_mtd"] - row["adclick_m1"]
        row["ctr_mtd"] = rate(row["adclick_mtd"], row["adimp_mtd"])
        row["ctr_m1"] = rate(row["adclick_m1"], row["adimp_m1"])
        row["cr_mtd"] = rate(row["ado_mtd"], row["adclick_mtd"])
        row["cr_m1"] = rate(row["ado_m1"], row["adclick_m1"])
        row["adg_per_order_mtd"] = rate(row["adg_mtd"], row["ado_mtd"])
        row["adg_per_order_m1"] = rate(row["adg_m1"], row["ado_m1"])
        row["ctr_delta_pp"] = delta_pp(row["ctr_mtd"], row["ctr_m1"])
        row["cr_delta_pp"] = delta_pp(row["cr_mtd"], row["cr_m1"])
        row["adg_per_order_delta"] = "" if row["adg_per_order_mtd"] == "" or row["adg_per_order_m1"] == "" else row["adg_per_order_mtd"] - row["adg_per_order_m1"]
        row["adg_mom"] = pct(row["adg_mtd"], row["adg_m1"])
        row["ado_mom"] = pct(row["ado_mtd"], row["ado_m1"])
        row["adimp_mom"] = pct(row["adimp_mtd"], row["adimp_m1"])
        row["adclick_mom"] = pct(row["adclick_mtd"], row["adclick_m1"])
        row["primary_driver"] = primary_driver(row)
        return row

    for (site, shop_id), values in grouped.items():
        adg = values["adg_mtd"]
        ado = values["ado_mtd"]
        prev_adg = values["adg_m1"]
        prev_ado = values["ado_m1"]
        if not any([adg, ado, prev_adg, prev_ado]):
            continue
        site_rows.append(finalize_row({
            "scope": site,
            "site": site,
            "top_site": site,
            "shop_id": shop_id,
            "shop_name": names.get(shop_id, ""),
            "l3": "",
            "price_range": "",
            "adg_mtd": adg,
            "ado_mtd": ado,
            "adimp_mtd": values["adimp_mtd"],
            "adclick_mtd": values["adclick_mtd"],
            "adg_m1": prev_adg,
            "ado_m1": prev_ado,
            "adimp_m1": values["adimp_m1"],
            "adclick_m1": values["adclick_m1"],
            "is_official_shop": values["is_official_shop"],
            "days_cnt": values["days_cnt"],
        }))

    site_total_adg: Dict[str, float] = defaultdict(float)
    site_total_delta: Dict[str, float] = defaultdict(float)
    site_total_abs_delta: Dict[str, float] = defaultdict(float)
    for row in site_rows:
        site_total_adg[row["site"]] += row["adg_mtd"]
        site_total_delta[row["site"]] += row["adg_delta"]
        site_total_abs_delta[row["site"]] += abs(row["adg_delta"])
    for row in site_rows:
        total_adg = site_total_adg.get(row["site"], 0)
        total_abs_delta = site_total_abs_delta.get(row["site"], 0)
        row["site_adg_share"] = row["adg_mtd"] / total_adg * 100 if total_adg else ""
        row["site_delta_contribution_pct"] = abs(row["adg_delta"]) / total_abs_delta * 100 if total_abs_delta else ""

    overall_rows: List[Dict[str, Any]] = []
    total_overall_adg = sum(row["adg_mtd"] for row in site_rows)
    for row in site_rows:
        out = dict(row)
        out["scope"] = "overall"
        out["site"] = "All"
        out["top_site"] = row["site"]
        out["site_adg_share"] = row["adg_mtd"] / total_overall_adg * 100 if total_overall_adg else ""
        out["site_delta_contribution_pct"] = ""
        overall_rows.append(out)

    l3_price_rows: List[Dict[str, Any]] = []
    for (site, shop_id, l3, price_range), values in l3_price_grouped.items():
        adg = values["adg_mtd"]
        ado = values["ado_mtd"]
        prev_adg = values["adg_m1"]
        prev_ado = values["ado_m1"]
        if not any([adg, ado, prev_adg, prev_ado]):
            continue
        row = finalize_row({
            "scope": site,
            "site": site,
            "top_site": site,
            "shop_id": shop_id,
            "shop_name": names.get(shop_id, ""),
            "l3": l3,
            "price_range": price_range,
            "adg_mtd": adg,
            "ado_mtd": ado,
            "adimp_mtd": values["adimp_mtd"],
            "adclick_mtd": values["adclick_mtd"],
            "adg_m1": prev_adg,
            "ado_m1": prev_ado,
            "adimp_m1": values["adimp_m1"],
            "adclick_m1": values["adclick_m1"],
            "is_official_shop": values["is_official_shop"],
            "days_cnt": values["days_cnt"],
        })
        total_abs_delta = site_total_abs_delta.get(site, 0)
        row["site_adg_share"] = row["adg_mtd"] / site_total_adg[site] * 100 if site_total_adg.get(site) else ""
        row["site_delta_contribution_pct"] = abs(row["adg_delta"]) / total_abs_delta * 100 if total_abs_delta else ""
        l3_price_rows.append(row)

    output: List[List[Any]] = [HEADER]

    def append_ranked(rows: Iterable[Dict[str, Any]], rank_type: str, limit: Optional[int] = None) -> None:
        selected = list(rows)
        if limit is not None:
            selected = selected[:limit]
        for rank, row in enumerate(selected, 1):
            output.append([
                row["scope"],
                rank_type,
                rank,
                row["site"],
                row["top_site"],
                row["shop_id"],
                row.get("shop_name", ""),
                row.get("l3", ""),
                row.get("price_range", ""),
                row["adg_mtd"],
                row["ado_mtd"],
                row.get("adimp_mtd", ""),
                row.get("adclick_mtd", ""),
                row.get("ctr_mtd", ""),
                row.get("cr_mtd", ""),
                row.get("adg_per_order_mtd", ""),
                row["adg_m1"],
                row["ado_m1"],
                row.get("adimp_m1", ""),
                row.get("adclick_m1", ""),
                row.get("ctr_m1", ""),
                row.get("cr_m1", ""),
                row.get("adg_per_order_m1", ""),
                row["adg_delta"],
                row["ado_delta"],
                row.get("adimp_delta", ""),
                row.get("adclick_delta", ""),
                row.get("ctr_delta_pp", ""),
                row.get("cr_delta_pp", ""),
                row.get("adg_per_order_delta", ""),
                row["adg_mom"],
                row["ado_mom"],
                row.get("adimp_mom", ""),
                row.get("adclick_mom", ""),
                row.get("site_adg_share", ""),
                row.get("site_delta_contribution_pct", ""),
                row.get("primary_driver", ""),
                row["is_official_shop"],
                row["days_cnt"],
            ])

    append_ranked(sorted(overall_rows, key=lambda r: r["adg_mtd"], reverse=True), "top_adg", 10)
    append_ranked(sorted(overall_rows, key=lambda r: r["ado_mtd"], reverse=True), "top_ado", 10)
    append_ranked(sorted(site_rows, key=lambda r: abs(r["adg_delta"]), reverse=True), "shop_mover", 30)

    for site in sorted({row["site"] for row in site_rows}):
        site_subset = [row for row in site_rows if row["site"] == site]
        key_shops = sorted(site_subset, key=lambda r: abs(r["adg_delta"]), reverse=True)[:5]
        append_ranked(key_shops, "site_key_shop", 5)
        append_ranked([r for r in sorted(site_subset, key=lambda r: r["adg_delta"], reverse=True) if r["adg_delta"] > 0], "site_gain", 3)
        append_ranked([r for r in sorted(site_subset, key=lambda r: r["adg_delta"]) if r["adg_delta"] < 0], "site_loss", 3)
        for shop in key_shops:
            l3_subset = [row for row in l3_price_rows if row["site"] == site and row["shop_id"] == shop["shop_id"]]
            append_ranked([r for r in sorted(l3_subset, key=lambda r: r["adg_delta"], reverse=True) if r["adg_delta"] > 0], "l3_price_gain", 5)
            append_ranked([r for r in sorted(l3_subset, key=lambda r: r["adg_delta"]) if r["adg_delta"] < 0], "l3_price_loss", 5)

    return output


def enrich_shop_impact(oauth: str, sheet_id: str, month: str) -> Dict[str, Any]:
    service = build("sheets", "v4", credentials=build_credentials(oauth))
    raw_shop = read_tab(service, sheet_id, "raw_dws_shop")
    raw_item = read_tab(service, sheet_id, "raw_dws_item")
    if len(raw_shop) <= 1:
        return {"ok": False, "skipped": True, "reason": "raw_dws_shop missing or empty"}
    rows = enrich_rows(raw_shop, raw_item, month)
    write_tab(service, sheet_id, "sec_shop_impact", rows)
    rank_counts: Dict[str, int] = defaultdict(int)
    sites = set()
    for row in rows[1:]:
        rank_counts[str(row[1])] += 1
        if row[3] and row[3] != "All":
            sites.add(str(row[3]))
    return {
        "ok": True,
        "rows_written": len(rows) - 1,
        "sites": len(sites),
        "rank_counts": dict(rank_counts),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Enrich sec_shop_impact from raw_dws_shop.")
    parser.add_argument("--oauth", required=True)
    parser.add_argument("--sheet-id", required=True)
    parser.add_argument("--month", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = enrich_shop_impact(args.oauth, args.sheet_id, args.month)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result)
    return 0 if result.get("ok") or result.get("skipped") else 2


if __name__ == "__main__":
    raise SystemExit(main())
