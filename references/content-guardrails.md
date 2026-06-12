# Content Guardrails

Use these rules for the generated seller-facing HTML.

## Section Structure

Every section follows:

```text
Title
Subtitle / trigger status
Data display: compact evidence cards, chart, table, or expandable full data
Analysis block with generated takeaways
Expandable source table when raw rows are available
```

Data must appear before analysis. If the raw table is collapsed, a compact evidence snapshot can satisfy the data-first rule as long as every analysis claim links to same-section source rows. If a section has no data, show a visible empty-state note before analysis.

Metric cards or raw/filterable tables alone do not satisfy the data display requirement. Each section must show a chart-like primary visual before the analysis block, then a filterable important-row table as supporting evidence when rows exist.

Section 1 (`sec_12m_history`) must use the visit-reference screenshot pattern: one monthly stacked bar per period, site ADG contributions as colored stacks, total ADG labels above bars, date labels on the x-axis, and a site legend. Do not use a dual-axis or bar-plus-line chart for this section.

## Evidence Rule

Every numeric claim in analysis should be traceable to visible data in the same section. Cross-section jumps are only allowed in the executive summary. Section analysis may mention another section as plain text, but should not call `jumpTo(...)`.

Do not render raw `{placeholder}` analysis templates from `sec_text` as seller-facing copy. Treat those templates as an analysis framework only; generated bullets must substitute real values from section rows.

## Gate Rule

Show all storyline gate decisions in the executive area. If explicit gate tabs are missing, derive gate state from approved section rows and show both triggered and reference gates with their reason.

## Highlighting

- Positive values use `.up`.
- Negative or risk values use `.dn` or `.warn`.
- Values referenced in analysis should have matching table emphasis where practical.

## Benchmark Rule

Never expose market benchmark absolute values in seller-facing HTML. Use relative values only: MoM%, share%, growth percentile, gap pp, or seller count.

## Visual V1

The renderer should feel like a working seller-visit diagnosis report: dense, scan-friendly, restrained, and tied to evidence. Use compact cards, clear section hierarchy, and table disclosure controls rather than long raw tables as the first thing users read.
