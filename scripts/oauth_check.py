#!/usr/bin/env python3
"""Validate a local Google OAuth authorized-user credential for AutoDeck."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


REQUIRED_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/script.projects",
    "https://www.googleapis.com/auth/script.deployments",
]


def _expand(path: str) -> Path:
    return Path(path).expanduser().resolve()


def load_oauth(path: str) -> Dict[str, Any]:
    p = _expand(path)
    with p.open("r", encoding="utf-8") as f:
      data = json.load(f)
    return data


def load_client(client_json: Optional[str]) -> Dict[str, Any]:
    if not client_json:
        return {}
    data = load_oauth(client_json)
    return data.get("installed") or data.get("web") or data


def credential_scopes(data: Dict[str, Any]) -> List[str]:
    scopes = data.get("scopes", data.get("scope", []))
    if isinstance(scopes, str):
        scopes = scopes.split()
    return sorted(set(scopes))


def missing_scopes(data: Dict[str, Any], required: Iterable[str] = REQUIRED_SCOPES) -> List[str]:
    have = set(credential_scopes(data))
    return [scope for scope in required if scope not in have]


def build_credentials(path: str, scopes: Iterable[str] = REQUIRED_SCOPES, refresh: bool = True, client_json: Optional[str] = None) -> Credentials:
    data = load_oauth(path)
    client = load_client(client_json)
    creds = Credentials(
        token=data.get("token") or data.get("access_token"),
        refresh_token=data.get("refresh_token"),
        token_uri=data.get("token_uri") or client.get("token_uri"),
        client_id=data.get("client_id") or client.get("client_id"),
        client_secret=data.get("client_secret") or client.get("client_secret"),
        scopes=list(scopes),
    )
    if refresh and not creds.valid and creds.refresh_token:
        creds.refresh(Request())
        data["token"] = creds.token
        data["expiry"] = creds.expiry.isoformat() if creds.expiry else data.get("expiry")
        _expand(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return creds


def check(path: str, refresh: bool = True, client_json: Optional[str] = None) -> Dict[str, Any]:
    p = _expand(path)
    data = load_oauth(str(p))
    missing = missing_scopes(data)
    out: Dict[str, Any] = {
        "path": str(p),
        "exists": p.exists(),
        "scopes": credential_scopes(data),
        "required_scopes": REQUIRED_SCOPES,
        "missing_scopes": missing,
        "ok": not missing,
    }
    if not missing and refresh:
        creds = build_credentials(str(p), refresh=True, client_json=client_json)
        out["valid_after_refresh"] = bool(creds.valid)
        out["expired"] = bool(creds.expired)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AutoDeck Google OAuth credential scopes.")
    parser.add_argument("--oauth", required=True, help="Path to authorized-user OAuth JSON.")
    parser.add_argument("--oauth-client-json", help="Optional desktop OAuth client JSON when the token JSON lacks client fields.")
    parser.add_argument("--no-refresh", action="store_true", help="Do not refresh the token.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    result = check(args.oauth, refresh=not args.no_refresh, client_json=args.oauth_client_json)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"OAuth: {result['path']}")
        print(f"Scopes: {len(result['scopes'])}")
        if result["missing_scopes"]:
            print("Missing required scopes:")
            for scope in result["missing_scopes"]:
                print(f"  - {scope}")
        else:
            print("All required AutoDeck scopes are present.")
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
