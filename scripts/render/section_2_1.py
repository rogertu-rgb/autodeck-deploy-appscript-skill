#!/usr/bin/env python3
"""
Section 2.1 — Subsidy & Promotion Structure (促销补贴结构)

Stacked bar: seller vs platform funding (item rebate + shipping rebate).
CFS/LPP/Campaign promotion share.

Requirements (Master Design §7, Section 2.1):
  ✅ Subsidy breakdown by type
  ✅ Seller vs platform funding comparison
  ✅ CFS/LPP/Campaign visibility
"""

from __future__ import annotations


def subsidy_chart_js() -> str:
    return r"""
function subsidyChart(model) {
  if (!model || !model.body.length) return emptyStateChart(model);

  var sites = [];
  var sellerFundPct = [], platformFundPct = [];
  var cfsShare = [], lppShare = [], campShare = [];
  var subsidyShare = [];
  var totalAdg = [];

  model.body.forEach(function(item) {
    var site = String(val(item, "site") || "").trim();
    if (!site) return;
    sites.push(site);
    sellerFundPct.push(num(item, "seller_funded_share") || 0);
    platformFundPct.push(num(item, "platform_funded_share") || 0);
    cfsShare.push(num(item, "cfs_share") || 0);
    lppShare.push(num(item, "lpp_share") || 0);
    campShare.push(num(item, "campaign_share") || 0);
    subsidyShare.push(num(item, "subsidy_share") || 0);
    totalAdg.push(num(item, "total_adg") || 0);
  });

  if (!sites.length) return emptyStateChart(model);

  // ── 1. Stacked bar: seller vs platform funding % ──
  var chartId = "sub-chart-" + Math.random().toString(36).slice(2, 6);
  var html = '<div id="' + chartId + '" style="width:100%;height:280px" role="img" aria-label="Subsidy funding source stacked bar"></div>';

  setTimeout(function() {
    var dom = document.getElementById(chartId);
    if (!dom) return;
    function tryInit() {
      if (dom.clientWidth === 0) { setTimeout(tryInit, 150); return; }
      var existing = echarts.getInstanceByDom(dom);
      if (existing) existing.dispose();
      var chart = echarts.init(dom);
      chart.setOption({
        tooltip: { trigger: "axis", axisPointer: { type: "shadow" }, backgroundColor: "rgba(32,33,36,.94)", borderColor: "transparent", textStyle: { color: "#fff", fontSize: 12 } },
        legend: { data: ["Seller Funded", "Platform Funded"], top: 0, left: "center", textStyle: { fontSize: 11 }, itemWidth: 12, itemHeight: 12, itemGap: 14, padding: [0, 0, 8, 0] },
        grid: { left: 12, right: 12, top: 40, bottom: 24 },
        xAxis: { type: "category", data: sites, axisLabel: { fontSize: 12, fontWeight: 700 }, axisTick: { alignWithLabel: true } },
        yAxis: { type: "value", axisLabel: { fontSize: 10, formatter: function(v) { return formatCompact(v) + "%"; } },
          splitLine: { lineStyle: { color: "#edf0f3", type: "dashed" } } },
        series: [
          { name: "Seller Funded", type: "bar", stack: "fund", data: sellerFundPct, itemStyle: { color: "#7aa6f9" }, barMaxWidth: 48, label: { show: true, position: "inside", fontSize: 9, formatter: function(p) { return p.value > 12 ? p.value + "%" : ""; } } },
          { name: "Platform Funded", type: "bar", stack: "fund", data: platformFundPct, itemStyle: { color: "#fb8f67" }, barMaxWidth: 48, label: { show: true, position: "inside", fontSize: 9, formatter: function(p) { return p.value > 12 ? p.value + "%" : ""; } } }
        ]
      });
      var ro = new ResizeObserver(function() { chart.resize(); });
      ro.observe(dom); dom._resizeObserver = ro;
    }
    tryInit();
  }, 200);

  // ── 2. Detail table ──
  html += '<div style="margin-top:10px"><table class="report-table"><thead><tr>';
  html += '<th>Site</th><th>ADG</th><th>Subsidy/ADG</th><th>Seller Fund%</th><th>Platform Fund%</th><th>CFS%</th><th>LPP%</th><th>Campaign%</th>';
  html += '</tr></thead><tbody>';
  sites.forEach(function(site, i) {
    html += '<tr><td><strong>' + esc(site) + '</strong></td>';
    html += '<td>' + formatCompact(totalAdg[i]) + '</td>';
    html += '<td>' + formatCompact(subsidyShare[i]) + '%</td>';
    html += '<td>' + formatCompact(sellerFundPct[i]) + '%</td>';
    html += '<td>' + formatCompact(platformFundPct[i]) + '%</td>';
    html += '<td>' + formatCompact(cfsShare[i]) + '%</td>';
    html += '<td>' + formatCompact(lppShare[i]) + '%</td>';
    html += '<td>' + formatCompact(campShare[i]) + '%</td>';
    html += '</tr>';
  });
  html += '</tbody></table></div>';

  return html;
}
"""


def build_section_js() -> str:
    return subsidy_chart_js()


SECTION_ID = "sec_subsidy"
FUNC_NAME = "subsidyChart"
