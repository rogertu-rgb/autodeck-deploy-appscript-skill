#!/usr/bin/env python3
"""
Section 1.8 — Top Listing Contributions (Top商品贡献榜)

Enriched from raw_dws_item. Shows best-selling listings, largest growth/loss
listings, and an item-level funnel using ADIMP -> ADPV -> ADO.
"""

from __future__ import annotations


def listing_change_chart_js() -> str:
    return r"""
function listingChangeChart(model) {
  if (!model || !model.body.length) return emptyStateChart(model);

  function rows(rankType) {
    return model.body.filter(function(item) { return String(val(item, "rank_type") || "") === rankType; });
  }
  function rowSite(item) { return String(val(item, "site") || "").trim(); }
  function shortName(item, n) {
    return String(val(item, "item_name") || val(item, "item_id") || "—").slice(0, n || 58);
  }
  function pctText(value, digits) {
    var n = parseNum(value);
    return n == null ? "—" : (n * 100).toFixed(digits == null ? 1 : digits) + "%";
  }
  function ppText(value) {
    var n = parseNum(value);
    return n == null ? "—" : (n > 0 ? "+" : "") + n.toFixed(1) + "pp";
  }
  function deltaText(item, col) {
    var n = num(item, col);
    if (n == null) return "—";
    return (n > 0 ? "+" : "") + formatCompact(n);
  }
  function toneClass(n) {
    n = parseNum(n);
    return n == null ? "" : (n > 0 ? "up-text" : (n < 0 ? "dn-text" : ""));
  }

  var baseRows = rows("top_adg").concat(rows("top_growth")).concat(rows("top_loss")).concat(rows("site_top_adg")).concat(rows("site_growth")).concat(rows("site_loss"));
  var siteSet = {};
  baseRows.forEach(function(item) { var s = rowSite(item); if (s) siteSet[s] = true; });
  var sites = Object.keys(siteSet).sort();
  if (!sites.length) return emptyStateChart(model);

  var topAdg = rows("top_adg").slice().sort(function(a,b){ return (num(b,"mtd_adg")||0) - (num(a,"mtd_adg")||0); });
  var topGrowth = rows("top_growth").slice().sort(function(a,b){ return (num(b,"adg_delta")||0) - (num(a,"adg_delta")||0); });
  var topLoss = rows("top_loss").slice().sort(function(a,b){ return (num(a,"adg_delta")||0) - (num(b,"adg_delta")||0); });
  var top = topAdg[0];
  var loss = topLoss[0];
  var gain = topGrowth[0];
  var maxAdg = Math.max.apply(null, topAdg.slice(0, 10).map(function(r){ return num(r, "mtd_adg") || 0; }).concat([1]));

  var hostId = "listing-workbench-" + Math.random().toString(36).slice(2, 6);
  var html = '<div id="' + hostId + '" class="listing-workbench">';
  html += '<div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin-bottom:10px">';
  html += '<div class="metric-card"><div class="label">Top Listing ADG</div><div class="value" style="font-size:16px">' + (top ? formatCompact(num(top,"mtd_adg")||0) : "—") + '</div><div class="context">' + (top ? esc(rowSite(top) + " · " + shortName(top, 22)) : "—") + '</div></div>';
  html += '<div class="metric-card"><div class="label">最大增长Listing</div><div class="value up-text" style="font-size:16px">' + (gain ? deltaText(gain,"adg_delta") : "—") + '</div><div class="context">' + (gain ? esc(rowSite(gain) + " · " + shortName(gain, 22)) : "—") + '</div></div>';
  html += '<div class="metric-card"><div class="label">最大跌幅Listing</div><div class="value dn-text" style="font-size:16px">' + (loss ? deltaText(loss,"adg_delta") : "—") + '</div><div class="context">' + (loss ? esc(rowSite(loss) + " · " + shortName(loss, 22)) : "—") + '</div></div>';
  html += '<div class="metric-card"><div class="label">Funnel口径</div><div class="value" style="font-size:13px">ADIMP → ADPV → ADO</div><div class="context">CTR=ADPV/ADIMP</div></div>';
  html += '</div>';

  html += '<div class="site-filter-bar" style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:2px 0 10px">';
  html += '<span style="font-size:11px;color:var(--muted);font-weight:650;margin-right:4px">Site</span>';
  html += '<button class="listing-site active" data-site="__ALL__" style="border:1px solid var(--ink);background:var(--ink);color:var(--surface);border-radius:14px;padding:3px 10px;font-size:11px;cursor:pointer">All</button>';
  sites.forEach(function(site) {
    html += '<button class="listing-site" data-site="' + esc(site) + '" style="border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:14px;padding:3px 10px;font-size:11px;cursor:pointer">' + esc(site) + '</button>';
  });
  html += '</div>';

  function itemBars(activeSite) {
    var filtered = (activeSite === "__ALL__" ? topAdg : rows("site_top_adg").filter(function(r){ return rowSite(r) === activeSite; }))
      .sort(function(a,b){ return (num(b,"mtd_adg")||0) - (num(a,"mtd_adg")||0); })
      .slice(0, 8);
    if (!filtered.length) return '<div class="muted" style="padding:12px">该站点暂无Top listing数据</div>';
    var localMax = Math.max.apply(null, filtered.map(function(r){ return num(r,"mtd_adg") || 0; }).concat([1]));
    var out = '<div style="display:flex;flex-direction:column;gap:7px">';
    filtered.forEach(function(item, idx) {
      var adg = num(item, "mtd_adg") || 0;
      var w = Math.max(3, adg / localMax * 100);
      out += '<div style="display:grid;grid-template-columns:26px minmax(180px,1fr) 92px;gap:8px;align-items:center">';
      out += '<div style="width:22px;height:22px;border-radius:50%;display:grid;place-items:center;background:var(--accent-soft);color:var(--accent-dark);font-weight:800;font-size:11px">' + (idx + 1) + '</div>';
      out += '<div style="min-width:0"><div style="font-size:11px;font-weight:750;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + esc(shortName(item, 72)) + '</div>';
      out += '<div style="height:7px;background:var(--line-soft);border-radius:5px;overflow:hidden;margin-top:4px"><div style="width:' + w.toFixed(1) + '%;height:100%;background:var(--accent)"></div></div></div>';
      out += '<div style="text-align:right;font-size:11px;font-weight:750">' + formatCompact(adg) + '<div style="font-size:10px;color:var(--muted);font-weight:500">' + esc(rowSite(item)) + '</div></div>';
      out += '</div>';
    });
    out += '</div>';
    return out;
  }

  function movementRows(activeSite, rankType) {
    var selected = rows(activeSite === "__ALL__" ? rankType.replace("site_", "top_") : rankType)
      .filter(function(r) { return activeSite === "__ALL__" || rowSite(r) === activeSite; });
    selected = selected.sort(function(a,b) {
      if (rankType.indexOf("loss") >= 0) return (num(a,"adg_delta")||0) - (num(b,"adg_delta")||0);
      return (num(b,"adg_delta")||0) - (num(a,"adg_delta")||0);
    }).slice(0, 8);
    var title = rankType.indexOf("loss") >= 0 ? "跌幅最多Listing排查" : "增长最多Listing共性";
    var out = '<div><div style="font-size:12px;font-weight:800;margin:0 0 6px">' + title + '</div>';
    if (!selected.length) return out + '<div class="muted" style="padding:10px">暂无可展示listing</div></div>';
    out += '<table class="report-table"><thead><tr><th>Listing</th><th>Site</th><th>ADG</th><th>ADG Δ</th><th>曝光</th><th>CTR</th><th>CR</th><th>Driver</th></tr></thead><tbody>';
    selected.forEach(function(item) {
      out += '<tr><td><strong>' + esc(shortName(item, 46)) + '</strong><div style="font-size:10px;color:var(--muted)">' + esc(val(item,"shop_name") || val(item,"shop_id") || "") + '</div></td>';
      out += '<td>' + esc(rowSite(item)) + '</td>';
      out += '<td>' + formatCompact(num(item,"mtd_adg") || 0) + '</td>';
      out += '<td class="' + toneClass(num(item,"adg_delta")) + '">' + deltaText(item,"adg_delta") + '</td>';
      out += '<td>' + formatCompact(num(item,"mtd_adimp") || 0) + '</td>';
      out += '<td>' + pctText(val(item,"ctr")) + '</td>';
      out += '<td>' + pctText(val(item,"cr")) + '</td>';
      out += '<td><span class="pill" style="font-size:10px">' + esc(val(item,"primary_driver") || "—") + '</span></td></tr>';
    });
    out += '</tbody></table></div>';
    return out;
  }

  function render(activeSite) {
    return '<div style="display:grid;grid-template-columns:minmax(280px,.9fr) minmax(420px,1.4fr);gap:12px;align-items:start">' +
      '<div style="border:1px solid var(--line);border-radius:8px;background:var(--surface);padding:10px"><div style="font-size:12px;font-weight:800;margin-bottom:8px">卖得最好的商品</div>' + itemBars(activeSite) + '</div>' +
      '<div style="display:flex;flex-direction:column;gap:12px">' + movementRows(activeSite, "site_growth") + movementRows(activeSite, "site_loss") + '</div>' +
      '</div>';
  }

  html += '<div class="listing-body">' + render("__ALL__") + '</div>';
  html += '<div style="font-size:10px;color:var(--muted);margin-top:8px">数据口径：来自 cncbbi_general.autodeck__dws_item_rpt_mi，CTR = mtd_adpv / mtd_adimp，CR = mtd_ado / mtd_adpv。</div>';
  html += '</div>';

  setTimeout(function() {
    var host = document.getElementById(hostId);
    if (!host) return;
    var body = host.querySelector(".listing-body");
    host.addEventListener("click", function(e) {
      var btn = e.target.closest(".listing-site");
      if (!btn) return;
      host.querySelectorAll(".listing-site").forEach(function(b) {
        var active = b === btn;
        b.classList.toggle("active", active);
        b.style.background = active ? "var(--ink)" : "var(--surface)";
        b.style.color = active ? "var(--surface)" : "var(--ink)";
        b.style.borderColor = active ? "var(--ink)" : "var(--line)";
      });
      body.innerHTML = render(btn.getAttribute("data-site"));
    });
  }, 100);

  return html;
}
"""


def build_section_js() -> str:
    return listing_change_chart_js()


SECTION_ID = "sec_listing_change"
FUNC_NAME = "listingChangeChart"
