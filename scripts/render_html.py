#!/usr/bin/env python3
"""Render the AutoDeck Apps Script Index.html report.

Production uses the modular auto_html_0602 renderer:

- render/shell.py owns the report chrome, boot flow, and Apps Script fallback.
- render/engine.py owns shared interaction and analysis helpers.
- render/section_*.py owns each section's chart/table module.

This file stays as the compatibility entrypoint used by autodeck_run.py.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from render.engine import Engine
from render.shell import SECTION_ORDER_EN, SECTION_ORDER_ZH, generate_shell
from render.test_harness import SECTION_REGISTRY, generate_section_stub
from sheet_sections_to_json import read_sheet_payload


def _safe_json(data: Dict[str, Any]) -> str:
    """Embed JSON safely inside an HTML script block."""
    return json.dumps(data, ensure_ascii=False, default=str).replace("</", "<\\/")


def _section_ids(lang: str = "zh") -> List[str]:
    order = SECTION_ORDER_ZH if lang == "zh" else SECTION_ORDER_EN
    return [section_id for section_id, _title in order]


def _section_js(section_ids: List[str], lang: str = "zh") -> str:
    """Load the per-section chart functions used by the shared renderer."""
    parts: List[str] = []
    for section_id in section_ids:
        if section_id not in SECTION_REGISTRY:
            parts.append(generate_section_stub(section_id, lang))
            continue
        module_path, function_name = SECTION_REGISTRY[section_id]
        module = importlib.import_module(module_path)
        parts.append(getattr(module, function_name)())
    return "\n".join(parts)


def render_index_html(payload: Dict[str, Any], ggp: str, month: str, lang: str = "zh") -> str:
    """Return a complete Apps Script Index.html document."""
    section_ids = _section_ids(lang)
    html = generate_shell(
        ggp=ggp,
        month=month,
        lang=lang,
        local_data_json=_safe_json(payload),
        section_js=_section_js(section_ids, lang),
    )
    return (
        html.replace("__ENGINE_JS__", Engine(lang=lang).all_shared_js())
        .replace("__GGP__", ggp.replace("\\", "\\\\").replace("'", "\\'"))
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Render AutoDeck Index.html.")
    parser.add_argument("--oauth")
    parser.add_argument("--sheet-id")
    parser.add_argument("--input-json", help="Use an existing sheet payload JSON instead of reading Sheets.")
    parser.add_argument("--ggp", required=True)
    parser.add_argument("--month", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--lang", choices=["zh", "en"], default="zh")
    args = parser.parse_args()

    if args.input_json:
        payload = json.loads(Path(args.input_json).expanduser().resolve().read_text(encoding="utf-8"))
    else:
        if not args.oauth or not args.sheet_id:
            raise SystemExit("--oauth and --sheet-id are required unless --input-json is used")
        payload = read_sheet_payload(args.oauth, args.sheet_id)

    out = Path(args.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_index_html(payload, args.ggp, args.month, lang=args.lang), encoding="utf-8")
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
