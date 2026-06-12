#!/usr/bin/env python3
"""
Test Harness — render one or all AutoDeck sections as standalone HTML.

Usage:
  # Single section
  python3 scripts/render/test_harness.py \\
    --section sec_12m_history \\
    --input-json /tmp/sheet_payload.json \\
    --ggp "浙江格蕾美" --month 2026-05 \\
    --output /tmp/test_section.html

  # All sections
  python3 scripts/render/test_harness.py \\
    --section all \\
    --input-json /tmp/sheet_payload.json \\
    --ggp "浙江格蕾美" --month 2026-05 \\
    --output /tmp/test_full.html

  # Open in browser
  python3 scripts/render/test_harness.py --section sec_12m_history ... --open
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add parent to path so we can import from scripts/
_SCRIPT_DIR = Path(__file__).resolve().parent
_SKILL_DIR = _SCRIPT_DIR.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))

from render.engine import Engine
from render.shell import generate_shell, SECTION_ORDER_ZH, SECTION_ORDER_EN


# ── Section registry ──
# Maps section_id to (module, function_name) for import-on-demand
# Tab dependencies: some sections read from additional tabs beyond their own
TAB_DEPS: Dict[str, List[str]] = {
    "sec_l1_overview": ["sec_l1_matrix"],         # Section 1.2 reads site×L1 granular data
    "sec_volatility": ["sec_volatility_meta"],     # Section 1.6 reads from meta tab
    "sec_listing_change": ["sec_listing_change_meta"],  # Section 1.8 reads from meta tab
    "sec_root_cause": ["sec_root_cause_meta"],     # Section 2.3 reads diagnostic cards from meta tab
}

SECTION_REGISTRY: Dict[str, tuple] = {
    "sec_12m_history": ("render.section_1_0", "build_section_js"),
    "sec_site_benchmark": ("render.section_1_1", "build_section_js"),
    "sec_l1_overview": ("render.section_1_2", "build_section_js"),
    "sec_l1_matrix": ("render.section_1_3", "build_section_js"),
    "sec_l2_drill": ("render.section_1_4", "build_section_js"),
    "sec_l3_granular": ("render.section_1_5", "build_section_js"),
    "sec_volatility": ("render.section_1_6", "build_section_js"),
    "sec_shop_impact": ("render.section_1_7", "build_section_js"),
    "sec_listing_change": ("render.section_1_8", "build_section_js"),
    "sec_fulfillment": ("render.section_1_9", "build_section_js"),
    "sec_traffic_channel": ("render.section_2_0", "build_section_js"),
    "sec_subsidy": ("render.section_2_1", "build_section_js"),
    "sec_price_band": ("render.section_2_2", "build_section_js"),
    "sec_ams": ("render.section_2_4", "build_section_js"),
    "sec_root_cause": ("render.section_2_3", "build_section_js"),
}


def load_payload(path: str) -> dict:
    """Load a sheet_payload.json file."""
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"Payload file not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_section_tabs(payload: dict, section_id: str) -> dict:
    """Extract only the tabs needed for a specific section from the payload."""
    tabs = payload.get("tabs", {})
    needed = {section_id}
    # Also include sec_text and sec_config for analysis/rendering
    needed.add("sec_text")
    needed.add("sec_config")
    # Include meta tabs
    needed.add(f"{section_id}_meta")

    filtered = {}
    for key in needed:
        if key in tabs:
            filtered[key] = tabs[key]
    return filtered


def generate_section_stub(section_id: str, lang: str = "zh") -> str:
    """Generate a stub chart function for sections that don't have one yet."""
    order = SECTION_ORDER_ZH if lang == "zh" else SECTION_ORDER_EN
    title = "Unknown Section"
    for pair in order:
        if pair[0] == section_id:
            title = pair[1]
            break

    func_name = section_id_to_func_name(section_id)
    return f"""
function {func_name}(model) {{
  if (!model || !model.rowCount) return emptyStateChart(model);
  // TODO: Implement {section_id} chart — {title}
  var html = '<div class="muted" style="padding:16px;text-align:center;border:2px dashed var(--line);border-radius:8px">';
  html += '<strong>{title}</strong><br>';
  html += 'Section {section_id} — chart module not yet built.<br>';
  html += '<span style="font-size:11px">Data: ' + model.rowCount + ' rows, ' + model.header.length + ' columns</span>';
  html += '</div>';
  return html;
}}
"""


def section_id_to_func_name(section_id: str) -> str:
    """Convert section_id to JavaScript function name."""
    # sec_12m_history → historyStackedChart (special case)
    # sec_site_benchmark → siteBenchmarkChart
    # sec_l1_overview → l1OverviewChart
    special_cases = {
        "sec_12m_history": "historyStackedChart",
        "sec_site_benchmark": "siteBenchmarkChart",
        "sec_l1_overview": "l1OverviewChart",
        "sec_l1_matrix": "l1MatrixChart",
        "sec_l2_drill": "l2DrillChart",
        "sec_l3_granular": "l3GranularChart",
        "sec_volatility": "volatilityChart",
        "sec_shop_impact": "shopImpactChart",
        "sec_listing_change": "listingChangeChart",
        "sec_fulfillment": "fulfillmentChart",
        "sec_traffic_channel": "trafficChannelChart",
        "sec_subsidy": "subsidyChart",
        "sec_price_band": "priceBandChart",
        "sec_ams": "amsChart",
        "sec_root_cause": "rootCauseChart",
    }
    return special_cases.get(section_id, section_id.replace("sec_", "") + "Chart")


def build_section_list(section_arg: str, lang: str = "zh") -> List[str]:
    """Resolve section argument to list of section IDs. Supports comma-separated lists."""
    order = SECTION_ORDER_ZH if lang == "zh" else SECTION_ORDER_EN
    all_ids = [pair[0] for pair in order]

    if section_arg == "all":
        return all_ids

    # Support comma-separated list
    if "," in section_arg:
        parts = [s.strip() for s in section_arg.split(",")]
        result = []
        for part in parts:
            result.extend(build_section_list(part, lang))
        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for s in result:
            if s not in seen:
                seen.add(s)
                deduped.append(s)
        return deduped

    if section_arg in all_ids:
        return [section_arg]

    # Try prefix match
    matches = [s for s in all_ids if s.startswith(section_arg)]
    if matches:
        return matches

    raise ValueError(f"Unknown section: {section_arg}. Known: {', '.join(all_ids)}")


def generate_test_html(
    ggp: str,
    month: str,
    payload: dict,
    section_ids: List[str],
    lang: str = "zh",
) -> str:
    """
    Generate a standalone HTML file for testing one or more sections.

    For each section:
    - If a section module exists, load its chart function
    - Otherwise, generate a stub
    """
    engine = Engine(lang=lang)
    engine_js = engine.all_shared_js()

    # Filter payload to only needed tabs (include dependencies)
    all_tabs = payload.get("tabs", {})
    needed_tabs: dict = {"sec_text": all_tabs.get("sec_text", []),
                         "sec_config": all_tabs.get("sec_config", [])}
    for sid in section_ids:
        if sid in all_tabs:
            needed_tabs[sid] = all_tabs[sid]
        meta_id = f"{sid}_meta"
        if meta_id in all_tabs:
            needed_tabs[meta_id] = all_tabs[meta_id]
        # Include tab dependencies (sections that read from other tabs)
        for dep_id in TAB_DEPS.get(sid, []):
            if dep_id in all_tabs and dep_id not in needed_tabs:
                needed_tabs[dep_id] = all_tabs[dep_id]

    filtered_payload = {
        "sheetId": payload.get("sheetId", "test"),
        "sheetUrl": payload.get("sheetUrl", "#"),
        "tabs": needed_tabs,
    }
    local_data_json = json.dumps(filtered_payload, ensure_ascii=False, default=str)

    # Generate section JS
    section_js_parts = []
    for sid in section_ids:
        if sid in SECTION_REGISTRY:
            module_path, func_name = SECTION_REGISTRY[sid]
            # Dynamic import
            import importlib
            mod = importlib.import_module(module_path)
            fn = getattr(mod, func_name)
            section_js_parts.append(fn())
        else:
            section_js_parts.append(generate_section_stub(sid, lang))

    section_js = "\n".join(section_js_parts)

    # Also generate a modified renderReport that only builds the selected sections
    order = SECTION_ORDER_ZH if lang == "zh" else SECTION_ORDER_EN
    order_entries = [pair for pair in order if pair[0] in section_ids]
    order_json = str(order_entries).replace("'", '"')

    full_html = generate_shell(
        ggp=ggp,
        month=month,
        lang=lang,
        local_data_json=local_data_json,
        section_js=section_js,
    )

    # Replace the engine token
    full_html = full_html.replace("__ENGINE_JS__", engine_js)

    # Override section order to only include selected sections
    full_html = full_html.replace(
        f"window.AUTODECK_SECTION_ORDER = {{ order: {str(SECTION_ORDER_EN).replace(chr(39), chr(34))} }}.order;",
        f"window.AUTODECK_SECTION_ORDER = {order_json};"
    )
    # Also fix the ZH order
    zh_filtered = str([pair for pair in SECTION_ORDER_ZH if pair[0] in section_ids]).replace("'", '"')
    full_html = full_html.replace(
        f"window.AUTODECK_SECTION_ORDER_ZH = {str(SECTION_ORDER_ZH).replace(chr(39), chr(34))};",
        f"window.AUTODECK_SECTION_ORDER_ZH = {zh_filtered};"
    )

    # Replace GGP token
    full_html = full_html.replace("__GGP__", ggp.replace("'", "\\'"))

    return full_html


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AutoDeck Section Test Harness — render sections as standalone HTML for visual testing."
    )
    parser.add_argument("--section", required=True,
                        help="Section ID (e.g., sec_12m_history) or 'all'")
    parser.add_argument("--input-json", required=True,
                        help="Path to sheet_payload.json")
    parser.add_argument("--ggp", required=True,
                        help="GGP account name")
    parser.add_argument("--month", required=True,
                        help="Report month (YYYY-MM)")
    parser.add_argument("--output", required=True,
                        help="Output HTML file path")
    parser.add_argument("--lang", choices=["zh", "en"], default="zh",
                        help="Language (default: zh)")
    parser.add_argument("--open", action="store_true",
                        help="Open in browser after generation")
    args = parser.parse_args()

    try:
        payload = load_payload(args.input_json)
        section_ids = build_section_list(args.section, args.lang)
        print(f"Building test HTML for: {', '.join(section_ids)}")
        print(f"Data source: {args.input_json}")

        html = generate_test_html(
            ggp=args.ggp,
            month=args.month,
            payload=payload,
            section_ids=section_ids,
            lang=args.lang,
        )

        out_path = Path(args.output).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")
        print(f"Wrote {len(html):,} bytes → {out_path}")

        if args.open:
            subprocess.run(["open", str(out_path)], check=False)

        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
