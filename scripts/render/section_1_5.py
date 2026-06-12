#!/usr/bin/env python3
"""
Section 1.5 — L3 Granular Diagnosis (三级品类粒度诊断)

Same pattern as L1/L2:
  - Multi-select site filter
  - Heatmap: site × L3, color = MoM%
  - Growth positioning card (p10/p25/p50 benchmarks)
  - Top 5 Rising (Site × L3) table
  - Top 5 Falling (Site × L3) table
"""

from __future__ import annotations


def l3_granular_chart_js() -> str:
    return r"""
function l3GranularChart(model) {
  if (!model || !model.body.length) return emptyStateChart(model);

  var allSites = {}, l3Set = {};
  model.body.forEach(function(item) {
    var s = String(val(item, "site") || "").trim();
    var l = String(val(item, "l3") || "").trim();
    if (s) allSites[s] = true;
    if (l) l3Set[l] = true;
  });
  var siteList = Object.keys(allSites).sort();
  var l3List = Object.keys(l3Set).sort();

  // Pattern detection
  var totalPairs = model.body.length;
  var anomalyPairs = 0;
  model.body.forEach(function(item) {
    var mom = num(item, "adg_mom");
    if (mom != null && Math.abs(mom) > 10) anomalyPairs++;
  });

  // Heatmap
  var heatData = [];
  var maxAbsMom = 5;
  model.body.forEach(function(item) {
    var s = String(val(item, "site") || "").trim();
    var l = String(val(item, "l3") || "").trim();
    var mom = num(item, "adg_mom");
    if (!s || !l) return;
    if (mom != null) maxAbsMom = Math.max(maxAbsMom, Math.abs(mom));
    heatData.push([l3List.indexOf(l), siteList.indexOf(s), mom != null ? parseFloat(mom.toFixed(1)) : 0]);
  });

  // Site filter
  var filterId = "l3-site-filter-" + Math.random().toString(36).slice(2, 6);
  var html = '<div id="' + filterId + '" class="site-filter-bar" style="display:flex;flex-wrap:wrap;gap:6px;padding:8px 0;align-items:center">';
  html += '<span style="font-size:11px;color:var(--muted);font-weight:650;margin-right:4px">Site:</span>';
  html += '<button class="site-pill active" data-site="__ALL__" style="border:1px solid var(--line);border-radius:14px;padding:3px 10px;font-size:11px;cursor:pointer;background:var(--ink);color:#fff;border-color:var(--ink)">All (' + siteList.length + ')</button>';
  siteList.forEach(function(s) {
    html += '<button class="site-pill active" data-site="' + esc(s) + '" style="border:1px solid var(--line);border-radius:14px;padding:3px 10px;font-size:11px;cursor:pointer;background:var(--accent-soft);color:var(--accent-dark);border-color:var(--accent)">' + esc(s) + '</button>';
  });
  html += '</div>';

  // Heatmap
  var heatmapId = "l3-heat-" + Math.random().toString(36).slice(2, 6);
  html += '<div id="' + heatmapId + '" style="width:100%;height:' + Math.max(180, siteList.length * 28 + 50) + 'px;margin:6px 0" role="img" aria-label="Site×L3 MoM% heatmap"></div>';
  setTimeout(function() {
    var dom = document.getElementById(heatmapId);
    if (!dom) return;
    function tryInit() {
      if (dom.clientWidth === 0) { setTimeout(tryInit, 150); return; }
      var existing = echarts.getInstanceByDom(dom);
      if (existing) existing.dispose();
      var chart = echarts.init(dom);
      chart.setOption({
        tooltip: { backgroundColor: "rgba(32,33,36,.94)", borderColor: "transparent", textStyle: { color: "#fff", fontSize: 12 },
          formatter: function(p) { return "<strong>" + siteList[p.value[1]] + " × " + l3List[p.value[0]] + "</strong><br>MoM: " + formatCompact(p.value[2]) + "%"; } },
        grid: { left: 60, right: 30, top: 5, bottom: 60 },
        xAxis: { type: "category", data: l3List, position: "bottom", axisLabel: { fontSize: 9, rotate: 25 } },
        yAxis: { type: "category", data: siteList, axisLabel: { fontSize: 11, fontWeight: 700 } },
        visualMap: { min: -maxAbsMom, max: maxAbsMom, calculable: true, orient: "horizontal", left: "center", bottom: 0,
          inRange: { color: ["#137a4b", "#ffffff", "#ee4d2d"] }, text: ["+MoM%", "−MoM%"], textStyle: { fontSize: 9 } },
        series: [{ type: "heatmap", data: heatData, label: { show: true, fontSize: 9,
          formatter: function(p) { var v = p.value[2]; return v === 0 ? "" : formatCompact(v) + "%"; }
        }, emphasis: { itemStyle: { shadowBlur: 8 } } }]
      });
      var ro = new ResizeObserver(function() { chart.resize(); });
      ro.observe(dom); dom._resizeObserver = ro;
    }
    tryInit();
  }, 180);

  // Growth positioning card
  var totalSellerCnt = 0;
  model.body.forEach(function(item) { totalSellerCnt += num(item, "seller_cnt") || 0; });
  html += '<div style="display:flex;flex-wrap:wrap;gap:8px;margin:8px 0">';
  html += '<div class="metric-card" style="flex:1 1 140px;min-width:120px"><div class="label">Site × L3 Pairs</div><div class="value" style="font-size:16px">' + totalPairs + '</div><div class="context">' + siteList.length + ' sites × ' + l3List.length + ' L3s</div></div>';
  html += '<div class="metric-card" style="flex:1 1 140px;min-width:120px"><div class="label">Volatile L3s (|MoM|>10%)</div><div class="value" style="font-size:16px">' + anomalyPairs + '</div><div class="context">of ' + totalPairs + ' pairs</div></div>';
  html += '<div class="metric-card" style="flex:1 1 140px;min-width:120px"><div class="label">Total Sellers</div><div class="value" style="font-size:16px">' + formatCompact(totalSellerCnt) + '</div><div class="context">Across all L3s</div></div>';
  html += '</div>';

  // Tables
  var buildTables = function(activeSites) {
    var filtered = model.body.filter(function(item) {
      var s = String(val(item, "site") || "").trim();
      return activeSites.__ALL__ || activeSites[s];
    });
    var entries = [];
    filtered.forEach(function(item) {
      var site = String(val(item, "site") || "").trim();
      var l3 = String(val(item, "l3") || "").trim();
      var adg = num(item, "adg_mtd") || 0;
      var mom = num(item, "adg_mom");
      var share = num(item, "share_in_l2") || 0;
      var p50 = num(item, "p50_growth");
      var cnt = num(item, "seller_cnt") || 0;
      if (!site || !l3) return;
      entries.push({ site: site, l3: l3, adg_mtd: adg, adg_mom: mom, share_pct: share, p50: p50, seller_cnt: cnt });
    });
    var gainers = entries.filter(function(e) { return e.adg_mom != null && e.adg_mom > 0; });
    var losers = entries.filter(function(e) { return e.adg_mom != null && e.adg_mom < 0; });
    gainers.sort(function(a, b) { return b.adg_mom - a.adg_mom; });
    losers.sort(function(a, b) { return a.adg_mom - b.adg_mom; });

    var renderTable = function(title, rows, tone) {
      var t = '<div style="margin-bottom:12px">';
      t += '<div style="font-size:12px;font-weight:700;padding:6px 0;color:var(--' + (tone === 'up' ? 'up' : 'down') + ')">' + title + '</div>';
      if (!rows.length) { t += '<div class="muted" style="padding:8px;font-size:11px">No entries</div>'; return t + '</div>'; }
      t += '<table class="report-table"><thead><tr>';
      t += '<th>Site</th><th>L3</th><th>ADG MTD</th><th>MoM%</th><th>P50 Growth</th><th>Share%</th><th>Sellers</th>';
      t += '</tr></thead><tbody>';
      rows.slice(0, 5).forEach(function(r) {
        var momTone = r.adg_mom > 0 ? 'up-text' : 'dn-text';
        var vsP50 = r.adg_mom != null && r.p50 != null ? (r.adg_mom > r.p50 ? '↑ above' : '↓ below') : '';
        t += '<tr>';
        t += '<td>' + esc(r.site) + '</td><td><strong>' + esc(r.l3) + '</strong></td>';
        t += '<td>' + formatCompact(r.adg_mtd) + '</td>';
        t += '<td class="' + momTone + '">' + (r.adg_mom != null ? formatCompact(r.adg_mom) + '%' : '—') + '</td>';
        t += '<td>' + (r.p50 != null ? formatCompact(r.p50) + '% ' + vsP50 : '—') + '</td>';
        t += '<td>' + (r.share_pct > 0 ? formatCompact(r.share_pct) + '%' : '—') + '</td>';
        t += '<td>' + r.seller_cnt + '</td>';
        t += '</tr>';
      });
      t += '</tbody></table></div>';
      return t;
    };
    return renderTable('⬆ Top 5 Rising (Site × L3)', gainers, 'up') +
           renderTable('⬇ Top 5 Falling (Site × L3)', losers, 'down');
  };

  var tableContainerId = "l3-tables-" + Math.random().toString(36).slice(2, 6);
  html += '<div id="' + tableContainerId + '">';
  html += buildTables({ __ALL__: true });
  html += '</div>';

  // Filter interactions
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
    return l3_granular_chart_js()


SECTION_ID = "sec_l3_granular"
FUNC_NAME = "l3GranularChart"
