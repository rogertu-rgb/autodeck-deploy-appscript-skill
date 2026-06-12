#!/usr/bin/env python3
"""Validate generated AutoDeck HTML and Apps Script deployment files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


INTERNAL_CODE_RE = re.compile(r"\b(?:B_12M|B_MTD|G[1-4][A-Z]?_|N[0-9]_HIST|N[0-9]_MTD|Task\s+\d)\b")


def validate_html(html_path: Path) -> List[str]:
    text = html_path.read_text(encoding="utf-8")
    script_free = re.sub(r"<script[\s\S]*?</script>", "", text, flags=re.I)
    failures: List[str] = []
    if INTERNAL_CODE_RE.search(text):
        failures.append("Visible/internal code-like labels found in HTML.")
    if "Data display first" not in text:
        failures.append("Renderer does not mark data-first section structure.")
    if "google.script.run" not in text:
        failures.append("Index.html does not call google.script.run for live Sheet loading.")
    if "AUTODECK_LOCAL_DATA" not in text:
        failures.append("Index.html lacks local data fallback.")
    if "filterableTableHtml(model, 8, true)" in text:
        failures.append("Primary visual still falls back to a raw/filterable table.")
    if "No chartable rows available" in script_free:
        failures.append("Primary visual contains a blank no-chartable-rows panel instead of a route/meta visual.")
    if "function emptyStateChart" not in text or "function metaChart" not in text:
        failures.append("Renderer lacks required no-row/meta chart visualizers.")
    if "function historyStackedChart" not in text or not ('model.id === "sec_12m_history"' in text or 'id === "sec_12m_history"' in text):
        failures.append("Section 1 must use the screenshot-style stacked monthly site chart, not a dual-axis fallback.")
    analysis_blocks = re.findall(r'<div class="analysis".*?</div>', text, flags=re.S)
    if any("jumpTo(" in block for block in analysis_blocks):
        failures.append("Section analysis contains cross-section jump links.")

    # CRITICAL: No raw JSON visible on the page
    if re.search(r'[\[{]\s*"[^"]{3,}"\s*:', script_free):
        failures.append("Raw JSON detected in visible page content — use safeDisplay() to summarize meta tabs.")
    if "function safeDisplay" not in text:
        failures.append("Renderer missing safeDisplay() guard — raw JSON may leak into meta tile charts.")
    if 'data-analysis-mode="computed"' not in text or "function computedAnalysisFindings" not in text:
        failures.append("Renderer must use computed section analysis, not raw sec_text template directions.")
    if "TEXT_TEMPLATES[model.id]" in text or 'text.replace("{" + m.col + "}",' in text:
        failures.append("Renderer still appears to fill sec_text templates directly instead of generating analysis findings.")
    if re.search(r"<div class=\"analysis\"[\s\S]*?(?:\{[a-z_]+\}|待分析|待填充|Key metrics available|from sec_|从sec_)", script_free, flags=re.I):
        failures.append("Visible analysis contains placeholder/framework text instead of computed findings.")
    required_interactions = {
        "sticky/search header": 'id="section-search"',
        "section accordion toggles": "data-toggle-section",
        "left rail navigation": "data-target-section",
        "collapsible source tables": "source-data",
        "evidence chip cell highlighting": "function focusEvidence",
        "interaction binder": "function bindInteractions",
        "live Apps Script loader": "google.script.run",
        "embedded fallback renderer": "AutoDeck fallback render",
        "ECharts init lifecycle": "echarts.init",
        "chart resize observer": "ResizeObserver",
        "executive summary cards": "summary-grid",
        "storyline gate strip": "gate-grid",
        "v_0602 provenance": "AutoDeck v_0602",
    }
    for label, snippet in required_interactions.items():
        if snippet not in text:
            failures.append(f"Golden auto_html_0602 interaction missing: {label}.")
    if '<div class="topbar" style="display:none"' in text:
        failures.append("Topbar is hidden; renderer is not using the golden auto_html_0602 shell.")
    if "__ENGINE_JS__" in text:
        failures.append("Shared render engine token was not replaced.")
    if "__GGP__" in text:
        failures.append("GGP placeholder token was not replaced.")
    return failures


def validate_manifest(path: Path) -> List[str]:
    failures: List[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    webapp = data.get("webapp", {})
    if webapp.get("access") != "DOMAIN":
        failures.append("appsscript.json webapp.access must be DOMAIN.")
    if webapp.get("executeAs") != "USER_DEPLOYING":
        failures.append("appsscript.json webapp.executeAs must be USER_DEPLOYING.")
    scopes = data.get("oauthScopes", [])
    if "https://www.googleapis.com/auth/spreadsheets" not in scopes:
        failures.append("appsscript.json missing spreadsheets scope.")
    return failures


def validate_code_gs(path: Path, sheet_id: Optional[str]) -> List[str]:
    text = path.read_text(encoding="utf-8")
    failures: List[str] = []
    if "function loadAutodeckData()" not in text:
        failures.append("Code.gs missing loadAutodeckData().")
    if sheet_id and sheet_id not in text:
        failures.append("Code.gs does not contain the expected SHEET_ID.")
    return failures


def validate(html: str, code: Optional[str] = None, manifest: Optional[str] = None, sheet_id: Optional[str] = None) -> Dict[str, Any]:
    failures: List[str] = []
    failures.extend(validate_html(Path(html).expanduser().resolve()))
    if code:
        failures.extend(validate_code_gs(Path(code).expanduser().resolve(), sheet_id))
    if manifest:
        failures.extend(validate_manifest(Path(manifest).expanduser().resolve()))
    return {"ok": not failures, "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AutoDeck report artifacts.")
    parser.add_argument("--html", required=True)
    parser.add_argument("--code")
    parser.add_argument("--manifest")
    parser.add_argument("--sheet-id")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = validate(args.html, args.code, args.manifest, args.sheet_id)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        if result["ok"]:
            print("Validation passed.")
        else:
            print("Validation failed:")
            for item in result["failures"]:
                print(f"  - {item}")
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
