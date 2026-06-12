#!/usr/bin/env python3
"""One-command AutoDeck deploy orchestrator."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from build_sections_adapter import run_build
from create_report_sheet import create_or_update_report_sheet
from deploy_appscript import deploy
from oauth_check import check as check_oauth
from query_raw_data import query_raw_data
from render_html import render_index_html
from sheet_sections_to_json import read_sheet_payload
from validate_report import validate


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_BRIDGE = os.environ.get("AUTODECK_BRIDGE", "")
DEFAULT_BUILD_SCRIPT = str(SCRIPT_DIR / "section_builder" / "build_sections.py")


def default_month() -> str:
    return datetime.now().strftime("%Y-%m")


def default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path.cwd() / "outputs" / "autodeck_runs" / stamp


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def run(args) -> Dict[str, Any]:
    out_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else default_output_dir().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = out_dir / "raw"
    artifacts_dir = out_dir / "appscript"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    oauth_result = check_oauth(args.oauth, refresh=True)
    if not oauth_result["ok"]:
        raise RuntimeError("OAuth credential is missing required scopes: " + ", ".join(oauth_result["missing_scopes"]))

    sheet_id: Optional[str] = args.sheet_id
    query_summary: Optional[Dict[str, Any]] = None
    sheet_summary: Optional[Dict[str, str]] = None
    build_summary: Optional[Dict[str, Any]] = None
    report_ggp = args.ggp

    if args.data_mode in ("sdk", "datasuite", "bridge"):
        backend = "bridge" if args.data_mode == "bridge" else "sdk"
        query_summary = query_raw_data(
            ggp=args.ggp,
            month=args.month,
            output_dir=raw_dir,
            backend=backend,
            bridge=args.bridge,
            asset_id=args.asset_id,
            limit=args.query_limit,
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
        report_ggp = query_summary.get("resolved_ggp") or query_summary.get("ggp") or args.ggp
        sheet_summary = create_or_update_report_sheet(args.oauth, report_ggp, args.month, raw_dir, sheet_id=sheet_id)
        sheet_id = sheet_summary["sheet_id"]
    elif args.data_mode == "existing-sheet":
        if not sheet_id:
            raise RuntimeError("--sheet-id is required with --data-mode existing-sheet")
        sheet_summary = {
            "sheet_id": sheet_id,
            "sheet_url": f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit",
        }
    else:
        raise RuntimeError(f"Unsupported data mode: {args.data_mode}")

    if not args.skip_build:
        build_summary = run_build(
            oauth=args.oauth,
            sheet_id=sheet_id,
            ggp=report_ggp,
            build_script=args.build_script,
            l1=args.l1,
            l2=args.l2,
        )
        if build_summary.get("error"):
            raise RuntimeError(build_summary["error"])

    payload = read_sheet_payload(args.oauth, sheet_id)
    payload_path = out_dir / "sheet_payload.json"
    write_json(payload_path, payload)

    html_path = artifacts_dir / "Index.html"
    html_path.write_text(render_index_html(payload, report_ggp, args.month), encoding="utf-8")

    title = args.title or f"AutoDeck - {report_ggp} - {args.month}"
    dry_deploy = deploy(
        oauth=args.oauth,
        sheet_id=sheet_id,
        html_path=str(html_path),
        title=title,
        output_dir=str(artifacts_dir),
        domain=args.domain,
        dry_run=True,
    )

    validation = validate(
        html=str(html_path),
        code=dry_deploy["code_gs"],
        manifest=dry_deploy["manifest"],
        sheet_id=sheet_id,
    )
    if not validation["ok"] and not args.allow_validation_failures:
        summary = {
            "ok": False,
            "stage": "validation",
            "validation": validation,
            "output_dir": str(out_dir),
            "sheet": sheet_summary,
            "query": query_summary,
            "build": build_summary,
        }
        write_json(out_dir / "run_summary.json", summary)
        raise RuntimeError("Validation failed: " + "; ".join(validation["failures"]))

    deployment: Dict[str, Any]
    if args.dry_run:
        deployment = dry_deploy
    else:
        deployment = deploy(
            oauth=args.oauth,
            sheet_id=sheet_id,
            html_path=str(html_path),
            title=title,
            output_dir=str(artifacts_dir),
            domain=args.domain,
            dry_run=False,
        )

    summary = {
        "ok": True,
        "input_ggp": args.ggp,
        "ggp": report_ggp,
        "month": args.month,
        "output_dir": str(out_dir),
        "sheet": sheet_summary,
        "query": query_summary,
        "build": build_summary,
        "payload": str(payload_path),
        "html": str(html_path),
        "validation": validation,
        "deployment": deployment,
    }
    write_json(out_dir / "run_summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AutoDeck end-to-end and deploy to Apps Script.")
    parser.add_argument("--oauth", required=True)
    parser.add_argument("--ggp", required=True)
    parser.add_argument("--month", default=default_month())
    parser.add_argument("--sheet-id")
    parser.add_argument("--data-mode", choices=["sdk", "existing-sheet", "bridge", "datasuite"], default=None)
    parser.add_argument("--output-dir")
    parser.add_argument("--title")
    parser.add_argument("--domain", default="shopee.com")
    parser.add_argument("--dry-run", action="store_true", help="Generate artifacts but do not create Apps Script deployment.")
    parser.add_argument("--skip-build", action="store_true", help="Render existing sec_* tabs without running build_sections.py.")
    parser.add_argument("--allow-validation-failures", action="store_true")

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
    parser.add_argument("--query-limit", type=int, default=2000)
    parser.add_argument("--months-back", type=int, default=12)
    parser.add_argument("--build-script", default=DEFAULT_BUILD_SCRIPT)
    parser.add_argument("--l1")
    parser.add_argument("--l2")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.data_mode is None:
        args.data_mode = "existing-sheet" if args.sheet_id else "sdk"

    try:
        summary = run(args)
    except Exception as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2, ensure_ascii=False))
        else:
            print(f"AutoDeck run failed: {exc}")
        return 2

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print("AutoDeck run complete.")
        print(f"Sheet: {summary['sheet']['sheet_url']}")
        deployment = summary.get("deployment", {})
        if deployment.get("web_app_url"):
            print(f"Web App: {deployment['web_app_url']}")
        else:
            print(f"Artifacts: {summary['output_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
