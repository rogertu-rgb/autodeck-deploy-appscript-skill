#!/usr/bin/env python3
"""
Section 1.1 — Site Attribution vs Market Benchmark (当前月站点归因)

NO benchmark absolute values. MoM% comparison only.

Visual:
  - Current-month priority dumbbell sorted by |ADG gap pp| × ADG share.
  - Equal-size Market/Seller dots to avoid misleading scale.
  - Thin gap bridge, colored by out/under-performance.
  - Numbered callouts link top evidence rows to computed-analysis bullets.

Data source: sec_site_benchmark. raw_benchmark_site must use Total-dimension
site benchmark rows from autodeck__site_bu_benchmark_rpt.
"""

from __future__ import annotations


def site_benchmark_chart_js() -> str:
    return r"""
function siteBenchmarkChart(model) {
  if (!model || !model.body.length) return emptyStateChart(model);

  function firstNum(item, names) {
    for (var i = 0; i < names.length; i++) {
      var v = num(item, names[i]);
      if (v != null) return v;
    }
    return null;
  }

  function signedPpLocal(v) {
    if (v == null) return "—";
    return (v > 0 ? "+" : "") + formatCompact(v) + "pp";
  }

  function signedPctLocal(v) {
    if (v == null) return "—";
    return (v > 0 ? "+" : "") + formatCompact(v) + "%";
  }

  function perfTag(gap) {
    if (gap == null) return "不可对标";
    if (gap >= 5) return "跑赢大盘";
    if (gap <= -5) return "跑输大盘";
    return "接近大盘";
  }

  function perfColor(gap) {
    if (gap == null) return "#9ca3af";
    if (gap >= 5) return "#1f8f58";
    if (gap <= -5) return "#d83a2e";
    return "#737373";
  }

  function svgText(s) {
    return esc(String(s == null ? "" : s));
  }

  // ── 1. Extract current-month attribution rows ──
  var rows = [];
  model.body.forEach(function(item) {
    var site = String(val(item, "site") || "").trim();
    if (!site) return;
    var seller = num(item, "seller_adg_mom");
    var market = firstNum(item, ["mom_mkt_adg_pct", "mkt_adg_mom"]);
    var gap = num(item, "adg_gap_pp");
    var share = num(item, "adg_share") || 0;
    var adg = num(item, "adg_mtd") || 0;
    var sellerAdo = num(item, "seller_ado_mom");
    var marketAdo = firstNum(item, ["mom_mkt_ado_pct", "mkt_ado_mom"]);
    var adoGap = num(item, "ado_gap_pp");
    var comparable = seller != null && market != null && gap != null && adg > 0;
    rows.push({
      item: item,
      site: site,
      seller: seller,
      market: market,
      gap: gap,
      share: share,
      adg: adg,
      sellerAdo: sellerAdo,
      marketAdo: marketAdo,
      adoGap: adoGap,
      comparable: comparable,
      tag: perfTag(gap),
      priority: comparable ? Math.abs(gap) * Math.max(share, 0) : -1
    });
  });

  if (!rows.length) return emptyStateChart(model);

  var comparableRows = rows.filter(function(r) { return r.comparable; });
  comparableRows.sort(function(a, b) { return (b.priority || 0) - (a.priority || 0); });
  var visualRows = comparableRows.slice(0, Math.min(8, comparableRows.length));
  var calloutRows = visualRows.slice(0, Math.min(3, visualRows.length));
  var calloutBySite = {};
  calloutRows.forEach(function(r, idx) { calloutBySite[r.site] = idx + 1; });

  var biggestWin = comparableRows.filter(function(r) { return r.gap >= 5; })[0] || null;
  var biggestDrag = comparableRows.filter(function(r) { return r.gap <= -5; })[0] || null;
  comparableRows.forEach(function(r) {
    if (!biggestWin || r.gap > biggestWin.gap) biggestWin = r.gap >= 5 ? r : biggestWin;
    if (!biggestDrag || r.gap < biggestDrag.gap) biggestDrag = r.gap <= -5 ? r : biggestDrag;
  });
  var highShareRisk = comparableRows.slice().sort(function(a, b) {
    var ar = a.gap != null && a.gap < 0 ? a.share : -1;
    var br = b.gap != null && b.gap < 0 ? b.share : -1;
    return br - ar;
  })[0] || null;

  var values = [];
  visualRows.forEach(function(r) {
    if (r.seller != null) values.push(r.seller);
    if (r.market != null) values.push(r.market);
  });
  var minVal = values.length ? Math.min.apply(null, values) : -10;
  var maxVal = values.length ? Math.max.apply(null, values) : 10;
  var minX = Math.min(-20, Math.floor((minVal - 5) / 10) * 10);
  var maxX = Math.max(30, Math.ceil((maxVal + 5) / 10) * 10);
  if (maxX - minX < 50) {
    var mid = (maxX + minX) / 2;
    minX = Math.floor((mid - 25) / 10) * 10;
    maxX = Math.ceil((mid + 25) / 10) * 10;
  }

  function xPos(v, left, plotW) {
    return left + (v - minX) / (maxX - minX) * plotW;
  }

  function tickValues() {
    var out = [];
    var step = 15;
    var start = Math.ceil(minX / step) * step;
    for (var t = start; t <= maxX; t += step) out.push(t);
    if (out.indexOf(0) < 0 && minX < 0 && maxX > 0) out.push(0);
    return out.sort(function(a, b) { return a - b; });
  }

  function chartSvg() {
    var width = 860;
    var height = 348;
    var left = 126;
    var right = 118;
    var top = 34;
    var bottom = 68;
    var plotW = width - left - right;
    var rowH = (height - top - bottom) / Math.max(1, visualRows.length);
    var dotR = 5;
    var html = '<svg viewBox="0 0 ' + width + ' ' + height + '" role="img" aria-label="Current month site attribution dumbbell">';
    html += '<text x="' + left + '" y="16" fill="#111827" font-size="12" font-weight="800">当月ADG环比</text>';
    tickValues().forEach(function(t) {
      var x = xPos(t, left, plotW);
      html += '<line x1="' + x + '" x2="' + x + '" y1="' + (top - 8) + '" y2="' + (height - bottom + 7) + '" stroke="' + (t === 0 ? '#333' : '#d9d9d9') + '" stroke-width="' + (t === 0 ? '1.1' : '1') + '" stroke-dasharray="' + (t === 0 ? '' : '3 4') + '"></line>';
      html += '<text x="' + x + '" y="' + (height - bottom + 22) + '" text-anchor="middle" fill="#555" font-size="10">' + t + '%</text>';
    });

    visualRows.forEach(function(r, idx) {
      var y = top + idx * rowH + rowH * 0.55;
      var color = perfColor(r.gap);
      var marketX = xPos(r.market, left, plotW);
      var sellerX = xPos(r.seller, left, plotW);
      var callout = calloutBySite[r.site];
      if (callout) {
        html += '<rect x="6" y="' + (y - rowH * 0.42) + '" width="' + (width - 12) + '" height="' + (rowH * 0.84) + '" rx="4" fill="#fff3ef" opacity=".75"></rect>';
        html += '<line x1="8" x2="8" y1="' + (y - rowH * 0.34) + '" y2="' + (y + rowH * 0.34) + '" stroke="#ee4d2d" stroke-width="1.4" stroke-linecap="round"></line>';
      }
      html += '<line x1="8" x2="' + (width - 8) + '" y1="' + y + '" y2="' + y + '" stroke="#eeeeee" stroke-width="1"></line>';
      html += '<text x="12" y="' + (y + 4) + '" fill="#111827" font-size="12" font-weight="800">' + svgText(r.site) + '</text>';
      html += '<text x="50" y="' + (y + 4) + '" fill="#666" font-size="10">' + formatCompact(r.share) + '% share</text>';
      html += '<line x1="' + marketX + '" x2="' + sellerX + '" y1="' + y + '" y2="' + y + '" stroke="' + color + '" stroke-width="2.1" stroke-linecap="round" opacity=".62"></line>';
      html += '<circle cx="' + marketX + '" cy="' + y + '" r="' + dotR + '" fill="#9ca3af" stroke="#555" stroke-width="1"></circle>';
      html += '<circle cx="' + sellerX + '" cy="' + y + '" r="' + dotR + '" fill="' + color + '" stroke="#fff" stroke-width="1.8"></circle>';
      html += '<text x="' + (width - 106) + '" y="' + (y - 2) + '" fill="' + color + '" font-size="11" font-weight="800">' + signedPpLocal(r.gap) + '</text>';
      html += '<text x="' + (width - 106) + '" y="' + (y + 13) + '" fill="#555" font-size="9">' + svgText(r.tag) + '</text>';
      if (callout) {
        var cx = Math.min(width - 132, Math.max(left + 18, sellerX + (r.gap >= 0 ? 18 : -18)));
        html += '<circle cx="' + cx + '" cy="' + (y - 11) + '" r="10" fill="#ee4d2d"></circle>';
        html += '<text x="' + cx + '" y="' + (y - 7) + '" text-anchor="middle" fill="#fff" font-size="11" font-weight="900">' + callout + '</text>';
      }
    });

    var legendY = height - 20;
    html += '<circle cx="' + left + '" cy="' + (legendY - 4) + '" r="' + dotR + '" fill="#9ca3af"></circle><text x="' + (left + 10) + '" y="' + legendY + '" fill="#333" font-size="10">大盘</text>';
    html += '<circle cx="' + (left + 80) + '" cy="' + (legendY - 4) + '" r="' + dotR + '" fill="#1f8f58"></circle><text x="' + (left + 92) + '" y="' + legendY + '" fill="#333" font-size="10">卖家跑赢</text>';
    html += '<circle cx="' + (left + 200) + '" cy="' + (legendY - 4) + '" r="' + dotR + '" fill="#d83a2e"></circle><text x="' + (left + 212) + '" y="' + legendY + '" fill="#333" font-size="10">卖家跑输</text>';
    html += '</svg>';
    return html;
  }

  function rankingTable() {
    var rowsForTable = comparableRows.slice(0, 6);
    var html = '<table class="report-table site-attribution-table"><thead><tr>';
    html += '<th>序号</th><th>站点</th><th>占比</th><th>卖家</th><th>大盘</th><th>差距</th>';
    html += '</tr></thead><tbody>';
    rowsForTable.forEach(function(r, idx) {
      var tone = r.gap >= 5 ? "up-text" : (r.gap <= -5 ? "dn-text" : "");
      var callout = calloutBySite[r.site];
      html += '<tr>';
      html += '<td>' + (callout ? '<span class="mini-callout">' + callout + '</span>' : (idx + 1)) + '</td>';
      html += '<td><strong>' + esc(r.site) + '</strong></td>';
      html += '<td>' + formatCompact(r.share) + '%</td>';
      html += '<td>' + signedPctLocal(r.seller) + '</td>';
      html += '<td>' + signedPctLocal(r.market) + '</td>';
      html += '<td class="' + tone + '"><strong>' + signedPpLocal(r.gap) + '</strong></td>';
      html += '</tr>';
    });
    html += '</tbody></table>';
    return html;
  }

  var html = '<style>';
  html += '.site-attribution-grid{display:grid;grid-template-columns:minmax(0,1.55fr) minmax(330px,.85fr);gap:12px;margin:8px 0 10px;}';
  html += '.site-attribution-panel{min-width:0;border:1px solid var(--line);border-radius:8px;background:#fff;padding:10px 12px;}';
  html += '.site-attribution-title{font-size:13px;font-weight:760;color:var(--ink);line-height:1.2;}';
  html += '.site-attribution-subtitle{font-size:11px;color:var(--muted);line-height:1.35;margin-top:2px;}';
  html += '.site-attribution-chart{width:100%;height:370px;margin-top:4px;}';
  html += '.site-attribution-chart svg{display:block;width:100%;height:100%;}';
  html += '.site-attribution-table{width:100%;font-size:11px;}';
  html += '.site-attribution-table th,.site-attribution-table td{text-align:center;padding:5px 4px;}';
  html += '.mini-callout{display:inline-grid;place-items:center;width:20px;height:20px;border-radius:50%;background:#ee4d2d;color:#fff;font-weight:900;font-size:11px;line-height:1;flex:0 0 20px;}';
  html += '@media(max-width:900px){.site-attribution-grid{grid-template-columns:1fr}.site-attribution-chart{height:350px}}';
  html += '</style>';

  html += '<div class="chart-container site-attribution-grid">';
  html += '<div class="site-attribution-panel">';
  html += '<div class="site-attribution-title">当前月站点归因对标</div>';
  html += '<div class="site-attribution-subtitle">按 |gap pp| × ADG share 排序；大盘/卖家点等尺寸，share只用于排序和标签，避免比例误导。</div>';
  html += '<div class="site-attribution-chart">' + chartSvg() + '</div>';
  html += '</div>';
  html += '<div class="site-attribution-panel">';
  html += '<div class="site-attribution-title">影响优先级</div>';
  html += '<div class="site-attribution-subtitle">1/2/3 对应图上站点，并在下方数据诊断中合并解释。</div>';
  html += rankingTable();
  html += '</div>';
  html += '</div>';

  return html;
}
"""


def build_section_js() -> str:
    return site_benchmark_chart_js()


SECTION_ID = "sec_site_benchmark"
FUNC_NAME = "siteBenchmarkChart"
