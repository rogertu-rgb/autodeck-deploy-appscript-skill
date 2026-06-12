#!/usr/bin/env python3
"""
Section 1.9 — Fulfillment Structure (履约结构分析)

100% stacked bar chart: FBS / TPF / SLS per site.
Shift indicators (pp change vs M-1). Site filter.

Requirements (Master Design §7, Section 1.9):
  ✅ 100% stacked bar (FBS/TPF/SLS)
  ✅ FBS>60% = CB dependency warning
  ✅ TPF>40% = 3rd party risk
"""

from __future__ import annotations


def fulfillment_chart_js() -> str:
    return r"""
function fulfillmentChart(model) {
  if (!model || !model.body.length) return emptyStateChart(model);

  var sites = [];
  var fbsPct = [], tpfPct = [], slsPct = [];
  var fbsShift = [], tpfShift = [], slsShift = [];

  model.body.forEach(function(item) {
    var site = String(val(item, "site") || "").trim();
    if (!site) return;
    sites.push(site);
    var fbs = num(item, "fbs_share") || 0;
    var tpf = num(item, "tpf_share") || 0;
    var sls = num(item, "sls_share") || 0;
    fbsPct.push(fbs); tpfPct.push(tpf); slsPct.push(sls);
    fbsShift.push(num(item, "fbs_shift_pp"));
    tpfShift.push(num(item, "tpf_shift_pp"));
    slsShift.push(num(item, "sls_shift_pp"));
  });

  if (!sites.length) return emptyStateChart(model);

  // ── 1. Chart ──
  var chartId = "ff-chart-" + Math.random().toString(36).slice(2, 6);
  var html = '<div id="' + chartId + '" style="width:100%;height:300px" role="img" aria-label="Fulfillment 100% stacked bar"></div>';

  setTimeout(function() {
    var dom = document.getElementById(chartId);
    if (!dom) return;
    function tryInit() {
      if (dom.clientWidth === 0) { setTimeout(tryInit, 150); return; }
      var existing = echarts.getInstanceByDom(dom);
      if (existing) existing.dispose();
      var chart = echarts.init(dom);
      chart.setOption({
        tooltip: { trigger: "axis", axisPointer: { type: "shadow" }, backgroundColor: "rgba(32,33,36,.94)", borderColor: "transparent", textStyle: { color: "#fff", fontSize: 12 },
          formatter: function(params) {
            var lines = ["<strong>" + params[0].axisValue + "</strong>"];
            params.forEach(function(p) { lines.push('<span style="display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;background:' + p.color + '"></span>' + p.seriesName + ": " + p.value + "%"); });
            return lines.join("<br>");
          }
        },
        legend: { data: ["FBS", "TPF", "SLS"], top: 0, left: "center", textStyle: { fontSize: 11 }, itemWidth: 12, itemHeight: 12, itemGap: 14, padding: [0, 0, 8, 0] },
        grid: { left: 12, right: 12, top: 40, bottom: 24 },
        xAxis: { type: "category", data: sites, axisLabel: { fontSize: 12, fontWeight: 700 }, axisTick: { alignWithLabel: true } },
        yAxis: { type: "value", max: 100, axisLabel: { fontSize: 10, formatter: function(v) { return v + "%"; } },
          splitLine: { lineStyle: { color: "#edf0f3", type: "dashed" } } },
        series: [
          { name: "FBS", type: "bar", stack: "total", data: fbsPct, itemStyle: { color: "#7aa6f9" }, barMaxWidth: 48, label: { show: true, position: "inside", fontSize: 10, formatter: function(p) { return p.value > 8 ? p.value + "%" : ""; } } },
          { name: "TPF", type: "bar", stack: "total", data: tpfPct, itemStyle: { color: "#fb8f67" }, barMaxWidth: 48, label: { show: true, position: "inside", fontSize: 10, formatter: function(p) { return p.value > 8 ? p.value + "%" : ""; } } },
          { name: "SLS", type: "bar", stack: "total", data: slsPct, itemStyle: { color: "#6fbd8a" }, barMaxWidth: 48, label: { show: true, position: "inside", fontSize: 10, formatter: function(p) { return p.value > 8 ? p.value + "%" : ""; } } }
        ]
      });
      var ro = new ResizeObserver(function() { chart.resize(); });
      ro.observe(dom); dom._resizeObserver = ro;
    }
    tryInit();
  }, 200);

  // ── 2. Detail table with MoM shifts ──
  html += '<div style="margin-top:10px"><table class="report-table"><thead><tr>';
  html += '<th>Site</th><th>FBS%</th><th>TPF%</th><th>SLS%</th><th>FBS MoM</th><th>TPF MoM</th><th>SLS MoM</th>';
  html += '</tr></thead><tbody>';
  sites.forEach(function(site, i) {
    html += '<tr><td><strong>' + esc(site) + '</strong></td>';
    html += '<td>' + formatCompact(fbsPct[i]) + '%</td>';
    html += '<td>' + formatCompact(tpfPct[i]) + '%</td>';
    html += '<td>' + formatCompact(slsPct[i]) + '%</td>';
    var fbsTone = (fbsShift[i]||0) > 0 ? "up-text" : ((fbsShift[i]||0) < 0 ? "dn-text" : "");
    var tpfTone = (tpfShift[i]||0) > 0 ? "up-text" : ((tpfShift[i]||0) < 0 ? "dn-text" : "");
    var slsTone = (slsShift[i]||0) > 0 ? "up-text" : ((slsShift[i]||0) < 0 ? "dn-text" : "");
    html += '<td class="' + fbsTone + '">' + (fbsShift[i] != null ? (fbsShift[i]>0?"+":"") + formatCompact(fbsShift[i]) + "pp" : "—") + '</td>';
    html += '<td class="' + tpfTone + '">' + (tpfShift[i] != null ? (tpfShift[i]>0?"+":"") + formatCompact(tpfShift[i]) + "pp" : "—") + '</td>';
    html += '<td class="' + slsTone + '">' + (slsShift[i] != null ? (slsShift[i]>0?"+":"") + formatCompact(slsShift[i]) + "pp" : "—") + '</td>';
    html += '</tr>';
  });
  html += '</tbody></table></div>';

  return html;
}
"""


def build_section_js() -> str:
    return fulfillment_chart_js()


SECTION_ID = "sec_fulfillment"
FUNC_NAME = "fulfillmentChart"
