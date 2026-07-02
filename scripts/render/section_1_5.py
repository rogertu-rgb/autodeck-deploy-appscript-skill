#!/usr/bin/env python3
"""
Section 1.5 — L3 Granular Diagnosis (三级品类粒度诊断)

Primary visual:
  - Evidence/proof table for the L2 drilldown route
  - Share bars, seller MoM, optional P50 benchmark, gap, and action tag
  - If P50 is missing, label the row as seller-side evidence instead of
    overclaiming a market gap
"""

from __future__ import annotations


def l3_granular_chart_js() -> str:
    return r"""
function l3GranularChart(model) {
  if (!model || !model.body.length) return emptyStateChart(model);

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
  function actionTag(r) {
    if ((r.share || 0) >= 20 && r.mom != null && r.mom < -10) return "进listing验证";
    if (r.gap != null && r.gap < -10 && (r.share || 0) >= 10) return "对标差距复盘";
    if (r.mom != null && r.mom > 10) return "正向复制";
    if ((r.adg || 0) < 1) return "长尾观察";
    return "继续观察";
  }
  function hasSellerData(adg, prev, share, mom) {
    return (adg != null && adg > 0) ||
           (prev != null && prev > 0) ||
           (share != null && share > 0) ||
           (mom != null && isFinite(mom));
  }
  function categoryPathL3(r) {
    return [r.l1, r.l2, r.l3].filter(function(x) { return x != null && String(x).trim() !== ""; }).join(" > ") || r.l3 || "—";
  }

  var entries = [];
  var p50Rows = 0;
  var md = typeof metaDict === "function" ? metaDict("sec_l3_granular") : {};
  model.body.forEach(function(item) {
    var site = String(val(item, "site") || "").trim();
    var l1 = String(val(item, "l1") || md.l1 || "").trim();
    var l2 = String(val(item, "l2") || md.l2 || "").trim();
    var l3 = String(val(item, "l3") || "").trim();
    if (!site || !l3) return;
    var adgRaw = num(item, "adg_mtd");
    var prevRaw = num(item, "adg_m1");
    var mom = num(item, "adg_mom");
    var shareRaw = num(item, "share_in_l2");
    if (!hasSellerData(adgRaw, prevRaw, shareRaw, mom)) return;
    var adg = adgRaw || 0;
    var prev = prevRaw || 0;
    var share = shareRaw || 0;
    var p50 = num(item, "p50_growth");
    var sellers = num(item, "seller_cnt");
    var gap = (mom != null && p50 != null) ? mom - p50 : null;
    if (p50 != null) p50Rows++;
    entries.push({ item: item, site: site, l1: l1, l2: l2, l3: l3, adg: adg, prev: prev, mom: mom, share: share, p50: p50, gap: gap, sellers: sellers });
  });

  if (!entries.length) return emptyStateChart(model);

  entries.forEach(function(r) {
    var gapSignal = r.gap != null ? Math.abs(r.gap) : Math.abs(r.mom || 0);
    r.score = gapSignal * Math.max(r.share || 0, 0.5) + Math.log((r.adg || 0) + 1) * 2;
    r.action = actionTag(r);
  });
  entries.sort(function(a, b) { return b.score - a.score; });
  var rows = entries.slice(0, 12);
  var maxShare = rows.reduce(function(m, r) { return Math.max(m, r.share || 0); }, 1);
  var maxAdg = rows.reduce(function(m, r) { return Math.max(m, r.adg || 0); }, 1);

  var topDecline = entries.filter(function(r) { return r.mom != null && r.mom < 0; }).sort(function(a, b) { return a.mom - b.mom; })[0];
  var topGrowth = entries.filter(function(r) { return r.mom != null && r.mom > 0; }).sort(function(a, b) { return b.mom - a.mom; })[0];
  var topScale = entries.slice().sort(function(a, b) { return b.adg - a.adg; })[0];

  var style = [
    '<style>',
    '.cat-proof-summary{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:8px 0 10px}',
    '.cat-proof-card{border:1px solid var(--line);background:#fff;padding:10px;min-width:0}',
    '.cat-proof-card b{display:block;font-size:13px;margin-bottom:4px}.cat-proof-card small{color:var(--muted);line-height:1.35}',
    '.cat-l3-proof{width:100%;border-collapse:collapse;margin:8px 0 12px}',
    '.cat-l3-proof th{background:#3f4146;color:#fff;border:1px solid #fff;padding:7px;font-size:11px;white-space:nowrap}',
    '.cat-l3-proof td{padding:7px;border-bottom:1px solid #eceff3;text-align:center;font-size:12px}',
    '.cat-l3-proof td:first-child{width:38px;min-width:38px;text-align:center}',
    '.cat-l3-proof td:nth-child(3){text-align:left;font-weight:700;max-width:260px;line-height:1.25;word-break:break-word}',
    '.l3-rank-dot{display:inline-block!important;position:static!important;transform:none!important;float:none!important;width:22px!important;height:22px!important;min-width:22px!important;border-radius:999px!important;background:#ee4d2d!important;color:#fff!important;text-align:center!important;font-weight:900!important;font-size:12px!important;line-height:22px!important;vertical-align:middle!important}',
    '.cat-table-bar{width:82px;height:8px;display:inline-block;background:#f3f4f6;border:1px solid #d9dee6;vertical-align:middle;margin-right:6px;overflow:hidden}',
    '.cat-table-bar i{display:block;height:100%;background:var(--accent);opacity:.78}',
    '.cat-risk{color:var(--down);font-weight:800}.cat-up{color:var(--up);font-weight:800}.cat-muted{color:var(--muted)}',
    '.cat-action-tag{display:inline-block;background:#f1f3f5;border:1px solid #d9dee6;padding:3px 6px;font-weight:700;white-space:nowrap}',
    '.cat-caption{font-size:11px;color:var(--muted);line-height:1.45;margin:0 0 8px}',
    '@media(max-width:900px){.cat-proof-summary{grid-template-columns:1fr}.cat-l3-proof{min-width:780px}.cat-proof-wrap{overflow:auto}}',
    '</style>'
  ].join('');

  function summaryCard(title, r, metricText) {
    if (!r) return '<div class="cat-proof-card"><b>' + esc(title) + '</b><small>暂无可用行</small></div>';
    return '<div class="cat-proof-card"><b>' + esc(title) + '</b><small>' + esc(r.site) + ' · ' + esc(label(categoryPathL3(r), 64)) + '<br>' + metricText(r) + '</small></div>';
  }

  var html = style;
  html += '<div class="cat-caption">L3 用来验证 L2 归因：优先看占L2比重、卖家MoM、P50对标是否可用，以及下一步应该进入 listing/shop/流量/履约哪条证据链。</div>';
  html += '<div class="cat-proof-summary">';
  html += summaryCard("最大体量", topScale, function(r) { return formatCompact(r.adg || 0) + " ADG · 占L2 " + formatCompact(r.share || 0) + "%"; });
  html += summaryCard("增长最好", topGrowth, function(r) { return "卖家MoM " + pct(r.mom) + " · P50 " + pct(r.p50); });
  html += summaryCard("跌幅最大", topDecline, function(r) { return "卖家MoM " + pct(r.mom) + " · 占L2 " + formatCompact(r.share || 0) + "%"; });
  html += '</div>';

  html += '<div class="cat-proof-wrap"><table class="cat-l3-proof"><thead><tr>';
  html += '<th>#</th><th>Site</th><th>类目路径</th><th>占L2</th><th>ADG</th><th>卖家MoM</th><th>P50</th><th>卖家-P50</th><th>Action</th>';
  html += '</tr></thead><tbody>';
  rows.forEach(function(r, idx) {
    var momTone = r.mom != null && r.mom >= 0 ? "cat-up" : "cat-risk";
    var gapTone = r.gap != null && r.gap >= 0 ? "cat-up" : "cat-risk";
    var call = idx < 3 ? '<span class="l3-rank-dot" data-l3-callout-rank="' + (idx + 1) + '">' + (idx + 1) + '</span>' : String(idx + 1);
    html += '<tr>';
    html += '<td>' + call + '</td>';
    html += '<td>' + esc(r.site) + '</td>';
    html += '<td title="' + esc(categoryPathL3(r)) + '">' + esc(label(categoryPathL3(r), 68)) + '</td>';
    html += '<td><span class="cat-table-bar"><i style="width:' + clamp((r.share || 0) / maxShare * 100, 0, 100).toFixed(1) + '%"></i></span>' + formatCompact(r.share || 0) + '%</td>';
    html += '<td><span class="cat-table-bar"><i style="width:' + clamp((r.adg || 0) / maxAdg * 100, 0, 100).toFixed(1) + '%"></i></span>' + formatCompact(r.adg || 0) + '</td>';
    html += '<td class="' + momTone + '">' + pct(r.mom) + '</td>';
    html += '<td>' + (r.p50 != null ? pct(r.p50) : '<span class="cat-muted">缺P50</span>') + '</td>';
    html += '<td class="' + (r.gap != null ? gapTone : 'cat-muted') + '">' + (r.gap != null ? pp(r.gap) : 'seller-side') + '</td>';
    html += '<td><span class="cat-action-tag">' + esc(r.action) + '</span></td>';
    html += '</tr>';
  });
  html += '</tbody></table></div>';
  html += '<div class="cat-caption">' + (p50Rows ? ('P50覆盖 ' + p50Rows + '/' + entries.length + ' 行；有P50时用卖家-P50判断相对表现。') : '当前L3缺少P50覆盖，因此本表只作为卖家侧证据，不直接声称大盘跑赢/跑输。') + '</div>';
  return html;
}
"""


def build_section_js() -> str:
    return l3_granular_chart_js()


SECTION_ID = "sec_l3_granular"
FUNC_NAME = "l3GranularChart"
