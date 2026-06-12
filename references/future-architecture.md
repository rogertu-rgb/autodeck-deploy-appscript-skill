# Future Architecture Summary

Use this reference when running or modifying the skill pipeline.

## Layer Contract

The AutoDeck pipeline has four layers:

```text
L1 Hive RPT tables
  -> L2 fixed raw data pull
  -> L3 Python section builder
  -> L4 Sheet-backed HTML and Apps Script deployment
```

Each layer only depends on the immediately lower layer:

- L2 reads three AutoDeck RPT tables and writes raw Google Sheet tabs.
- L3 reads raw tabs and writes section tabs plus `sec_text` and `sec_config`.
- L4 reads section tabs, `sec_text`, and `sec_config`; it never queries Hive.
- Apps Script hosts the HTML and uses `SpreadsheetApp.openById(SHEET_ID)` to load live Sheet content.

## Sheet As Shared State

The report Sheet is both data store and content management surface.

Required raw tabs:

- `raw_dws_shop`
- `raw_benchmark`
- `raw_dws_item`

Required L3 output tabs:

- section tabs, currently `sec_*`
- `sec_text`
- `sec_config`

Optional L4 writeback tabs:

- `Chart Registry`
- `Gate Config`
- `Feedback Log`

## Execution Dependency

Create/write the Sheet before rendering or deploying Apps Script. `Code.gs` must contain the final `SHEET_ID`; deploying before Sheet creation produces an empty report.

## Replaceable Pieces

- DataSuite bridge can be replaced by an MCP query tool if it preserves the raw tab contract.
- HTML style can be replaced if the section/data/analysis contract remains intact.
- Apps Script can be replaced by another host if it preserves live access to the Sheet state.
