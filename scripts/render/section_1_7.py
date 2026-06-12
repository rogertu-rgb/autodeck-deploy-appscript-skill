#!/usr/bin/env python3
"""
Section 1.7 — Shop Impact Decomposition (店铺贡献分解)

Shop ranking table + concentration (HHI) + shop health signals.
Waterfall if multiple shops, simple table if sparse.

Requirements (Master Design §7, Section 1.7):
  ✅ Shop ranking + waterfall + concentration (HHI)
  ✅ Top1>40% warning
  ✅ Shop health signals (days_active, type)
"""

from __future__ import annotations


def shop_impact_chart_js() -> str:
    return r"""
function shopImpactChart(model) {
  if (!model || !model.body.length) return emptyStateChart(model);

  var shops = [];
  var totalAdg = 0;
  model.body.forEach(function(item) {
    var id = String(val(item, "shop_id") || "").trim();
    var adg = num(item, "adg_mtd") || 0;
    var delta = num(item, "adg_delta") || 0;
    var share = num(item, "share_in_l3") || 0;
    var isMall = val(item, "is_official_shop");
    var days = num(item, "days_cnt") || 0;
    if (!id) return;
    totalAdg += adg;
    shops.push({ id: id, adg: adg, delta: delta, share: share, isMall: isMall, days: days });
  });

  if (!shops.length) return emptyStateChart(model);

  // Sort by ADG descending
  shops.sort(function(a, b) { return b.adg - a.adg; });

  // HHI calculation
  var hhi = 0;
  shops.forEach(function(s) { if (totalAdg > 0) hhi += Math.pow((s.adg / totalAdg) * 100, 2); });
  var top1Share = shops.length ? (shops[0].adg / totalAdg) * 100 : 0;

  var html = "";

  // ── 1. Summary cards ──
  html += '<div style="display:flex;flex-wrap:wrap;gap:8px;margin:8px 0">';
  html += '<div class="metric-card" style="flex:1 1 120px;min-width:100px"><div class="label">Total Shops</div><div class="value" style="font-size:16px">' + shops.length + '</div><div class="context">Total ADG: ' + formatCompact(totalAdg) + '</div></div>';
  var concTone = top1Share > 40 ? "warn" : "";
  html += '<div class="metric-card' + (concTone ? ' ' + concTone : '') + '" style="flex:1 1 140px;min-width:120px' + (top1Share > 40 ? ';border-left:3px solid var(--warn)' : '') + '"><div class="label">Top1 Concentration</div><div class="value" style="font-size:16px">' + formatCompact(top1Share) + '%</div><div class="context">' + (top1Share > 40 ? '⚠️ Single-shop dependency risk' : 'Healthy distribution') + '</div></div>';
  html += '<div class="metric-card" style="flex:1 1 120px;min-width:100px"><div class="label">HHI</div><div class="value" style="font-size:16px">' + Math.round(hhi) + '</div><div class="context">' + (hhi > 2500 ? 'Highly concentrated' : hhi > 1500 ? 'Moderately concentrated' : 'Diversified') + '</div></div>';
  html += '</div>';

  // ── 2. Waterfall if >1 shop, otherwise simple bar ──
  if (shops.length > 1) {
    var chartId = "shop-wf-" + Math.random().toString(36).slice(2, 6);
    var labels = shops.map(function(s) { return s.id; });
    var deltas = shops.map(function(s) { return parseFloat(s.delta.toFixed(1)); });
    var positives = deltas.map(function(v) { return v > 0 ? v : 0; });
    var negatives = deltas.map(function(v) { return v < 0 ? v : 0; });

    html += '<div id="' + chartId + '" style="width:100%;height:' + Math.max(200, shops.length * 32 + 60) + 'px" role="img" aria-label="Shop contribution waterfall"></div>';

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
          legend: { data: ["ADG Gain", "ADG Loss"], top: 0, left: "center", textStyle: { fontSize: 11 } },
          grid: { left: 80, right: 20, top: 30, bottom: 8 },
          xAxis: { type: "category", data: labels, axisLabel: { fontSize: 10 } },
          yAxis: { type: "value", axisLabel: { fontSize: 10, formatter: function(v) { return formatCompact(v); } } },
          series: [
            { name: "ADG Gain", type: "bar", stack: "wf", data: positives, itemStyle: { color: "#137a4b" }, barMaxWidth: 40,
              label: { show: true, position: "top", fontSize: 9, formatter: function(p) { return p.value > 0 ? "+" + formatCompact(p.value) : ""; } } },
            { name: "ADG Loss", type: "bar", stack: "wf", data: negatives, itemStyle: { color: "#b42318" }, barMaxWidth: 40,
              label: { show: true, position: "bottom", fontSize: 9, formatter: function(p) { return p.value < 0 ? formatCompact(p.value) : ""; } } }
          ]
        });
        var ro = new ResizeObserver(function() { chart.resize(); });
        ro.observe(dom); dom._resizeObserver = ro;
      }
      tryInit();
    }, 200);
  }

  // ── 3. Shop detail table ──
  html += '<div style="margin-top:8px"><table class="report-table"><thead><tr>';
  html += '<th>Shop ID</th><th>ADG MTD</th><th>ADG Δ</th><th>Contribution%</th><th>Share in L3</th><th>Mall</th><th>Days Active</th>';
  html += '</tr></thead><tbody>';
  shops.forEach(function(s) {
    var deltaTone = s.delta > 0 ? "up-text" : (s.delta < 0 ? "dn-text" : "");
    html += '<tr>';
    html += '<td class="shop-id">' + esc(s.id) + '</td>';
    html += '<td>' + formatCompact(s.adg) + '</td>';
    html += '<td class="' + deltaTone + '">' + (s.delta > 0 ? "+" : "") + formatCompact(s.delta) + '</td>';
    html += '<td>' + formatCompact(s.share) + '%</td>';
    html += '<td>' + formatCompact(s.share) + '%</td>';
    html += '<td>' + (s.isMall == 1 ? "Mall" : "Non-Mall") + '</td>';
    html += '<td>' + s.days + '</td>';
    html += '</tr>';
  });
  html += '</tbody></table></div>';

  return html;
}
"""


def build_section_js() -> str:
    return shop_impact_chart_js()


SECTION_ID = "sec_shop_impact"
FUNC_NAME = "shopImpactChart"
