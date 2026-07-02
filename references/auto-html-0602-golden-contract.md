# auto_html_0602 Golden Contract

The report target is not just a visual theme. It is the full AutoDeck HTML product shell plus the interaction model from:

a user-provided golden report artifact such as `outputs/autodeck_runs/<seller_month>/sections_review.html`

Use that file, its payload, and its generated JS structure as the quality bar when editing the Apps Script HTML skill.

## Required Composition

Production `scripts/render_html.py` must stay a compatibility wrapper over the modular renderer:

- `scripts/render/shell.py`: page chrome, CSS, sticky topbar, side rail, boot script, Apps Script live loader, local fallback.
- `scripts/render/engine.py`: shared JS utilities, section model building, summary/gate derivation, evidence chips, source table highlighting, nav/search/accordion binding.
- `scripts/render/section_*.py`: one chart/table module per section.
- `scripts/render/test_harness.py`: standalone visual and behavior harness for one section or all sections.

Do not rebuild a second monolithic renderer unless the user explicitly asks for a rewrite. Production and harness should share the same shell and engine.

## Required Interactions

Every generated report must include:

- Sticky topbar with seller/month context, Sheet link, and `#section-search`.
- Desktop side navigation with `data-target-section` buttons that open and scroll to the section.
- Accordion sections with `data-toggle-section` and correct open/closed body behavior.
- Executive `summary-grid` and `gate-grid`; expose triggered and untriggered storyline gates.
- Section-level primary chart/visual before analysis.
- Visible important-row support table after the primary visual.
- Evidence chips generated from the same section's numeric rows.
- Evidence click behavior through `focusEvidence(...)`: open the source table, scroll to the row, and highlight the exact cell when possible.
- Collapsible `<details class="source-data">` tables for auditability.
- ECharts lifecycle that waits for DOM width, disposes prior instances, initializes with `echarts.init`, and uses `ResizeObserver` for responsive charts.
- Embedded `AUTODECK_LOCAL_DATA` render, `google.script.run.loadAutodeckData()` live load, and a timeout/failsafe fallback.

## Visual/Content Baseline

- Keep the compact Shopee seller-visit report feel: dense, operational, and evidence-first.
- Section 1.0 must use the screenshot-style monthly stacked bar by site ADG with total labels and site legend, not a dual-axis chart.
- Do not allow metric cards or raw/filterable tables to become the only visual for a section.
- Do not expose raw JSON, placeholder `sec_text`, internal task codes, or absolute market benchmark values.
- Generated analysis must turn the section data into actual seller-facing takeaways and keep claims evidence-linked.

## Local Regression Command

Use this payload for quick regression:

```bash
python3 scripts/render_html.py \
  --input-json outputs/autodeck_runs/<seller_month>/sheet_payload.json \
  --ggp "深圳市迈四方科技有限公司 - GGP" \
  --month 2026-06 \
  --output /tmp/autodeck_index.html \
  --lang zh

python3 scripts/validate_report.py \
  --html /tmp/autodeck_index.html \
  --json
```

If the output visually or behaviorally drifts from the golden file, fix the modular shell/engine/section module rather than adding one-off HTML in `render_html.py`.
