---
name: autodeck-deploy-appscript
description: Generate and publish a complete AutoDeck seller visit diagnosis HTML report to Google Apps Script from a local OAuth credential and a GGP account name. Use when a user asks to run AutoDeck end-to-end, create a seller monthly diagnosis HTML, publish a seller visit report, deploy AutoDeck to App Script, or generate an AutoDeck report from v_0602/Future Architecture materials. The workflow validates OAuth, pulls or reuses raw AutoDeck data, creates or reuses a Google Sheet, runs the existing build_sections.py section builder, renders a Sheet-backed HTML report, runs guardrail checks, and deploys Code.gs/Index.html/appsscript.json through the Apps Script API.
version: 0.2.0
---

# AutoDeck Deploy AppScript

## Overview

This skill runs the AutoDeck Future Architecture flow as one deployable pipeline:

```text
OAuth + GGP name
  -> resolve/search exact GGP account name when the input is a query or partial name
  -> 3 fixed raw data pulls through DataService SDK
  -> Google Sheet raw tabs
  -> build_sections.py section tabs
  -> Sheet-backed HTML (auto_html_0602 modular render engine)
  -> QA checks
  -> Apps Script Web App URL
```

Default user-facing goal: the user should be able to provide a local OAuth file, the GGP account name or query they are visiting, and a `YYYY-MM` month, then wait for the published seller diagnosis report URL.

## Render Engine Architecture (v0.2.0)

The HTML renderer is the `auto_html_0602` modular, section-by-section system. Production `scripts/render_html.py` is only a compatibility wrapper around the shared shell, engine, and section modules; do not let it drift into a separate monolithic renderer.

```
scripts/render/
├── __init__.py           # Module exports
├── engine.py             # Shared JS generator (15 method groups, ~31KB valid JS)
├── shell.py              # HTML shell: CSS, layout, boot flow, Apps Script fallback
├── test_harness.py       # Single-section visual test tool
├── section_1_0.py        # 12M History — stacked bar chart ✅
├── section_1_1.py        # Site Benchmark — MoM% grouped bar
└── ...                   # 14 more section modules
```

**Key principles:**
- One section = one file — a bug in section 1.6 can't corrupt section 1.0
- Shared engine — `esc()`, `safeDisplay()`, `formatValue()`, `rowsModel()` defined once
- Test harness — `--section sec_12m_history` renders standalone HTML for visual testing
- Section registry — each section auto-registers via `SECTION_REGISTRY` in test_harness.py
- Golden baseline — match both visual style and interaction model from the bundled golden-contract reference or a user-provided golden report artifact
- Interaction parity — preserve search, side rail navigation, section accordion, evidence-chip source highlighting, collapsible source tables, ECharts resize lifecycle, embedded data fallback, and Apps Script live loading
- Analysis parity — use `references/section-analysis-harness.md` to generate actual data-derived findings per section; never print `sec_text` template directions or unfilled placeholders as analysis

**Bundled build logic:** `scripts/section_builder/build_sections.py`

## Quick Start

Use the orchestrator:

```bash
python3 scripts/autodeck_run.py \
  --oauth "$AUTODECK_GOOGLE_OAUTH" \
  --ggp "浙江格蕾美电子商务有限公司 - GGP" \
  --month 2026-06
```

If the data source is not ready but an existing Sheet already has `raw_dws_shop`, `raw_benchmark`, and `raw_dws_item`, use:

```bash
python3 scripts/autodeck_run.py \
  --oauth "$AUTODECK_GOOGLE_OAUTH" \
  --ggp "浙江格蕾美电子商务有限公司 - GGP" \
  --month 2026-06 \
  --sheet-id "<existing_sheet_id>" \
  --data-mode existing-sheet
```

Outputs are written under `outputs/autodeck_runs/<timestamp>/` unless `--output-dir` is provided.

## Required Inputs

- `--oauth`: local authorized-user OAuth JSON with these scopes:
  - `https://www.googleapis.com/auth/spreadsheets`
  - `https://www.googleapis.com/auth/script.projects`
  - `https://www.googleapis.com/auth/script.deployments`
- `--ggp`: exact GGP account name.
- `--month`: report month as `YYYY-MM`. If omitted, the current month is used.
- DataService SDK credentials for raw extraction. The helper resolves them from CLI args, environment variables, optional JSON config, or Tech Reference v_0602 section 11.

Optional DataService overrides:

- `--dataservice-config`
- `--dataservice-app-key`
- `--dataservice-app-secret`
- `--dataservice-api-name`
- `--dataservice-api-version`
- `--dataservice-base-url`
- `--dataservice-queue`
- `--dataservice-end-user`

Recommended environment variables for GitHub installs:

- `AUTODECK_GOOGLE_OAUTH`: path to local Google authorized-user OAuth JSON
- `AUTODECK_DATASERVICE_APP_KEY`: DataService app key
- `AUTODECK_DATASERVICE_APP_SECRET`: DataService app secret
- `AUTODECK_DATASERVICE_END_USER`: DataService end-user identity, if required by the API
- `AUTODECK_TECH_REFERENCE`: optional local Tech Reference file if credentials are stored there
- `AUTODECK_BRIDGE`: optional DataSuite bridge path for debug-only bridge mode

Use `.env.example` or `config/dataservice.example.json` as templates. Never commit populated OAuth files, token files, or DataService app secrets.

## Architecture Rules

Follow `references/future-architecture.md`:

1. L2 data pull only writes raw tabs: `raw_dws_shop`, `raw_benchmark`, `raw_dws_item`.
2. L3 only runs the existing section builder. Do not reimplement pivot logic in conversation.
3. L4 reads section tabs plus `sec_text` and `sec_config`; it does not query Hive.
4. Apps Script deployment always happens after the Sheet exists, because `Code.gs` needs the final `SHEET_ID`.

## Workflow

### 1. Preflight

Run `scripts/oauth_check.py` before doing real work. If scopes are missing, stop and ask the user to re-authorize. Do not continue to data pull.

### 2. Raw Data

Preferred current path:

- In SDK mode, `scripts/query_raw_data.py` resolves `--ggp` before pulling raw data: exact match first, then partial-name lookup against `autodeck__dws_shop_rpt_mi` for the report month and prior month. If multiple plausible accounts match, stop with candidates instead of silently choosing.
- If `--sheet-id` is provided and raw tabs exist, reuse it.
- Otherwise use `scripts/query_raw_data.py` with the DataService SDK backend from `references/dataservice-sdk-contract.md`.

The SDK path follows Tech Reference v_0602 section 11, "SDK — DataService API (Skill 专用数据通道)". It directly calls the authorized DataService API and writes the same raw CSV artifacts as before.

Fallback path:

- `--data-mode bridge` remains available only for debugging or emergency fallback.
- Do not use the DataSuite Chrome bridge as the normal skill path.

### 3. Sheet

Use `scripts/create_report_sheet.py` to create or reuse a Google Sheet and write raw tabs. Sheet tabs are values, not formulas.

### 4. Build

Use `scripts/build_sections_adapter.py`. It imports the bundled `scripts/section_builder/build_sections.py`, patches its credential path from `--oauth`, and calls `run_all(...)`.

### 5. Render

**Production path:** Use `scripts/render_html.py` to generate `Index.html`. This file must delegate to `scripts/render/shell.py`, `scripts/render/engine.py`, and `scripts/render/section_*.py`. The HTML calls `google.script.run.loadAutodeckData()` in Apps Script, with an embedded local snapshot as fallback for local preview.

**Section-by-section testing path:** Use `scripts/render/test_harness.py` to test individual sections before integration:

```bash
# Test one section as standalone HTML
python3 scripts/render/test_harness.py \
  --section sec_12m_history \
  --input-json <sheet_payload.json> \
  --ggp "浙江格蕾美" --month 2026-05 \
  --output /tmp/test.html --open

# Test all sections
python3 scripts/render/test_harness.py \
  --section all \
  --input-json <sheet_payload.json> \
  --ggp "浙江格蕾美" --month 2026-05 \
  --output /tmp/test_all.html
```

The test harness uses the modular `render/engine.py` (shared JS) and `render/shell.py` (HTML shell) plus per-section chart modules. Each section gets a stub until its module is built.

**Section module pattern:**
```python
# scripts/render/section_X_Y.py
def build_section_js() -> str:
    """Return the complete JS for this section's chart + analysis."""
    ...

SECTION_ID = "sec_12m_history"
FUNC_NAME = "historyStackedChart"

# Register in test_harness.py SECTION_REGISTRY
```

The renderer must follow `references/report-interaction-and-analysis-contract.md`:

- show a professional seller-visit report shell with sticky header, section rail, section search, storyline gate decisions, chart/table visuals, compact evidence cards, generated takeaways, and collapsible source tables
- expose all storyline gate decisions in the executive area, even if the source Sheet does not include a literal `Gate Config` tab; derive gate state from `sec_site_benchmark`, `sec_l1_overview`, and `sec_subsidy`
- render each section with a chart-like primary visual before analysis; metric cards or raw/filterable tables alone are not sufficient
- render `sec_12m_history` as a screenshot-style monthly stacked bar chart by site ADG contribution with total labels, date labels, and site legend; do not use a dual-axis bar/line chart for this section
- keep a visible filterable important-row table after the primary visual as supporting evidence, not as the primary visual fallback
- use the section analysis framework to generate actual bullet points from numeric section rows, not raw placeholder text from `sec_text`
- make every generated takeaway traceable to a same-section evidence chip that highlights the source row and metric in the table
- keep full raw tables available as supporting evidence, but do not let raw tables become the primary report experience

It must also follow `references/auto-html-0602-golden-contract.md`: the Maisifang golden report is the reference for both formatting and JS interaction behavior, not only colors or chart choices.

For analysis content, it must follow `references/section-analysis-harness.md`: each section has deterministic findings derived from rows/meta tabs, including Section 2.3 site-level synthesis. `sec_text` is not a render source for visible analysis.

### 6. Validate

Run `scripts/validate_report.py`. Any failure blocks deployment unless the user explicitly asks to deploy a broken test artifact.

Core checks:

- no internal section codes in visible copy
- data blocks come before analysis blocks
- no cross-section links inside section analysis
- computed analysis is present and raw `sec_text` template filling is absent
- golden auto_html_0602 shell interactions are present: section search, side rail, accordion toggles, evidence focus/highlight, source tables, ECharts init/ResizeObserver, summary grid, gate strip, embedded fallback, and Apps Script live load
- `appsscript.json` uses `webapp.access = DOMAIN`
- `Code.gs` has the correct `SHEET_ID`
- generated HTML can render from a local data snapshot

### 7. Deploy

Use `scripts/deploy_appscript.py`. It creates a new Apps Script project, uploads:

- `appsscript` manifest
- `Code` server JS
- `Index` HTML

Then creates a version and deployment. Return both:

- Google Sheet URL
- Apps Script Web App URL

## Important References

- `references/future-architecture.md`: layer contract and Sheet-as-state model.
- `references/dataservice-sdk-contract.md`: SDK-only raw data extraction contract.
- `references/data-contract.md`: raw tabs, section tabs, and benchmark exposure rules.
- `references/appscript-deploy-contract.md`: OAuth, manifest, and deployment details.
- `references/content-guardrails.md`: seller-facing report guardrails.
- `references/report-interaction-and-analysis-contract.md`: report formatting, interaction, and evidence-linked analysis requirements.
- `references/auto-html-0602-golden-contract.md`: golden Maisifang HTML baseline and required interaction components.
- `references/section-analysis-harness.md`: per-section computed-analysis rules from Obsidian Section Design v_0602.
- `references/failure-recovery.md`: known failure modes from prior deployments.

## Boundaries

- Do not write new analytical SQL when the user asks for a standard AutoDeck report.
- Do not modify `scripts/section_builder/build_sections.py` unless the user explicitly asks to change the product logic.
- Do not expose Shopee/CNCB benchmark absolute values in seller-facing HTML. Use MoM%, share%, growth percentile, gap pp, or seller count only.
- If a new section or metric is needed, stop and flag it as BI/product logic work.
