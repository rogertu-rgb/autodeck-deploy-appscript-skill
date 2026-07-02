#!/usr/bin/env python3
"""
Section 1.9 — Fulfillment Structure (履约结构分析)

Shows current local-fulfillment penetration and whether each site is migrating
toward local fulfillment. Local fulfillment = FBS + TPF. SLS = cross-border.
"""

from __future__ import annotations


def fulfillment_chart_js() -> str:
    return r"""
function fulfillmentChart(model) {
  if (!model || !model.body.length) return emptyStateChart(model);

  var rows = model.body.filter(function(item) {
    return String(val(item, "site") || "").trim() && ((num(item, "fulfillment_ado") || num(item, "total") || 0) > 0);
  });
  if (!rows.length) return emptyStateChart(model);
  rows.sort(function(a,b){ return (num(b,"local_share")||num(b,"fbs_share")||0) - (num(a,"local_share")||num(a,"fbs_share")||0); });

  function pctVal(item, col) { var n = num(item, col); return n == null ? 0 : n; }
  function signedPpLocal(item, col) {
    var n = num(item, col);
    return n == null ? "—" : (n > 0 ? "+" : "") + formatCompact(n) + "pp";
  }
  var avgLocal = rows.reduce(function(s,r){ return s + (num(r,"local_share") || 0); }, 0) / rows.length;
  var topLocal = rows[0];
  var fastest = rows.slice().sort(function(a,b){ return (num(b,"local_shift_pp")||-999) - (num(a,"local_shift_pp")||-999); })[0];
  var laggard = rows.slice().sort(function(a,b){ return (num(a,"local_share")||999) - (num(b,"local_share")||999); })[0];

  var chartId = "fulfill-chart-" + Math.random().toString(36).slice(2, 6);
  var html = '<div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin-bottom:10px">';
  html += '<div class="metric-card"><div class="label">平均本地履约占比</div><div class="value" style="font-size:16px">' + avgLocal.toFixed(1) + '%</div><div class="context">FBS + TPF / tracked ADO</div></div>';
  html += '<div class="metric-card"><div class="label">本地化最高站点</div><div class="value" style="font-size:16px">' + esc(val(topLocal,"site") || "—") + '</div><div class="context">' + formatCompact(num(topLocal,"local_share") || 0) + '% local</div></div>';
  html += '<div class="metric-card"><div class="label">本地化增长最快</div><div class="value up-text" style="font-size:16px">' + esc(val(fastest,"site") || "—") + '</div><div class="context">' + signedPpLocal(fastest,"local_shift_pp") + '</div></div>';
  html += '<div class="metric-card"><div class="label">优先推进站点</div><div class="value" style="font-size:16px">' + esc(val(laggard,"site") || "—") + '</div><div class="context">' + formatCompact(num(laggard,"local_share") || 0) + '% local</div></div>';
  html += '</div>';
  html += '<div id="' + chartId + '" style="width:100%;height:' + Math.max(240, rows.length * 32 + 92) + 'px" role="img" aria-label="Fulfillment local share stacked bar"></div>';

  setTimeout(function() {
    var dom = document.getElementById(chartId);
    if (!dom) return;
    function tryInit() {
      if (dom.clientWidth === 0) { setTimeout(tryInit, 150); return; }
      var existing = echarts.getInstanceByDom(dom);
      if (existing) existing.dispose();
      var chart = echarts.init(dom);
      var sites = rows.map(function(r){ return val(r,"site"); });
      chart.setOption({
        tooltip: { trigger: "axis", axisPointer: { type: "shadow" }, backgroundColor: "rgba(32,33,36,.94)", borderColor: "transparent", textStyle: { color: "var(--surface)", fontSize: 12 },
          formatter: function(params) {
            var idx = params[0].dataIndex;
            var row = rows[idx];
            var lines = ["<strong>" + esc(val(row,"site")) + "</strong>"];
            lines.push("FBS: " + formatCompact(num(row,"fbs_ado") || 0) + " ADO");
            lines.push("TPF: " + formatCompact(num(row,"tpf_ado") || 0) + " ADO");
            lines.push("SLS: " + formatCompact(num(row,"sls_ado") || 0) + " ADO");
            lines.push("Local shift: " + signedPpLocal(row,"local_shift_pp"));
            return lines.join("<br>");
          }
        },
        legend: { data: ["FBS官方仓", "TPF三方仓", "SLS跨境"], top: 0, left: "center", textStyle: { fontSize: 11 }, itemWidth: 12, itemHeight: 12 },
        grid: { left: 54, right: 28, top: 42, bottom: 28 },
        xAxis: { type: "value", max: 100, axisLabel: { formatter: "{value}%", fontSize: 10 }, splitLine: { lineStyle: { color: "#edf0f3", type: "dashed" } } },
        yAxis: { type: "category", data: sites, axisLabel: { fontSize: 11, fontWeight: 700 } },
        series: [
          { name: "FBS官方仓", type: "bar", stack: "fulfill", data: rows.map(function(r){ return pctVal(r,"fbs_share"); }), itemStyle: { color: "#7aa6f9" }, label: { show: true, position: "inside", fontSize: 10, formatter: function(p){ return p.value >= 8 ? p.value.toFixed(0) + "%" : ""; } } },
          { name: "TPF三方仓", type: "bar", stack: "fulfill", data: rows.map(function(r){ return pctVal(r,"tpf_share"); }), itemStyle: { color: "#fb8f67" }, label: { show: true, position: "inside", fontSize: 10, formatter: function(p){ return p.value >= 8 ? p.value.toFixed(0) + "%" : ""; } } },
          { name: "SLS跨境", type: "bar", stack: "fulfill", data: rows.map(function(r){ return pctVal(r,"sls_share"); }), itemStyle: { color: "#6fbd8a" }, label: { show: true, position: "inside", fontSize: 10, formatter: function(p){ return p.value >= 8 ? p.value.toFixed(0) + "%" : ""; } } }
        ]
      });
      var ro = new ResizeObserver(function() { chart.resize(); });
      ro.observe(dom); dom._resizeObserver = ro;
    }
    tryInit();
  }, 180);

  html += '<div style="margin-top:10px"><table class="report-table"><thead><tr>';
  html += '<th>Site</th><th>Local ADO</th><th>FBS</th><th>TPF</th><th>SLS</th><th>Local%</th><th>Local MoM</th><th>Coverage</th><th>判断</th>';
  html += '</tr></thead><tbody>';
  rows.forEach(function(item) {
    var shift = num(item,"local_shift_pp");
    html += '<tr><td><strong>' + esc(val(item,"site") || "") + '</strong></td>';
    html += '<td>' + formatCompact(num(item,"local_ado") || 0) + '</td>';
    html += '<td>' + formatCompact(num(item,"fbs_ado") || 0) + '</td>';
    html += '<td>' + formatCompact(num(item,"tpf_ado") || 0) + '</td>';
    html += '<td>' + formatCompact(num(item,"sls_ado") || 0) + '</td>';
    html += '<td>' + formatCompact(num(item,"local_share") || 0) + '%</td>';
    html += '<td class="' + (shift > 0 ? "up-text" : (shift < 0 ? "dn-text" : "")) + '">' + signedPpLocal(item,"local_shift_pp") + '</td>';
    html += '<td>' + (num(item,"fulfillment_coverage") != null ? formatCompact(num(item,"fulfillment_coverage")) + '%' : "—") + '</td>';
    html += '<td><span class="pill" style="font-size:10px">' + esc(val(item,"localization_status") || "—") + '</span></td></tr>';
  });
  html += '</tbody></table></div>';
  return html;
}
"""


def build_section_js() -> str:
    return fulfillment_chart_js()


SECTION_ID = "sec_fulfillment"
FUNC_NAME = "fulfillmentChart"
