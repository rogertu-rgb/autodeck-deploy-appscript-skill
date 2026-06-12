#!/usr/bin/env python3
"""
Section 2.4 — AMS Advertising Efficiency (AMS广告效率审计)

ROAS heatmap (site × L1) + detail table with spend, ACP.
"""

from __future__ import annotations


def ams_chart_js() -> str:
    return r"""
function amsChart(model) {
  if (!model || !model.body.length) return emptyStateChart(model);

  var sites = [], l1s = [], siteSet = {}, l1Set = {};
  var heatData = [], rows = [];

  model.body.forEach(function(item) {
    var site = String(val(item, "site") || "").trim();
    var l1 = String(val(item, "l1") || "").trim();
    var roas = num(item, "roas");
    var spend = num(item, "spend") || 0;
    var adsAdg = num(item, "ads_adg") || 0;
    var acp = num(item, "acp");
    if (!site || !l1) return;
    if (!siteSet[site]) { siteSet[site] = true; sites.push(site); }
    if (!l1Set[l1]) { l1Set[l1] = true; l1s.push(l1); }
    rows.push({ site: site, l1: l1, roas: roas, spend: spend, adsAdg: adsAdg, acp: acp });
    heatData.push([l1s.indexOf(l1), sites.indexOf(site), roas != null ? parseFloat(roas.toFixed(1)) : 0]);
  });

  if (!sites.length) return emptyStateChart(model);

  var maxRoas = 5;
  rows.forEach(function(r) { if (r.roas != null) maxRoas = Math.max(maxRoas, r.roas); });

  // Heatmap
  var chartId = "ams-heat-" + Math.random().toString(36).slice(2, 6);
  var html = '<div id="' + chartId + '" style="width:100%;height:' + Math.max(180, sites.length * 30 + 60) + 'px" role="img" aria-label="AMS ROAS heatmap"></div>';

  setTimeout(function() {
    var dom = document.getElementById(chartId);
    if (!dom) return;
    function tryInit() {
      if (dom.clientWidth === 0) { setTimeout(tryInit, 150); return; }
      var existing = echarts.getInstanceByDom(dom);
      if (existing) existing.dispose();
      var chart = echarts.init(dom);
      chart.setOption({
        tooltip: { backgroundColor: "rgba(32,33,36,.94)", borderColor: "transparent", textStyle: { color: "#fff", fontSize: 12 },
          formatter: function(p) { return "<strong>" + sites[p.value[1]] + " × " + l1s[p.value[0]] + "</strong><br>ROAS: " + p.value[2].toFixed(1); }
        },
        grid: { left: 50, right: 30, top: 5, bottom: 60 },
        xAxis: { type: "category", data: l1s, position: "bottom", axisLabel: { fontSize: 10, rotate: 20 } },
        yAxis: { type: "category", data: sites, axisLabel: { fontSize: 11, fontWeight: 700 } },
        visualMap: { min: 0, max: maxRoas, calculable: true, orient: "horizontal", left: "center", bottom: 0,
          inRange: { color: ["#b42318", "#f5f5f5", "#137a4b"] }, text: ["High ROAS", "Low"], textStyle: { fontSize: 9 } },
        series: [{ type: "heatmap", data: heatData, label: { show: true, fontSize: 10,
          formatter: function(p) { var v = p.value[2]; return v > 0 ? v.toFixed(1) : ""; }
        }, emphasis: { itemStyle: { shadowBlur: 8 } } }]
      });
      var ro = new ResizeObserver(function() { chart.resize(); });
      ro.observe(dom); dom._resizeObserver = ro;
    }
    tryInit();
  }, 200);

  // Detail table
  html += '<div style="margin-top:8px"><table class="report-table"><thead><tr>';
  html += '<th>Site</th><th>L1</th><th>Ads ADG</th><th>Spend</th><th>ROAS</th><th>ACP</th>';
  html += '</tr></thead><tbody>';
  rows.sort(function(a,b){return (b.roas||0)-(a.roas||0);});
  rows.forEach(function(r) {
    var roasTone = r.roas != null ? (r.roas >= 5 ? "up-text" : (r.roas < 2 ? "dn-text" : "")) : "";
    html += '<tr><td>' + esc(r.site) + '</td><td><strong>' + esc(r.l1) + '</strong></td>';
    html += '<td>' + formatCompact(r.adsAdg) + '</td>';
    html += '<td>' + formatCompact(r.spend) + '</td>';
    html += '<td class="' + roasTone + '">' + (r.roas != null ? r.roas.toFixed(1) : "—") + '</td>';
    html += '<td>' + (r.acp != null ? formatCompact(r.acp) : "—") + '</td>';
    html += '</tr>';
  });
  html += '</tbody></table></div>';

  return html;
}
"""


def build_section_js() -> str:
    return ams_chart_js()


SECTION_ID = "sec_ams"
FUNC_NAME = "amsChart"
