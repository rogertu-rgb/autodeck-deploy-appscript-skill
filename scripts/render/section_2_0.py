#!/usr/bin/env python3
"""
Section 2.0 — Order Source Split (订单来源拆分)

Source levers are not MECE. The visual shows site x source ADO share and
highlights the primary, growth, and loss driver for each site.
"""

from __future__ import annotations


def traffic_channel_chart_js() -> str:
    return r"""
function trafficChannelChart(model) {
  if (!model || !model.body.length) return emptyStateChart(model);

  var rows = model.body.filter(function(item) {
    return String(val(item, "site") || "").trim() && String(val(item, "source_label") || "").trim();
  });
  if (!rows.length) return emptyStateChart(model);

  var siteSet = {}, sourceSet = {};
  rows.forEach(function(item) {
    siteSet[String(val(item,"site"))] = true;
    sourceSet[String(val(item,"source_label"))] = true;
  });
  var sites = Object.keys(siteSet).sort();
  var sources = Object.keys(sourceSet).sort(function(a,b) {
    var order = ["自然/Organic","ADS广告","Livestream","Campaign活动","卖家商品补贴","平台商品补贴","平台运费补贴","卖家运费补贴","CFS闪购"];
    return order.indexOf(a) - order.indexOf(b);
  });

  function bySite(site) { return rows.filter(function(r){ return site === "__ALL__" || val(r,"site") === site; }); }
  function siteSummary(site) {
    var r = bySite(site);
    var primary = r.slice().sort(function(a,b){ return (num(b,"ado_mtd")||0) - (num(a,"ado_mtd")||0); })[0];
    var growth = r.filter(function(x){ return (num(x,"ado_delta")||0) > 0; }).sort(function(a,b){ return (num(b,"ado_delta")||0) - (num(a,"ado_delta")||0); })[0];
    var loss = r.filter(function(x){ return (num(x,"ado_delta")||0) < 0; }).sort(function(a,b){ return (num(a,"ado_delta")||0) - (num(b,"ado_delta")||0); })[0];
    return { primary: primary, growth: growth, loss: loss };
  }
  function signed(n) {
    n = parseNum(n);
    return n == null ? "—" : (n > 0 ? "+" : "") + formatCompact(n);
  }
  function sourceTable(activeSite) {
    var selected = bySite(activeSite).sort(function(a,b){ return (num(b,"ado_mtd")||0) - (num(a,"ado_mtd")||0); });
    if (!selected.length) return '<div class="muted" style="padding:12px">该站点暂无订单来源数据</div>';
    var out = '<table class="report-table"><thead><tr><th>Site</th><th>来源/手段</th><th>ADO</th><th>ADO占比</th><th>ADO Δ</th><th>ADG</th><th>ADG占比</th><th>类型</th></tr></thead><tbody>';
    selected.forEach(function(item) {
      var d = num(item,"ado_delta");
      out += '<tr><td><strong>' + esc(val(item,"site")) + '</strong></td>';
      out += '<td>' + esc(val(item,"source_label")) + '</td>';
      out += '<td>' + formatCompact(num(item,"ado_mtd") || 0) + '</td>';
      out += '<td>' + (num(item,"ado_share") != null ? formatCompact(num(item,"ado_share")) + '%' : "—") + '</td>';
      out += '<td class="' + (d > 0 ? "up-text" : (d < 0 ? "dn-text" : "")) + '">' + signed(d) + '</td>';
      out += '<td>' + formatCompact(num(item,"adg_mtd") || 0) + '</td>';
      out += '<td>' + (num(item,"adg_share") != null ? formatCompact(num(item,"adg_share")) + '%' : "—") + '</td>';
      out += '<td><span class="pill" style="font-size:10px">' + esc(val(item,"source_group") || "—") + '</span></td></tr>';
    });
    out += '</tbody></table>';
    return out;
  }

  var chartId = "traffic-heat-" + Math.random().toString(36).slice(2, 6);
  var hostId = "traffic-workbench-" + Math.random().toString(36).slice(2, 6);
  var html = '<div id="' + hostId + '">';
  html += '<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-bottom:10px">';
  var allSummary = siteSummary("__ALL__");
  html += '<div class="metric-card"><div class="label">最大出单来源</div><div class="value" style="font-size:16px">' + (allSummary.primary ? esc(val(allSummary.primary,"source_label")) : "—") + '</div><div class="context">' + (allSummary.primary ? esc(val(allSummary.primary,"site")) + " · " + formatCompact(num(allSummary.primary,"ado_mtd") || 0) + " ADO" : "—") + '</div></div>';
  html += '<div class="metric-card"><div class="label">增长最强手段</div><div class="value up-text" style="font-size:16px">' + (allSummary.growth ? esc(val(allSummary.growth,"source_label")) : "—") + '</div><div class="context">' + (allSummary.growth ? esc(val(allSummary.growth,"site")) + " · " + signed(num(allSummary.growth,"ado_delta")) + " ADO" : "—") + '</div></div>';
  html += '<div class="metric-card"><div class="label">下滑最大手段</div><div class="value dn-text" style="font-size:16px">' + (allSummary.loss ? esc(val(allSummary.loss,"source_label")) : "—") + '</div><div class="context">' + (allSummary.loss ? esc(val(allSummary.loss,"site")) + " · " + signed(num(allSummary.loss,"ado_delta")) + " ADO" : "—") + '</div></div>';
  html += '</div>';
  html += '<div style="font-size:10px;color:var(--muted);margin-bottom:8px">注意：来源/补贴/活动不是MECE，同一订单可能同时命中多个手段，占比用于判断driver，不能相加为100%。</div>';
  html += '<div class="site-filter-bar" style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:8px"><span style="font-size:11px;color:var(--muted);font-weight:650;margin-right:4px">Site</span>';
  html += '<button class="traffic-site active" data-site="__ALL__" style="border:1px solid var(--ink);background:var(--ink);color:var(--surface);border-radius:14px;padding:3px 10px;font-size:11px;cursor:pointer">All</button>';
  sites.forEach(function(site) { html += '<button class="traffic-site" data-site="' + esc(site) + '" style="border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:14px;padding:3px 10px;font-size:11px;cursor:pointer">' + esc(site) + '</button>'; });
  html += '</div>';
  html += '<div id="' + chartId + '" style="width:100%;height:' + Math.max(230, sites.length * 30 + 96) + 'px" role="img" aria-label="Order source heatmap"></div>';
  html += '<div class="traffic-table" style="margin-top:10px">' + sourceTable("__ALL__") + '</div>';
  html += '</div>';

  var activeSite = "__ALL__";
  function drawChart() {
    var dom = document.getElementById(chartId);
    if (!dom) return;
    if (dom.clientWidth === 0) { setTimeout(drawChart, 150); return; }
    var selectedSites = activeSite === "__ALL__" ? sites : [activeSite];
    var data = [];
    selectedSites.forEach(function(site, y) {
      sources.forEach(function(src, x) {
        var match = rows.filter(function(r){ return val(r,"site") === site && val(r,"source_label") === src; })[0];
        data.push([x, y, match ? (num(match,"ado_share") || 0) : 0, match ? (num(match,"ado_mtd") || 0) : 0]);
      });
    });
    var existing = echarts.getInstanceByDom(dom);
    if (existing) existing.dispose();
    var chart = echarts.init(dom);
    chart.setOption({
      tooltip: { backgroundColor: "rgba(32,33,36,.94)", borderColor: "transparent", textStyle: { color: "#f8fafc", fontSize: 12 },
        formatter: function(p) { return "<strong>" + selectedSites[p.value[1]] + " · " + sources[p.value[0]] + "</strong><br>ADO占比: " + p.value[2].toFixed(1) + "%<br>ADO: " + formatCompact(p.value[3]); }
      },
      grid: { left: 64, right: 20, top: 8, bottom: 74 },
      xAxis: { type: "category", data: sources, axisLabel: { fontSize: 10, rotate: 25 } },
      yAxis: { type: "category", data: selectedSites, axisLabel: { fontSize: 11, fontWeight: 700 } },
      visualMap: { min: 0, max: Math.max(10, Math.max.apply(null, data.map(function(d){ return d[2]; }))), calculable: false, orient: "horizontal", left: "center", bottom: 0, inRange: { color: ["#f4f5f7", "#f7cf5b", "#ee4d2d"] }, textStyle: { fontSize: 9 } },
      series: [{ type: "heatmap", data: data, label: { show: true, fontSize: 9, formatter: function(p){ return p.value[2] >= 8 ? p.value[2].toFixed(0) + "%" : ""; } }, itemStyle: { borderColor: "#ffffff", borderWidth: 1 } }]
    });
    var ro = new ResizeObserver(function(){ chart.resize(); });
    ro.observe(dom); dom._resizeObserver = ro;
  }
  setTimeout(function() {
    drawChart();
    var host = document.getElementById(hostId);
    if (!host) return;
    host.addEventListener("click", function(e) {
      var btn = e.target.closest(".traffic-site");
      if (!btn) return;
      activeSite = btn.getAttribute("data-site");
      host.querySelectorAll(".traffic-site").forEach(function(b) {
        var active = b === btn;
        b.style.background = active ? "var(--ink)" : "var(--surface)";
        b.style.color = active ? "var(--surface)" : "var(--ink)";
        b.style.borderColor = active ? "var(--ink)" : "var(--line)";
      });
      var table = host.querySelector(".traffic-table");
      if (table) table.innerHTML = sourceTable(activeSite);
      drawChart();
    });
  }, 180);

  return html;
}
"""


def build_section_js() -> str:
    return traffic_channel_chart_js()


SECTION_ID = "sec_traffic_channel"
FUNC_NAME = "trafficChannelChart"
