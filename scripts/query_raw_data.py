#!/usr/bin/env python3
"""Pull the three fixed AutoDeck raw datasets through DataService SDK."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from dataservice.sdk import Client
from dataservice.query_configuration import QueryConfiguration


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_BRIDGE = os.environ.get("AUTODECK_BRIDGE", "")
DEFAULT_TECH_REFERENCE = os.environ.get("AUTODECK_TECH_REFERENCE", "")
# The SDK allowlist exposes the mom-only rpt table, not the legacy benchmark_mi
# source. This SELECT normalizes the rpt table back to the section-builder column
# contract without exposing absolute market values.
BENCHMARK_MOM_SQL = SCRIPT_DIR / "sql" / "taskB_benchmark_mom_select_v2.sql"

DEFAULT_API_NAME = "cncbbi_general.autodeck__rpt_table_list"
DEFAULT_API_VERSION = "n4rfgou3k5r5mhu7"
DEFAULT_BASE_URL = "https://open-api.datasuite.shopee.io"
DEFAULT_QUEUE = "cncbbi-scheduled"
DEFAULT_SYSTEM_NAME = "autodeck_skill"
DEFAULT_END_USER = os.environ.get("AUTODECK_DATASERVICE_END_USER", "")


@dataclass
class DataServiceConfig:
    app_key: str
    app_secret: str
    api_name: str = DEFAULT_API_NAME
    api_version: str = DEFAULT_API_VERSION
    base_url: str = DEFAULT_BASE_URL
    queue: str = DEFAULT_QUEUE
    system_name: str = DEFAULT_SYSTEM_NAME
    end_user: str = DEFAULT_END_USER
    enable_cache: bool = True


def month_start(month: str) -> date:
    y, m = [int(x) for x in month.split("-", 1)]
    return date(y, m, 1)


def add_months(d: date, months: int) -> date:
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    return date(y, m, 1)


def month_list(month: str, months_back: int) -> List[str]:
    start = month_start(month)
    return [add_months(start, -i).isoformat() for i in range(months_back + 1)]


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def date_in(values: Iterable[str]) -> str:
    return ", ".join(f"DATE '{v}'" for v in values)


def build_queries(ggp: str, month: str, months_back: int = 12) -> Dict[str, str]:
    months = month_list(month, months_back)
    current_prev = month_list(month, 1)
    benchmark_sql = Path(BENCHMARK_MOM_SQL).read_text(encoding="utf-8").strip().rstrip(";")

    # Seller's sites subquery — used to filter benchmark to relevant sites only
    seller_sites_subquery = f"""(
  SELECT DISTINCT site
  FROM cncbbi_general.autodeck__dws_shop_rpt_mi
  WHERE ggp_account_name = {sql_quote(ggp)}
    AND year_month IN ({date_in(current_prev)})
)"""

    return {
        # ── Table A: shop data (already filtered by GGP, typically <2000 rows) ──
        "raw_dws_shop": f"""
SELECT *
FROM cncbbi_general.autodeck__dws_shop_rpt_mi
WHERE ggp_account_name = {sql_quote(ggp)}
  AND year_month IN ({date_in(months)})
""".strip(),

        # ── Benchmark: site-level MoM (Section 1.1) — ~10 rows ──
        "raw_benchmark_site": f"""
SELECT site, year_month,
  AVG(mkt_adg_mom) AS mkt_adg_mom,
  AVG(mkt_ado_mom) AS mkt_ado_mom,
  AVG(mkt_mall_adg_mom) AS mkt_mall_adg_mom,
  AVG(mkt_cb_adg_mom) AS mkt_cb_adg_mom,
  AVG(mkt_local_adg_mom) AS mkt_local_adg_mom
FROM (
{benchmark_sql}
) t
WHERE site IN {seller_sites_subquery}
  AND year_month IN ({date_in(months)})
  AND seller_type = 'CNCB'
GROUP BY site, year_month
""".strip(),

        # ── Benchmark: site×L1 MoM (Section 1.2, 1.3) — ~200 rows ──
        "raw_benchmark_l1": f"""
SELECT site, l1, year_month,
  AVG(mkt_adg_mom) AS mkt_adg_mom,
  AVG(mkt_ado_mom) AS mkt_ado_mom
FROM (
{benchmark_sql}
) t
WHERE site IN {seller_sites_subquery}
  AND year_month IN ({date_in(current_prev)})
  AND seller_type = 'CNCB'
GROUP BY site, l1, year_month
""".strip(),

        # ── Benchmark: site×L1×L2 MoM (Section 1.4) — filtered by seller's L1 ──
        "raw_benchmark_l2": f"""
SELECT site, l1, l2, year_month,
  AVG(mkt_adg_mom) AS mkt_adg_mom
FROM (
{benchmark_sql}
) t
WHERE site IN {seller_sites_subquery}
  AND l1 IN (SELECT DISTINCT l1 FROM cncbbi_general.autodeck__dws_shop_rpt_mi
             WHERE ggp_account_name = {sql_quote(ggp)} AND year_month IN ({date_in(current_prev)}))
  AND year_month IN ({date_in(current_prev)})
  AND seller_type = 'CNCB'
GROUP BY site, l1, l2, year_month
""".strip(),

        # ── Benchmark: site×L3 growth distribution (Section 1.5, 1.6) ──
        "raw_benchmark_l3": f"""
SELECT site, l1, l2, l3, year_month,
  AVG(mkt_adg_mom) AS mkt_adg_mom,
  AVG(p10_growth) AS p10_growth,
  AVG(p25_growth) AS p25_growth,
  AVG(p50_growth) AS p50_growth,
  MAX(seller_cnt) AS seller_cnt
FROM (
{benchmark_sql}
) t
WHERE site IN {seller_sites_subquery}
  AND l2 IN (SELECT DISTINCT l2 FROM cncbbi_general.autodeck__dws_shop_rpt_mi
             WHERE ggp_account_name = {sql_quote(ggp)} AND year_month IN ({date_in(current_prev)}))
  AND year_month IN ({date_in(current_prev)})
  AND seller_type = 'CNCB'
GROUP BY site, l1, l2, l3, year_month
""".strip(),

        # ── Benchmark: price band share (Section 2.2) ──
        "raw_benchmark_price": f"""
SELECT site, l1, l2, l3, price_band, year_month,
  AVG(mkt_price_share) AS mkt_price_share,
  AVG(mom_price_share_pp) AS mom_price_share_pp
FROM (
{benchmark_sql}
) t
WHERE site IN {seller_sites_subquery}
  AND year_month IN ({date_in(current_prev)})
GROUP BY site, l1, l2, l3, price_band, year_month
""".strip(),

        # ── Table C: item data (top 50 per site×L3) ──
        "raw_dws_item": f"""
SELECT * FROM (
  SELECT *,
    ROW_NUMBER() OVER (PARTITION BY site, l3 ORDER BY mtd_adg DESC) AS rn
  FROM cncbbi_general.autodeck__dws_item_rpt_mi
  WHERE ggp_account_name = {sql_quote(ggp)}
    AND year_month IN ({date_in(current_prev)})
) t
WHERE rn <= 50
""".strip(),
    }


def read_json_config(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {}
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"DataService config JSON not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def tech_ref_value(name: str, tech_reference: str = DEFAULT_TECH_REFERENCE) -> Optional[str]:
    if not tech_reference:
        return None
    path = Path(tech_reference).expanduser().resolve()
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    match = re.search(rf'\b{name}\s*=\s*["\']([^"\']+)["\']', text)
    return match.group(1) if match else None


def pick_config_value(json_config: Dict[str, Any], *names: str, default: Optional[str] = None) -> Optional[str]:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    for name in names:
        for key in {name, name.lower(), name.replace("AUTODECK_DATASERVICE_", "").lower(), name.replace("DATASERVICE_", "").lower()}:
            value = json_config.get(key)
            if value:
                return str(value)
    return default


def load_dataservice_config(
    config_path: Optional[str] = None,
    app_key: Optional[str] = None,
    app_secret: Optional[str] = None,
    api_name: Optional[str] = None,
    api_version: Optional[str] = None,
    base_url: Optional[str] = None,
    queue: Optional[str] = None,
    system_name: Optional[str] = None,
    end_user: Optional[str] = None,
    enable_cache: bool = True,
) -> DataServiceConfig:
    json_config = read_json_config(config_path)
    resolved_app_key = app_key or pick_config_value(json_config, "AUTODECK_DATASERVICE_APP_KEY", "DATASERVICE_APP_KEY", "APP_KEY") or tech_ref_value("APP_KEY")
    resolved_app_secret = app_secret or pick_config_value(json_config, "AUTODECK_DATASERVICE_APP_SECRET", "DATASERVICE_APP_SECRET", "APP_SECRET") or tech_ref_value("APP_SECRET")
    if not resolved_app_key or not resolved_app_secret:
        raise RuntimeError("DataService SDK credentials are missing. Set AUTODECK_DATASERVICE_APP_KEY/AUTODECK_DATASERVICE_APP_SECRET or provide --dataservice-config.")
    return DataServiceConfig(
        app_key=resolved_app_key,
        app_secret=resolved_app_secret,
        api_name=api_name or pick_config_value(json_config, "AUTODECK_DATASERVICE_API_NAME", "DATASERVICE_API_NAME", "API_NAME", default=tech_ref_value("API_NAME") or DEFAULT_API_NAME) or DEFAULT_API_NAME,
        api_version=api_version or pick_config_value(json_config, "AUTODECK_DATASERVICE_API_VERSION", "DATASERVICE_API_VERSION", "API_VERSION", default=tech_ref_value("API_VERSION") or DEFAULT_API_VERSION) or DEFAULT_API_VERSION,
        base_url=base_url or pick_config_value(json_config, "AUTODECK_DATASERVICE_BASE_URL", "DATASERVICE_BASE_URL", "DATA_API_URL", default=tech_ref_value("DATA_API_URL") or DEFAULT_BASE_URL) or DEFAULT_BASE_URL,
        queue=queue or pick_config_value(json_config, "AUTODECK_DATASERVICE_QUEUE", "DATASERVICE_QUEUE", "QUEUE", default=DEFAULT_QUEUE) or DEFAULT_QUEUE,
        system_name=system_name or pick_config_value(json_config, "AUTODECK_DATASERVICE_SYSTEM_NAME", "DATASERVICE_SYSTEM_NAME", "SYSTEM_NAME", default=DEFAULT_SYSTEM_NAME) or DEFAULT_SYSTEM_NAME,
        end_user=end_user or pick_config_value(json_config, "AUTODECK_DATASERVICE_END_USER", "DATASERVICE_END_USER", "END_USER", default=DEFAULT_END_USER) or DEFAULT_END_USER,
        enable_cache=enable_cache,
    )


def write_csv(path: Path, header: List[str], rows: List[List[Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def normalize_sdk_rows(rows: List[Dict[str, Any]]) -> Tuple[List[str], List[List[Any]]]:
    if not rows:
        return [], []
    header: List[str] = list(rows[0].keys())
    for row in rows[1:]:
        for key in row.keys():
            if key not in header:
                header.append(key)
    body = [[row.get(col, "") for col in header] for row in rows]
    return header, body


def build_sdk_client(config: DataServiceConfig):
    client = Client().create() \
        .appKey(config.app_key) \
        .appSecret(config.app_secret) \
        .env(config.base_url) \
        .systemName(config.system_name) \
        .endUser(config.end_user) \
        .timeout(30) \
        .refresh()
    return client, QueryConfiguration
def run_sdk_sql(client: Any, query_configuration_cls: Any, config: DataServiceConfig, sql: str, use_personal: bool = False) -> List[Dict[str, Any]]:
    if use_personal:
        # PERSONAL_PRESTO: no 2000-row limit. Uses client.personalCall().
        from dataservice.body import Body, PersonalPayload
        payload = PersonalPayload(sql=sql, prestoQueue=config.queue, idcRegion="SG", priority=3)
        body = Body(personalPayload=payload)
        client._queryPattern = 4
        rows: List[Dict[str, Any]] = []
        for shard in client.personalCall(body):
            for row in shard:
                if isinstance(row, dict) and isinstance(row.get("values"), dict):
                    rows.append(row["values"])
                elif isinstance(row, dict):
                    rows.append(row)
        return rows

    body = {
        "prestoPayload": {
            "expressions": [{"parameterName": "SQL", "value": sql}],
            "prestoQueueName": config.queue,
        }
    }
    query_config = query_configuration_cls(
        apiName=config.api_name,
        version=config.api_version,
        requestBody=body,
        queryPattern=query_configuration_cls.QueryPattern.OLAP,
        enableCache=config.enable_cache,
        prestoQueueName=config.queue,
        network=config.base_url,
    )
    rows: List[Dict[str, Any]] = []
    for shard in client.callWithQueryConfig(query_config):
        for row in shard:
            if isinstance(row, dict) and isinstance(row.get("values"), dict):
                rows.append(row["values"])
            elif isinstance(row, dict):
                rows.append(row)
            else:
                raise RuntimeError(f"Unexpected DataService row shape: {type(row).__name__}")
    return rows


def row_value(row: Dict[str, Any], *names: str) -> Any:
    lowered = {str(k).lower(): v for k, v in row.items()}
    for name in names:
        if name.lower() in lowered:
            return lowered[name.lower()]
    return None


def resolve_ggp_name_sdk(
    client: Any,
    query_configuration_cls: Any,
    config: DataServiceConfig,
    ggp_query: str,
    month: str,
) -> Tuple[str, Dict[str, Any]]:
    """Resolve a partial GGP query to one exact account name when possible."""
    query = ggp_query.strip()
    if not query:
        raise RuntimeError("--ggp cannot be blank")

    current_prev = date_in(month_list(month, 1))
    exact_sql = f"""
SELECT DISTINCT ggp_account_name
FROM cncbbi_general.autodeck__dws_shop_rpt_mi
WHERE year_month IN ({current_prev})
  AND lower(ggp_account_name) = lower({sql_quote(query)})
ORDER BY ggp_account_name
LIMIT 20
""".strip()
    exact_rows = run_sdk_sql(client, query_configuration_cls, config, exact_sql)
    exact_candidates = sorted({str(row_value(row, "ggp_account_name") or "").strip() for row in exact_rows if row_value(row, "ggp_account_name")})
    if exact_candidates:
        return exact_candidates[0], {
            "input": ggp_query,
            "resolved": exact_candidates[0],
            "mode": "exact",
            "candidates": exact_candidates,
        }

    like_sql = f"""
SELECT DISTINCT ggp_account_name
FROM cncbbi_general.autodeck__dws_shop_rpt_mi
WHERE year_month IN ({current_prev})
  AND lower(ggp_account_name) LIKE lower({sql_quote('%' + query + '%')})
ORDER BY ggp_account_name
LIMIT 20
""".strip()
    like_rows = run_sdk_sql(client, query_configuration_cls, config, like_sql)
    like_candidates = sorted({str(row_value(row, "ggp_account_name") or "").strip() for row in like_rows if row_value(row, "ggp_account_name")})

    if len(like_candidates) == 1:
        return like_candidates[0], {
            "input": ggp_query,
            "resolved": like_candidates[0],
            "mode": "partial_unique",
            "candidates": like_candidates,
        }
    if len(like_candidates) > 1:
        raise RuntimeError(
            "Ambiguous GGP account name/query. Please rerun with the exact account name. Candidates: "
            + "; ".join(like_candidates[:20])
        )

    return query, {
        "input": ggp_query,
        "resolved": query,
        "mode": "no_lookup_match_used_input",
        "candidates": [],
    }


PAGE_SIZE = 2000


def run_sdk_count(client: Any, query_configuration_cls: Any, config: DataServiceConfig, sql: str) -> int:
    """Run a COUNT query to get total rows."""
    count_sql = f"SELECT COUNT(*) AS cnt FROM (\n{sql}\n) t"
    rows = run_sdk_sql(client, query_configuration_cls, config, count_sql)
    if rows:
        return int(rows[0].get("cnt", 0))
    return 0


def run_sdk_sql_paginated(
    client: Any, query_configuration_cls: Any, config: DataServiceConfig,
    sql: str, name: str
) -> List[Dict[str, Any]]:
    """
    Execute SQL with automatic pagination by year_month.
    If the result hits the PAGE_SIZE limit, splits query into per-month batches.
    """
    # First attempt: run the full query
    rows = run_sdk_sql(client, query_configuration_cls, config, sql)
    if len(rows) < PAGE_SIZE:
        return rows

    print(f"  ⚠️ {name}: {len(rows)} rows hit limit, paginating by month...")

    # Extract year_month values from the WHERE clause
    ym_match = re.findall(r"DATE '(\d{4}-\d{2}-\d{2})'", sql)
    if not ym_match:
        # Try to get distinct months from a COUNT query
        ym_sql = f"SELECT DISTINCT year_month FROM (\n{sql}\n) t ORDER BY year_month"
        ym_rows = run_sdk_sql(client, query_configuration_cls, config, ym_sql)
        ym_match = [r.get("year_month", "") for r in ym_rows if r.get("year_month")]
        ym_match = [str(y)[:10] for y in ym_match if y]

    if not ym_match:
        print(f"  ⚠️ Cannot paginate {name}: no year_month values found")
        return rows

    # Paginate: one query per month
    all_rows = []
    base_sql = sql.rstrip(";").rstrip()
    for ym in sorted(set(ym_match)):
        # Replace the year_month IN (...) clause with a single month
        paginated_sql = re.sub(
            r"year_month IN \(.*?\)",
            f"year_month = DATE '{ym}'",
            base_sql
        )
        if paginated_sql == base_sql:
            # If no IN clause, try WHERE year_month BETWEEN approach
            paginated_sql = f"SELECT * FROM (\n{base_sql}\n) t WHERE year_month = DATE '{ym}'"

        batch_rows = run_sdk_sql(client, query_configuration_cls, config, paginated_sql)
        all_rows.extend(batch_rows)
        print(f"    {ym}: {len(batch_rows)} rows")

    print(f"  ✅ {name}: {len(all_rows)} total rows from {len(set(ym_match))} months")
    return all_rows


def run_sdk_query(client: Any, query_configuration_cls: Any, config: DataServiceConfig, name: str, sql: str, out_dir: Path, limit: int) -> Dict[str, Any]:
    sql_path = out_dir / f"{name}.sql"
    sql_path.write_text(sql, encoding="utf-8")

    use_personal = (name == "raw_benchmark")
    rows = run_sdk_sql(client, query_configuration_cls, config, sql, use_personal=use_personal)

    if limit and len(rows) > limit and limit > 0:
        rows = rows[:limit]
    header, body = normalize_sdk_rows(rows)
    csv_path = out_dir / f"{name}.csv"
    write_csv(csv_path, header, body)
    return {"name": name, "backend": "sdk", "rows": len(body), "csv": str(csv_path), "sql": str(sql_path)}


def query_raw_data_sdk(
    ggp: str,
    month: str,
    output_dir: Path,
    limit: int = 2000,
    months_back: int = 12,
    config_path: Optional[str] = None,
    app_key: Optional[str] = None,
    app_secret: Optional[str] = None,
    api_name: Optional[str] = None,
    api_version: Optional[str] = None,
    base_url: Optional[str] = None,
    queue: Optional[str] = None,
    system_name: Optional[str] = None,
    end_user: Optional[str] = None,
    enable_cache: bool = True,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    config = load_dataservice_config(
        config_path=config_path,
        app_key=app_key,
        app_secret=app_secret,
        api_name=api_name,
        api_version=api_version,
        base_url=base_url,
        queue=queue,
        system_name=system_name,
        end_user=end_user,
        enable_cache=enable_cache,
    )
    client, query_configuration_cls = build_sdk_client(config)
    resolved_ggp, ggp_resolution = resolve_ggp_name_sdk(client, query_configuration_cls, config, ggp, month)
    if resolved_ggp != ggp:
        print(f"  ✅ Resolved GGP: {ggp} → {resolved_ggp}")
    results = []
    for name, sql in build_queries(resolved_ggp, month, months_back=months_back).items():
        results.append(run_sdk_query(client, query_configuration_cls, config, name, sql, output_dir, limit=limit))
    summary = {
        "backend": "sdk",
        "api_name": config.api_name,
        "api_version": config.api_version,
        "base_url": config.base_url,
        "queue": config.queue,
        "month": month,
        "input_ggp": ggp,
        "ggp": resolved_ggp,
        "resolved_ggp": resolved_ggp,
        "ggp_resolution": ggp_resolution,
        "results": results,
        "limit": limit,
    }
    (output_dir / "query_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def run_bridge(bridge: str, args: List[str], timeout: int = 120) -> Dict[str, Any]:
    proc = subprocess.run([bridge] + args, text=True, capture_output=True, timeout=timeout, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"Bridge command failed: {' '.join(args)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
    text = proc.stdout.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\})", text, flags=re.S)
        if match:
            return json.loads(match.group(1))
        raise RuntimeError(f"Bridge returned non-JSON output: {text[:500]}")


def create_or_find_asset(bridge: str, asset_id: Optional[int]) -> int:
    if asset_id:
        return int(asset_id)
    run_bridge(bridge, ["create-temp"], timeout=30)
    time.sleep(2)
    tabs = run_bridge(bridge, ["temp-tabs"], timeout=30).get("tabs", [])
    if not tabs:
        raise RuntimeError("No DataSuite temp tabs found after create-temp.")

    def tab_asset_id(tab: Dict[str, Any]) -> int:
        return int(tab.get("assetId") or tab.get("asset_id") or tab.get("id") or 0)

    tabs = sorted(tabs, key=tab_asset_id, reverse=True)
    asset = tab_asset_id(tabs[0])
    if not asset:
        raise RuntimeError(f"Temp tab did not expose an asset id: {json.dumps(tabs[0])[:500]}")
    return asset


def poll_success(bridge: str, execution_id: int, timeout_seconds: int = 600) -> Dict[str, Any]:
    deadline = time.time() + timeout_seconds
    last = {}
    while time.time() < deadline:
        last = run_bridge(bridge, ["log", str(execution_id)], timeout=30)
        data = last.get("data", last)
        status = data.get("status")
        if status == 20:
            return last
        if status in (15, 30, 40, 50):
            raise RuntimeError(f"DataSuite execution failed/stopped with status={status}: {json.dumps(data)[:1000]}")
        time.sleep(5)
    raise TimeoutError(f"Timed out waiting for execution {execution_id}. Last log: {json.dumps(last)[:1000]}")


def normalize_bridge_result(result: Dict[str, Any]) -> Tuple[List[str], List[List[Any]]]:
    data = result.get("data", result)
    header = data.get("header") or data.get("headers") or []
    body = data.get("body") or data.get("rows") or []
    if header and isinstance(header[0], dict):
        header = [h.get("name") or h.get("columnName") or str(h) for h in header]
    return [str(h) for h in header], body


def run_bridge_query(bridge: str, asset_id: int, name: str, sql: str, out_dir: Path, limit: int) -> Dict[str, Any]:
    sql_path = out_dir / f"{name}.sql"
    sql_path.write_text(sql, encoding="utf-8")
    run_bridge(bridge, ["save-sql", str(asset_id), str(sql_path)], timeout=120)
    submitted = run_bridge(bridge, ["run-sql", str(asset_id), str(sql_path)], timeout=120)
    execution_id = submitted.get("executionId") or submitted.get("submit", {}).get("executionId")
    if not execution_id:
        text = json.dumps(submitted)
        match = re.search(r'"executionId"\s*:\s*(\d+)', text)
        if match:
            execution_id = int(match.group(1))
    if not execution_id:
        raise RuntimeError(f"No executionId returned for {name}: {json.dumps(submitted)[:1000]}")
    poll_success(bridge, int(execution_id))
    result = run_bridge(bridge, ["result", str(execution_id), str(limit)], timeout=120)
    header, rows = normalize_bridge_result(result)
    csv_path = out_dir / f"{name}.csv"
    write_csv(csv_path, header, rows)
    return {"name": name, "backend": "bridge", "execution_id": int(execution_id), "rows": len(rows), "csv": str(csv_path), "sql": str(sql_path)}


def query_raw_data_bridge(
    ggp: str,
    month: str,
    output_dir: Path,
    bridge: str = DEFAULT_BRIDGE,
    asset_id: Optional[int] = None,
    limit: int = 2000,
    months_back: int = 12,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    if not bridge:
        raise RuntimeError("Bridge mode requires --bridge or AUTODECK_BRIDGE. SDK mode is the default supported path.")
    bridge_path = str(Path(bridge).expanduser().resolve())
    asset = create_or_find_asset(bridge_path, asset_id)
    results = []
    for name, sql in build_queries(ggp, month, months_back=months_back).items():
        results.append(run_bridge_query(bridge_path, asset, name, sql, output_dir, limit=limit))
    summary = {"backend": "bridge", "asset_id": asset, "month": month, "ggp": ggp, "results": results, "limit": limit}
    (output_dir / "query_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def query_raw_data(
    ggp: str,
    month: str,
    output_dir: Path,
    backend: str = "sdk",
    bridge: str = DEFAULT_BRIDGE,
    asset_id: Optional[int] = None,
    limit: int = 2000,
    months_back: int = 12,
    dataservice_config: Optional[str] = None,
    dataservice_app_key: Optional[str] = None,
    dataservice_app_secret: Optional[str] = None,
    dataservice_api_name: Optional[str] = None,
    dataservice_api_version: Optional[str] = None,
    dataservice_base_url: Optional[str] = None,
    dataservice_queue: Optional[str] = None,
    dataservice_system_name: Optional[str] = None,
    dataservice_end_user: Optional[str] = None,
    dataservice_enable_cache: bool = True,
) -> Dict[str, Any]:
    if backend == "bridge":
        return query_raw_data_bridge(
            ggp=ggp,
            month=month,
            output_dir=output_dir,
            bridge=bridge,
            asset_id=asset_id,
            limit=limit,
            months_back=months_back,
        )
    if backend != "sdk":
        raise RuntimeError(f"Unsupported raw data backend: {backend}")
    return query_raw_data_sdk(
        ggp=ggp,
        month=month,
        output_dir=output_dir,
        limit=limit,
        months_back=months_back,
        config_path=dataservice_config,
        app_key=dataservice_app_key,
        app_secret=dataservice_app_secret,
        api_name=dataservice_api_name,
        api_version=dataservice_api_version,
        base_url=dataservice_base_url,
        queue=dataservice_queue,
        system_name=dataservice_system_name,
        end_user=dataservice_end_user,
        enable_cache=dataservice_enable_cache,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Query AutoDeck raw tabs through the DataService SDK.")
    parser.add_argument("--ggp", required=True)
    parser.add_argument("--month", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--backend", choices=["sdk", "bridge"], default="sdk")
    parser.add_argument("--limit", type=int, default=2000)
    parser.add_argument("--months-back", type=int, default=12)

    parser.add_argument("--dataservice-config")
    parser.add_argument("--dataservice-app-key")
    parser.add_argument("--dataservice-app-secret")
    parser.add_argument("--dataservice-api-name")
    parser.add_argument("--dataservice-api-version")
    parser.add_argument("--dataservice-base-url")
    parser.add_argument("--dataservice-queue")
    parser.add_argument("--dataservice-system-name")
    parser.add_argument("--dataservice-end-user")
    parser.add_argument("--disable-cache", action="store_true")

    parser.add_argument("--bridge", default=DEFAULT_BRIDGE)
    parser.add_argument("--asset-id", type=int)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = query_raw_data(
        ggp=args.ggp,
        month=args.month,
        output_dir=Path(args.output_dir).expanduser().resolve(),
        backend=args.backend,
        bridge=args.bridge,
        asset_id=args.asset_id,
        limit=args.limit,
        months_back=args.months_back,
        dataservice_config=args.dataservice_config,
        dataservice_app_key=args.dataservice_app_key,
        dataservice_app_secret=args.dataservice_app_secret,
        dataservice_api_name=args.dataservice_api_name,
        dataservice_api_version=args.dataservice_api_version,
        dataservice_base_url=args.dataservice_base_url,
        dataservice_queue=args.dataservice_queue,
        dataservice_system_name=args.dataservice_system_name,
        dataservice_end_user=args.dataservice_end_user,
        dataservice_enable_cache=not args.disable_cache,
    )
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
