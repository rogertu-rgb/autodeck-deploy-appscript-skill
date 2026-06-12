#!/usr/bin/env python3
"""Create/reuse an AutoDeck report Sheet and write raw CSV tabs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from googleapiclient.discovery import build

from oauth_check import build_credentials


RAW_FILES = {
    "raw_dws_shop": "raw_dws_shop.csv",
    "raw_benchmark": "raw_benchmark.csv",
    "raw_benchmark_site": "raw_benchmark_site.csv",
    "raw_benchmark_l1": "raw_benchmark_l1.csv",
    "raw_benchmark_l2": "raw_benchmark_l2.csv",
    "raw_benchmark_l3": "raw_benchmark_l3.csv",
    "raw_benchmark_price": "raw_benchmark_price.csv",
    "raw_dws_item": "raw_dws_item.csv",
}
SHEETS_SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]


def read_csv_rows(path: Path) -> List[List[str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return [row for row in csv.reader(f)]


def sheets_service(oauth: str, oauth_client_json: Optional[str] = None):
    return build("sheets", "v4", credentials=build_credentials(oauth, scopes=SHEETS_SCOPE, client_json=oauth_client_json))


def create_sheet(service, title: str) -> str:
    created = service.spreadsheets().create(body={"properties": {"title": title}}).execute()
    return created["spreadsheetId"]


def existing_tab_names(service, sheet_id: str) -> Dict[str, int]:
    meta = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    return {
        s["properties"]["title"]: s["properties"]["sheetId"]
        for s in meta.get("sheets", [])
    }


def ensure_tabs(service, sheet_id: str, tab_names: Iterable[str]) -> None:
    existing = existing_tab_names(service, sheet_id)
    requests = []
    for name in tab_names:
        if name not in existing:
            requests.append({"addSheet": {"properties": {"title": name}}})
    if requests:
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={"requests": requests},
        ).execute()


def write_tab(service, sheet_id: str, tab_name: str, rows: List[List[str]]) -> None:
    ensure_tabs(service, sheet_id, [tab_name])
    service.spreadsheets().values().clear(spreadsheetId=sheet_id, range=f"'{tab_name}'").execute()
    if rows:
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"'{tab_name}'!A1",
            valueInputOption="USER_ENTERED",
            body={"values": rows},
        ).execute()


def create_or_update_report_sheet(
    oauth: str,
    ggp: str,
    month: str,
    raw_dir: Path,
    sheet_id: Optional[str] = None,
    oauth_client_json: Optional[str] = None,
) -> Dict[str, str]:
    service = sheets_service(oauth, oauth_client_json=oauth_client_json)
    if not sheet_id:
        sheet_id = create_sheet(service, f"AutoDeck - {ggp} - {month}")
    for tab_name, filename in RAW_FILES.items():
        path = raw_dir / filename
        if not path.exists():
            print(f"  ⚠️ Skipping {tab_name}: {filename} not found")
            continue
        rows = read_csv_rows(path)
        if len(rows) <= 1:
            print(f"  ⚠️ Skipping {tab_name}: empty (only header)")
            continue
        write_tab(service, sheet_id, tab_name, rows)
    return {
        "sheet_id": sheet_id,
        "sheet_url": f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create/reuse AutoDeck Sheet and write raw tabs.")
    parser.add_argument("--oauth", required=True)
    parser.add_argument("--oauth-client-json")
    parser.add_argument("--ggp", required=True)
    parser.add_argument("--month", required=True)
    parser.add_argument("--raw-dir", required=True)
    parser.add_argument("--sheet-id")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = create_or_update_report_sheet(
        oauth=args.oauth,
        ggp=args.ggp,
        month=args.month,
        raw_dir=Path(args.raw_dir).expanduser().resolve(),
        sheet_id=args.sheet_id,
        oauth_client_json=args.oauth_client_json,
    )
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Sheet: {result['sheet_url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
