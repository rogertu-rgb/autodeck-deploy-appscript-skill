#!/usr/bin/env python3
"""Read AutoDeck Sheet tabs into a JSON payload."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from googleapiclient.discovery import build

from oauth_check import build_credentials


DEFAULT_INCLUDE_PREFIXES = ("sec_",)
DEFAULT_INCLUDE_NAMES = ("Gate Config", "Chart Registry", "Feedback Log")


def _tab_is_included(name: str, prefixes: Iterable[str], names: Iterable[str]) -> bool:
    return any(name.startswith(prefix) for prefix in prefixes) or name in set(names)


def read_sheet_payload(oauth: str, sheet_id: str, include_raw: bool = False) -> Dict[str, Any]:
    creds = build_credentials(oauth)
    service = build("sheets", "v4", credentials=creds)
    meta = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    prefixes = list(DEFAULT_INCLUDE_PREFIXES)
    if include_raw:
        prefixes.append("raw_")
    tab_names = [
        s["properties"]["title"]
        for s in meta.get("sheets", [])
        if _tab_is_included(s["properties"]["title"], prefixes, DEFAULT_INCLUDE_NAMES)
    ]
    payload: Dict[str, Any] = {
        "sheetId": sheet_id,
        "sheetUrl": f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit",
        "tabs": {},
    }
    if not tab_names:
        return payload
    ranges = [f"'{name}'" for name in tab_names]
    result = service.spreadsheets().values().batchGet(
        spreadsheetId=sheet_id,
        ranges=ranges,
        valueRenderOption="UNFORMATTED_VALUE",
    ).execute()
    for value_range in result.get("valueRanges", []):
        raw_range = value_range.get("range", "")
        tab_name = raw_range.split("!", 1)[0].strip("'")
        payload["tabs"][tab_name] = value_range.get("values", [])
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Read AutoDeck Sheet tabs into JSON.")
    parser.add_argument("--oauth", required=True)
    parser.add_argument("--sheet-id", required=True)
    parser.add_argument("--include-raw", action="store_true")
    parser.add_argument("--output", help="Output JSON path. Defaults to stdout.")
    args = parser.parse_args()

    payload = read_sheet_payload(args.oauth, args.sheet_id, include_raw=args.include_raw)
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).expanduser().resolve().write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
