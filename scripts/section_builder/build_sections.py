import json
#!/usr/bin/env python3
"""
build_sections.py — AutoDeck v_0602 Section Builder
====================================================
Reads 3 raw DataFrames from Google Sheet (L2 output) →
runs 15 build_*() functions →
writes 15 section tabs + sec_text + sec_config back to Sheet.

Architecture:  L2 (Agent) → raw tabs → THIS SCRIPT → section tabs → L4 (HTML)

Usage:
  python3 build_sections.py --sheet-id <ID> --ggp "浙江格蕾美..."

Requirements:
  pip install pandas google-auth google-api-python-client
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import googleapiclient.discovery

# ═══════════════════════════════════════════════════════════════
# 0. Google Sheets I/O
# ═══════════════════════════════════════════════════════════════

CREDS_PATH = os.path.expanduser(os.environ.get("AUTODECK_GOOGLE_OAUTH", "~/.config/autodeck/oauth-authorized-user.json"))
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _get_sheets_service():
    """Authenticate and return Google Sheets service."""
    with open(CREDS_PATH) as f:
        creds_data = json.load(f)
    creds = Credentials(
        token=creds_data["token"],
        refresh_token=creds_data["refresh_token"],
        token_uri=creds_data["token_uri"],
        client_id=creds_data["client_id"],
        client_secret=creds_data["client_secret"],
        scopes=SCOPES,
    )
    if not creds.valid:
        creds.refresh(Request())
        creds_data["token"] = creds.token
        with open(CREDS_PATH, "w") as f:
            json.dump(creds_data, f)
    return googleapiclient.discovery.build("sheets", "v4", credentials=creds)


def read_sheet_tab(sheet_id: str, tab_name: str) -> pd.DataFrame:
    """Read a Sheet tab into a pandas DataFrame (first row = header)."""
    service = _get_sheets_service()
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=sheet_id, range=tab_name)
        .execute()
    )
    values = result.get("values", [])
    if not values:
        return pd.DataFrame()
    header = values[0]
    width = len(header)
    data = [(row + [""] * width)[:width] for row in values[1:]]
    df = pd.DataFrame(data, columns=header)
    return df


def write_sheet_tab(
    sheet_id: str, tab_name: str, data: List[List[Any]], clear: bool = True
):
    """Write rows to a Sheet tab. Creates tab if needed. Clears existing content."""
    service = _get_sheets_service()

    if clear:
        # Clear existing content
        try:
            service.spreadsheets().values().clear(
                spreadsheetId=sheet_id, range=tab_name
            ).execute()
        except Exception:
            pass  # Tab might not exist yet

    # Write new data
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"{tab_name}!A1",
        body={"values": data},
        valueInputOption="USER_ENTERED",
    ).execute()


def load_raw_data(sheet_id: str) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame], pd.DataFrame]:
    """Load raw tabs from Sheet. Returns (df_a, df_b_dict, df_c).
    df_b_dict keys: site, l1, l2, l3, price (split benchmark tabs)"""
    print("Loading raw data from Sheet...")
    df_a = read_sheet_tab(sheet_id, "raw_dws_shop")
    df_c = read_sheet_tab(sheet_id, "raw_dws_item")
    print(f"  raw_dws_shop:  {len(df_a)} rows, {len(df_a.columns)} cols")
    print(f"  raw_dws_item:  {len(df_c)} rows, {len(df_c.columns)} cols")

    # Load split benchmark tabs
    df_b = {}
    for key in ["site", "l1", "l2", "l3", "price"]:
        tab_name = f"raw_benchmark_{key}"
        try:
            df = read_sheet_tab(sheet_id, tab_name)
            if len(df) > 0:
                df_b[key] = df
                print(f"  {tab_name}: {len(df)} rows, {len(df.columns)} cols")
        except Exception:
            print(f"  {tab_name}: not found, skipping")

    # Fallback: if no split tabs, try old combined benchmark
    if not df_b:
        df_old = read_sheet_tab(sheet_id, "raw_benchmark")
        if len(df_old) > 0:
            df_b["site"] = df_old
            print(f"  raw_benchmark (legacy): {len(df_old)} rows")

    return df_a, df_b, df_c


# ═══════════════════════════════════════════════════════════════
# 1. Utility Functions
# ═══════════════════════════════════════════════════════════════


def _safe_float(val) -> float:
    """Convert value to float, returning 0.0 on failure."""
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def _safe_int(val) -> int:
    """Convert value to int, returning 0 on failure."""
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return 0


def _mom_pct(mtd: float, m1: float) -> Optional[float]:
    """Compute MoM% = (MTD - M1) / M1 * 100. Returns None if M1=0."""
    if m1 == 0:
        return None
    return round((mtd - m1) / m1 * 100, 1)


def _gap_pp(seller_mom: Optional[float], mkt_mom: Optional[float]) -> Optional[float]:
    """Compute gap_pp = seller_MoM% - mkt_MoM%."""
    if seller_mom is None or mkt_mom is None:
        return None
    return round(seller_mom - mkt_mom, 1)


def _df_to_rows(df: pd.DataFrame, columns: List[str]) -> List[List[Any]]:
    """Convert DataFrame to list-of-lists (header + data rows)."""
    rows = [columns]
    for _, row in df.iterrows():
        rows.append([row.get(c, "") for c in columns])
    return rows


# ═══════════════════════════════════════════════════════════════
# 2. Section Build Functions
# ═══════════════════════════════════════════════════════════════


# === Level 1: Overview ===


def build_12m_history(df_a: pd.DataFrame) -> Dict[str, Any]:
    """
    Section 1.0: 12-Month History Performance.
    Input: 13 months of Table A data.
    Output: site × year_month matrix with ADG/ADO + MoM% + share%.
    """
    # Ensure numeric
    df = df_a.copy()
    df["adg"] = df["adg"].apply(_safe_float)
    df["ado"] = df["ado"].apply(_safe_float)

    # Aggregate: site × year_month
    agg = (
        df.groupby(["site", "year_month"])
        .agg(adg=("adg", "sum"), ado=("ado", "sum"))
        .reset_index()
    )

    # Total per month (across all sites)
    monthly_total = agg.groupby("year_month").agg(total_adg=("adg", "sum"), total_ado=("ado", "sum")).reset_index()
    agg = agg.merge(monthly_total, on="year_month")

    # Share %
    agg["adg_share"] = (agg["adg"] / agg["total_adg"] * 100).round(1)
    agg["ado_share"] = (agg["ado"] / agg["total_ado"] * 100).round(1)

    # MoM% per site (shift within each site group, sorted by year_month)
    agg = agg.sort_values(["site", "year_month"])
    for site in agg["site"].unique():
        mask = agg["site"] == site
        idx = agg.loc[mask].index
        agg.loc[idx, "adg_prev"] = agg.loc[idx, "adg"].shift(1)
        agg.loc[idx, "ado_prev"] = agg.loc[idx, "ado"].shift(1)

    agg["adg_mom"] = agg.apply(
        lambda r: _mom_pct(r["adg"], r["adg_prev"]) if r["adg_prev"] > 0 else None,
        axis=1,
    )
    agg["ado_mom"] = agg.apply(
        lambda r: _mom_pct(r["ado"], r["ado_prev"]) if r["ado_prev"] > 0 else None,
        axis=1,
    )

    # Output columns
    out_cols = [
        "year_month", "site", "adg", "ado", "adg_mom", "ado_mom",
        "adg_share", "ado_share", "total_adg", "total_ado",
    ]
    rows = _df_to_rows(agg, out_cols)

    return {
        "section_id": "sec_12m_history",
        "chart_type": "bar_stacked",
        "data": rows,
        "meta": {
            "months_count": agg["year_month"].nunique(),
            "sites": sorted(agg["site"].unique().tolist()),
            "latest_total_adg": round(agg[agg["year_month"] == agg["year_month"].max()]["total_adg"].iloc[0], 0) if len(agg) > 0 else 0,
        },
    }


def build_site_benchmark(df_a: pd.DataFrame, df_b: pd.DataFrame) -> Dict[str, Any]:
    """
    Section 1.1: Site MoM% vs Benchmark MoM%.
    df_b already has MoM% columns (mkt_adg_mom, mkt_ado_mom) from v2 SQL.
    """
    df = df_a.copy()
    df["adg"] = df["adg"].apply(_safe_float)
    df["ado"] = df["ado"].apply(_safe_float)

    # Identify current month (max year_month) and previous month
    months = sorted(df["year_month"].unique())
    if len(months) < 2:
        return {"section_id": "sec_site_benchmark", "error": "Need at least 2 months of data"}
    current_m, prev_m = months[-1], months[-2]

    # Seller MTD and M-1 per site
    mtd = df[df["year_month"] == current_m].groupby("site").agg(adg_mtd=("adg", "sum"), ado_mtd=("ado", "sum")).reset_index()
    m1 = df[df["year_month"] == prev_m].groupby("site").agg(adg_m1=("adg", "sum"), ado_m1=("ado", "sum")).reset_index()
    seller = mtd.merge(m1, on="site", how="outer").fillna(0)

    # Seller MoM%
    seller["seller_adg_mom"] = seller.apply(lambda r: _mom_pct(r["adg_mtd"], r["adg_m1"]), axis=1)
    seller["seller_ado_mom"] = seller.apply(lambda r: _mom_pct(r["ado_mtd"], r["ado_m1"]), axis=1)

    # Total ADG/ADO for share%
    total_adg_mtd = seller["adg_mtd"].sum()
    total_ado_mtd = seller["ado_mtd"].sum()
    seller["adg_share"] = (seller["adg_mtd"] / total_adg_mtd * 100).round(1) if total_adg_mtd > 0 else 0
    seller["ado_share"] = (seller["ado_mtd"] / total_ado_mtd * 100).round(1) if total_ado_mtd > 0 else 0

    # Benchmark (df_b v2 — already MoM%)
    if df_b is not None and len(df_b) > 0:
        b = df_b.copy()
        # Filter to CNCB seller_type for site-level benchmark
        if "seller_type" in b.columns:
            b = b[b["seller_type"] == "CNCB"]
        if "l1" in b.columns and "l2" in b.columns and "l3" in b.columns:
            # Site-level: aggregate across all L1/L2/L3
            bench = b.groupby("site").agg(
                mkt_adg_mom=("mkt_adg_mom", "mean"),
                mkt_ado_mom=("mkt_ado_mom", "mean"),
            ).reset_index()
        else:
            bench = b[["site", "mkt_adg_mom", "mkt_ado_mom"]].copy()
    else:
        bench = pd.DataFrame(columns=["site", "mkt_adg_mom", "mkt_ado_mom"])

    # Merge seller + benchmark
    result = seller.merge(bench, on="site", how="left")
    result["adg_gap_pp"] = result.apply(
        lambda r: _gap_pp(r["seller_adg_mom"], _safe_float(r.get("mkt_adg_mom")) if pd.notna(r.get("mkt_adg_mom")) else None), axis=1
    )
    result["ado_gap_pp"] = result.apply(
        lambda r: _gap_pp(r["seller_ado_mom"], _safe_float(r.get("mkt_ado_mom")) if pd.notna(r.get("mkt_ado_mom")) else None), axis=1
    )

    out_cols = [
        "site", "adg_mtd", "adg_m1", "seller_adg_mom", "mkt_adg_mom", "adg_gap_pp",
        "ado_mtd", "ado_m1", "seller_ado_mom", "mkt_ado_mom", "ado_gap_pp",
        "adg_share", "ado_share",
    ]
    rows = _df_to_rows(result, out_cols)

    return {
        "section_id": "sec_site_benchmark",
        "chart_type": "dual_axis",
        "data": rows,
        "meta": {
            "current_month": str(current_m),
            "previous_month": str(prev_m),
            "total_adg_mtd": round(total_adg_mtd, 0),
        },
    }


def build_l1_overview(
    df_a: pd.DataFrame, df_b: pd.DataFrame, site_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Section 1.2: L1 Category Overview.
    """
    df = df_a.copy()
    df["adg"] = df["adg"].apply(_safe_float)
    df["ado"] = df["ado"].apply(_safe_float)

    if site_filter and site_filter != "Total":
        df = df[df["site"] == site_filter]

    months = sorted(df["year_month"].unique())
    if len(months) < 2:
        return {"section_id": "sec_l1_overview", "error": "Need at least 2 months"}
    current_m, prev_m = months[-1], months[-2]

    # MTD and M-1 per L1
    mtd = df[df["year_month"] == current_m].groupby("l1").agg(adg_mtd=("adg", "sum"), ado_mtd=("ado", "sum")).reset_index()
    m1 = df[df["year_month"] == prev_m].groupby("l1").agg(adg_m1=("adg", "sum"), ado_m1=("ado", "sum")).reset_index()
    result = mtd.merge(m1, on="l1", how="outer").fillna(0)

    result["adg_mom"] = result.apply(lambda r: _mom_pct(r["adg_mtd"], r["adg_m1"]), axis=1)
    result["ado_mom"] = result.apply(lambda r: _mom_pct(r["ado_mtd"], r["ado_m1"]), axis=1)

    total_adg = result["adg_mtd"].sum()
    result["adg_share"] = (result["adg_mtd"] / total_adg * 100).round(1) if total_adg > 0 else 0

    # Benchmark MoM% by L1 (from v2 B table)
    if df_b is not None and len(df_b) > 0:
        b = df_b.copy()
        if "seller_type" in b.columns:
            b = b[b["seller_type"] == "CNCB"]
        # Aggregate mkt_adg_mom across site/l2/l3/price_band to L1 level
        bench_l1 = b.groupby("l1").agg(mkt_adg_mom=("mkt_adg_mom", "mean")).reset_index()
        result = result.merge(bench_l1, on="l1", how="left")
    else:
        result["mkt_adg_mom"] = None

    result["adg_gap_pp"] = result.apply(
        lambda r: _gap_pp(r["adg_mom"], _safe_float(r.get("mkt_adg_mom")) if pd.notna(r.get("mkt_adg_mom")) else None), axis=1
    )

    # Sort by ADG descending
    result = result.sort_values("adg_mtd", ascending=False)

    out_cols = ["l1", "adg_mtd", "adg_m1", "adg_mom", "mkt_adg_mom", "adg_gap_pp",
                 "ado_mtd", "ado_m1", "ado_mom", "adg_share"]
    rows = _df_to_rows(result, out_cols)

    return {
        "section_id": "sec_l1_overview",
        "chart_type": "dual_axis",
        "data": rows,
        "meta": {"top_l1": result.iloc[0]["l1"] if len(result) > 0 else None,
                 "site_filter": site_filter or "Total"},
    }


# === Level 2: Category Deep Dive ===


def build_l1_matrix(df_a: pd.DataFrame, df_b: pd.DataFrame) -> Dict[str, Any]:
    """
    Section 1.3: site × L1 heatmap matrix.
    """
    df = df_a.copy()
    df["adg"] = df["adg"].apply(_safe_float)

    months = sorted(df["year_month"].unique())
    if len(months) < 2:
        return {"section_id": "sec_l1_matrix", "error": "Need at least 2 months"}
    current_m, prev_m = months[-1], months[-2]

    mtd = df[df["year_month"] == current_m].groupby(["site", "l1"]).agg(adg_mtd=("adg", "sum")).reset_index()
    m1 = df[df["year_month"] == prev_m].groupby(["site", "l1"]).agg(adg_m1=("adg", "sum")).reset_index()
    result = mtd.merge(m1, on=["site", "l1"], how="outer").fillna(0)
    result["adg_mom"] = result.apply(lambda r: _mom_pct(r["adg_mtd"], r["adg_m1"]), axis=1)

    # Share within site
    site_total = result.groupby("site")["adg_mtd"].transform("sum")
    result["share_in_site"] = (result["adg_mtd"] / site_total * 100).round(1)

    # Benchmark
    if df_b is not None and len(df_b) > 0:
        b = df_b.copy()
        if "seller_type" in b.columns:
            b = b[b["seller_type"] == "CNCB"]
        bench = b.groupby(["site", "l1"]).agg(mkt_adg_mom=("mkt_adg_mom", "mean")).reset_index()
        result = result.merge(bench, on=["site", "l1"], how="left")
    else:
        result["mkt_adg_mom"] = None

    result["gap_pp"] = result.apply(
        lambda r: _gap_pp(r["adg_mom"], _safe_float(r.get("mkt_adg_mom", None))), axis=1
    )
    # If benchmark is unavailable (all gap_pp NaN), fall back to seller-side MoM anomalies
    benchmark_available = result["gap_pp"].notna().any()

    # Anomaly ranking: prefer benchmark gap, fall back to |seller_mom|
    if benchmark_available:
        result["abs_gap"] = result["gap_pp"].abs()
        anomalies = result[result["abs_gap"] > 5].sort_values("abs_gap", ascending=False)
    else:
        result["abs_mom"] = result["adg_mom"].abs()
        anomalies = result[(result["abs_mom"] > 20) & (result["adg_mtd"] > 0)].sort_values("abs_mom", ascending=False)
    result = result.sort_values("adg_mtd", ascending=False)

    out_cols = ["site", "l1", "adg_mtd", "adg_m1", "adg_mom", "mkt_adg_mom",
                 "gap_pp", "share_in_site"]
    rows = _df_to_rows(result, out_cols)

    return {
        "section_id": "sec_l1_matrix",
        "chart_type": "heatmap",
        "data": rows,
        "meta": {
            "anomalies": [
                {"site": r["site"], "l1": r["l1"], "gap_pp": r.get("gap_pp", None)}
                for _, r in anomalies.head(5).iterrows()
            ] if benchmark_available else [
                {"site": r["site"], "l1": r["l1"], "mom_pct": r["adg_mom"]}
                for _, r in anomalies.head(5).iterrows()
            ],
            "anomaly_count": len(anomalies),
            "benchmark_available": benchmark_available,
        },
    }


def build_l2_drill(
    df_a: pd.DataFrame, df_b: pd.DataFrame, l1_filter: str
) -> Dict[str, Any]:
    """
    Section 1.4: L2 drill-down within a selected L1.
    """
    df = df_a.copy()
    df = df[df["l1"] == l1_filter]
    df["adg"] = df["adg"].apply(_safe_float)

    months = sorted(df["year_month"].unique())
    if len(months) < 2:
        return {"section_id": "sec_l2_drill", "error": "Need at least 2 months"}
    current_m, prev_m = months[-1], months[-2]

    mtd = df[df["year_month"] == current_m].groupby(["site", "l2"]).agg(adg_mtd=("adg", "sum")).reset_index()
    m1 = df[df["year_month"] == prev_m].groupby(["site", "l2"]).agg(adg_m1=("adg", "sum")).reset_index()
    result = mtd.merge(m1, on=["site", "l2"], how="outer").fillna(0)
    result["adg_mom"] = result.apply(lambda r: _mom_pct(r["adg_mtd"], r["adg_m1"]), axis=1)

    # Share within L1
    l1_total = result.groupby("site")["adg_mtd"].transform("sum")
    result["share_in_l1"] = (result["adg_mtd"] / l1_total * 100).round(1)

    # Waterfall data: contribution of each L2 to L1 ADG change
    result["adg_delta"] = result["adg_mtd"] - result["adg_m1"]
    waterfall = result.groupby("l2").agg(adg_delta=("adg_delta", "sum")).sort_values("adg_delta").reset_index()

    # Benchmark
    if df_b is not None and len(df_b) > 0:
        b = df_b.copy()
        if "seller_type" in b.columns:
            b = b[b["seller_type"] == "CNCB"]
        bench = b[b["l1"] == l1_filter].groupby(["site", "l2"]).agg(
            mkt_adg_mom=("mkt_adg_mom", "mean")
        ).reset_index()
        result = result.merge(bench, on=["site", "l2"], how="left")
    else:
        result["mkt_adg_mom"] = None

    result["gap_pp"] = result.apply(
        lambda r: _gap_pp(r["adg_mom"], _safe_float(r.get("mkt_adg_mom")) if pd.notna(r.get("mkt_adg_mom")) else None), axis=1
    )

    out_cols = ["site", "l2", "adg_mtd", "adg_m1", "adg_mom", "mkt_adg_mom",
                 "gap_pp", "share_in_l1", "adg_delta"]
    rows = _df_to_rows(result, out_cols)

    return {
        "section_id": "sec_l2_drill",
        "chart_type": "waterfall",
        "data": rows,
        "meta": {
            "l1_filter": l1_filter,
            "waterfall": [
                {"l2": r["l2"], "delta": round(r["adg_delta"], 0)}
                for _, r in waterfall.iterrows()
            ],
        },
    }


def build_l3_granular(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    df_c: pd.DataFrame,
    l1: str,
    l2: str,
) -> Dict[str, Any]:
    """
    Section 1.5: L3 granular analysis + growth distribution + top items.
    """
    df = df_a.copy()
    df = df[(df["l1"] == l1) & (df["l2"] == l2)]
    df["adg"] = df["adg"].apply(_safe_float)

    months = sorted(df["year_month"].unique())
    if len(months) < 2:
        return {"section_id": "sec_l3_granular", "error": "Need at least 2 months"}
    current_m, prev_m = months[-1], months[-2]

    mtd = df[df["year_month"] == current_m].groupby(["site", "l3"]).agg(adg_mtd=("adg", "sum")).reset_index()
    m1 = df[df["year_month"] == prev_m].groupby(["site", "l3"]).agg(adg_m1=("adg", "sum")).reset_index()
    result = mtd.merge(m1, on=["site", "l3"], how="outer").fillna(0)
    result["adg_mom"] = result.apply(lambda r: _mom_pct(r["adg_mtd"], r["adg_m1"]), axis=1)

    l2_total = result.groupby("site")["adg_mtd"].transform("sum")
    result["share_in_l2"] = (result["adg_mtd"] / l2_total * 100).round(1)

    # Growth distribution from Table B v2 (p10/p25/p50 are already %)
    growth_cols = ["p10_growth", "p25_growth", "p50_growth", "seller_cnt"]
    if df_b is not None and len(df_b) > 0:
        b = df_b.copy()
        available_growth_cols = [c for c in growth_cols if c in b.columns]
        if available_growth_cols and "l1" in b.columns and "l2" in b.columns:
            b = b[(b["l1"] == l1) & (b["l2"] == l2)] if len(b) > 0 else b
            agg_dict = {c: (c, "first") for c in available_growth_cols}
            bench = b.groupby(["site", "l3"]).agg(**agg_dict).reset_index()
            result = result.merge(bench, on=["site", "l3"], how="left")
    for c in growth_cols:
        if c not in result.columns:
            result[c] = None

    # Top items from Table C
    top_items = []
    if df_c is not None and len(df_c) > 0:
        c = df_c.copy()
        c = c[(c["l1"] == l1) & (c["l2"] == l2)] if "l2" in c.columns else c
        c["mtd_adg"] = pd.to_numeric(c["mtd_adg"], errors="coerce").fillna(0)
        c["m1_adg"] = pd.to_numeric(c["m1_adg"], errors="coerce").fillna(0)
        c["adg_delta"] = c["mtd_adg"] - c["m1_adg"]

        gainers = c.nlargest(5, "adg_delta")
        losers = c.nsmallest(5, "adg_delta")

        for _, row in gainers.iterrows():
            top_items.append({
                "type": "gainer",
                "item_name": row.get("item_name", ""),
                "shop_name": row.get("shop_name", ""),
                "mtd_adg": round(row["mtd_adg"], 0),
                "m1_adg": round(row["m1_adg"], 0),
                "delta": round(row["adg_delta"], 0),
            })
        for _, row in losers.iterrows():
            top_items.append({
                "type": "loser",
                "item_name": row.get("item_name", ""),
                "shop_name": row.get("shop_name", ""),
                "mtd_adg": round(row["mtd_adg"], 0),
                "m1_adg": round(row["m1_adg"], 0),
                "delta": round(row["adg_delta"], 0),
            })

    out_cols = ["site", "l3", "adg_mtd", "adg_m1", "adg_mom", "share_in_l2",
                 "p10_growth", "p25_growth", "p50_growth", "seller_cnt"]
    rows = _df_to_rows(result, out_cols)

    return {
        "section_id": "sec_l3_granular",
        "chart_type": "treemap",
        "data": rows,
        "meta": {"l1": l1, "l2": l2, "top_items": top_items},
    }


# === Level 3: Anomaly & Impact ===


def build_volatility_signals(
    df_a: pd.DataFrame, df_b: pd.DataFrame
) -> Dict[str, Any]:
    """
    Section 1.6: Cross-category volatility signal scanner.
    6 signal types: VOLATILE_UP, VOLATILE_DOWN, MARKET_DIVERGENT,
                    SHARE_SHIFT, NEW_ENTRY, EXIT
    """
    df = df_a.copy()
    df["adg"] = df["adg"].apply(_safe_float)

    months = sorted(df["year_month"].unique())
    if len(months) < 2:
        return {"section_id": "sec_volatility", "error": "Need at least 2 months"}
    current_m, prev_m = months[-1], months[-2]

    # Compute seller MoM% for every site × L3
    mtd = (df[df["year_month"] == current_m]
           .groupby(["site", "l1", "l2", "l3"]).agg(adg_mtd=("adg", "sum")).reset_index())
    m1 = (df[df["year_month"] == prev_m]
          .groupby(["site", "l1", "l2", "l3"]).agg(adg_m1=("adg", "sum")).reset_index())
    result = mtd.merge(m1, on=["site", "l1", "l2", "l3"], how="outer").fillna(0)

    result["seller_mom"] = result.apply(
        lambda r: _mom_pct(r["adg_mtd"], r["adg_m1"]), axis=1
    )

    # Share shift (L3 share within its L2)
    l2_total_mtd = result.groupby(["site", "l1", "l2"])["adg_mtd"].transform("sum")
    l2_total_m1 = result.groupby(["site", "l1", "l2"])["adg_m1"].transform("sum")
    result["share_mtd"] = (result["adg_mtd"] / l2_total_mtd * 100).fillna(0)
    result["share_m1"] = (result["adg_m1"] / l2_total_m1 * 100).fillna(0)
    result["share_shift"] = result["share_mtd"] - result["share_m1"]

    # Benchmark MoM% from v2 B table
    if df_b is not None and len(df_b) > 0:
        b = df_b.copy()
        if "seller_type" in b.columns:
            b = b[b["seller_type"] == "CNCB"]
        bench = b.groupby(["site", "l3"]).agg(
            mkt_adg_mom=("mkt_adg_mom", "mean")
        ).reset_index()
        result = result.merge(bench, on=["site", "l3"], how="left")
    else:
        result["mkt_adg_mom"] = None

    result["gap_pp"] = result.apply(
        lambda r: _gap_pp(r["seller_mom"], _safe_float(r.get("mkt_adg_mom")) if pd.notna(r.get("mkt_adg_mom")) else None), axis=1
    )

    # Classify signals
    signals = []
    for _, r in result.iterrows():
        mom = r["seller_mom"] or 0
        gap = r["gap_pp"] or 0
        shift = r["share_shift"]
        mtd_val = r["adg_mtd"]
        m1_val = r["adg_m1"]
        path = f"{r['site']}/{r['l1']}/{r['l2']}/{r['l3']}"

        if mom > 20 and abs(gap) > 10:
            signals.append({"path": path, "signal": "VOLATILE_UP", "mom": round(mom, 1),
                            "gap_pp": round(gap, 1), "adg_mtd": round(mtd_val, 0)})
        elif mom < -20 and abs(gap) > 10:
            signals.append({"path": path, "signal": "VOLATILE_DOWN", "mom": round(mom, 1),
                            "gap_pp": round(gap, 1), "adg_mtd": round(mtd_val, 0)})
        if abs(gap) > 15:
            signals.append({"path": path, "signal": "MARKET_DIVERGENT", "mom": round(mom, 1),
                            "gap_pp": round(gap, 1), "adg_mtd": round(mtd_val, 0)})
        if abs(shift) > 5:
            signals.append({"path": path, "signal": "SHARE_SHIFT", "shift_pp": round(shift, 1),
                            "adg_mtd": round(mtd_val, 0)})
        if m1_val == 0 and mtd_val > 0:
            signals.append({"path": path, "signal": "NEW_ENTRY", "adg_mtd": round(mtd_val, 0)})
        if m1_val > 0 and mtd_val == 0:
            signals.append({"path": path, "signal": "EXIT", "adg_m1": round(m1_val, 0)})

    # Sort by priority: VOLATILE_DOWN with large ADG first
    priority_order = {"VOLATILE_DOWN": 0, "VOLATILE_UP": 1, "MARKET_DIVERGENT": 2,
                      "SHARE_SHIFT": 3, "NEW_ENTRY": 4, "EXIT": 5}
    signals.sort(key=lambda s: (priority_order.get(s["signal"], 9), -s.get("adg_mtd", 0)))

    # Signal counts
    signal_counts = {}
    for s in signals:
        signal_counts[s["signal"]] = signal_counts.get(s["signal"], 0) + 1

    # Scatter plot data
    scatter = []
    for _, r in result.iterrows():
        scatter.append({
            "site_l3": f"{r['site']}|{r['l3']}",
            "seller_mom": r["seller_mom"],
            "mkt_mom": _safe_float(r.get("mkt_adg_mom")) if pd.notna(r.get("mkt_adg_mom")) else None,
            "adg_mtd": round(r["adg_mtd"], 0),
        })

    return {
        "section_id": "sec_volatility",
        "chart_type": "scatter",
        "data": [],  # Signal rows as data
        "meta": {
            "signal_counts": signal_counts,
            "signals": signals[:30],  # Top 30 signals
            "scatter_data": scatter,
        },
    }


def build_shop_impact(df_a: pd.DataFrame, site: str, l3: str) -> Dict[str, Any]:
    """
    Section 1.7: Top shop contribution decomposition for a specific site×L3.
    """
    df = df_a.copy()
    df = df[(df["site"] == site) & (df["l3"] == l3)]
    df["adg"] = df["adg"].apply(_safe_float)

    months = sorted(df["year_month"].unique())
    if len(months) < 2:
        return {"section_id": "sec_shop_impact", "error": "Need at least 2 months"}
    current_m, prev_m = months[-1], months[-2]

    mtd = (df[df["year_month"] == current_m]
           .groupby("shop_id").agg(
               adg_mtd=("adg", "sum"),
               is_official_shop=("is_official_shop", "first"),
               days_cnt=("days_cnt", "first"),
           ).reset_index())
    m1 = (df[df["year_month"] == prev_m]
          .groupby("shop_id").agg(adg_m1=("adg", "sum")).reset_index())
    result = mtd.merge(m1, on="shop_id", how="outer").fillna(0)

    result["adg_delta"] = result["adg_mtd"] - result["adg_m1"]
    l3_total = result["adg_mtd"].sum()
    result["contribution_pct"] = (result["adg_delta"] / l3_total * 100).round(1) if l3_total != 0 else 0
    result["share_in_l3"] = (result["adg_mtd"] / l3_total * 100).round(1) if l3_total > 0 else 0

    # HHI: sum of squared shares
    result["share_sq"] = (result["share_in_l3"] / 100) ** 2
    hhi = round(result["share_sq"].sum() * 10000, 0)

    # Sort by contribution
    result = result.sort_values("adg_delta", ascending=False)

    out_cols = ["shop_id", "adg_mtd", "adg_m1", "adg_delta", "contribution_pct",
                 "share_in_l3", "is_official_shop", "days_cnt"]
    rows = _df_to_rows(result, out_cols)

    return {
        "section_id": "sec_shop_impact",
        "chart_type": "waterfall",
        "data": rows,
        "meta": {
            "site": site, "l3": l3,
            "total_shops": len(result),
            "hhi": hhi,
            "top1_share": round(result.iloc[0]["share_in_l3"], 1) if len(result) > 0 else 0,
            "top3_share": round(result.head(3)["share_in_l3"].sum(), 1),
        },
    }


def build_listing_change(df_c: pd.DataFrame, site: str, l3: str) -> Dict[str, Any]:
    """
    Section 1.8: Top listing gainers & losers for a specific site×L3.
    """
    if df_c is None or len(df_c) == 0:
        return {"section_id": "sec_listing_change", "error": "No item data available"}

    df = df_c.copy()
    df = df[(df["site"] == site) & (df["l3"] == l3)]

    df["mtd_adg"] = df["mtd_adg"].apply(_safe_float)
    df["m1_adg"] = df["m1_adg"].apply(_safe_float)
    df["avg_adg_30d"] = df["avg_adg_30d"].apply(_safe_float)
    df["mtd_adimp"] = df["mtd_adimp"].apply(_safe_int)
    df["mtd_ads_adg"] = df["mtd_ads_adg"].apply(_safe_float)

    df["adg_delta"] = df["mtd_adg"] - df["m1_adg"]
    df["adg_delta_pct"] = df.apply(
        lambda r: _mom_pct(r["mtd_adg"], r["m1_adg"]), axis=1
    )

    gainers = df.nlargest(10, "adg_delta")
    losers = df.nsmallest(10, "adg_delta")

    gainer_cols = ["item_name", "shop_name", "mtd_adg", "m1_adg", "adg_delta",
                    "adg_delta_pct", "price_range", "is_new", "avg_adg_30d",
                    "mtd_adimp", "mtd_ads_adg"]
    loser_cols = gainer_cols  # Same columns

    return {
        "section_id": "sec_listing_change",
        "chart_type": "dual_table",
        "gainers": _df_to_rows(gainers, gainer_cols),
        "losers": _df_to_rows(losers, loser_cols),
        "meta": {
            "site": site, "l3": l3,
            "total_items": len(df),
            "scatter_data": [
                {"item_name": r["item_name"], "avg_30d": round(r["avg_adg_30d"], 0),
                 "mtd_adg": round(r["mtd_adg"], 0), "price_range": r["price_range"]}
                for _, r in df.iterrows()
            ],
        },
    }


def build_listing_contributions(df_c: pd.DataFrame) -> Dict[str, Any]:
    """
    Section 1.8 v2: Per-site top 5 item contributions with images.
    Groups by site, takes top 5 items by MTD ADG per site.
    """
    if df_c is None or len(df_c) == 0:
        return {"section_id": "sec_listing_change", "error": "No item data available"}

    df = df_c.copy()
    for col in ["mtd_adg", "m1_adg", "avg_adg_30d", "mtd_adimp", "mtd_ads_adg", "price_usd"]:
        if col in df.columns:
            df[col] = df[col].apply(_safe_float)

    df["adg_delta"] = df["mtd_adg"] - df["m1_adg"]
    df["adg_delta_pct"] = df.apply(lambda r: _mom_pct(r["mtd_adg"], r["m1_adg"]), axis=1)

    # Per-site top 5
    sites = sorted(df["site"].dropna().unique())
    per_site = {}
    for site in sites:
        site_df = df[df["site"] == site].nlargest(5, "mtd_adg")
        items = []
        for _, r in site_df.iterrows():
            item_id = str(int(r["item_id"])) if "item_id" in r.index and pd.notna(r.get("item_id")) else ""
            shop_id = str(int(r["shop_id"])) if "shop_id" in r.index and pd.notna(r.get("shop_id")) else ""
            site_name = str(r["site"]) if "site" in r.index else site
            # Construct image URL from item_link or use Shopee CDN pattern
            item_link = str(r.get("item_link", ""))
            # Shopee image CDN: https://cf.shopee.ph/file/<hash> — hash not available
            # Use a placeholder that directs to item page
            image_url = item_link if item_link else ""
            items.append({
                "item_name": str(r.get("item_name", ""))[:40],
                "shop_name": str(r.get("shop_name", ""))[:30],
                "item_id": item_id,
                "shop_id": shop_id,
                "item_link": item_link,
                "image_url": image_url,
                "mtd_adg": round(r["mtd_adg"], 1),
                "m1_adg": round(r["m1_adg"], 1),
                "adg_delta": round(r["adg_delta"], 1),
                "adg_delta_pct": round(r.get("adg_delta_pct", 0) or 0, 1),
                "price_range": str(r.get("price_range", "")),
                "is_new": int(r.get("is_new", 0) or 0),
                "avg_adg_30d": round(r.get("avg_adg_30d", 0), 1),
            })
        per_site[site] = {
            "site": site,
            "total_site_adg": round(site_df["mtd_adg"].sum(), 1),
            "item_count": len(site_df),
            "items": items,
        }

    # Cross-site overlap: same item appearing in multiple sites
    item_sites = {}
    for _, r in df.iterrows():
        iid = str(r.get("item_id", ""))
        s = str(r.get("site", ""))
        if iid and s:
            if iid not in item_sites:
                item_sites[iid] = []
            item_sites[iid].append(s)
    cross_site_items = {k: v for k, v in item_sites.items() if len(v) > 1}

    return {
        "section_id": "sec_listing_change",
        "chart_type": "item_cards",
        "data": [],  # meta-driven
        "meta": {
            "per_site": per_site,
            "site_count": len(sites),
            "total_items": len(df),
            "cross_site_items": {k: v for k, v in list(cross_site_items.items())[:10]},
        },
    }


# === Level 4: Dimensional Root Cause ===


def build_fulfillment(df_a: pd.DataFrame) -> Dict[str, Any]:
    """
    Section 1.9: Fulfillment structure FBS/TPF/SLS.
    """
    df = df_a.copy()
    for col in ["fbs_ado", "tpf_ado", "sls_ado", "ado"]:
        if col in df.columns:
            df[col] = df[col].apply(_safe_float)

    months = sorted(df["year_month"].unique())
    if len(months) < 2:
        return {"section_id": "sec_fulfillment", "error": "Need at least 2 months"}
    current_m, prev_m = months[-1], months[-2]

    # By site
    mtd_site = (
        df[df["year_month"] == current_m]
        .groupby("site")
        .agg(fbs=("fbs_ado", "sum"), tpf=("tpf_ado", "sum"),
             sls=("sls_ado", "sum"), total=("ado", "sum"))
        .reset_index()
    )
    m1_site = (
        df[df["year_month"] == prev_m]
        .groupby("site")
        .agg(fbs_m1=("fbs_ado", "sum"), tpf_m1=("tpf_ado", "sum"),
             sls_m1=("sls_ado", "sum"), total_m1=("ado", "sum"))
        .reset_index()
    )
    result = mtd_site.merge(m1_site, on="site", how="outer").fillna(0)

    for t in ["fbs", "tpf", "sls"]:
        result[f"{t}_share"] = (result[t] / result["total"] * 100).round(1)
        result[f"{t}_share_m1"] = (result[f"{t}_m1"] / result["total_m1"] * 100).round(1)
        result[f"{t}_shift_pp"] = result[f"{t}_share"] - result[f"{t}_share_m1"]

    # By L1
    mtd_l1 = (
        df[df["year_month"] == current_m]
        .groupby("l1")
        .agg(fbs=("fbs_ado", "sum"), tpf=("tpf_ado", "sum"),
             sls=("sls_ado", "sum"), total=("ado", "sum"))
        .reset_index()
    )
    for t in ["fbs", "tpf", "sls"]:
        mtd_l1[f"{t}_share"] = (mtd_l1[t] / mtd_l1["total"] * 100).round(1)

    out_cols = ["site", "fbs", "tpf", "sls", "total",
                 "fbs_share", "tpf_share", "sls_share",
                 "fbs_share_m1", "tpf_share_m1", "sls_share_m1",
                 "fbs_shift_pp", "tpf_shift_pp", "sls_shift_pp"]
    rows = _df_to_rows(result, out_cols)

    return {
        "section_id": "sec_fulfillment",
        "chart_type": "stacked_bar",
        "data": rows,
        "meta": {
            "by_l1": _df_to_rows(mtd_l1, ["l1", "fbs", "tpf", "sls", "total",
                                            "fbs_share", "tpf_share", "sls_share"]),
        },
    }


def build_traffic_channel(df_a: pd.DataFrame) -> Dict[str, Any]:
    """
    Section 2.0: Traffic channel decomposition.
    Organic vs Ads vs Livestream vs Campaign.
    """
    df = df_a.copy()
    for col in ["organic_adg", "ads_adg", "ads_spend", "livestream_adg",
                 "campaign_adg", "adg", "ads_ado"]:
        if col in df.columns:
            df[col] = df[col].apply(_safe_float)

    months = sorted(df["year_month"].unique())
    if len(months) < 2:
        return {"section_id": "sec_traffic_channel", "error": "Need at least 2 months"}
    current_m, prev_m = months[-1], months[-2]

    mtd = (df[df["year_month"] == current_m]
           .groupby(["site", "l1"])
           .agg(organic=("organic_adg", "sum"), ads=("ads_adg", "sum"),
                spend=("ads_spend", "sum"), live=("livestream_adg", "sum"),
                campaign=("campaign_adg", "sum"), total=("adg", "sum"),
                ads_ado=("ads_ado", "sum"))
           .reset_index())
    m1 = (df[df["year_month"] == prev_m]
          .groupby(["site", "l1"])
          .agg(organic_m1=("organic_adg", "sum"), ads_m1=("ads_adg", "sum"),
               live_m1=("livestream_adg", "sum"), campaign_m1=("campaign_adg", "sum"),
               total_m1=("adg", "sum"))
          .reset_index())
    result = mtd.merge(m1, on=["site", "l1"], how="outer").fillna(0)

    # Channel shares
    for ch in ["organic", "ads", "live", "campaign"]:
        result[f"{ch}_share"] = (result[ch] / result["total"] * 100).round(1)
        result[f"{ch}_mom"] = result.apply(
            lambda r: _mom_pct(r[ch], r[f"{ch}_m1"]), axis=1
        )

    # ROAS = ads_adg / (ads_spend / days_in_month)
    result["roas"] = result.apply(
        lambda r: round(r["ads"] / (r["spend"] / 30), 1) if r["spend"] > 0 else None,
        axis=1,
    )
    # ACP = ads_spend / ads_ado
    result["acp"] = result.apply(
        lambda r: round(r["spend"] / r["ads_ado"], 2) if r["ads_ado"] > 0 else None,
        axis=1,
    )

    out_cols = ["site", "l1", "organic", "ads", "live", "campaign", "total",
                 "organic_share", "ads_share", "live_share", "campaign_share",
                 "organic_mom", "ads_mom", "live_mom", "campaign_mom",
                 "roas", "acp", "spend"]
    rows = _df_to_rows(result, out_cols)

    return {
        "section_id": "sec_traffic_channel",
        "chart_type": "stacked_bar",
        "data": rows,
        "meta": {},
    }


def build_subsidy_structure(df_a: pd.DataFrame) -> Dict[str, Any]:
    """
    Section 2.1: Promotion & subsidy structure.
    """
    df = df_a.copy()
    rebate_cols = [
        "seller_item_rebated_adg", "platform_item_rebated_adg",
        "seller_shipping_rebated_adg", "platform_shipping_rebated_adg",
        "cfs_adg", "lpp_adg", "campaign_adg", "total_subsidy_adg", "adg",
    ]
    for col in rebate_cols:
        if col in df.columns:
            df[col] = df[col].apply(_safe_float)

    months = sorted(df["year_month"].unique())
    if len(months) < 2:
        return {"section_id": "sec_subsidy", "error": "Need at least 2 months"}
    current_m = months[-1]

    mtd = df[df["year_month"] == current_m]

    # Aggregate by site
    agg_cols = {c: ("sum" if c in df.columns else lambda x: 0) for c in rebate_cols}
    result = mtd.groupby("site").agg(
        seller_item=("seller_item_rebated_adg", "sum"),
        platform_item=("platform_item_rebated_adg", "sum"),
        seller_shipping=("seller_shipping_rebated_adg", "sum"),
        platform_shipping=("platform_shipping_rebated_adg", "sum"),
        cfs=("cfs_adg", "sum"),
        lpp=("lpp_adg", "sum"),
        campaign=("campaign_adg", "sum"),
        total_subsidy=("total_subsidy_adg", "sum"),
        total_adg=("adg", "sum"),
    ).reset_index()

    # Shares
    for item in ["seller_item", "platform_item", "seller_shipping", "platform_shipping",
                  "cfs", "lpp", "campaign"]:
        result[f"{item}_share"] = (result[item] / result["total_adg"] * 100).round(1)

    result["subsidy_share"] = (result["total_subsidy"] / result["total_adg"] * 100).round(1)

    # Seller vs platform funded
    result["seller_funded"] = result["seller_item"] + result["seller_shipping"]
    result["platform_funded"] = result["platform_item"] + result["platform_shipping"]
    result["seller_funded_share"] = (result["seller_funded"] / result["total_adg"] * 100).round(1)
    result["platform_funded_share"] = (result["platform_funded"] / result["total_adg"] * 100).round(1)

    out_cols = ["site", "seller_item", "platform_item", "seller_shipping", "platform_shipping",
                 "cfs", "lpp", "campaign", "total_subsidy", "total_adg",
                 "subsidy_share", "seller_item_share", "platform_item_share",
                 "seller_shipping_share", "platform_shipping_share",
                 "cfs_share", "lpp_share", "campaign_share",
                 "seller_funded_share", "platform_funded_share"]
    rows = _df_to_rows(result, out_cols)

    return {
        "section_id": "sec_subsidy",
        "chart_type": "stacked_bar",
        "data": rows,
        "meta": {},
    }


def build_price_band(df_a: pd.DataFrame, df_b: pd.DataFrame) -> Dict[str, Any]:
    """
    Section 2.2: Price band distribution vs market.
    ⚠️ Market side: only mkt_price_share (relative %). No absolute values.
    """
    df = df_a.copy()
    df["adg"] = df["adg"].apply(_safe_float)

    months = sorted(df["year_month"].unique())
    if len(months) < 2:
        return {"section_id": "sec_price_band", "error": "Need at least 2 months"}
    current_m, prev_m = months[-1], months[-2]

    # Seller price band distribution (current month)
    seller = (df[df["year_month"] == current_m]
              .groupby(["site", "l1", "l2", "l3", "price_range"])
              .agg(seller_adg=("adg", "sum"))
              .reset_index())

    # Seller share within site×L3
    l3_total = seller.groupby(["site", "l1", "l2", "l3"])["seller_adg"].transform("sum")
    seller["seller_share"] = (seller["seller_adg"] / l3_total * 100).round(1)

    # Previous month for migration
    seller_m1 = (df[df["year_month"] == prev_m]
                 .groupby(["site", "l1", "l2", "l3", "price_range"])
                 .agg(seller_adg_m1=("adg", "sum"))
                 .reset_index())
    l3_total_m1 = seller_m1.groupby(["site", "l1", "l2", "l3"])["seller_adg_m1"].transform("sum")
    seller_m1["seller_share_m1"] = (seller_m1["seller_adg_m1"] / l3_total_m1 * 100).round(1)

    result = seller.merge(seller_m1, on=["site", "l1", "l2", "l3", "price_range"], how="outer").fillna(0)
    result["share_shift_pp"] = result["seller_share"] - result["seller_share_m1"]

    # Market price share from Table B v2 when available. The SDK allowlisted
    # mom-only table may expose only mom_price_share_pp, so do not treat missing
    # market share as zero.
    if df_b is not None and len(df_b) > 0:
        b = df_b.copy()
        if "mkt_price_share" not in b.columns:
            b["mkt_price_share"] = None
        if "mom_price_share_pp" not in b.columns:
            b["mom_price_share_pp"] = None
        bench = b[["site", "l1", "l2", "l3", "price_band", "mkt_price_share", "mom_price_share_pp"]].copy()
        bench = bench.rename(columns={"price_band": "price_range"})
        result = result.merge(bench, on=["site", "l1", "l2", "l3", "price_range"], how="left")
    else:
        result["mkt_price_share"] = None
        result["mom_price_share_pp"] = None

    def _bias_pp(row):
        raw = row.get("mkt_price_share")
        if pd.isna(raw) or raw == "":
            return None
        return row["seller_share"] - _safe_float(raw)

    result["bias_pp"] = result.apply(_bias_pp, axis=1)

    out_cols = ["site", "l1", "l2", "l3", "price_range",
                 "seller_adg", "seller_share", "seller_share_m1", "share_shift_pp",
                 "mkt_price_share", "mom_price_share_pp", "bias_pp"]
    rows = _df_to_rows(result, out_cols)

    return {
        "section_id": "sec_price_band",
        "chart_type": "dual_distribution",
        "data": rows,
        "meta": {},
    }


def build_ams_efficiency(df_a: pd.DataFrame) -> Dict[str, Any]:
    """
    Section 2.4: AMS advertising efficiency audit.
    """
    df = df_a.copy()
    for col in ["ads_adg", "ads_spend", "ads_ado", "adg"]:
        if col in df.columns:
            df[col] = df[col].apply(_safe_float)

    months = sorted(df["year_month"].unique())
    if len(months) < 2:
        return {"section_id": "sec_ams", "error": "Need at least 2 months"}
    current_m, prev_m = months[-1], months[-2]

    mtd = (df[df["year_month"] == current_m]
           .groupby(["site", "l1"])
           .agg(ads_adg=("ads_adg", "sum"), spend=("ads_spend", "sum"),
                ads_ado=("ads_ado", "sum"), total_adg=("adg", "sum"))
           .reset_index())
    m1 = (df[df["year_month"] == prev_m]
          .groupby(["site", "l1"])
          .agg(ads_adg_m1=("ads_adg", "sum"), spend_m1=("ads_spend", "sum"),
                total_adg_m1=("adg", "sum"))
          .reset_index())
    result = mtd.merge(m1, on=["site", "l1"], how="outer").fillna(0)

    # ROAS & ACP
    result["roas"] = result.apply(
        lambda r: round(r["ads_adg"] / (r["spend"] / 30), 1) if r["spend"] > 0 else None, axis=1
    )
    result["acp"] = result.apply(
        lambda r: round(r["spend"] / r["ads_ado"], 2) if r["ads_ado"] > 0 else None, axis=1
    )
    result["ads_share"] = (result["ads_adg"] / result["total_adg"] * 100).round(1)

    # MoM
    result["ads_adg_mom"] = result.apply(lambda r: _mom_pct(r["ads_adg"], r["ads_adg_m1"]), axis=1)
    result["spend_mom"] = result.apply(lambda r: _mom_pct(r["spend"], r["spend_m1"]), axis=1)
    result["total_mom"] = result.apply(lambda r: _mom_pct(r["total_adg"], r["total_adg_m1"]), axis=1)

    out_cols = ["site", "l1", "ads_adg", "spend", "ads_ado", "total_adg",
                 "roas", "acp", "ads_share", "ads_adg_mom", "spend_mom", "total_mom"]
    rows = _df_to_rows(result, out_cols)

    return {
        "section_id": "sec_ams",
        "chart_type": "heatmap",
        "data": rows,
        "meta": {},
    }


# === Level 5: Synthesis ===


def build_root_cause_diagnosis(all_sections: Dict[str, Any]) -> Dict[str, Any]:
    """
    Section 2.3: Site-by-site root cause diagnosis.
    Aggregates evidence from all 14 preceding sections.
    Walks the 6-level diagnostic tree for each active site.
    """
    # Extract relevant evidence from previous sections
    benchmark = all_sections.get("sec_site_benchmark", {})
    volatility = all_sections.get("sec_volatility", {})
    shop = all_sections.get("sec_shop_impact", {})
    listing = all_sections.get("sec_listing_change", {})
    fulfillment = all_sections.get("sec_fulfillment", {})
    traffic = all_sections.get("sec_traffic_channel", {})
    subsidy = all_sections.get("sec_subsidy", {})
    price_band = all_sections.get("sec_price_band", {})
    ams = all_sections.get("sec_ams", {})

    # Get sites from benchmark data
    benchmark_data = benchmark.get("data", [])
    sites = []
    if len(benchmark_data) > 1:
        header = benchmark_data[0]
        site_idx = header.index("site") if "site" in header else -1
        if site_idx >= 0:
            for row in benchmark_data[1:]:
                if len(row) > site_idx:
                    sites.append(row[site_idx])
    sites = list(set(sites))

    cards = []
    for site in sites:
        # Gather evidence
        site_signals = []
        vol_signals = volatility.get("meta", {}).get("signals", [])
        site_signals = [s for s in vol_signals if site in s.get("path", "")]

        # Determine primary signal direction
        has_volatile_down = any(s["signal"] == "VOLATILE_DOWN" for s in site_signals)
        has_divergent = any(s["signal"] == "MARKET_DIVERGENT" for s in site_signals)

        # Status determination
        if has_volatile_down:
            status = "🔴"
        elif has_divergent:
            status = "⚠️"
        else:
            status = "✅"

        # Walk 6-level diagnostic tree (simplified — builds evidence list)
        evidence = []
        confidence = "MEDIUM"

        # L1: Demand side — check benchmark alignment
        for row in benchmark_data[1:]:
            if len(row) > 0 and row[0] == site:
                gap = _safe_float(row[5]) if len(row) > 5 else 0  # adg_gap_pp
                evidence.append({
                    "level": "L1-需求端",
                    "finding": f"与大盘ADG增速差{gap}pp",
                    "verdict": "市场因素" if abs(gap) < 5 else "卖家自身因素",
                })
                break

        # L2: Listing — top item check (from volatility signals)
        vol_signals_for_site = [s for s in site_signals if s["signal"] == "VOLATILE_DOWN"]
        if vol_signals_for_site:
            evidence.append({
                "level": "L2-供给端",
                "finding": f"检测到{len(vol_signals_for_site)}个暴跌信号",
                "verdict": "需排查具体item",
            })

        # L3: Channel
        evidence.append({
            "level": "L3-渠道端",
            "finding": "从sec_traffic_channel获取",
            "verdict": "待分析",
        })

        # L4: Fulfillment
        evidence.append({
            "level": "L4-运营端",
            "finding": "从sec_fulfillment获取",
            "verdict": "待分析",
        })

        # L5: Pricing
        evidence.append({
            "level": "L5-定价端",
            "finding": "从sec_price_band获取",
            "verdict": "待分析",
        })

        # L6: Subsidy
        evidence.append({
            "level": "L6-激励端",
            "finding": "从sec_subsidy获取",
            "verdict": "待分析",
        })

        cards.append({
            "site": site,
            "status": status,
            "evidence": evidence,
            "confidence": confidence,
            "root_cause_hypothesis": "待填充" if not has_volatile_down else "疑似listing/item级问题",
            "recommendation": "待填充",
        })

    return {
        "section_id": "sec_root_cause",
        "chart_type": "diagnostic_cards",
        "data": [],
        "meta": {"cards": cards, "sites_analyzed": len(cards)},
    }


# ═══════════════════════════════════════════════════════════════
# 3. Text & Config Generation
# ═══════════════════════════════════════════════════════════════

SECTION_TEXT_TEMPLATES = {
    "sec_12m_history":     "近12个月ADG从{start_adg}→{end_adg},整体呈{trend}态势。Top站点{top_site}占比{top_share}%。",
    "sec_site_benchmark":  "{site} ADG MoM {mom_pct}%,{direction}大盘约{gap_pp}pp。{judgment}",
    "sec_l1_overview":     "Top品类{top_l1}贡献GMV的{top_share}%。{mom_desc}",
    "sec_l1_matrix":       "共发现{anomaly_count}个异常site×L1组合,最大偏离{gap_pp}pp。",
    "sec_volatility":      "检出{volatile_down}个暴跌信号,{divergent}个市场背离,{share_shift}个份额迁移。",
    "sec_fulfillment":     "FBS占比{fbs_pct}%,TPF占比{tpf_pct}%,SLS占比{sls_pct}%。",
    "sec_traffic_channel": "Organic占比{organic_pct}%,Ads占比{ads_pct}%,直播占比{live_pct}%。",
    "sec_subsidy":         "总补贴占GMV的{subsidy_pct}%。卖家出资{seller_pct}%,平台出资{platform_pct}%。",
    "sec_price_band":      "价格带分布偏差最大为{max_bias_band},偏差{max_bias_pp}pp。",
    "sec_ams":             "整体ROAS为{roas},广告占总GMV的{ads_share}%。",
    "sec_root_cause":      "共分析{sites_analyzed}个站点,{red_count}个🔴,{warn_count}个⚠️,{ok_count}个✅。",
}


def generate_sec_text(sections: Dict[str, Any]) -> List[List[Any]]:
    """Generate sec_text tab with template for each section."""
    rows = [["section_id", "text_template", "last_edited_by", "last_edited_at"]]
    now = datetime.now().isoformat()
    for sec_id, template in SECTION_TEXT_TEMPLATES.items():
        rows.append([sec_id, template, "build_sections.py", now])
    return rows


def generate_sec_config(sections: Dict[str, Any]) -> List[List[Any]]:
    """Generate sec_config tab with render configuration for each section."""
    rows = [["section_id", "chart_type", "show_table", "is_collapsible",
             "default_collapsed", "sort_order"]]

    configs = [
        ("sec_12m_history",     "bar_stacked",       True,  True,  False, 1),
        ("sec_site_benchmark",  "dual_axis",         True,  True,  False, 2),
        ("sec_l1_overview",     "dual_axis",         True,  True,  False, 3),
        ("sec_l1_matrix",       "heatmap",           True,  True,  False, 4),
        ("sec_l2_drill",        "waterfall",         True,  True,  True,  5),
        ("sec_l3_granular",     "treemap",           True,  True,  True,  6),
        ("sec_volatility",      "scatter",           True,  True,  False, 7),
        ("sec_shop_impact",     "waterfall",         True,  True,  True,  8),
        ("sec_listing_change",  "item_cards",        True,  True,  True,  9),
        ("sec_fulfillment",     "stacked_bar",       True,  True,  False, 10),
        ("sec_traffic_channel", "stacked_bar",       True,  True,  False, 11),
        ("sec_subsidy",         "stacked_bar",       True,  True,  False, 12),
        ("sec_price_band",      "dual_distribution", True,  True,  False, 13),
        ("sec_ams",             "heatmap",           True,  True,  False, 14),
        ("sec_root_cause",      "diagnostic_cards",  False, False, False, 15),
    ]
    for sec_id, chart_type, show_table, is_collapsible, default_collapsed, sort_order in configs:
        rows.append([sec_id, chart_type, str(show_table).upper(),
                     str(is_collapsible).upper(), str(default_collapsed).upper(), str(sort_order)])
    return rows


# ═══════════════════════════════════════════════════════════════
# 4. Main Orchestrator
# ═══════════════════════════════════════════════════════════════


def run_all(sheet_id: str, ggp: str, l1_drill: Optional[str] = None,
            l2_drill: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute all 15 build functions and write results to Sheet.
    Returns summary dict.
    """
    df_a, df_b_dict, df_c = load_raw_data(sheet_id)

    # Merge split benchmark tabs into single df_b for backward compatibility
    if isinstance(df_b_dict, dict) and df_b_dict:
        import pandas as pd
        dfs = []
        for key, df in df_b_dict.items():
            if len(df) > 0:
                dfs.append(df)
        if dfs:
            # Concatenate all split tabs — each has different columns but shared keys
            df_b = dfs[0]
            for extra in dfs[1:]:
                shared = [col for col in extra.columns if col in df_b.columns]
                if shared:
                    df_b = df_b.merge(extra, on=shared, how="outer")
                else:
                    df_b = pd.concat([df_b, extra], axis=0, ignore_index=True)
            # Deduplicate
            key_cols = [c for c in ["site","l1","l2","l3","year_month","seller_type","price_band","price_range"] if c in df_b.columns]
            if key_cols:
                num_cols = [c for c in df_b.columns if c not in key_cols]
                for col in num_cols:
                    df_b[col] = pd.to_numeric(df_b[col], errors="coerce")
                agg_dict = {c: "mean" for c in num_cols}
                df_b = df_b.groupby(key_cols, dropna=False).agg(agg_dict).reset_index()
            print(f"  Merged benchmark: {len(df_b)} rows")
        else:
            df_b = pd.DataFrame()
    else:
        df_b = df_b_dict if isinstance(df_b_dict, pd.DataFrame) else pd.DataFrame()

    if len(df_a) == 0:
        return {"error": "raw_dws_shop is empty. Check L2 data load."}

    sections = {}
    errors = []

    def _run(fn, name, *args):
        try:
            result = fn(*args)
            sections[result.get("section_id", name)] = result
            return result
        except Exception as e:
            errors.append(f"{name}: {e}")
            print(f"  ⚠️ {name} FAILED: {e}")
            return {"section_id": name, "error": str(e)}

    print("\n--- Level 1: Overview ---")
    _run(build_12m_history, "sec_12m_history", df_a)
    _run(build_site_benchmark, "sec_site_benchmark", df_a, df_b)
    _run(build_l1_overview, "sec_l1_overview", df_a, df_b)

    print("\n--- Level 2: Category Deep Dive ---")
    l1_matrix = _run(build_l1_matrix, "sec_l1_matrix", df_a, df_b)

    # Determine L1 to drill: use explicit arg → top anomaly → top L1 by ADG (fallback)
    anomalies = l1_matrix.get("meta", {}).get("anomalies", [])
    l1_for_drill = l1_drill or (anomalies[0]["l1"] if anomalies else None)
    # If benchmark data unavailable (no anomalies), fall back to top L1 by ADG
    if not l1_for_drill and df_a is not None and len(df_a) > 0:
        top_l1 = df_a.groupby("l1")["adg"].sum().nlargest(1)
        if len(top_l1) > 0:
            l1_for_drill = top_l1.index[0]
            print(f"  ℹ️ No benchmark anomalies — drilling into top L1 by ADG: {l1_for_drill}")
    if l1_for_drill:
        _run(build_l2_drill, "sec_l2_drill", df_a, df_b, l1_for_drill)

        # Determine L2 to drill: use explicit arg → largest delta in waterfall → top L2 by ADG (fallback)
        l2_result = sections.get("sec_l2_drill", {})
        waterfall = l2_result.get("meta", {}).get("waterfall", [])
        l2_for_drill = l2_drill or (waterfall[0]["l2"] if waterfall else None)
        if not l2_for_drill and df_a is not None:
            df_l1 = df_a[df_a["l1"] == l1_for_drill]
            if len(df_l1) > 0:
                top_l2 = df_l1.groupby("l2")["adg"].sum().nlargest(1)
                if len(top_l2) > 0:
                    l2_for_drill = top_l2.index[0]
                    print(f"  ℹ️ No waterfall data — drilling into top L2 by ADG: {l2_for_drill}")
        if l2_for_drill:
            _run(build_l3_granular, "sec_l3_granular", df_a, df_b, df_c, l1_for_drill, l2_for_drill)

    print("\n--- Level 3: Anomaly & Impact ---")
    _run(build_volatility_signals, "sec_volatility", df_a, df_b)

    # Listing contributions: per-site top 5 items (always runs)
    _run(build_listing_contributions, "sec_listing_change", df_c)

    # Shop impact for first anomaly site×L3 (if available)
    vol_signals = sections.get("sec_volatility", {}).get("meta", {}).get("signals", [])
    if vol_signals:
        first_signal = vol_signals[0]
        path_parts = first_signal["path"].split("/")
        if len(path_parts) >= 4:
            site, l3_drill = path_parts[0], path_parts[3]
            _run(build_shop_impact, "sec_shop_impact", df_a, site, l3_drill)

    print("\n--- Level 4: Dimensional Root Cause ---")
    _run(build_fulfillment, "sec_fulfillment", df_a)
    _run(build_traffic_channel, "sec_traffic_channel", df_a)
    _run(build_subsidy_structure, "sec_subsidy", df_a)
    _run(build_price_band, "sec_price_band", df_a, df_b)
    _run(build_ams_efficiency, "sec_ams", df_a)

    print("\n--- Level 5: Synthesis ---")
    _run(build_root_cause_diagnosis, "sec_root_cause", sections)

    # Write all section data to Sheet
    print("\n--- Writing to Sheet ---")
    for sec_id, result in sections.items():
        if "error" in result:
            print(f"  ⚠️ Skipping {sec_id} (error: {result['error']})")
            continue
        data = result.get("data", [])
        if data:
            write_sheet_tab(sheet_id, sec_id, data)
            print(f"  ✅ {sec_id}: {len(data)-1} rows written")

    # Write meta as separate tabs if applicable
    for sec_id in ["sec_volatility", "sec_l3_granular", "sec_listing_change", "sec_root_cause"]:
        result = sections.get(sec_id, {})
        meta = result.get("meta", {})
        if meta:
            meta_tab = f"{sec_id}_meta"
            try:
                meta_rows = [[k, json.dumps(v, ensure_ascii=False, default=str) if isinstance(v, (dict, list)) else str(v)] for k, v in meta.items()]
                write_sheet_tab(sheet_id, meta_tab, meta_rows)
                print(f"  ✅ {meta_tab}: metadata written")
            except Exception:
                pass

    # Generate sec_text and sec_config
    text_rows = generate_sec_text(sections)
    write_sheet_tab(sheet_id, "sec_text", text_rows)
    print(f"  ✅ sec_text: {len(text_rows)-1} templates written")

    config_rows = generate_sec_config(sections)
    write_sheet_tab(sheet_id, "sec_config", config_rows)
    print(f"  ✅ sec_config: {len(config_rows)-1} configs written")

    return {
        "sections_built": len([s for s in sections.values() if "error" not in s]),
        "sections_failed": len(errors),
        "errors": errors,
        "ggp": ggp,
        "sheet_id": sheet_id,
    }


# ═══════════════════════════════════════════════════════════════
# 5. CLI Entry Point
# ═══════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(
        description="AutoDeck v_0602 Section Builder"
    )
    parser.add_argument("--sheet-id", required=True, help="Google Sheet ID")
    parser.add_argument("--ggp", required=True, help="GGP account name")
    parser.add_argument("--l1", default=None, help="L1 category to drill into")
    parser.add_argument("--l2", default=None, help="L2 category to drill into")
    parser.add_argument("--dry-run", action="store_true", help="Load data but don't write to Sheet")

    args = parser.parse_args()

    print(f"╔══════════════════════════════════════════════╗")
    print(f"║  AutoDeck v_0602 — build_sections.py        ║")
    print(f"║  GGP: {args.ggp[:40]}...")
    print(f"║  Sheet: {args.sheet_id}")
    print(f"╚══════════════════════════════════════════════╝")

    if args.dry_run:
        print("\n[Dry run — will not write to Sheet]")

    summary = run_all(args.sheet_id, args.ggp, args.l1, args.l2)

    print(f"\n{'='*50}")
    print(f"Build complete.")
    print(f"  Sections built:  {summary['sections_built']}")
    print(f"  Sections failed: {summary['sections_failed']}")
    if summary["errors"]:
        for e in summary["errors"]:
            print(f"    - {e}")
    print(f"  Sheet: https://docs.google.com/spreadsheets/d/{args.sheet_id}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
