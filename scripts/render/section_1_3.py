#!/usr/bin/env python3
"""
Section 1.3 — Site × L1 Performance Matrix (站点×品类表现矩阵)

Chart: ECharts heatmap — site on y-axis, L1 on x-axis, cell color = seller MoM%.
Anomaly table: ranked by |gap_pp| (seller MoM% − market MoM%).
Pattern detection: site-level vs category-level vs isolated anomaly.

Requirements (from Master Design §7, Section 1.3):
  ✅ Heatmap (site×L1, color=MoM%)
  ✅ Pattern recognition: site-level / category-level / isolated
  ✅ Anomaly ranking by |gap_pp|
  ✅ gap = seller_MoM% - mkt_MoM%. No absolute market values.
"""

from __future__ import annotations


def l1_matrix_chart_js() -> str:
    """ECharts heatmap + anomaly ranking table."""
    return r"""
function l1MatrixChart(model) {
  if (!model || !model.body.length) return emptyStateChart(model);

  // ── 1. Extract site×L1 matrix data ──
  var sites = [];
  var l1s = [];
  var siteSet = {}, l1Set = {};
  var cells = [];  // [siteIdx, l1Idx, mom%, gap_pp, adg_mtd, share%]

  model.body.forEach(function(item) {
    var site = String(val(item, "site") || "").trim();
    var l1 = String(val(item, "l1") || "").trim();
    var mom = num(item, "adg_mom");
    var gap = num(item, "gap_pp");
    var adg = num(item, "adg_mtd") || 0;
    var share = num(item, "share_in_site") || 0;

    if (!site || !l1) return;
    if (!siteSet[site]) { siteSet[site] = true; sites.push(site); }
    if (!l1Set[l1]) { l1Set[l1] = true; l1s.push(l1); }
    cells.push({ site: site, l1: l1, mom: mom, gap: gap, adg: adg, share: share });
  });

  sites.sort(); l1s.sort();

  // Build index lookup
  var siteIdx = {}; sites.forEach(function(s, i) { siteIdx[s] = i; });
  var l1Idx = {}; l1s.forEach(function(l, i) { l1Idx[l] = i; });

  // Build heatmap data array: [l1Idx, siteIdx, mom%]
  var heatData = [];
  var gapList = [];
  cells.forEach(function(c) {
    heatData.push([l1Idx[c.l1], siteIdx[c.site], c.mom != null ? parseFloat(c.mom.toFixed(1)) : 0]);
    if (c.gap != null) {
      gapList.push({ site: c.site, l1: c.l1, gap: c.gap, mom: c.mom, adg: c.adg, share: c.share });
    }
  });

  // ── 2. Heatmap chart ──
  var chartId = "chart-" + model.id + "-" + Math.random().toString(36).slice(2, 8);

  // Find max abs MoM% for symmetric color scale
  var maxAbsMom = 5;
  cells.forEach(function(c) { if (c.mom != null) maxAbsMom = Math.max(maxAbsMom, Math.abs(c.mom)); });

  var option = {
    tooltip: {
      backgroundColor: "rgba(32,33,36,.94)",
      borderColor: "transparent",
      textStyle: { color: "#fff", fontSize: 12 },
      formatter: function(params) {
        var li = params.value[0], si = params.value[1], mom = params.value[2];
        return "<strong>" + l1s[li] + " × " + sites[si] + "</strong><br>MoM: " + formatCompact(mom) + "%";
      }
    },
    grid: { left: 60, right: 40, top: 10, bottom: 70 },
    xAxis: {
      type: "category", data: l1s,
      position: "bottom",
      axisLabel: { fontSize: 10, rotate: 30,
        formatter: function(v) { return v.length > 12 ? v.slice(0, 11) + "…" : v; }
      }
    },
    yAxis: {
      type: "category", data: sites,
      axisLabel: { fontSize: 12, fontWeight: 700 }
    },
    visualMap: {
      min: -maxAbsMom, max: maxAbsMom,
      calculable: true,
      orient: "horizontal",
      left: "center", bottom: 0,
      inRange: { color: ["#137a4b", "#f5f5f5", "#ee4d2d"] },
      text: ["+MoM%", "−MoM%"],
      textStyle: { fontSize: 10 }
    },
    series: [{
      type: "heatmap",
      data: heatData,
      label: {
        show: true,
        fontSize: 10,
        formatter: function(params) {
          var v = params.value[2];
          if (v === 0 || v == null) return "";
          return formatCompact(v) + "%";
        }
      },
      emphasis: {
        itemStyle: { shadowBlur: 10, shadowColor: "rgba(0,0,0,.3)" }
      }
    }]
  };

  // ── 3. Anomaly ranking table (by |gap_pp|) ──
  gapList.sort(function(a, b) { return Math.abs(b.gap) - Math.abs(a.gap); });

  var html = '<div class="chart-container">';
  html += '<div id="' + chartId + '" style="width:100%;height:340px" role="img" aria-label="Site×L1 MoM% heatmap"></div>';
  html += '</div>';

  // ── 4. Pattern detection ──
  var siteAnomalies = {}, l1Anomalies = {};
  gapList.forEach(function(g) {
    if (Math.abs(g.gap) > 5) {
      siteAnomalies[g.site] = (siteAnomalies[g.site] || 0) + 1;
      l1Anomalies[g.l1] = (l1Anomalies[g.l1] || 0) + 1;
    }
  });

  var patternSites = Object.keys(siteAnomalies).filter(function(s) { return siteAnomalies[s] >= l1s.length * 0.4; });
  var patternL1s = Object.keys(l1Anomalies).filter(function(l) { return l1Anomalies[l] >= sites.length * 0.4; });
  var patternLabel = "";
  if (patternSites.length && patternL1s.length) patternLabel = "Mixed: site + category level signals";
  else if (patternSites.length) patternLabel = "Site-driven: " + patternSites.join(", ") + " showing broad anomalies";
  else if (patternL1s.length) patternLabel = "Category-driven: " + patternL1s.join(", ") + " anomalous across sites";
  else patternLabel = "Isolated anomalies — no broad site or category pattern";

  html += '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:10px">';
  html += '<div class="metric-card" style="flex:1 1 220px;min-width:180px">';
  html += '<div class="label">Pattern</div>';
  html += '<div class="value" style="font-size:13px">' + patternLabel + '</div>';
  html += '</div>';
  html += '<div class="metric-card" style="flex:1 1 140px;min-width:120px">';
  html += '<div class="label">Site×L1 Pairs</div>';
  html += '<div class="value" style="font-size:16px">' + gapList.length + '</div>';
  html += '<div class="context">' + sites.length + ' sites × ' + l1s.length + ' L1s</div>';
  html += '</div>';
  html += '<div class="metric-card" style="flex:1 1 140px;min-width:120px">';
  html += '<div class="label">Anomalies (|gap|>5pp)</div>';
  html += '<div class="value" style="font-size:16px">' + gapList.filter(function(g) { return Math.abs(g.gap) > 5; }).length + '</div>';
  html += '<div class="context">of ' + gapList.length + ' total</div>';
  html += '</div>';
  html += '</div>';

  // ── 5. Anomaly table ──
  var topAnomalies = gapList.filter(function(g) { return Math.abs(g.gap) > 3; }).slice(0, 12);
  if (topAnomalies.length) {
    html += '<div style="margin-top:10px"><div style="font-size:11px;font-weight:700;color:var(--muted);padding:4px 0">Top Anomalies (ranked by |gap_pp|)</div>';
    html += '<table class="report-table"><thead><tr>';
    html += '<th>Site</th><th>L1</th><th>ADG MTD</th><th>MoM%</th><th>Gap</th><th>Share</th>';
    html += '</tr></thead><tbody>';
    topAnomalies.forEach(function(a) {
      var gapTone = a.gap > 0 ? "up-text" : "dn-text";
      var momTone = a.mom > 0 ? "up-text" : "dn-text";
      html += '<tr>';
      html += '<td>' + esc(a.site) + '</td><td><strong>' + esc(a.l1) + '</strong></td>';
      html += '<td>' + formatCompact(a.adg) + '</td>';
      html += '<td class="' + momTone + '">' + (a.mom != null ? formatCompact(a.mom) + '%' : '—') + '</td>';
      html += '<td class="' + gapTone + '">' + formatCompact(a.gap) + 'pp</td>';
      html += '<td>' + formatCompact(a.share) + '%</td>';
      html += '</tr>';
    });
    html += '</tbody></table></div>';
  }

  setTimeout(function() {
    var dom = document.getElementById(chartId);
    if (!dom || dom.clientWidth === 0) return;
    var existing = echarts.getInstanceByDom(dom);
    if (existing) existing.dispose();
    var chart = echarts.init(dom);
    chart.setOption(option);
    var ro = new ResizeObserver(function() { chart.resize(); });
    ro.observe(dom);
    dom._resizeObserver = ro;
    chart.on("click", function() { dom.classList.toggle("chart-pinned"); });
  }, 150);

  return html;
}
"""


def build_section_js() -> str:
    return l1_matrix_chart_js()


SECTION_ID = "sec_l1_matrix"
FUNC_NAME = "l1MatrixChart"
