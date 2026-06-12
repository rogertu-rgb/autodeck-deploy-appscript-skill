#!/usr/bin/env python3
"""Run the existing AutoDeck v_0602 build_sections.py with a caller-provided OAuth path."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path
from typing import Any, Dict, Optional

import googleapiclient.discovery
import pandas as pd

from oauth_check import build_credentials


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_BUILD_SCRIPT = str(SCRIPT_DIR / "section_builder" / "build_sections.py")
SHEETS_SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]
TEXT_COLUMNS = {
    "year_month",
    "ggp_account_name",
    "site",
    "l1",
    "l2",
    "l3",
    "shop_name",
    "item_name",
    "price_range",
    "price_band",
}
METRIC_HINTS = (
    "adg",
    "ado",
    "mom",
    "gap",
    "share",
    "spend",
    "total",
    "cnt",
    "days",
    "price",
    "rebate",
    "organic",
    "ads",
    "live",
    "campaign",
    "mtd",
    "m1",
    "gmv",
    "growth",
)


def coerce_metric_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        name = str(col).lower()
        if name in TEXT_COLUMNS or "name" in name or name.endswith("_id") or name == "id":
            continue
        series = out[col]
        text = series.astype(str).str.strip()
        non_empty = text.ne("") & text.ne("nan") & text.ne("None")
        if not non_empty.any():
            continue
        cleaned = text.str.replace(",", "", regex=False).str.replace("%", "", regex=False).str.replace("$", "", regex=False)
        numeric = pd.to_numeric(cleaned, errors="coerce")
        should_force_metric = any(hint in name for hint in METRIC_HINTS)
        if should_force_metric or numeric[non_empty].notna().sum() / non_empty.sum() >= 0.8:
            out[col] = numeric
    return out


def safe_cell(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float) and not math.isfinite(value):
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return value


def sanitize_sheet_rows(data: Any) -> Any:
    if not isinstance(data, list):
        return data
    return [[safe_cell(cell) for cell in row] if isinstance(row, list) else row for row in data]


def ensure_tab(module: Any, sheet_id: str, tab_name: str) -> None:
    service = module._get_sheets_service()
    meta = service.spreadsheets().get(spreadsheetId=sheet_id, fields="sheets.properties.title").execute()
    titles = {s["properties"]["title"] for s in meta.get("sheets", [])}
    if tab_name not in titles:
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={"requests": [{"addSheet": {"properties": {"title": tab_name}}}]},
        ).execute()


def load_build_module(build_script: str, oauth: str, oauth_client_json: Optional[str] = None):
    path = Path(build_script).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"build_sections.py not found: {path}")
    spec = importlib.util.spec_from_file_location("autodeck_v0602_build_sections", str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import build script: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.CREDS_PATH = str(Path(oauth).expanduser().resolve())
    original_read_sheet_tab = module.read_sheet_tab
    original_write_sheet_tab = module.write_sheet_tab

    def read_sheet_tab(sheet_id: str, tab_name: str):
        return coerce_metric_columns(original_read_sheet_tab(sheet_id, tab_name))

    def write_sheet_tab(sheet_id: str, tab_name: str, data, clear: bool = True):
        ensure_tab(module, sheet_id, tab_name)
        return original_write_sheet_tab(sheet_id, tab_name, sanitize_sheet_rows(data), clear=clear)

    module.read_sheet_tab = read_sheet_tab
    module.write_sheet_tab = write_sheet_tab
    if oauth_client_json:
        def _get_sheets_service():
            creds = build_credentials(oauth, scopes=SHEETS_SCOPE, client_json=oauth_client_json)
            return googleapiclient.discovery.build("sheets", "v4", credentials=creds)

        module._get_sheets_service = _get_sheets_service
    return module


def run_build(
    oauth: str,
    sheet_id: str,
    ggp: str,
    build_script: str = DEFAULT_BUILD_SCRIPT,
    l1: Optional[str] = None,
    l2: Optional[str] = None,
    oauth_client_json: Optional[str] = None,
) -> Dict[str, Any]:
    module = load_build_module(build_script, oauth, oauth_client_json=oauth_client_json)
    return module.run_all(sheet_id, ggp, l1, l2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AutoDeck build_sections.py via adapter.")
    parser.add_argument("--oauth", required=True)
    parser.add_argument("--oauth-client-json")
    parser.add_argument("--sheet-id", required=True)
    parser.add_argument("--ggp", required=True)
    parser.add_argument("--build-script", default=DEFAULT_BUILD_SCRIPT)
    parser.add_argument("--l1")
    parser.add_argument("--l2")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_build(args.oauth, args.sheet_id, args.ggp, args.build_script, args.l1, args.l2, oauth_client_json=args.oauth_client_json)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not result.get("error") else 2


if __name__ == "__main__":
    raise SystemExit(main())
