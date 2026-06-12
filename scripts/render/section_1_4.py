#!/usr/bin/env python3
"""
Section 1.4 — L2 Category Drilldown (二级品类钻取)

Same pattern as Section 1.2:
  - Multi-select site filter
  - Heatmap: site × L2, color = MoM%
  - Top 5 Rising (Site × L2) table
  - Top 5 Falling (Site × L2) table

Requirements (from Master Design §7, Section 1.4):
  ✅ Site × L2 heatmap
  ✅ Top 5 rising/falling by MoM%
  ✅ Market MoM% + gap comparison
  ❌ No absolute market L2 values
"""

from __future__ import annotations


def l2_drill_chart_js() -> str:
    return r"""
function l2DrillChart(model) {
  if (!model || !model.body.length) return emptyStateChart(model);

  // ── 1. Extract unique sites and L2s ──
  var allSites = {}, l2Set = {};
  model.body.forEach(function(item) {
    var s = String(val(item, "site") || "").trim();
    var l = String(val(item, "l2") || "").trim();
    if (s) allSites[s] = true;
    if (l) l2Set[l] = true;
  });
  var siteList = Object.keys(allSites).sort();
  var l2List = Object.keys(l2Set).sort();

  // ── 2. Pattern detection ──
  var totalPairs = model.body.length;
  var anomalyPairs = 0;
  var siteAnomalyCount = {}, l2AnomalyCount = {};
  model.body.forEach(function(item) {
    var gap = num(item, "gap_pp");
    var s = String(val(item, "site") || "").trim();
    var l = String(val(item, "l2") || "").trim();
    if (gap != null && Math.abs(gap) > 5) {
      anomalyPairs++;
      siteAnomalyCount[s] = (siteAnomalyCount[s] || 0) + 1;
      l2AnomalyCount[l] = (l2AnomalyCount[l] || 0) + 1;
    }
  });
  var patternSites = Object.keys(siteAnomalyCount).filter(function(s) { return siteAnomalyCount[s] >= l2List.length * 0.4; });
  var patternL2s = Object.keys(l2AnomalyCount).filter(function(l) { return l2AnomalyCount[l] >= siteList.length * 0.4; });
  var patternLabel = "";
  if (patternSites.length && patternL2s.length) patternLabel = "Mixed signals across sites and L2 categories";
  else if (patternSites.length) patternLabel = "Site-driven: " + patternSites.join(", ");
  else if (patternL2s.length) patternLabel = "L2-driven: " + patternL2s.join(", ");
  else patternLabel = "Isolated anomalies — no broad pattern";

  // ── 3. Site filter pills ──
  var filterId = "l2-site-filter-" + Math.random().toString(36).slice(2, 6);
  var html = '<div id="' + filterId + '" class="site-filter-bar" style="display:flex;flex-wrap:wrap;gap:6px;padding:8px 0;align-items:center">';
  html += '<span style="font-size:11px;color:var(--muted);font-weight:650;margin-right:4px">Site:</span>';
  html += '<button class="site-pill active" data-site="__ALL__" style="border:1px solid var(--line);border-radius:14px;padding:3px 10px;font-size:11px;cursor:pointer;background:var(--ink);color:#fff;border-color:var(--ink)">All (' + siteList.length + ')</button>';
  siteList.forEach(function(s) {
    html += '<button class="site-pill active" data-site="' + esc(s) + '" style="border:1px solid var(--line);border-radius:14px;padding:3px 10px;font-size:11px;cursor:pointer;background:var(--accent-soft);color:var(--accent-dark);border-color:var(--accent)">' + esc(s) + '</button>';
  });
  html += '</div>';

  // ── 4. Heatmap: site × L2 MoM% ──
  var heatData = [];
  var maxAbsMom = 5;
  model.body.forEach(function(item) {
    var s = String(val(item, "site") || "").trim();
    var l = String(val(item, "l2") || "").trim();
    var mom = num(item, "adg_mom");
    if (!s || !l) return;
    if (mom != null) maxAbsMom = Math.max(maxAbsMom, Math.abs(mom));
    heatData.push([l2List.indexOf(l), siteList.indexOf(s), mom != null ? parseFloat(mom.toFixed(1)) : 0]);
  });

  var heatmapId = "l2-heat-" + Math.random().toString(36).slice(2, 6);
  html += '<div id="' + heatmapId + '" style="width:100%;height:' + Math.max(180, siteList.length * 28 + 50) + 'px;margin:6px 0" role="img" aria-label="Site×L2 MoM% heatmap"></div>';

  setTimeout(function() {
    var dom = document.getElementById(heatmapId);
    if (!dom) return;
    function tryInitHeatmap() {
      if (dom.clientWidth === 0) { setTimeout(tryInitHeatmap, 150); return; }
      var existing = echarts.getInstanceByDom(dom);
      if (existing) existing.dispose();
      var chart = echarts.init(dom);
      chart.setOption({
        tooltip: {
          backgroundColor: "rgba(32,33,36,.94)", borderColor: "transparent",
          textStyle: { color: "#fff", fontSize: 12 },
          formatter: function(p) { return "<strong>" + siteList[p.value[1]] + " × " + l2List[p.value[0]] + "</strong><br>MoM: " + formatCompact(p.value[2]) + "%"; }
        },
        grid: { left: 50, right: 30, top: 5, bottom: 60 },
        xAxis: { type: "category", data: l2List, position: "bottom", axisLabel: { fontSize: 10, rotate: l2List.length > 4 ? 20 : 0 } },
        yAxis: { type: "category", data: siteList, axisLabel: { fontSize: 11, fontWeight: 700 } },
        visualMap: { min: -maxAbsMom, max: maxAbsMom, calculable: true, orient: "horizontal", left: "center", bottom: 0,
          inRange: { color: ["#137a4b", "#ffffff", "#ee4d2d"] }, text: ["+MoM%", "−MoM%"], textStyle: { fontSize: 9 } },
        series: [{ type: "heatmap", data: heatData, label: { show: true, fontSize: 9,
          formatter: function(p) { var v = p.value[2]; return v === 0 ? "" : formatCompact(v) + "%"; }
        }, emphasis: { itemStyle: { shadowBlur: 8 } } }]
      });
      var ro = new ResizeObserver(function() { chart.resize(); });
      ro.observe(dom);
      dom._resizeObserver = ro;
    }
    tryInitHeatmap();
  }, 180);

  // ── 5. Pattern summary cards ──
  html += '<div style="display:flex;flex-wrap:wrap;gap:8px;margin:8px 0">';
  html += '<div class="metric-card" style="flex:1 1 140px;min-width:120px"><div class="label">Site × L2 Pairs</div><div class="value" style="font-size:16px">' + totalPairs + '</div><div class="context">' + siteList.length + ' sites × ' + l2List.length + ' L2s</div></div>';
  html += '<div class="metric-card" style="flex:1 1 140px;min-width:120px"><div class="label">Anomalies (|gap|>5pp)</div><div class="value" style="font-size:16px">' + anomalyPairs + '</div><div class="context">of ' + totalPairs + ' pairs</div></div>';
  html += '<div class="metric-card" style="flex:2 1 240px;min-width:200px"><div class="label">Pattern</div><div class="value" style="font-size:13px">' + patternLabel + '</div></div>';
  html += '</div>';

  // ── 6. Build tables function (site×L2 granularity) ──
  var buildTables = function(activeSites) {
    var filtered = model.body.filter(function(item) {
      var s = String(val(item, "site") || "").trim();
      return activeSites.__ALL__ || activeSites[s];
    });

    var entries = [];
    filtered.forEach(function(item) {
      var site = String(val(item, "site") || "").trim();
      var l2 = String(val(item, "l2") || "").trim();
      var adg = num(item, "adg_mtd") || 0;
      var mom = num(item, "adg_mom");
      var mktMom = num(item, "mkt_adg_mom");
      var gap = num(item, "gap_pp");
      var share = num(item, "share_in_l1") || 0;
      if (!site || !l2) return;
      entries.push({ site: site, l2: l2, adg_mtd: adg, adg_mom: mom, mkt_adg_mom: mktMom, gap_pp: gap, share_pct: share });
    });

    var gainers = entries.filter(function(e) { return e.adg_mom != null && e.adg_mom > 0; });
    var losers = entries.filter(function(e) { return e.adg_mom != null && e.adg_mom < 0; });
    gainers.sort(function(a, b) { return b.adg_mom - a.adg_mom; });
    losers.sort(function(a, b) { return a.adg_mom - b.adg_mom; });
    var topGainers = gainers.slice(0, 5);
    var topLosers = losers.slice(0, 5);

    var renderTable = function(title, rows, tone) {
      var t = '<div style="margin-bottom:12px">';
      t += '<div style="font-size:12px;font-weight:700;padding:6px 0;color:var(--' + (tone === 'up' ? 'up' : 'down') + ')">' + title + '</div>';
      if (!rows.length) {
        t += '<div class="muted" style="padding:8px;font-size:11px">No ' + (tone === 'up' ? 'gainers' : 'losers') + ' in selected sites</div>';
      } else {
        t += '<table class="report-table"><thead><tr>';
        t += '<th>Site</th><th>L2</th><th>ADG MTD</th><th>MoM%</th><th>Market MoM%</th><th>Gap</th><th>Share%</th>';
        t += '</tr></thead><tbody>';
        rows.forEach(function(r) {
          var momTone = r.adg_mom > 0 ? 'up-text' : 'dn-text';
          var gapTone = r.gap_pp != null ? (r.gap_pp > 0 ? 'up-text' : 'dn-text') : '';
          t += '<tr>';
          t += '<td>' + esc(r.site) + '</td>';
          t += '<td><strong>' + esc(r.l2) + '</strong></td>';
          t += '<td>' + formatCompact(r.adg_mtd) + '</td>';
          t += '<td class="' + momTone + '">' + (r.adg_mom != null ? formatCompact(r.adg_mom) + '%' : '—') + '</td>';
          t += '<td>' + (r.mkt_adg_mom != null ? formatCompact(r.mkt_adg_mom) + '%' : '—') + '</td>';
          t += '<td class="' + gapTone + '">' + (r.gap_pp != null ? formatCompact(r.gap_pp) + 'pp' : '—') + '</td>';
          t += '<td>' + (r.share_pct > 0 ? formatCompact(r.share_pct) + '%' : '—') + '</td>';
          t += '</tr>';
        });
        t += '</tbody></table>';
      }
      t += '</div>';
      return t;
    };

    return renderTable('⬆ Top 5 Rising (Site × L2)', topGainers, 'up') +
           renderTable('⬇ Top 5 Falling (Site × L2)', topLosers, 'down');
  };

  // ── 7. Initial render ──
  var tableContainerId = "l2-tables-" + Math.random().toString(36).slice(2, 6);
  html += '<div id="' + tableContainerId + '">';
  html += buildTables({ __ALL__: true });
  html += '</div>';

  // ── 8. Filter interactions ──
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
      if (activePills.length === 0) {
        document.getElementById(tableContainerId).innerHTML = '<div class="muted" style="padding:16px">Select at least one site to view L2 data.</div>';
        return;
      }
      document.getElementById(tableContainerId).innerHTML = buildTables(activeSites);
    });
  }, 100);

  return html;
}
"""


def build_section_js() -> str:
    return l2_drill_chart_js()


SECTION_ID = "sec_l2_drill"
FUNC_NAME = "l2DrillChart"
