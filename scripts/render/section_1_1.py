#!/usr/bin/env python3
"""
Section 1.1 — Site Momentum vs Market Benchmark (各站点增速vs大盘对标)

NO absolute values. MoM% comparison only.
Chart: Grouped bar — seller MoM% vs market MoM% per site.
Table: site | seller_adg_mom | mom_mkt_adg_pct | gap_pp | adg_share
       (+ seller_ado_mom | mom_mkt_ado_pct | ado_gap_pp when available)
Benchmark breakdown: mom_mkt_mall_adg_pct, mom_mkt_cb_adg_pct, mom_mkt_local_adg_pct (if in data)

Data source: sec_site_benchmark (from autodeck__site_bu_benchmark_mi — MoM% only)
"""

from __future__ import annotations


def site_benchmark_chart_js() -> str:
    return r"""
function siteBenchmarkChart(model) {
  if (!model || !model.body.length) return emptyStateChart(model);

  function firstNum(item, names) {
    for (var i = 0; i < names.length; i++) {
      var v = num(item, names[i]);
      if (v != null) return v;
    }
    return null;
  }

  // ── 1. Extract MoM% data (NO absolute values) ──
  var sites = [];
  var sellerAdgMom = [], mktAdgMom = [], gapPp = [], sharePct = [];
  var sellerAdoMom = [], mktAdoMom = [], adoGapPp = [];
  var hasAdo = false;

  model.body.forEach(function(item) {
    var site = String(val(item, "site") || "").trim();
    if (!site) return;
    sites.push(site);
    sellerAdgMom.push(num(item, "seller_adg_mom"));
    mktAdgMom.push(firstNum(item, ["mom_mkt_adg_pct", "mkt_adg_mom"]));
    gapPp.push(num(item, "adg_gap_pp"));
    sharePct.push(num(item, "adg_share"));
    // ADO MoM if available
    var sAdo = num(item, "seller_ado_mom");
    var mAdo = firstNum(item, ["mom_mkt_ado_pct", "mkt_ado_mom"]);
    var aGap = num(item, "ado_gap_pp");
    sellerAdoMom.push(sAdo);
    mktAdoMom.push(mAdo);
    adoGapPp.push(aGap);
    if (sAdo != null || mAdo != null) hasAdo = true;
  });

  if (!sites.length) return emptyStateChart(model);

  // ── 2. Grouped bar chart: Seller MoM% vs Market MoM% ──
  var chartId = "bm-chart-" + Math.random().toString(36).slice(2, 8);

  var option = {
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      backgroundColor: "rgba(32,33,36,.94)",
      borderColor: "transparent",
      textStyle: { color: "#fff", fontSize: 12 },
      formatter: function(params) {
        var site = params[0].axisValue;
        var lines = ["<strong>" + site + "</strong>"];
        params.forEach(function(p) {
          if (p.value != null) lines.push(p.marker + p.seriesName + ": " + formatCompact(p.value) + "%");
        });
        return lines.join("<br>");
      }
    },
    legend: {
      data: ["Seller ADG MoM%", "Market ADG MoM%"],
      top: 0, left: "center",
      textStyle: { fontSize: 11 },
      itemWidth: 12, itemHeight: 12, itemGap: 14,
      padding: [0, 0, 8, 0]
    },
    grid: { left: 12, right: 12, top: 40, bottom: 8 },
    xAxis: {
      type: "category", data: sites,
      axisLabel: { fontSize: 12, fontWeight: 700 }
    },
    yAxis: {
      type: "value",
      axisLabel: { fontSize: 10, formatter: function(v) { return formatCompact(v) + "%"; } },
      splitLine: { lineStyle: { color: "#edf0f3", type: "dashed" } }
    },
    series: [
      {
        name: "Seller ADG MoM%", type: "bar",
        data: sellerAdgMom,
        itemStyle: { color: function(params) { return siteColor(sites[params.dataIndex]); } },
        barMaxWidth: 40,
        label: { show: true, position: "top", fontSize: 9,
          formatter: function(p) { return p.value != null ? formatCompact(p.value) + "%" : ""; }
        }
      },
      {
        name: "Market ADG MoM%", type: "bar",
        data: mktAdgMom,
        itemStyle: { color: "#d5d9e0" },
        barMaxWidth: 40,
        label: { show: true, position: "top", fontSize: 9,
          formatter: function(p) { return p.value != null ? formatCompact(p.value) + "%" : ""; }
        }
      }
    ]
  };

  var html = '<div id="' + chartId + '" style="width:100%;height:300px" role="img" aria-label="Seller vs Market MoM% comparison"></div>';

  // ── 3. Table: MoM% only, no absolute values ──
  html += '<div style="margin-top:10px"><table class="report-table"><thead><tr>';
  html += '<th>Site</th><th>Seller ADG MoM%</th><th>Market ADG MoM%</th><th>Gap (pp)</th><th>ADG Share</th>';
  if (hasAdo) html += '<th>Seller ADO MoM%</th><th>Market ADO MoM%</th><th>ADO Gap (pp)</th>';
  html += '</tr></thead><tbody>';
  sites.forEach(function(site, i) {
    var gapTone = gapPp[i] != null ? (Math.abs(gapPp[i]) > 5 ? (gapPp[i] > 0 ? "up-text" : "dn-text") : "") : "";
    var sMomTone = sellerAdgMom[i] != null ? (sellerAdgMom[i] > 0 ? "up-text" : "dn-text") : "";
    html += '<tr><td><strong>' + esc(site) + '</strong></td>';
    html += '<td class="' + sMomTone + '">' + (sellerAdgMom[i] != null ? formatCompact(sellerAdgMom[i]) + '%' : '—') + '</td>';
    html += '<td>' + (mktAdgMom[i] != null ? formatCompact(mktAdgMom[i]) + '%' : '—') + '</td>';
    html += '<td class="' + gapTone + '">' + (gapPp[i] != null ? (gapPp[i] > 0 ? '+' : '') + formatCompact(gapPp[i]) + 'pp' : '—') + '</td>';
    html += '<td>' + (sharePct[i] != null ? formatCompact(sharePct[i]) + '%' : '—') + '</td>';
    if (hasAdo) {
      var aMomTone = sellerAdoMom[i] != null ? (sellerAdoMom[i] > 0 ? "up-text" : "dn-text") : "";
      var aGapTone = adoGapPp[i] != null ? (Math.abs(adoGapPp[i]) > 5 ? (adoGapPp[i] > 0 ? "up-text" : "dn-text") : "") : "";
      html += '<td class="' + aMomTone + '">' + (sellerAdoMom[i] != null ? formatCompact(sellerAdoMom[i]) + '%' : '—') + '</td>';
      html += '<td>' + (mktAdoMom[i] != null ? formatCompact(mktAdoMom[i]) + '%' : '—') + '</td>';
      html += '<td class="' + aGapTone + '">' + (adoGapPp[i] != null ? (adoGapPp[i] > 0 ? '+' : '') + formatCompact(adoGapPp[i]) + 'pp' : '—') + '</td>';
    }
    html += '</tr>';
  });
  html += '</tbody></table></div>';

  // ── 4. Gap >5pp alerts ──
  var flagSites = [];
  for (var j = 0; j < gapPp.length; j++) {
    if (gapPp[j] != null && Math.abs(gapPp[j]) > 5) {
      flagSites.push({ site: sites[j], gap: gapPp[j], mom: sellerAdgMom[j], mkt: mktAdgMom[j], share: sharePct[j] });
    }
  }
  if (flagSites.length) {
    html += '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px">';
    flagSites.forEach(function(f) {
      html += '<div class="metric-card" style="flex:1 1 160px;min-width:140px;border-left:3px solid ' + (f.gap > 0 ? 'var(--up)' : 'var(--down)') + '">';
      html += '<div class="label">⚠️ ' + esc(f.site) + ' |gap|>5pp</div>';
      html += '<div class="value" style="font-size:14px">' + (f.gap > 0 ? '+' : '') + formatCompact(f.gap) + 'pp</div>';
      html += '<div class="context">Seller: ' + (f.mom != null ? formatCompact(f.mom) + '%' : '—') + ' | Market: ' + (f.mkt != null ? formatCompact(f.mkt) + '%' : '—') + ' | Share: ' + formatCompact(f.share) + '%</div>';
      html += '</div>';
    });
    html += '</div>';
  }

  // ── 5. Benchmark breakdown (mkt_mall, mkt_cb, mkt_local — if available from Table B) ──
  var hasMall = hasCol(model, "mom_mkt_mall_adg_pct");
  var hasCb = hasCol(model, "mom_mkt_cb_adg_pct");
  var hasLocal = hasCol(model, "mom_mkt_local_adg_pct");
  if (hasMall || hasCb || hasLocal) {
    html += '<div style="margin-top:10px"><div style="font-size:11px;font-weight:700;color:var(--muted);padding:4px 0">Market Breakdown (from autodeck__site_bu_benchmark_mi — MoM% only)</div>';
    html += '<table class="report-table"><thead><tr><th>Site</th>';
    if (hasMall) html += '<th>Mall MoM%</th>';
    if (hasCb) html += '<th>CB MoM%</th>';
    if (hasLocal) html += '<th>Local MoM%</th>';
    html += '</tr></thead><tbody>';
    sites.forEach(function(site, i) {
      html += '<tr><td><strong>' + esc(site) + '</strong></td>';
      if (hasMall) { var v = num(model.body[i], "mom_mkt_mall_adg_pct"); html += '<td>' + (v != null ? formatCompact(v) + '%' : '—') + '</td>'; }
      if (hasCb)   { var v = num(model.body[i], "mom_mkt_cb_adg_pct");   html += '<td>' + (v != null ? formatCompact(v) + '%' : '—') + '</td>'; }
      if (hasLocal){ var v = num(model.body[i], "mom_mkt_local_adg_pct"); html += '<td>' + (v != null ? formatCompact(v) + '%' : '—') + '</td>'; }
      html += '</tr>';
    });
    html += '</tbody></table></div>';
  }

  setTimeout(function() {
    var dom = document.getElementById(chartId);
    if (!dom) return;
    function tryInit() {
      if (dom.clientWidth === 0) { setTimeout(tryInit, 150); return; }
      var existing = echarts.getInstanceByDom(dom);
      if (existing) existing.dispose();
      var chart = echarts.init(dom);
      chart.setOption(option);
      var ro = new ResizeObserver(function() { chart.resize(); });
      ro.observe(dom); dom._resizeObserver = ro;
    }
    tryInit();
  }, 200);

  return html;
}
"""


def build_section_js() -> str:
    return site_benchmark_chart_js()


SECTION_ID = "sec_site_benchmark"
FUNC_NAME = "siteBenchmarkChart"
