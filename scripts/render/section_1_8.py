#!/usr/bin/env python3
"""
Section 1.8 — Top Listing Contributions (Top商品贡献榜)

Per-site item ranking. Top 5 Rising / Top 5 Falling by ADG delta.
Multi-select site filter. Data from sec_listing_change_meta (JSON).

Columns: Item ID, Item Name, Shop, Site, MTD ADG, ADG Δ, ADO, ADO MoM%,
         Impression, Clicks, CTR, CR, Price

Requirements (Master Design §7, Section 1.8):
  ✅ Per-site top 5 items
  ✅ item_id, item_name, shop_name, MTD ADG, Δ vs M-1
  ✅ ADO, ADO MoM, Impression, Clicks/Views, CTR, CR
  ✅ Grouped by site with multi-select filter
"""

from __future__ import annotations


def listing_change_chart_js() -> str:
    return r"""
function listingChangeChart(model) {
  var tabs = (window.AUTODECK_LOCAL_DATA && window.AUTODECK_LOCAL_DATA.tabs) || {};
  var metaRows = tabs.sec_listing_change_meta || [];
  if (!metaRows.length) return emptyStateChart(model);

  var metaDict = {};
  metaRows.forEach(function(row) { if (row.length >= 2) metaDict[row[0]] = String(row[1] || ""); });

  // Parse per_site JSON
  var perSite = {};
  try { perSite = JSON.parse((metaDict.per_site || "{}").replace(/\bnan\b/g,"null").replace(/\bNone\b/g,"null").replace(/\bTrue\b/g,"true").replace(/\bFalse\b/g,"false")); } catch(e) {}

  var siteList = Object.keys(perSite).sort();
  if (!siteList.length) return emptyStateChart(model);

  // Collect all items across sites
  var allItems = [];
  siteList.forEach(function(site) {
    var sd = perSite[site] || {};
    (sd.items || []).forEach(function(item) {
      if (item.mtd_adg == null || isNaN(item.mtd_adg)) return;
      item._site = site;
      item._delta = (item.adg_delta != null && isFinite(item.adg_delta)) ? item.adg_delta : 0;
      allItems.push(item);
    });
  });

  // ── 1. Site filter ──
  var filterId = "list-site-filter-" + Math.random().toString(36).slice(2, 6);
  var html = '<div id="' + filterId + '" class="site-filter-bar" style="display:flex;flex-wrap:wrap;gap:6px;padding:8px 0;align-items:center">';
  html += '<span style="font-size:11px;color:var(--muted);font-weight:650;margin-right:4px">Site:</span>';
  html += '<button class="site-pill active" data-site="__ALL__" style="border:1px solid var(--line);border-radius:14px;padding:3px 10px;font-size:11px;cursor:pointer;background:var(--ink);color:#fff;border-color:var(--ink)">All (' + siteList.length + ')</button>';
  siteList.forEach(function(s) {
    html += '<button class="site-pill active" data-site="' + esc(s) + '" style="border:1px solid var(--line);border-radius:14px;padding:3px 10px;font-size:11px;cursor:pointer;background:var(--accent-soft);color:var(--accent-dark);border-color:var(--accent)">' + esc(s) + '</button>';
  });
  html += '</div>';

  // ── 2. Summary ──
  var totalItems = allItems.length;
  var totalAdg = 0;
  allItems.forEach(function(i) { totalAdg += i.mtd_adg || 0; });
  html += '<div style="display:flex;flex-wrap:wrap;gap:8px;margin:8px 0">';
  html += '<div class="metric-card" style="flex:1 1 120px"><div class="label">Total Items</div><div class="value" style="font-size:16px">' + totalItems + '</div><div class="context">' + siteList.length + ' sites</div></div>';
  html += '<div class="metric-card" style="flex:1 1 140px"><div class="label">Total ADG</div><div class="value" style="font-size:16px">' + formatCompact(totalAdg) + '</div><div class="context">Across all items</div></div>';
  html += '<div class="metric-card" style="flex:1 1 140px"><div class="label">Top Item</div><div class="value" style="font-size:13px">' + (allItems.length ? esc((allItems.sort(function(a,b){return (b.mtd_adg||0)-(a.mtd_adg||0);})[0]||{}).item_name || "—").slice(0,40) : "—") + '</div></div>';
  html += '</div>';

  // ── 3. Build tables ──
  var buildTables = function(activeSites) {
    var filtered = allItems.filter(function(item) {
      return activeSites.__ALL__ || activeSites[item._site];
    });

    // Sort by delta
    var topGainers = filtered.filter(function(i) { return i._delta > 0; }).sort(function(a, b) { return b._delta - a._delta; }).slice(0, 5);
    var topLosers = filtered.filter(function(i) { return i._delta < 0; }).sort(function(a, b) { return a._delta - b._delta; }).slice(0, 5);

    var renderTable = function(title, rows, tone) {
      var t = '<div style="margin-bottom:12px">';
      t += '<div style="font-size:12px;font-weight:700;padding:6px 0;color:var(--' + (tone === 'up' ? 'up' : 'down') + ')">' + title + '</div>';
      if (!rows.length) { t += '<div class="muted" style="padding:8px;font-size:11px">No items</div>'; return t + '</div>'; }
      t += '<table class="report-table"><thead><tr>';
      t += '<th>Item ID</th><th>Item</th><th>Shop</th><th>Site</th><th>MTD ADG</th><th>ADG Δ</th><th>ADO</th><th>ADO MoM</th><th>Impr.</th><th>Clicks</th><th>CTR</th><th>CR</th><th>Price</th>';
      t += '</tr></thead><tbody>';
      rows.forEach(function(r) {
        var deltaTone = r._delta > 0 ? "up-text" : "dn-text";
        var adoMom = r.mtd_ado != null && r.m1_ado != null && r.m1_ado > 0 ? ((r.mtd_ado - r.m1_ado) / r.m1_ado * 100) : (r.ado_mom != null ? r.ado_mom : null);
        var adoMomTone = adoMom != null ? (adoMom > 0 ? "up-text" : "dn-text") : "";
        var impr = r.adimp || r.impression || r.mtd_adimp;
        var clicks = r.adclicks || r.clicks || r.mtd_adclicks;
        var ctr = impr > 0 && clicks > 0 ? (clicks / impr * 100) : (r.ctr != null ? r.ctr : null);
        var cr = clicks > 0 && r.mtd_ado != null ? (r.mtd_ado / clicks * 100) : (r.cr != null ? r.cr : null);
        t += '<tr>';
        t += '<td class="shop-id">' + esc(r.item_id || "—") + '</td>';
        t += '<td><strong>' + esc((r.item_name || "").slice(0, 40)) + '</strong></td>';
        t += '<td style="font-size:10px">' + esc((r.shop_name || "").slice(0, 20)) + '</td>';
        t += '<td>' + esc(r._site) + '</td>';
        t += '<td>' + formatCompact(r.mtd_adg || 0) + '</td>';
        t += '<td class="' + deltaTone + '">' + (r._delta > 0 ? "+" : "") + formatCompact(r._delta) + '</td>';
        t += '<td>' + (r.mtd_ado != null ? formatCompact(r.mtd_ado) : "—") + '</td>';
        t += '<td class="' + adoMomTone + '">' + (adoMom != null ? formatCompact(adoMom) + '%' : "—") + '</td>';
        t += '<td>' + (impr != null ? formatCompact(impr) : "—") + '</td>';
        t += '<td>' + (clicks != null ? formatCompact(clicks) : "—") + '</td>';
        t += '<td>' + (ctr != null ? ctr.toFixed(1) + '%' : "—") + '</td>';
        t += '<td>' + (cr != null ? cr.toFixed(1) + '%' : "—") + '</td>';
        t += '<td><span class="pill" style="font-size:10px">' + esc(r.price_range || "—") + '</span></td>';
        t += '</tr>';
      });
      t += '</tbody></table></div>';
      return t;
    };

    return renderTable('⬆ Top 5 Rising Items', topGainers, 'up') +
           renderTable('⬇ Top 5 Falling Items', topLosers, 'down');
  };

  var tableContainerId = "list-tables-" + Math.random().toString(36).slice(2, 6);
  html += '<div id="' + tableContainerId + '">';
  html += buildTables({ __ALL__: true });
  html += '</div>';

  // ── 3b. Build source table from parsed items (so model.table is populated) ──
  var srcHeader = ["item_id","item_name","shop_name","site","mtd_adg","adg_delta","mtd_ado","ado_mom","impression","clicks","ctr","cr","price_range"];
  var srcBody = allItems.map(function(r) {
    var impr = r.adimp || r.impression || r.mtd_adimp;
    var clicks = r.adclicks || r.clicks || r.mtd_adclicks;
    return [r.item_id||"", r.item_name||"", r.shop_name||"", r._site, r.mtd_adg||0, r._delta||0,
            r.mtd_ado!=null?r.mtd_ado:"", r.ado_mom!=null?r.ado_mom:"",
            impr!=null?impr:"", clicks!=null?clicks:"",
            r.ctr!=null?r.ctr:"", r.cr!=null?r.cr:"", r.price_range||""];
  });
  model.table = { header: srcHeader, body: srcBody };

  // ── 4. Filter interactions ──
  setTimeout(function() {
    var filterBar = document.getElementById(filterId);
    if (!filterBar) return;
    filterBar.addEventListener("click", function(e) {
      var pill = e.target.closest(".site-pill");
      if (!pill) return;
      var site = pill.getAttribute("data-site");
      if (site === "__ALL__") {
        var allActive = pill.classList.contains("active");
        filterBar.querySelectorAll(".site-pill").forEach(function(p) {
          if (allActive) { p.classList.remove("active"); p.style.background="#fff"; p.style.color="var(--ink)"; p.style.borderColor="var(--line)"; }
          else { p.classList.add("active"); if (p.getAttribute("data-site") === "__ALL__") { p.style.background="var(--ink)"; p.style.color="#fff"; p.style.borderColor="var(--ink)"; } else { p.style.background="var(--accent-soft)"; p.style.color="var(--accent-dark)"; p.style.borderColor="var(--accent)"; } }
        });
      } else {
        var wasActive = pill.classList.contains("active");
        if (wasActive) { pill.classList.remove("active"); pill.style.background="#fff"; pill.style.color="var(--ink)"; pill.style.borderColor="var(--line)"; }
        else { pill.classList.add("active"); pill.style.background="var(--accent-soft)"; pill.style.color="var(--accent-dark)"; pill.style.borderColor="var(--accent)"; }
        var allBtn = filterBar.querySelector('[data-site="__ALL__"]');
        var anyInactive = filterBar.querySelectorAll('.site-pill[data-site]:not([data-site="__ALL__"]):not(.active)');
        if (anyInactive.length > 0 && allBtn) { allBtn.classList.remove("active"); allBtn.style.background="#fff"; allBtn.style.color="var(--ink)"; allBtn.style.borderColor="var(--line)"; }
        else if (allBtn && anyInactive.length === 0) { allBtn.classList.add("active"); allBtn.style.background="var(--ink)"; allBtn.style.color="#fff"; allBtn.style.borderColor="var(--ink)"; }
      }
      var activePills = filterBar.querySelectorAll('.site-pill.active[data-site]:not([data-site="__ALL__"])');
      var activeSites = {};
      activePills.forEach(function(p) { activeSites[p.getAttribute("data-site")] = true; });
      if (activePills.length === siteList.length) activeSites = { __ALL__: true };
      if (activePills.length === 0) { document.getElementById(tableContainerId).innerHTML = '<div class="muted" style="padding:16px">Select at least one site.</div>'; return; }
      document.getElementById(tableContainerId).innerHTML = buildTables(activeSites);
    });
  }, 100);

  return html;
}
"""


def build_section_js() -> str:
    return listing_change_chart_js()


SECTION_ID = "sec_listing_change"
FUNC_NAME = "listingChangeChart"
