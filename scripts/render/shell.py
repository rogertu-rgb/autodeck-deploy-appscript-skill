#!/usr/bin/env python3
"""
AutoDeck HTML Shell — produces the outer HTML structure (CSS, header, nav rail,
hero banner, footer). Section content and JavaScript are injected via tokens.
"""

from __future__ import annotations

import html
from datetime import datetime
from typing import Dict, List, Optional


SECTION_ORDER_ZH: List[List[str]] = [
    ["sec_12m_history", "12个月业绩概览"],
    ["sec_site_benchmark", "各站点增速对标大盘"],
    ["sec_l1_overview", "一级品类总览"],
    ["sec_l2_drill", "二级品类钻取"],
    ["sec_l3_granular", "三级品类粒度诊断"],
    ["sec_volatility", "类目站点异常信号扫描"],
    ["sec_shop_impact", "店铺贡献分析"],
    ["sec_listing_change", "Top商品贡献榜"],
    ["sec_fulfillment", "履约结构分析"],
    ["sec_traffic_channel", "订单来源拆分"],
    ["sec_subsidy", "促销补贴有效性"],
    ["sec_price_band", "价格带竞争定位"],
    ["sec_ams", "ADS出单效率审计"],
    ["sec_root_cause", "站点根因诊断"],
]

SECTION_ORDER_EN: List[List[str]] = [
    ["sec_12m_history", "12-Month Performance Overview"],
    ["sec_site_benchmark", "Site Momentum vs Market"],
    ["sec_l1_overview", "L1 Category Overview"],
    ["sec_l2_drill", "L2 Category Drilldown"],
    ["sec_l3_granular", "L3 Granular Diagnosis"],
    ["sec_volatility", "Category-Site Anomaly Signal Scan"],
    ["sec_shop_impact", "Shop Contribution Analysis"],
    ["sec_listing_change", "Top Listing Contributions"],
    ["sec_fulfillment", "Fulfillment Structure"],
    ["sec_traffic_channel", "Order Source Split"],
    ["sec_subsidy", "Promotion Effectiveness"],
    ["sec_price_band", "Price Band Positioning"],
    ["sec_ams", "ADS Order Efficiency Audit"],
    ["sec_root_cause", "Site-by-Site Root Cause Diagnosis"],
]


def section_order_js(lang: str = "zh") -> str:
    """Generate the SECTION_ORDER JavaScript arrays."""
    zh_json = str(SECTION_ORDER_ZH).replace("'", '"')
    en_json = str(SECTION_ORDER_EN).replace("'", '"')
    return f"""
window.AUTODECK_SECTION_ORDER = {{ order: {en_json} }}.order;
window.AUTODECK_SECTION_ORDER_ZH = {zh_json};
"""


def css_block() -> str:
    """Complete CSS stylesheet for the AutoDeck report."""
    return r"""<style>
:root {
  --bg: #f4f5f7;
  --surface: #ffffff;
  --surface-soft: #fafafa;
  --ink: #202124;
  --muted: #68707c;
  --muted-2: #8a919b;
  --line: #dfe3e8;
  --line-soft: #edf0f3;
  --accent: #ee4d2d;
  --accent-dark: #bd3d22;
  --accent-soft: #fff1ed;
  --up: #137a4b;
  --up-bg: #eaf7f0;
  --down: #b42318;
  --down-bg: #fff0ed;
  --warn: #9a6500;
  --warn-bg: #fff6dd;
  --shadow: 0 16px 40px rgba(32, 33, 36, .08);
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: Inter, "Noto Sans SC", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.5;
}
a { color: var(--accent-dark); text-decoration: none; }
a:hover { text-decoration: underline; }

/* ── Top bar ── */
.topbar {
  position: sticky; top: 0; z-index: 20;
  display: flex; justify-content: space-between; align-items: center; gap: 16px;
  padding: 12px 24px;
  background: rgba(255,255,255,.94);
  border-bottom: 1px solid var(--line);
  backdrop-filter: blur(12px);
}
.brand { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.brand strong { font-size: 15px; }
.brand span { color: var(--muted); font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.top-actions { display: flex; align-items: center; gap: 10px; }
.search {
  width: min(280px, 34vw);
  border: 1px solid var(--line); border-radius: 6px;
  background: var(--surface-soft); color: var(--ink);
  font: inherit; font-size: 12px; padding: 8px 10px; outline: none;
}
.search:focus { border-color: var(--accent); background: #fff; }
.link-button {
  border: 1px solid var(--line); background: #fff; color: var(--ink);
  border-radius: 6px; padding: 8px 10px; font-size: 12px; line-height: 1; white-space: nowrap;
}

/* ── Layout ── */
.shell { width: min(1440px, 100%); margin: 0 auto; padding: 20px 24px 32px; }
.layout { display: grid; grid-template-columns: 250px minmax(0, 1fr); gap: 16px; align-items: start; }

/* ── Hero ── */
.hero {
  background: var(--surface); border: 1px solid var(--line); border-radius: 8px;
  box-shadow: var(--shadow); padding: 20px 22px; margin-bottom: 16px;
}
.hero h1 { margin: 0 0 8px; font-size: clamp(22px, 3vw, 34px); letter-spacing: 0; line-height: 1.16; }
.hero-meta { display: flex; flex-wrap: wrap; gap: 8px; color: var(--muted); font-size: 12px; }
.pill { display: inline-flex; align-items: center; gap: 6px; border: 1px solid var(--line); background: var(--surface-soft); border-radius: 999px; padding: 4px 9px; }

/* ── Side nav ── */
.side {
  position: sticky; top: 72px; max-height: calc(100vh - 96px); overflow: auto;
  background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 10px;
}
.side-title { color: var(--muted); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; padding: 8px 8px 6px; }
.nav-item {
  display: grid; grid-template-columns: 24px minmax(0, 1fr); gap: 8px;
  width: 100%; border: 0; border-radius: 6px; background: transparent; color: var(--ink);
  cursor: pointer; padding: 8px; text-align: left; font: inherit; font-size: 12px;
}
.nav-item:hover, .nav-item.active { background: var(--accent-soft); color: var(--accent-dark); }
.nav-item span:first-child { color: var(--muted-2); font-variant-numeric: tabular-nums; }
.nav-item span:last-child { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* ── Executive summary ── */
.summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-bottom: 14px; }
.summary-card, .metric-card { border: 1px solid var(--line); border-radius: 8px; background: var(--surface); padding: 12px; }
.summary-card .label, .metric-card .label { color: var(--muted); font-size: 11px; font-weight: 650; text-transform: uppercase; letter-spacing: .05em; }
.summary-card .value, .metric-card .value { margin-top: 4px; font-size: 20px; font-weight: 760; line-height: 1.2; }
.summary-card .context, .metric-card .context { margin-top: 4px; color: var(--muted); font-size: 12px; min-height: 18px; }
.summary-card.up { border-left: 3px solid var(--up); }
.summary-card.dn { border-left: 3px solid var(--down); }
.summary-card.warn { border-left: 3px solid var(--warn); }

/* ── Gate strip ── */
.gate-grid { margin-bottom: 14px; }
.gate-chip { display: inline-flex; align-items: center; gap: 6px; border: 1px solid var(--line); border-radius: 20px; padding: 4px 12px; margin: 4px; font-size: 11px; }
.gate-chip.triggered { background: var(--warn-bg); border-color: var(--warn); }

/* ── Narrative ── */
.narrative { background: linear-gradient(135deg, #f8f5f0, #fff); border: 1px solid var(--line); border-radius: 8px; padding: 16px 18px; margin-bottom: 12px; font-size: 13px; line-height: 1.8; }
.narrative strong { color: var(--accent-dark); }

/* ── Sections ── */
.report-stack { display: flex; flex-direction: column; gap: 14px; }
.sec { background: var(--surface); border: 1px solid var(--line); border-radius: 8px; overflow: hidden; box-shadow: 0 6px 20px rgba(32, 33, 36, .04); }
.sec.filtered { display: none; }
.sec:not(.open) .sec-body { display: none; }
.sec-head {
  display: grid; grid-template-columns: minmax(0, 1fr) auto auto; gap: 8px; align-items: center;
  width: 100%; border: 0; background: transparent; color: var(--ink);
  cursor: pointer; padding: 12px 16px; text-align: left; font: inherit; font-size: 13px;
}
.sec-head:hover { background: var(--surface-soft); }
.sec-title { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sec-title strong { font-size: 14px; }
.sec-title span { color: var(--muted); font-size: 11px; margin-left: 8px; }
.status-chip { font-size: 10px; padding: 2px 6px; border-radius: 10px; background: var(--line-soft); color: var(--muted); white-space: nowrap; }
.chev { color: var(--muted-2); font-size: 14px; transition: transform .18s ease; }
.sec.open .chev { transform: rotate(90deg); }

.sec-body { padding: 0 16px 16px; }
.analysis { background: var(--surface-soft); border-left: 3px solid var(--accent); border-radius: 4px; padding: 12px 14px; margin: 10px 0; font-size: 13px; }
.analysis-label { color: var(--muted); font-size: 10px; font-weight: 700; text-transform: uppercase; margin-bottom: 4px; }
.analysis-callout-line { list-style: none; margin-left: -18px; display: flex; align-items: flex-start; gap: 8px; }
.analysis-callout-marker { display: inline-grid; place-items: center; width: 20px; height: 20px; border-radius: 50%; background: var(--accent); color: #fff; font-weight: 900; font-size: 11px; line-height: 1; flex: 0 0 20px; margin-top: 2px; }
.analysis-callout-text { flex: 1; min-width: 0; }

/* ── Evidence ── */
.evidence-strip { display: flex; flex-wrap: wrap; gap: 6px; padding: 8px 0; }
.evidence-btn {
  display: inline-block; border: 1px solid var(--line); border-radius: 4px;
  background: #fff; padding: 3px 8px; font-size: 11px; cursor: pointer;
  transition: all .15s ease;
}
.evidence-btn:hover { transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,0,0,.06); }

/* ── Tables ── */
.report-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.report-table th, .report-table td { padding: 6px 10px; border-bottom: 1px solid var(--line-soft); text-align: right; white-space: nowrap; }
.report-table th { background: var(--surface-soft); color: var(--muted); font-size: 11px; font-weight: 700; text-align: right; position: sticky; top: 0; }
.report-table td:first-child, .report-table th:first-child { text-align: left; }
.source-data { margin-top: 8px; }
.source-data summary { cursor: pointer; font-size: 12px; color: var(--muted); padding: 4px 0; }
.row-hit { background: #fffde7 !important; }
.cell-hit { background: #ffecb3 !important; box-shadow: 0 0 0 2px var(--accent); }

/* ── Data tones ── */
.up-text { color: var(--up); font-weight: 650; }
.dn-text { color: var(--down); font-weight: 650; }
.warn-text { color: var(--warn); font-weight: 650; }

/* ── Muted / empty ── */
.empty, .muted { color: var(--muted); text-align: center; padding: 24px; }
.muted { font-size: 12px; }

/* ── Footer / Provenance ── */
.footer { color: var(--muted); font-size: 11px; margin-top: 22px; }
.provenance { border-top: 1px solid var(--line); margin-top: 24px; padding: 12px 0; color: var(--muted); font-size: 11px; line-height: 1.7; }
.provenance a { color: var(--accent-dark); }
.shop-id { font-family: monospace; font-size: 11px; color: var(--muted); }

/* ── Chart interaction ── */
.chart-svg [title] { cursor: pointer; }
.chart-svg [title]:hover { opacity: .85; }
.heatmap-cell { cursor: pointer; transition: outline .15s ease; }
.heatmap-cell:hover { outline: 2px solid rgba(238,77,45,.5); }

/* ── Accessibility ── */
.sec-head:focus-visible, .nav-item:focus-visible, .evidence-btn:focus-visible { outline: 2px solid #ee4d2d; outline-offset: 2px; }

/* ── Responsive ── */
@media (max-width: 980px) {
  .layout { grid-template-columns: 1fr; }
  .side { position: static; max-height: none; }
  .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .evidence-strip { grid-template-columns: 1fr; }
}
@media (max-width: 720px) {
  .topbar { align-items: stretch; flex-direction: column; padding: 12px 14px; }
  .top-actions { align-items: stretch; }
  .search { width: 100%; }
  .shell { padding: 14px; }
  .hero { padding: 16px; }
  .sec-head { grid-template-columns: minmax(0, 1fr) auto; }
  .status-chip { display: none; }
  .summary-grid { grid-template-columns: 1fr; }
}

/* ── Print ── */
@media print {
  .topbar, .side, .search, .link-button, .gate-grid, .source-data summary { display: none !important; }
  .layout { display: block !important; }
  .shell { max-width: 100%; padding: 0; }
  .sec { break-inside: avoid; border: 1px solid #ccc; box-shadow: none; margin-bottom: 12px; }
  .sec.open .sec-body, .sec-body { display: block !important; }
  body { font-size: 11px; color: #000; background: #fff; }
  .analysis { border-left: 2px solid #000; }
  .hero { border: none; box-shadow: none; padding: 8px 0; }
}
</style>"""


def html_body_open(ggp: str, month: str, lang: str = "zh") -> str:
    """Generate the body opening: topbar, hero, layout start, side rail."""
    escaped_ggp = html.escape(ggp)
    escaped_month = html.escape(month)
    return f"""
<body>
<div class="topbar">
  <div class="brand">
    <strong>AutoDeck</strong>
    <span id="seller-info">{escaped_ggp} · {escaped_month}</span>
  </div>
  <div class="top-actions">
    <input id="section-search" class="search" type="search" placeholder="{ '搜索板块...' if lang == 'zh' else 'Search sections...' }" aria-label="{ '搜索板块' if lang == 'zh' else 'Search sections' }">
    <span id="sheet-link"></span>
  </div>
</div>

<div class="shell">
  <!-- Hero -->
  <div class="hero">
    <h1>{escaped_ggp}</h1>
    <div class="hero-meta">
      <span class="pill">📅 {escaped_month}</span>
      <span class="pill">📊 <span id="hero-rows">—</span> rows</span>
      <span class="pill">📋 <span id="hero-sections">—</span> sections</span>
      <span class="pill" id="hero-refresh">Data: Shopee DWS (D-1)</span>
    </div>
  </div>

  <!-- Executive summary -->
  <div id="summary-grid" class="summary-grid"></div>
  <div id="gate-grid" class="gate-grid"></div>

  <div class="layout">
    <!-- Left rail -->
    <nav class="side" aria-label="{ '板块导航' if lang == 'zh' else 'Section navigation' }">
      <div class="side-title">{ '报告板块' if lang == 'zh' else 'Report Sections' }</div>
      <div id="section-nav-list"></div>
    </nav>

    <!-- Main report -->
    <div id="report-root" class="report-stack" data-contract="Data display first">
      <div class="empty">{ '正在加载报告数据...' if lang == 'zh' else 'Loading report data...' }</div>
    </div>
  </div>

  <!-- Footer -->
  <div class="footer">
    <div class="provenance">
      <strong>Data:</strong> AutoDeck v_0602 · Source: Shopee DWS (D-1) · Generated: __TIMESTAMP__<br>
      <strong>Methodology:</strong> All benchmark comparisons use MoM% and share% only. No absolute market values are exposed.
      Refresh via AutoDeck for latest D-1 data.
    </div>
  </div>
</div>
"""


def boot_script(lang: str = "zh") -> str:
    """Generate the boot/initialization JavaScript."""
    lang_flag = '"zh"' if lang == "zh" else '"en"'
    return r"""
<script>
window.AUTODECK_LANG = """ + lang_flag + r""";
window.AUTODECK_GGP = "__GGP__";

function loadReport() {
  if (window.google && google.script && google.script.run) {
    var rendered = false;
    var timer = setTimeout(function() {
      if (!rendered) { rendered = true; renderFallback("server callback timeout"); }
    }, 5000);
    google.script.run
      .withSuccessHandler(function(payload) {
        if (rendered) return;
        rendered = true; clearTimeout(timer);
        try { renderReport(payload); }
        catch(err) { renderFallback("render exception"); }
      })
      .withFailureHandler(function(err) {
        if (rendered) return;
        rendered = true; clearTimeout(timer);
        renderFallback("server failure");
      })
      .loadAutodeckData();
  } else {
    renderFallback("local preview");
  }
}

function renderFallback(reason) {
  console.log("AutoDeck fallback render:", reason);
  if (window.AUTODECK_LOCAL_DATA && window.AUTODECK_LOCAL_DATA.tabs) {
    renderReport(window.AUTODECK_LOCAL_DATA);
  }
}

// Boot: render from embedded data immediately
(function boot() {
  if (window.AUTODECK_LOCAL_DATA && window.AUTODECK_LOCAL_DATA.tabs) {
    try { renderReport(window.AUTODECK_LOCAL_DATA); }
    catch(e) {
      document.getElementById("report-root").innerHTML =
        '<div class="empty" style="color:red;padding:20px">Render Error: ' + e.message +
        '<br><pre style="font-size:10px">' + (e.stack||'').slice(0,500) + '</pre></div>';
    }
  }
})();

// Deferred: try live load
setTimeout(function() { loadReport(); }, 2000);

// Failsafe
setTimeout(function(){
  try {
    if (window.AUTODECK_LOCAL_DATA && window.AUTODECK_LOCAL_DATA.tabs && typeof renderReport === "function") {
      var root = document.getElementById("report-root");
      if (root && !root.querySelector(".sec")) { renderReport(window.AUTODECK_LOCAL_DATA); }
    }
  } catch(e) {
    document.getElementById("report-root").innerHTML = '<div class="empty" style="color:red">Error: ' + e.message + '</div>';
  }
}, 800);
</script>
"""


def generate_shell(
    ggp: str,
    month: str,
    lang: str = "zh",
    local_data_json: str = "{}",
    section_js: str = "",
    title: Optional[str] = None,
) -> str:
    """
    Generate a complete standalone HTML shell with all shared infrastructure.

    Args:
        ggp: GGP account name
        month: Report month (YYYY-MM)
        lang: 'zh' or 'en'
        local_data_json: JSON string of sheet payload for embedded data
        section_js: Injected section-specific JavaScript (chart functions)
        title: Page title (defaults to "AutoDeck - {ggp} - {month}")

    Returns:
        Complete HTML document string
    """
    if title is None:
        title = f"AutoDeck - {ggp} - {month}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""<!DOCTYPE html>
<html lang="{ 'zh-CN' if lang == 'zh' else 'en' }">
<head>
<meta charset="UTF-8">
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
{css_block()}
</head>
{html_body_open(ggp, month, lang).replace('__TIMESTAMP__', timestamp)}

<script>
window.AUTODECK_LOCAL_DATA = {local_data_json};
{section_order_js(lang)}
</script>

<script>
// ═══ ENGINE: shared utilities — generated by render/engine.py ═══
__ENGINE_JS__
</script>

<script>
// ═══ SECTIONS: per-section chart functions — generated by render/section_*.py ═══
{section_js}
</script>

{boot_script(lang)}
</body>
</html>"""
