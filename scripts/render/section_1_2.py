#!/usr/bin/env python3
"""
Section 1.2 — L1 Category Overview (一级品类总览)

Primary visual:
  - Site x L1 diagnostic matrix
  - Cell color = seller MoM gap versus market MoM
  - In-cell bar = L1 ADG share within the site
  - Circular 1/2/3 markers = highest-priority drilldown cells

The visual intentionally does not use a site filter: the matrix itself is the
site comparison surface, and the engine renders a filterable evidence table
after the primary visual.
"""

from __future__ import annotations


def l1_overview_table_js() -> str:
    """Site x L1 diagnostic matrix with priority callouts."""
    return r"""
function l1OverviewChart(model) {
  var tabs = ((window.AUTODECK_ACTIVE_DATA && window.AUTODECK_ACTIVE_DATA.tabs) ||
              (window.AUTODECK_LOCAL_DATA && window.AUTODECK_LOCAL_DATA.tabs) || {});
  var matrixModel = rowsModel(tabs.sec_l1_matrix || []);
  if (!matrixModel.body.length) matrixModel = model;
  if (!matrixModel || !matrixModel.body.length) return emptyStateChart(model);

  function pct(n) {
    if (n == null || !isFinite(n)) return "—";
    return (n > 0 ? "+" : "") + formatCompact(n) + "%";
  }
  function pp(n) {
    if (n == null || !isFinite(n)) return "—";
    return (n > 0 ? "+" : "") + formatCompact(n) + "pp";
  }
  function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
  function label(s, maxLen) {
    s = String(s == null ? "" : s);
    return s.length > maxLen ? s.slice(0, maxLen - 1) + "…" : s;
  }
  function rowKey(site, l1) { return site + "||" + l1; }
  function hasSellerData(adg, prev, share, mom) {
    return (adg != null && adg > 0) ||
           (prev != null && prev > 0) ||
           (share != null && share > 0) ||
           (mom != null && isFinite(mom));
  }
  function gapOf(item) {
    var g = num(item, "gap_pp");
    if (g == null) g = num(item, "adg_gap_pp");
    return g;
  }
  function cellBg(gap) {
    if (gap == null || !isFinite(gap)) return "#f5f6f8";
    var opacity = clamp(0.12 + Math.abs(gap) / 140, 0.14, 0.48);
    return gap >= 0 ? "rgba(33,163,102," + opacity.toFixed(3) + ")" : "rgba(238,77,45," + opacity.toFixed(3) + ")";
  }

  var byKey = {};
  var siteTotals = {};
  var l1Totals = {};
  var rows = [];
  matrixModel.body.forEach(function(item) {
    var site = String(val(item, "site") || "").trim();
    var l1 = String(val(item, "l1") || "").trim();
    if (!site || !l1) return;
    var adgRaw = num(item, "adg_mtd");
    var prevRaw = num(item, "adg_m1");
    var shareRaw = num(item, "share_in_site");
    if (shareRaw == null) shareRaw = num(item, "adg_share");
    var mom = num(item, "adg_mom");
    if (!hasSellerData(adgRaw, prevRaw, shareRaw, mom)) return;
    var adg = adgRaw || 0;
    var prev = prevRaw || 0;
    var share = shareRaw || 0;
    var mkt = num(item, "mkt_adg_mom");
    var gap = gapOf(item);
    var scale = Math.max(adg, prev);
    var entry = { item: item, site: site, l1: l1, adg: adg, prev: prev, share: share, mom: mom, mkt: mkt, gap: gap };
    byKey[rowKey(site, l1)] = entry;
    rows.push(entry);
    siteTotals[site] = (siteTotals[site] || 0) + scale;
    l1Totals[l1] = (l1Totals[l1] || 0) + scale;
  });

  if (!rows.length) return emptyStateChart(model);

  var sites = Object.keys(siteTotals).sort(function(a, b) { return siteTotals[b] - siteTotals[a]; });
  var l1s = Object.keys(l1Totals).sort(function(a, b) { return l1Totals[b] - l1Totals[a]; });
  var priorityCandidates = rows.filter(function(r) { return r.gap != null && (r.adg > 0 || r.share > 0); });
  priorityCandidates.sort(function(a, b) {
    var sa = Math.abs(a.gap || 0) * Math.max(a.share || 0, 0.5);
    var sb = Math.abs(b.gap || 0) * Math.max(b.share || 0, 0.5);
    return sb - sa;
  });
  var priorities = priorityCandidates.slice(0, 3);
  var calloutByKey = {};
  priorities.forEach(function(r, idx) { calloutByKey[rowKey(r.site, r.l1)] = idx + 1; });

  var topL1 = {};
  l1s.slice(0, 8).forEach(function(l) { topL1[l] = true; });
  priorities.forEach(function(r) { topL1[r.l1] = true; });
  l1s = l1s.filter(function(l) { return topL1[l]; });

  var style = [
    '<style>',
    '.cat-drill-grid{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(300px,.62fr);gap:12px;margin:8px 0 12px}',
    '.cat-panel{border:1px solid var(--line);background:#fff;padding:10px;min-width:0}',
    '.cat-matrix-wrap{overflow:auto}',
    '.cat-l1-matrix{border-collapse:collapse;width:100%;min-width:760px}',
    '.cat-l1-matrix th{background:#3f4146;color:#fff;border:1px solid #fff;padding:7px 8px;font-size:11px;white-space:nowrap}',
    '.cat-l1-matrix th:first-child{position:sticky;left:0;z-index:2}',
    '.cat-l1-matrix .site-head{position:sticky;left:0;z-index:1;background:#3f4146;color:#fff;min-width:48px}',
    '.cat-cell{position:relative;min-width:150px;height:74px;border:1px solid #fff;padding:8px;vertical-align:top}',
    '.cat-cell:hover{outline:2px solid var(--accent);outline-offset:-2px}',
    '.cat-cell-empty{background:#fff;color:transparent;border-color:#fff;text-align:center;font-size:12px}',
    '.cat-cell-top{display:flex;justify-content:space-between;gap:8px;align-items:flex-start;font-size:11px}',
    '.cat-cell-top b{font-size:15px;color:#111827}',
    '.cat-cell-foot{font-size:11px;color:#4d5662;margin-top:6px;white-space:nowrap}',
    '.cat-sharebar{height:7px;background:#fff;border:1px solid rgba(0,0,0,.12);margin-top:7px;overflow:hidden}',
    '.cat-sharebar i{display:block;height:100%;background:var(--accent);opacity:.78}',
    '.cat-callout{position:absolute;top:5px;right:6px;width:22px;height:22px;border-radius:50%;background:var(--accent);color:#fff;display:grid;place-items:center;font-weight:900;font-size:12px;box-shadow:0 1px 3px rgba(0,0,0,.15)}',
    '.cat-priority-list{display:grid;gap:8px}',
    '.cat-priority-row{display:grid;grid-template-columns:26px 1fr auto;gap:8px;align-items:center;padding:8px;background:#f7f8fa;border:1px solid #e6e9ee}',
    '.cat-priority-row .num{width:24px;height:24px;border-radius:50%;background:var(--accent);color:#fff;display:grid;place-items:center;font-weight:900}',
    '.cat-priority-row b{font-size:12px}.cat-priority-row small{display:block;color:var(--muted);margin-top:2px}.cat-risk{color:var(--down);font-weight:800}.cat-up{color:var(--up);font-weight:800}',
    '.cat-caption{font-size:11px;color:var(--muted);line-height:1.45;margin:0 0 8px}',
    '@media(max-width:1000px){.cat-drill-grid{grid-template-columns:1fr}.cat-panel{overflow:auto}}',
    '</style>'
  ].join('');

  var html = style;
  html += '<div class="cat-caption">颜色=卖家增速 vs 大盘增速差距；横条=该一级品类在站点内的ADG占比；编号=优先下钻入口。</div>';
  html += '<div class="cat-drill-grid">';
  html += '<div class="cat-panel cat-matrix-wrap">';
  html += '<table class="cat-l1-matrix"><thead><tr><th>Site</th>';
  l1s.forEach(function(l1) { html += '<th title="' + esc(l1) + '">' + esc(label(l1, 24)) + '</th>'; });
  html += '</tr></thead><tbody>';

  sites.forEach(function(site) {
    html += '<tr><th class="site-head">' + esc(site) + '</th>';
    l1s.forEach(function(l1) {
      var r = byKey[rowKey(site, l1)];
      if (!r) {
        html += '<td class="cat-cell cat-cell-empty"></td>';
        return;
      }
      var c = calloutByKey[rowKey(site, l1)];
      var gapClass = r.gap == null ? '' : (r.gap >= 0 ? 'cat-up' : 'cat-risk');
      html += '<td class="cat-cell" style="background:' + cellBg(r.gap) + '" title="' + esc(site + ' × ' + l1) + '">';
      if (c) html += '<span class="cat-callout">' + c + '</span>';
      html += '<div class="cat-cell-top"><b>' + pct(r.mom) + '</b><span class="' + gapClass + '">' + pp(r.gap) + '</span></div>';
      html += '<div class="cat-sharebar"><i style="width:' + clamp(r.share || 0, 0, 100).toFixed(1) + '%"></i></div>';
      html += '<div class="cat-cell-foot">' + formatCompact(r.adg) + ' ADG · ' + formatCompact(r.share || 0) + '%</div>';
      html += '</td>';
    });
    html += '</tr>';
  });
  html += '</tbody></table></div>';

  html += '<div class="cat-panel"><div class="cat-caption">优先级按 |gap pp| × 站点内占比排序，帮助从“站点问题”进入“类目归因”。</div>';
  html += '<div class="cat-priority-list">';
  if (!priorities.length) {
    html += '<div class="muted">暂无可排序的站点×一级品类差距。</div>';
  } else {
    priorities.forEach(function(r, idx) {
      var tone = r.gap != null && r.gap >= 0 ? 'cat-up' : 'cat-risk';
      html += '<div class="cat-priority-row">';
      html += '<span class="num">' + (idx + 1) + '</span>';
      html += '<div><b>' + esc(r.site) + ' × ' + esc(label(r.l1, 32)) + '</b><small>占站点 ' + formatCompact(r.share || 0) + '% · ' + formatCompact(r.adg) + ' ADG</small></div>';
      html += '<span class="' + tone + '">' + pp(r.gap) + '</span>';
      html += '</div>';
    });
  }
  html += '</div></div></div>';
  return html;
}
"""


def build_section_js() -> str:
    return l1_overview_table_js()


SECTION_ID = "sec_l1_overview"
FUNC_NAME = "l1OverviewChart"
