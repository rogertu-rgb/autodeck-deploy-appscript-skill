#!/usr/bin/env python3
"""
Section 1.4 — L2 Category Drilldown (二级品类钻取)

Primary visual:
  - Four attribution lanes instead of a dense heatmap
  - High-share underperformers, absolute scale leaders, fastest growers,
    and large-share decliners
  - Circular 1/2/3 markers stay linked to the highest-priority rows
"""

from __future__ import annotations


def l2_drill_chart_js() -> str:
    return r"""
function l2DrillChart(model) {
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
  function gapOf(item) {
    var g = num(item, "gap_pp");
    if (g == null) g = num(item, "adg_gap_pp");
    return g;
  }
  function hasSellerData(adg, prev, share, mom) {
    return (adg != null && adg > 0) ||
           (prev != null && prev > 0) ||
           (share != null && share > 0) ||
           (mom != null && isFinite(mom));
  }
  function categoryPathL2(r) {
    return [r.l1, r.l2].filter(function(x) { return x != null && String(x).trim() !== ""; }).join(" > ") || r.l2 || "—";
  }
  function rowId(r) { return r.site + "||" + r.l1 + "||" + r.l2 + "||" + r.adg; }

  var entries = [];
  var md = typeof metaDict === "function" ? metaDict("sec_l2_drill") : {};
  model.body.forEach(function(item) {
    var site = String(val(item, "site") || "").trim();
    var l1 = String(val(item, "l1") || md.l1_filter || md.l1 || "").trim();
    var l2 = String(val(item, "l2") || "").trim();
    if (!site || !l2) return;
    var adgRaw = num(item, "adg_mtd");
    var prevRaw = num(item, "adg_m1");
    var mom = num(item, "adg_mom");
    var mkt = num(item, "mkt_adg_mom");
    var gap = gapOf(item);
    var shareRaw = num(item, "share_in_l1");
    if (!hasSellerData(adgRaw, prevRaw, shareRaw, mom)) return;
    var adg = adgRaw || 0;
    var prev = prevRaw || 0;
    var share = shareRaw || 0;
    var delta = num(item, "adg_delta");
    if (delta == null) delta = adg - prev;
    entries.push({ item: item, site: site, l1: l1, l2: l2, adg: adg, prev: prev, mom: mom, mkt: mkt, gap: gap, share: share, delta: delta });
  });

  if (!entries.length) return emptyStateChart(model);

  var priority = entries.filter(function(r) { return r.gap != null && (r.adg > 0 || r.share > 0); });
  priority.sort(function(a, b) {
    var sa = Math.abs(a.gap || 0) * Math.max(a.share || 0, 0.5);
    var sb = Math.abs(b.gap || 0) * Math.max(b.share || 0, 0.5);
    return sb - sa;
  });
  var calloutById = {};
  priority.slice(0, 3).forEach(function(r, idx) { calloutById[rowId(r)] = idx + 1; });

  function topRows(rows, sorter, limit) {
    rows = rows.slice();
    rows.sort(sorter);
    return rows.slice(0, limit || 5);
  }
  function fallback(rows, sorter) {
    rows = rows.filter(function(r) { return r.adg > 0 || r.mom != null || r.gap != null; });
    return topRows(rows, sorter, 5);
  }

  var highShareUnder = entries.filter(function(r) { return r.gap != null && r.gap <= -5 && r.share >= 10; });
  if (!highShareUnder.length) highShareUnder = entries.filter(function(r) { return r.gap != null && r.gap < 0; });
  highShareUnder = topRows(highShareUnder, function(a, b) {
    return (Math.abs(b.gap || 0) * Math.max(b.share || 0, 0.5)) - (Math.abs(a.gap || 0) * Math.max(a.share || 0, 0.5));
  }, 5);

  var scaleLeaders = topRows(entries.filter(function(r) { return r.adg > 0; }), function(a, b) { return b.adg - a.adg; }, 5);

  var growers = entries.filter(function(r) { return r.mom != null && r.mom > 0; });
  growers = topRows(growers, function(a, b) { return b.mom - a.mom; }, 5);
  if (!growers.length) growers = fallback(entries, function(a, b) { return (b.mom || -999) - (a.mom || -999); });

  var largeDecliners = entries.filter(function(r) { return r.mom != null && r.mom < 0 && r.share >= 10; });
  if (!largeDecliners.length) largeDecliners = entries.filter(function(r) { return r.mom != null && r.mom < 0; });
  largeDecliners = topRows(largeDecliners, function(a, b) {
    var sa = Math.abs(a.delta || 0) * Math.max(a.share || 0, 0.5);
    var sb = Math.abs(b.delta || 0) * Math.max(b.share || 0, 0.5);
    return sb - sa;
  }, 5);

  var lanes = [
    { title: "高占比跑输大盘", sub: "优先解释站点差距", rows: highShareUnder, tone: "neg" },
    { title: "绝对体量最大", sub: "决定卖家主盘表现", rows: scaleLeaders, tone: "scale" },
    { title: "增长最快", sub: "可复制的正向打法", rows: growers, tone: "pos" },
    { title: "体量大但下跌", sub: "需要继续下钻到L3", rows: largeDecliners, tone: "neg" }
  ];

  var maxAdg = entries.reduce(function(m, r) { return Math.max(m, r.adg || 0, r.prev || 0); }, 1);
  var style = [
    '<style>',
    '.cat-l2-lanes{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:8px 0 12px}',
    '.cat-lane{border:1px solid var(--line);background:#fff;padding:10px;min-width:0}',
    '.cat-lane h3{margin:0 0 3px;font-size:13px;border-bottom:2px solid var(--accent);padding-bottom:5px}',
    '.cat-lane small{display:block;color:var(--muted);margin-bottom:8px;line-height:1.35}',
    '.cat-lane-row{position:relative;border:1px solid #e7eaf0;padding:8px;margin-bottom:8px;background:#fbfbfc;min-height:92px}',
    '.cat-lane-row.neg{background:#fff6f3}.cat-lane-row.pos{background:#f2fbf6}',
    '.cat-lane-main{display:flex;justify-content:space-between;gap:8px;align-items:flex-start}',
    '.cat-lane-main b{font-size:12px;line-height:1.25}.cat-lane-main span{font-size:11px;font-weight:800;white-space:nowrap}',
    '.cat-risk{color:var(--down);font-weight:800}.cat-up{color:var(--up);font-weight:800}.cat-muted{color:var(--muted)}',
    '.cat-mini-line{display:grid;grid-template-columns:42px 1fr 44px;gap:5px;align-items:center;font-size:11px;margin-top:7px;color:#4d5662}',
    '.cat-mini-line div{height:7px;background:#fff;border:1px solid rgba(0,0,0,.12);overflow:hidden}',
    '.cat-mini-line i{display:block;height:100%;background:var(--accent);opacity:.78}',
    '.cat-delta{font-size:11px;color:var(--muted);margin-top:6px;line-height:1.35}',
    '.cat-callout{position:absolute;top:6px;right:6px;width:22px;height:22px;border-radius:50%;background:var(--accent);color:#fff;display:grid;place-items:center;font-weight:900;font-size:12px;box-shadow:0 1px 3px rgba(0,0,0,.15)}',
    '.cat-lane-row .cat-callout + .cat-lane-main{padding-right:26px}',
    '.cat-caption{font-size:11px;color:var(--muted);line-height:1.45;margin:0 0 8px}',
    '@media(max-width:1100px){.cat-l2-lanes{grid-template-columns:1fr 1fr}}@media(max-width:720px){.cat-l2-lanes{grid-template-columns:1fr}}',
    '</style>'
  ].join('');

  var emittedCallouts = {};
  function renderRow(r) {
    var call = calloutById[rowId(r)];
    var showCall = call && !emittedCallouts[call];
    if (showCall) emittedCallouts[call] = true;
    var gapTone = r.gap != null && r.gap >= 0 ? "cat-up" : "cat-risk";
    var momTone = r.mom != null && r.mom >= 0 ? "cat-up" : "cat-risk";
    var rowTone = r.mom != null && r.mom >= 0 ? "pos" : (r.gap != null && r.gap < 0 ? "neg" : "");
    var html = '<div class="cat-lane-row ' + rowTone + '">';
    if (showCall) html += '<span class="cat-callout">' + call + '</span>';
    var fullPath = categoryPathL2(r);
    html += '<div class="cat-lane-main"><b title="' + esc(r.site + ' / ' + fullPath) + '">' + esc(r.site) + ' · ' + esc(label(fullPath, 54)) + '</b><span class="' + gapTone + '">' + pp(r.gap) + '</span></div>';
    html += '<div class="cat-mini-line"><span>占L1</span><div><i style="width:' + clamp(r.share || 0, 0, 100).toFixed(1) + '%"></i></div><span>' + formatCompact(r.share || 0) + '%</span></div>';
    html += '<div class="cat-mini-line"><span>ADG</span><div><i style="width:' + clamp((r.adg || 0) / maxAdg * 100, 0, 100).toFixed(1) + '%"></i></div><span>' + formatCompact(r.adg || 0) + '</span></div>';
    html += '<div class="cat-delta"><span class="' + momTone + '">卖家 ' + pct(r.mom) + '</span> · 大盘 ' + pct(r.mkt) + ' · ΔADG ' + formatCompact(r.delta || 0) + '</div>';
    html += '</div>';
    return html;
  }

  var html = style + '<div class="cat-caption">四条 lane 用同一批 L1 > L2 行回答不同诊断问题；编号 1/2/3 保持与最高优先级差距行一致。</div>';
  html += '<div class="cat-l2-lanes">';
  lanes.forEach(function(lane) {
    html += '<div class="cat-lane"><h3>' + esc(lane.title) + '</h3><small>' + esc(lane.sub) + '</small>';
    if (!lane.rows.length) {
      html += '<div class="muted" style="font-size:12px;padding:8px 0">暂无符合条件的L2。</div>';
    } else {
      lane.rows.forEach(function(r) { html += renderRow(r); });
    }
    html += '</div>';
  });
  html += '</div>';
  return html;
}
"""


def build_section_js() -> str:
    return l2_drill_chart_js()


SECTION_ID = "sec_l2_drill"
FUNC_NAME = "l2DrillChart"
