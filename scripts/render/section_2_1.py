#!/usr/bin/env python3
"""
Section 2.1 — Promotion Effectiveness (促销补贴有效性)

Companion to order-source split. It focuses on promotion/subsidy levers and
seller-vs-platform funding pressure. Levers are not MECE.
"""

from __future__ import annotations


def subsidy_chart_js() -> str:
    return r"""
function subsidyChart(model) {
  if (!model || !model.body.length) return emptyStateChart(model);

  var rows = model.body.filter(function(item) {
    return String(val(item,"site") || "").trim() && String(val(item,"source_label") || "").trim();
  });
  if (!rows.length) return '<div class="muted" style="padding:16px;text-align:center">本月无促销补贴相关出单</div>';

  var siteSet = {}, leverSet = {};
  rows.forEach(function(item) { siteSet[val(item,"site")] = true; leverSet[val(item,"source_label")] = true; });
  var sites = Object.keys(siteSet).sort();
  var levers = Object.keys(leverSet).sort(function(a,b) {
    var order = ["卖家商品补贴","卖家运费补贴","平台商品补贴","平台运费补贴","CFS闪购","Campaign活动","LPP低价秒杀"];
    return order.indexOf(a) - order.indexOf(b);
  });

  function siteRows(site) { return rows.filter(function(r){ return site === "__ALL__" || val(r,"site") === site; }); }
  function signed(n) { n = parseNum(n); return n == null ? "—" : (n > 0 ? "+" : "") + formatCompact(n); }
  function pctCell(item, col) { var n = num(item,col); return n == null ? "—" : formatCompact(n) + "%"; }
  function bestBy(col, predicate) {
    var selected = rows.filter(function(r){ return !predicate || predicate(num(r,col)||0, r); });
    return selected.sort(function(a,b){ return (num(b,col)||0) - (num(a,col)||0); })[0];
  }
  var topAdo = bestBy("ado_mtd");
  var topGrowth = rows.filter(function(r){ return (num(r,"ado_delta")||0) > 0 || (num(r,"adg_delta")||0) > 0; })
    .sort(function(a,b){ return Math.max(num(b,"ado_delta")||0,num(b,"adg_delta")||0) - Math.max(num(a,"ado_delta")||0,num(a,"adg_delta")||0); })[0];
  var highSeller = rows.slice().sort(function(a,b){ return (num(b,"seller_funded_share")||0) - (num(a,"seller_funded_share")||0); })[0];

  var hostId = "promo-workbench-" + Math.random().toString(36).slice(2, 6);
  var chartId = "promo-heat-" + Math.random().toString(36).slice(2, 6);
  var html = '<div id="' + hostId + '">';
  html += '<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-bottom:10px">';
  html += '<div class="metric-card"><div class="label">最大促销出单手段</div><div class="value" style="font-size:16px">' + (topAdo ? esc(val(topAdo,"source_label")) : "—") + '</div><div class="context">' + (topAdo ? esc(val(topAdo,"site")) + " · " + formatCompact(num(topAdo,"ado_mtd") || 0) + " ADO" : "—") + '</div></div>';
  html += '<div class="metric-card"><div class="label">增长最强促销手段</div><div class="value up-text" style="font-size:16px">' + (topGrowth ? esc(val(topGrowth,"source_label")) : "—") + '</div><div class="context">' + (topGrowth ? esc(val(topGrowth,"site")) + " · ADO Δ " + signed(num(topGrowth,"ado_delta")) : "—") + '</div></div>';
  html += '<div class="metric-card"><div class="label">卖家出资压力最高</div><div class="value" style="font-size:16px">' + (highSeller ? esc(val(highSeller,"site")) : "—") + '</div><div class="context">' + (highSeller ? pctCell(highSeller,"seller_funded_share") + " seller-funded" : "—") + '</div></div>';
  html += '</div>';
  html += '<div style="font-size:10px;color:var(--muted);margin-bottom:8px">促销、CFS、Campaign、LPP 可能与广告/自然出单重叠，占比不能相加。这里用于判断哪个手段对出单更有效，以及卖家出资压力是否过高。</div>';
  html += '<div class="site-filter-bar" style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:8px"><span style="font-size:11px;color:var(--muted);font-weight:650;margin-right:4px">Site</span>';
  html += '<button class="promo-site active" data-site="__ALL__" style="border:1px solid var(--ink);background:var(--ink);color:var(--surface);border-radius:14px;padding:3px 10px;font-size:11px;cursor:pointer">All</button>';
  sites.forEach(function(site) { html += '<button class="promo-site" data-site="' + esc(site) + '" style="border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:14px;padding:3px 10px;font-size:11px;cursor:pointer">' + esc(site) + '</button>'; });
  html += '</div>';
  html += '<div id="' + chartId + '" style="width:100%;height:' + Math.max(230, sites.length * 30 + 96) + 'px" role="img" aria-label="Promotion lever heatmap"></div>';
  html += '<div class="promo-table" style="margin-top:10px"></div>';
  html += '</div>';

  var activeSite = "__ALL__";
  function tableHtml(site) {
    var selected = siteRows(site).sort(function(a,b){ return Math.max(num(b,"ado_mtd")||0,num(b,"adg_mtd")||0) - Math.max(num(a,"ado_mtd")||0,num(a,"adg_mtd")||0); });
    if (!selected.length) return '<div class="muted" style="padding:12px">该站点暂无促销手段数据</div>';
    var out = '<table class="report-table"><thead><tr><th>Site</th><th>促销手段</th><th>ADO</th><th>ADO占比</th><th>ADO Δ</th><th>ADG</th><th>ADG占比</th><th>卖家出资</th><th>平台出资</th></tr></thead><tbody>';
    selected.forEach(function(item) {
      var d = num(item,"ado_delta");
      out += '<tr><td><strong>' + esc(val(item,"site")) + '</strong></td>';
      out += '<td>' + esc(val(item,"source_label")) + '</td>';
      out += '<td>' + ((num(item,"ado_mtd")||0) ? formatCompact(num(item,"ado_mtd")||0) : "—") + '</td>';
      out += '<td>' + pctCell(item,"ado_share") + '</td>';
      out += '<td class="' + (d > 0 ? "up-text" : (d < 0 ? "dn-text" : "")) + '">' + signed(d) + '</td>';
      out += '<td>' + formatCompact(num(item,"adg_mtd") || 0) + '</td>';
      out += '<td>' + pctCell(item,"adg_share") + '</td>';
      out += '<td>' + pctCell(item,"seller_funded_share") + '</td>';
      out += '<td>' + pctCell(item,"platform_funded_share") + '</td></tr>';
    });
    out += '</tbody></table>';
    return out;
  }

  function drawChart() {
    var dom = document.getElementById(chartId);
    if (!dom) return;
    if (dom.clientWidth === 0) { setTimeout(drawChart, 150); return; }
    var selectedSites = activeSite === "__ALL__" ? sites : [activeSite];
    var data = [];
    selectedSites.forEach(function(site, y) {
      levers.forEach(function(lever, x) {
        var match = rows.filter(function(r){ return val(r,"site") === site && val(r,"source_label") === lever; })[0];
        var share = match ? (num(match,"ado_share") != null ? num(match,"ado_share") : num(match,"adg_share")) : 0;
        data.push([x, y, share || 0]);
      });
    });
    var existing = echarts.getInstanceByDom(dom);
    if (existing) existing.dispose();
    var chart = echarts.init(dom);
    chart.setOption({
      tooltip: { backgroundColor: "rgba(32,33,36,.94)", borderColor: "transparent", textStyle: { color: "#f8fafc", fontSize: 12 },
        formatter: function(p) { return "<strong>" + selectedSites[p.value[1]] + " · " + levers[p.value[0]] + "</strong><br>占比: " + p.value[2].toFixed(1) + "%"; }
      },
      grid: { left: 64, right: 20, top: 8, bottom: 74 },
      xAxis: { type: "category", data: levers, axisLabel: { fontSize: 10, rotate: 25 } },
      yAxis: { type: "category", data: selectedSites, axisLabel: { fontSize: 11, fontWeight: 700 } },
      visualMap: { min: 0, max: Math.max(10, Math.max.apply(null, data.map(function(d){ return d[2]; }))), calculable: false, orient: "horizontal", left: "center", bottom: 0, inRange: { color: ["#f4f5f7", "#f7cf5b", "#ee4d2d"] }, textStyle: { fontSize: 9 } },
      series: [{ type: "heatmap", data: data, label: { show: true, fontSize: 9, formatter: function(p){ return p.value[2] >= 8 ? p.value[2].toFixed(0) + "%" : ""; } }, itemStyle: { borderColor: "#f8fafc", borderWidth: 1 } }]
    });
    var ro = new ResizeObserver(function(){ chart.resize(); });
    ro.observe(dom); dom._resizeObserver = ro;
  }

  setTimeout(function() {
    var host = document.getElementById(hostId);
    if (!host) return;
    host.querySelector(".promo-table").innerHTML = tableHtml("__ALL__");
    drawChart();
    host.addEventListener("click", function(e) {
      var btn = e.target.closest(".promo-site");
      if (!btn) return;
      activeSite = btn.getAttribute("data-site");
      host.querySelectorAll(".promo-site").forEach(function(b) {
        var active = b === btn;
        b.style.background = active ? "var(--ink)" : "var(--surface)";
        b.style.color = active ? "var(--surface)" : "var(--ink)";
        b.style.borderColor = active ? "var(--ink)" : "var(--line)";
      });
      host.querySelector(".promo-table").innerHTML = tableHtml(activeSite);
      drawChart();
    });
  }, 180);

  return html;
}
"""


def build_section_js() -> str:
    return subsidy_chart_js()


SECTION_ID = "sec_subsidy"
FUNC_NAME = "subsidyChart"
