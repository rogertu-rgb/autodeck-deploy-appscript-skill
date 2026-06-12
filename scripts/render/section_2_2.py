#!/usr/bin/env python3
"""
Section 2.2 — Price Band Positioning (价格带竞争定位)

Dual distribution: seller bars + market line per price band.
Site filter. Bias >20pp flags. Share migration direction.

Requirements (Master Design §7, Section 2.2):
  ✅ Dual distribution (seller bars + market line)
  ✅ Bias >20pp flag
  ✅ Price band migration direction
  ❌ Market side: only mkt_price_share% (relative), never absolute
"""

from __future__ import annotations


def price_band_chart_js() -> str:
    return r"""
function priceBandChart(model) {
  if (!model || !model.body.length) return emptyStateChart(model);

  // Collect sites
  var siteSet = {};
  model.body.forEach(function(item) {
    var s = String(val(item, "site") || "").trim();
    if (s) siteSet[s] = true;
  });
  var siteList = Object.keys(siteSet).sort();

  // Price band order
  var bandOrder = ["$0-5", "$5-10", "$10-15", "$15-20", "$20-25", "$25-30", "$30+"];

  // Site filter
  var filterId = "pb-site-filter-" + Math.random().toString(36).slice(2, 6);
  var html = '<div id="' + filterId + '" class="site-filter-bar" style="display:flex;flex-wrap:wrap;gap:6px;padding:8px 0;align-items:center">';
  html += '<span style="font-size:11px;color:var(--muted);font-weight:650;margin-right:4px">Site:</span>';
  html += '<button class="site-pill active" data-site="__ALL__" style="border:1px solid var(--line);border-radius:14px;padding:3px 10px;font-size:11px;cursor:pointer;background:var(--ink);color:#fff;border-color:var(--ink)">All</button>';
  siteList.forEach(function(s) {
    html += '<button class="site-pill active" data-site="' + esc(s) + '" style="border:1px solid var(--line);border-radius:14px;padding:3px 10px;font-size:11px;cursor:pointer;background:var(--accent-soft);color:var(--accent-dark);border-color:var(--accent)">' + esc(s) + '</button>';
  });
  // ADG/ADO toggle
  var metricToggleId = "pb-metric-" + Math.random().toString(36).slice(2, 6);
  html += '<span style="font-size:11px;color:var(--muted);font-weight:650;margin-left:12px">Metric:</span> ';
  html += '<select id="' + metricToggleId + '" style="border:1px solid var(--line);border-radius:6px;padding:4px 8px;font-size:11px;background:#fff;margin-left:4px">';
  html += '<option value="adg" selected>ADG</option>';
  html += '<option value="ado">ADO</option>';
  html += '</select>';
  html += '</div>';

  var chartId = "pb-chart-" + Math.random().toString(36).slice(2, 6);
  var tableContainerId = "pb-table-" + Math.random().toString(36).slice(2, 6);

  html += '<div id="' + chartId + '" style="width:100%;height:320px" role="img" aria-label="Price band distribution"></div>';
  html += '<div id="' + tableContainerId + '"></div>';

  // ── Build function ──
  var currentMetric = "adg";
  var buildContent = function(activeSites) {
    var metricCol = currentMetric === "ado" ? "seller_ado" : "seller_adg";
    var filtered = model.body.filter(function(item) {
      var s = String(val(item, "site") || "").trim();
      return activeSites.__ALL__ || activeSites[s];
    });

    // Aggregate absolute value by price band, then normalize to 100%
    var bandMap = {};
    bandOrder.forEach(function(b) { bandMap[b] = { band: b, sellerVal: 0, mktShare: 0, mktWeight: 0, shifts: [], bias: null }; });
    filtered.forEach(function(item) {
      var band = String(val(item, "price_range") || "").trim();
      if (!bandMap[band]) return;
      var itemVal = num(item, metricCol) || num(item, "seller_adg") || 0;  // fallback to ADG if ADO missing
      bandMap[band].sellerVal += itemVal;
      var mkt = num(item, "mkt_price_share");
      if (mkt != null) { bandMap[band].mktShare += mkt; bandMap[band].mktWeight++; }
      bandMap[band].shifts.push(num(item, "share_shift_pp") || 0);
      if (bandMap[band].bias == null) bandMap[band].bias = num(item, "bias_pp");
    });

    // Normalize to 100%
    var totalSellerAdg = 0;
    bandOrder.forEach(function(b) { totalSellerAdg += bandMap[b].sellerVal; });
    var bands = bandOrder.filter(function(b) { return bandMap[b].sellerVal > 0; });
    var sellerData = bands.map(function(b) { return totalSellerAdg > 0 ? parseFloat((bandMap[b].sellerVal / totalSellerAdg * 100).toFixed(1)) : 0; });
    var mktTotal = 0;
    bands.forEach(function(b) { mktTotal += bandMap[b].mktShare; });
    var mktData = bands.map(function(b) { return mktTotal > 0 ? parseFloat((bandMap[b].mktShare / mktTotal * 100).toFixed(1)) : 0; });

    // Update chart
    setTimeout(function() {
      var dom = document.getElementById(chartId);
      if (!dom) return;
      function tryInit() {
        if (dom.clientWidth === 0) { setTimeout(tryInit, 150); return; }
        var existing = echarts.getInstanceByDom(dom);
        if (existing) existing.dispose();
        var chart = echarts.init(dom);
        chart.setOption({
          tooltip: { trigger: "axis", backgroundColor: "rgba(32,33,36,.94)", borderColor: "transparent", textStyle: { color: "#fff", fontSize: 12 } },
          legend: { data: ["Seller " + currentMetric.toUpperCase() + "%", "Market Share%"], top: 0, left: "center", textStyle: { fontSize: 11 }, itemWidth: 12, itemHeight: 12, itemGap: 14, padding: [0, 0, 8, 0] },
          grid: { left: 12, right: 60, top: 40, bottom: 8 },
          xAxis: { type: "category", data: bands, axisLabel: { fontSize: 11 } },
          yAxis: [
            { type: "value", name: "Share%", axisLabel: { fontSize: 10, formatter: function(v) { return v + "%"; } } },
            { type: "value", name: "Share%", axisLabel: { fontSize: 10, formatter: function(v) { return v + "%"; } } }
          ],
          series: [
            { name: "Seller " + currentMetric.toUpperCase() + "%", type: "bar", data: sellerData, itemStyle: { color: "#7aa6f9" }, barMaxWidth: 44 },
            { name: "Market Share%", type: "line", yAxisIndex: 1, data: mktData, lineStyle: { color: "#ee4d2d", width: 2, type: "dashed" }, itemStyle: { color: "#ee4d2d" }, symbol: "diamond", symbolSize: 8 }
          ]
        });
        var ro = new ResizeObserver(function() { chart.resize(); });
        ro.observe(dom); dom._resizeObserver = ro;
      }
      tryInit();
    }, 80);

    // Build table with normalized values
    var t = '<table class="report-table"><thead><tr><th>Price Band</th><th>Seller ' + currentMetric.toUpperCase() + '</th><th>Seller Share</th><th>Market Share</th><th>Bias</th><th>Share Shift</th></tr></thead><tbody>';
    bands.forEach(function(b, i) {
      var bm = bandMap[b];
      var avgShift = bm.shifts.length ? bm.shifts.reduce(function(a,b){return a+b;},0) / bm.shifts.length : 0;
      var biasTone = bm.bias != null ? (Math.abs(bm.bias) > 20 ? "warn-text" : (bm.bias > 0 ? "up-text" : "dn-text")) : "";
      var shiftTone = avgShift > 0 ? "up-text" : (avgShift < 0 ? "dn-text" : "");
      t += '<tr><td><strong>' + esc(b) + '</strong></td>';
      t += '<td>' + formatCompact(bm.sellerVal) + '</td>';
      t += '<td>' + sellerData[i].toFixed(1) + '%</td>';
      t += '<td>' + (mktData[i] > 0 ? mktData[i].toFixed(1) + '%' : "—") + '</td>';
      t += '<td class="' + biasTone + '">' + (bm.bias != null ? (bm.bias>0?'+':'') + formatCompact(bm.bias) + 'pp' : "—") + (Math.abs(bm.bias||0) > 20 ? ' ⚠️' : '') + '</td>';
      t += '<td class="' + shiftTone + '">' + (avgShift !== 0 ? (avgShift>0?'+':'') + formatCompact(avgShift) + 'pp' : '—') + '</td>';
      t += '</tr>';
    });
    t += '</tbody></table>';
    document.getElementById(tableContainerId).innerHTML = t;
  };

  // Initial render — deferred so DOM exists
  setTimeout(function() { buildContent({ __ALL__: true }); }, 50);

  // Track current state
  var currentActiveSites = { __ALL__: true };

  // Filter
  setTimeout(function() {
    var filterBar = document.getElementById(filterId);
    if (!filterBar) return;
    filterBar.addEventListener("click", function(e) {
      var pill = e.target.closest(".site-pill");
      if (!pill) return;
      var site = pill.getAttribute("data-site");
      if (site === "__ALL__") {
        var allActive = pill.classList.contains("active");
        filterBar.querySelectorAll(".site-pill").forEach(function(p) {
          if (allActive) { p.classList.remove("active"); p.style.background="#fff"; p.style.color="var(--ink)"; p.style.borderColor="var(--line)"; }
          else { p.classList.add("active"); if (p.getAttribute("data-site") === "__ALL__") { p.style.background="var(--ink)"; p.style.color="#fff"; p.style.borderColor="var(--ink)"; } else { p.style.background="var(--accent-soft)"; p.style.color="var(--accent-dark)"; p.style.borderColor="var(--accent)"; } }
        });
      } else {
        var wasActive = pill.classList.contains("active");
        if (wasActive) { pill.classList.remove("active"); pill.style.background="#fff"; pill.style.color="var(--ink)"; pill.style.borderColor="var(--line)"; }
        else { pill.classList.add("active"); pill.style.background="var(--accent-soft)"; pill.style.color="var(--accent-dark)"; pill.style.borderColor="var(--accent)"; }
        var allBtn = filterBar.querySelector('[data-site="__ALL__"]');
        var anyInactive = filterBar.querySelectorAll('.site-pill[data-site]:not([data-site="__ALL__"]):not(.active)');
        if (anyInactive.length > 0 && allBtn) { allBtn.classList.remove("active"); allBtn.style.background="#fff"; allBtn.style.color="var(--ink)"; allBtn.style.borderColor="var(--line)"; }
        else if (allBtn && anyInactive.length === 0) { allBtn.classList.add("active"); allBtn.style.background="var(--ink)"; allBtn.style.color="#fff"; allBtn.style.borderColor="var(--ink)"; }
      }
      var activePills = filterBar.querySelectorAll('.site-pill.active[data-site]:not([data-site="__ALL__"])');
      var activeSites = {};
      activePills.forEach(function(p) { activeSites[p.getAttribute("data-site")] = true; });
      if (activePills.length === siteList.length || activePills.length === 0) activeSites = { __ALL__: true };
      currentActiveSites = activeSites;
      buildContent(activeSites);
    });

    // Metric toggle handler
    var metricToggle = document.getElementById(metricToggleId);
    if (metricToggle) {
      metricToggle.addEventListener("change", function() {
        currentMetric = metricToggle.value;
        buildContent(currentActiveSites);
      });
    }
  }, 100);

  return html;
}
"""


def build_section_js() -> str:
    return price_band_chart_js()


SECTION_ID = "sec_price_band"
FUNC_NAME = "priceBandChart"
