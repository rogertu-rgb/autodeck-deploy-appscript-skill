#!/usr/bin/env python3
"""Deploy an AutoDeck Index.html to Google Apps Script."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional

from googleapiclient.discovery import build

from oauth_check import build_credentials


SKILL_DIR = Path(__file__).resolve().parents[1]
ASSET_DIR = SKILL_DIR / "assets"


def render_template(path: Path, values: Dict[str, str]) -> str:
    text = path.read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def render_code_gs(sheet_id: str, title: str) -> str:
    return render_template(ASSET_DIR / "Code.gs.tpl", {"SHEET_ID": sheet_id, "TITLE": title.replace("'", "\\'")})


def render_manifest() -> str:
    return (ASSET_DIR / "appsscript.json.tpl").read_text(encoding="utf-8")


def deployment_url(deployment_id: str, domain: Optional[str] = "shopee.com") -> str:
    if domain:
        return f"https://script.google.com/a/macros/{domain}/s/{deployment_id}/exec"
    return f"https://script.google.com/macros/s/{deployment_id}/exec"


def deploy(
    oauth: str,
    sheet_id: str,
    html_path: str,
    title: str,
    output_dir: Optional[str] = None,
    domain: str = "shopee.com",
    dry_run: bool = False,
) -> Dict[str, Any]:
    out_dir = Path(output_dir).expanduser().resolve() if output_dir else Path(html_path).expanduser().resolve().parent
    out_dir.mkdir(parents=True, exist_ok=True)
    index_html = Path(html_path).expanduser().resolve().read_text(encoding="utf-8")
    code_gs = render_code_gs(sheet_id, title)
    manifest = render_manifest()
    (out_dir / "Code.gs").write_text(code_gs, encoding="utf-8")
    (out_dir / "appsscript.json").write_text(manifest, encoding="utf-8")

    if dry_run:
        return {
            "dry_run": True,
            "code_gs": str(out_dir / "Code.gs"),
            "manifest": str(out_dir / "appsscript.json"),
            "index_html": str(Path(html_path).expanduser().resolve()),
        }

    creds = build_credentials(oauth)
    script_service = build("script", "v1", credentials=creds)

    project = script_service.projects().create(body={"title": title}).execute()
    script_id = project["scriptId"]

    script_service.projects().updateContent(
        scriptId=script_id,
        body={
            "files": [
                {"name": "appsscript", "type": "JSON", "source": manifest},
                {"name": "Code", "type": "SERVER_JS", "source": code_gs},
                {"name": "Index", "type": "HTML", "source": index_html},
            ]
        },
    ).execute()

    version = script_service.projects().versions().create(
        scriptId=script_id,
        body={"description": "AutoDeck generated report"},
    ).execute()

    deployment = script_service.projects().deployments().create(
        scriptId=script_id,
        body={
            "versionNumber": version["versionNumber"],
            "manifestFileName": "appsscript",
            "description": "AutoDeck web app",
        },
    ).execute()

    dep_id = deployment["deploymentId"]
    return {
        "script_id": script_id,
        "deployment_id": dep_id,
        "version_number": version["versionNumber"],
        "web_app_url": deployment_url(dep_id, domain=domain),
        "code_gs": str(out_dir / "Code.gs"),
        "manifest": str(out_dir / "appsscript.json"),
        "index_html": str(Path(html_path).expanduser().resolve()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy AutoDeck report to Apps Script.")
    parser.add_argument("--oauth", required=True)
    parser.add_argument("--sheet-id", required=True)
    parser.add_argument("--html", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--output-dir")
    parser.add_argument("--domain", default="shopee.com")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = deploy(
        oauth=args.oauth,
        sheet_id=args.sheet_id,
        html_path=args.html,
        title=args.title,
        output_dir=args.output_dir,
        domain=args.domain,
        dry_run=args.dry_run,
    )
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
