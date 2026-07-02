#!/usr/bin/env python3
"""
Section 2.4 — ADS Order Efficiency Audit (ADS出单效率审计)

Site-level audit of ads order share, ads GMV share, spend/GMV, ROAS, and
efficiency status. Data is enriched from raw_dws_shop.
"""

from __future__ import annotations


def ams_chart_js() -> str:
    return r"""
function amsChart(model) {
  if (!model || !model.body.length) return emptyStateChart(model);

  var rows = model.body.filter(function(item) {
    return String(val(item, "site") || "").trim() && ((num(item,"total_adg") || 0) > 0 || (num(item,"ads_spend") || 0) > 0);
  });
  if (!rows.length) return emptyStateChart(model);
  rows.sort(function(a,b){ return (num(b,"total_adg")||0) - (num(a,"total_adg")||0); });

  function pctText(item, col) { var n = num(item,col); return n == null ? "—" : formatCompact(n) + "%"; }
  function signedPctText(item, col) { var n = num(item,col); return n == null ? "—" : (n > 0 ? "+" : "") + formatCompact(n) + "%"; }
  function roasText(item) { var n = num(item,"roas"); return n == null ? "—" : n.toFixed(2); }
  var highRoas = rows.filter(function(r){ return (num(r,"ads_spend")||0) > 0; }).sort(function(a,b){ return (num(b,"roas")||0) - (num(a,"roas")||0); })[0];
  var highDepend = rows.slice().sort(function(a,b){ return (num(b,"ads_adg_share")||0) - (num(a,"ads_adg_share")||0); })[0];
  var highSpend = rows.slice().sort(function(a,b){ return (num(b,"ads_spend_gmv")||0) - (num(a,"ads_spend_gmv")||0); })[0];

  var chartId = "ads-eff-" + Math.random().toString(36).slice(2, 6);
  var html = '<div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin-bottom:10px">';
  html += '<div class="metric-card"><div class="label">ROAS最高站点</div><div class="value" style="font-size:16px">' + (highRoas ? esc(val(highRoas,"site")) : "—") + '</div><div class="context">ROAS ' + (highRoas ? roasText(highRoas) : "—") + '</div></div>';
  html += '<div class="metric-card"><div class="label">广告GMV占比最高</div><div class="value" style="font-size:16px">' + (highDepend ? esc(val(highDepend,"site")) : "—") + '</div><div class="context">' + (highDepend ? pctText(highDepend,"ads_adg_share") : "—") + '</div></div>';
  html += '<div class="metric-card"><div class="label">Spend/GMV最高</div><div class="value" style="font-size:16px">' + (highSpend ? esc(val(highSpend,"site")) : "—") + '</div><div class="context">' + (highSpend ? pctText(highSpend,"ads_spend_gmv") : "—") + '</div></div>';
  html += '<div class="metric-card"><div class="label">HE1 Ads ADG %</div><div class="value" style="font-size:13px">ads_adg / total_adg</div><div class="context">raw无独立HE1字段</div></div>';
  html += '</div>';
  html += '<div id="' + chartId + '" style="width:100%;height:320px" role="img" aria-label="ADS efficiency scatter"></div>';

  setTimeout(function() {
    var dom = document.getElementById(chartId);
    if (!dom) return;
    function tryInit() {
      if (dom.clientWidth === 0) { setTimeout(tryInit, 150); return; }
      var existing = echarts.getInstanceByDom(dom);
      if (existing) existing.dispose();
      var chart = echarts.init(dom);
      var data = rows.map(function(r) {
        return [num(r,"ads_spend_gmv") || 0, num(r,"ads_adg_share") || 0, num(r,"roas") || 0, val(r,"site"), val(r,"efficiency_status") || ""];
      });
      chart.setOption({
        tooltip: { backgroundColor: "rgba(32,33,36,.94)", borderColor: "transparent", textStyle: { color: "#f8fafc", fontSize: 12 },
          formatter: function(p) {
            return "<strong>" + p.value[3] + "</strong><br>Spend/GMV: " + p.value[0].toFixed(1) + "%<br>Ads ADG%: " + p.value[1].toFixed(1) + "%<br>ROAS: " + p.value[2].toFixed(2) + "<br>" + esc(p.value[4]);
          }
        },
        grid: { left: 54, right: 28, top: 18, bottom: 46 },
        xAxis: { name: "Ads Spend / GMV", nameLocation: "middle", nameGap: 28, type: "value", axisLabel: { formatter: "{value}%", fontSize: 10 }, splitLine: { lineStyle: { color: "#edf0f3", type: "dashed" } } },
        yAxis: { name: "Ads ADG %", nameLocation: "middle", nameGap: 38, type: "value", axisLabel: { formatter: "{value}%", fontSize: 10 }, splitLine: { lineStyle: { color: "#edf0f3", type: "dashed" } } },
        series: [{
          type: "scatter",
          symbolSize: 16,
          data: data,
          itemStyle: { color: "#ee4d2d", opacity: .86, borderColor: "#bd3d22", borderWidth: 1 },
          label: { show: true, formatter: function(p){ return p.value[3]; }, position: "right", fontSize: 10, color: "#202124" },
          markLine: { silent: true, symbol: "none", lineStyle: { color: "#9aa0a6", type: "dashed" }, data: [{ xAxis: 8 }, { yAxis: 25 }] }
        }]
      });
      var ro = new ResizeObserver(function() { chart.resize(); });
      ro.observe(dom); dom._resizeObserver = ro;
    }
    tryInit();
  }, 180);

  html += '<div style="margin-top:10px"><table class="report-table"><thead><tr>';
  html += '<th>Site</th><th>Total ADG</th><th>Ads ADO%</th><th>Ads ADG%</th><th>Spend/GMV</th><th>ROAS</th><th>Ads ADG MoM</th><th>Spend MoM</th><th>判断</th>';
  html += '</tr></thead><tbody>';
  rows.forEach(function(item) {
    var roas = num(item,"roas");
    var roasTone = roas == null ? "" : (roas >= 5 ? "up-text" : (roas < 2 ? "dn-text" : ""));
    html += '<tr><td><strong>' + esc(val(item,"site") || "") + '</strong></td>';
    html += '<td>' + formatCompact(num(item,"total_adg") || 0) + '</td>';
    html += '<td>' + pctText(item,"ads_ado_share") + '</td>';
    html += '<td>' + pctText(item,"ads_adg_share") + '</td>';
    html += '<td>' + pctText(item,"ads_spend_gmv") + '</td>';
    html += '<td class="' + roasTone + '">' + roasText(item) + '</td>';
    html += '<td class="' + ((num(item,"ads_adg_mom")||0) > 0 ? "up-text" : ((num(item,"ads_adg_mom")||0) < 0 ? "dn-text" : "")) + '">' + signedPctText(item,"ads_adg_mom") + '</td>';
    html += '<td class="' + ((num(item,"ads_spend_mom")||0) > 0 ? "up-text" : ((num(item,"ads_spend_mom")||0) < 0 ? "dn-text" : "")) + '">' + signedPctText(item,"ads_spend_mom") + '</td>';
    html += '<td><span class="pill" style="font-size:10px">' + esc(val(item,"efficiency_status") || "—") + '</span></td></tr>';
  });
  html += '</tbody></table></div>';
  return html;
}
"""


def build_section_js() -> str:
    return ams_chart_js()


SECTION_ID = "sec_ams"
FUNC_NAME = "amsChart"
