#!/usr/bin/env python3
"""
Section 1.6 — Volatility Signal Scan (波动率信号扫描)

Scatter plot: x=mkt_MoM%, y=seller_MoM% with quadrant lines.
Signal count cards + priority-ranked signal table.
Data from sec_volatility_meta (JSON in meta tab).

Requirements (Master Design §7, Section 1.6):
  ✅ Scatter plot (x=mkt_MoM%, y=seller_MoM%) with quadrant lines
  ✅ Signal cards: count per signal type with priority ranking
  ✅ Cluster detection (site-concentrated vs L1-concentrated vs scattered)
  ❌ No absolute market values (x-axis = mkt_MoM% only)
"""

from __future__ import annotations


def volatility_chart_js() -> str:
    return r"""
function volatilityChart(model) {
  // Read from meta tab
  var tabs = (window.AUTODECK_LOCAL_DATA && window.AUTODECK_LOCAL_DATA.tabs) || {};
  var metaRows = tabs.sec_volatility_meta || [];
  if (!metaRows.length) return emptyStateChart(model);

  var metaDict = {};
  metaRows.forEach(function(row) {
    if (row.length >= 2) metaDict[row[0]] = String(row[1] || "");
  });

  // Parse signal counts
  var signalCounts = {};
  try { signalCounts = JSON.parse((metaDict.signal_counts || "{}").replace(/\bnan\b/g,"null").replace(/\bNone\b/g,"null").replace(/\bTrue\b/g,"true").replace(/\bFalse\b/g,"false")); } catch(e) {}

  // Parse signals array
  var signals = [];
  try { signals = JSON.parse((metaDict.signals || "[]").replace(/\bnan\b/g,"null").replace(/\bNone\b/g,"null").replace(/\bTrue\b/g,"true").replace(/\bFalse\b/g,"false")); } catch(e) {}

  // Parse scatter data
  var scatterPoints = [];
  try { scatterPoints = JSON.parse((metaDict.scatter_data || "[]").replace(/\bnan\b/g,"null").replace(/\bNone\b/g,"null").replace(/\bTrue\b/g,"true").replace(/\bFalse\b/g,"false")); } catch(e) {}

  if (!signals.length && !scatterPoints.length) return emptyStateChart(model);

  var html = "";

  // ── 1. Signal count cards ──
  var signalLabels = { "VOLATILE_UP": "Volatile Up", "VOLATILE_DOWN": "Volatile Down", "MARKET_DIVERGENT": "Market Divergent", "SHARE_SHIFT": "Share Shift", "NEW_ENTRY": "New Entry", "EXIT": "Exit" };
  var signalPriority = { "VOLATILE_DOWN": 1, "VOLATILE_UP": 2, "MARKET_DIVERGENT": 3, "SHARE_SHIFT": 4, "NEW_ENTRY": 5, "EXIT": 6 };
  var totalSignals = 0;
  Object.keys(signalCounts).forEach(function(k) { totalSignals += signalCounts[k] || 0; });

  html += '<div style="display:flex;flex-wrap:wrap;gap:8px;margin:8px 0">';
  html += '<div class="metric-card" style="flex:1 1 120px;min-width:100px"><div class="label">Total Signals</div><div class="value" style="font-size:16px">' + totalSignals + '</div></div>';
  Object.keys(signalCounts).sort(function(a,b) { return (signalPriority[a]||99) - (signalPriority[b]||99); }).forEach(function(key) {
    var count = signalCounts[key] || 0;
    if (!count) return;
    var tone = key.indexOf("DOWN") >= 0 ? "dn" : (key.indexOf("UP") >= 0 ? "up" : "");
    html += '<div class="metric-card' + (tone ? ' ' + tone : '') + '" style="flex:1 1 120px;min-width:100px"><div class="label">' + (signalLabels[key] || key) + '</div><div class="value" style="font-size:16px">' + count + '</div></div>';
  });
  html += '</div>';

  // ── 1b. Signal explanations ──
  html += '<details style="margin:6px 0;font-size:11px"><summary style="cursor:pointer;color:var(--muted);font-weight:650">Signal Definitions & Derivation</summary>';
  html += '<div style="padding:8px 12px;background:var(--surface-soft);border-radius:6px;line-height:1.7">';
  html += '<table style="font-size:11px;width:100%;border-collapse:collapse">';
  html += '<tr style="border-bottom:1px solid var(--line-soft)"><th style="text-align:left;padding:4px 6px;color:var(--muted)">Signal</th><th style="text-align:left;padding:4px 6px;color:var(--muted)">Derivation</th><th style="text-align:left;padding:4px 6px;color:var(--muted)">What It Means</th></tr>';
  html += '<tr style="border-bottom:1px solid var(--line-soft)"><td style="padding:4px 6px"><strong>VOLATILE_UP</strong></td><td style="padding:4px 6px">seller MoM% > +30% AND |gap_pp| > 10pp</td><td style="padding:4px 6px">Seller ADG surged significantly vs market — may indicate campaign, new listing, or seasonal spike</td></tr>';
  html += '<tr style="border-bottom:1px solid var(--line-soft)"><td style="padding:4px 6px"><strong>VOLATILE_DOWN</strong></td><td style="padding:4px 6px">seller MoM% < −30% AND |gap_pp| > 10pp</td><td style="padding:4px 6px">Seller ADG dropped significantly vs market — may indicate delisting, stock-out, or competitive pressure</td></tr>';
  html += '<tr style="border-bottom:1px solid var(--line-soft)"><td style="padding:4px 6px"><strong>MARKET_DIVERGENT</strong></td><td style="padding:4px 6px">seller MoM% and market MoM% move in opposite directions AND |gap_pp| > 15pp</td><td style="padding:4px 6px">Seller trend contradicts market trend — seller-specific issue, NOT a market-wide shift. Requires root cause investigation</td></tr>';
  html += '<tr style="border-bottom:1px solid var(--line-soft)"><td style="padding:4px 6px"><strong>SHARE_SHIFT</strong></td><td style="padding:4px 6px">share_in_l2 change > 5pp (positive or negative)</td><td style="padding:4px 6px">Category internal share redistribution — gainers taking share from losers within same L2. Structural change signal</td></tr>';
  html += '<tr style="border-bottom:1px solid var(--line-soft)"><td style="padding:4px 6px"><strong>NEW_ENTRY</strong></td><td style="padding:4px 6px">L3 had 0 ADG in M-1 but > 0 in MTD</td><td style="padding:4px 6px">New category/listing appeared this month — expansion signal. Monitor for sustainability</td></tr>';
  html += '<tr><td style="padding:4px 6px"><strong>EXIT</strong></td><td style="padding:4px 6px">L3 had > 0 ADG in M-1 but 0 in MTD</td><td style="padding:4px 6px">Category/listing disappeared this month — may indicate delisting or zero sales. Verify with seller</td></tr>';
  html += '</table>';
  html += '</div></details>';

  // ── 2. Scatter plot ──
  var scatterData = [];
  scatterPoints.forEach(function(p) {
    var sm = typeof p.seller_mom === "number" && isFinite(p.seller_mom) ? p.seller_mom : null;
    var mm = typeof p.mkt_mom === "number" && isFinite(p.mkt_mom) ? p.mkt_mom : null;
    if (sm == null) return;
    scatterData.push({ name: p.site_l3 || "", value: [mm || 0, sm] });
  });

  if (scatterData.length) {
    var chartId = "vol-scatter-" + Math.random().toString(36).slice(2, 6);

    // Find axis range
    var maxX = 5, maxY = 5;
    scatterData.forEach(function(p) {
      maxX = Math.max(maxX, Math.abs(p.value[0]) || 5);
      maxY = Math.max(maxY, Math.abs(p.value[1]) || 5);
    });
    maxX = niceAxisMax(maxX); maxY = niceAxisMax(maxY);

    html += '<div id="' + chartId + '" style="width:100%;height:380px" role="img" aria-label="Volatility scatter plot"></div>';

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
            formatter: function(p) { return "<strong>" + p.name + "</strong><br>Market MoM: " + formatCompact(p.value[0]) + "%<br>Seller MoM: " + formatCompact(p.value[1]) + "%"; }
          },
          grid: { left: 50, right: 30, top: 20, bottom: 50 },
          xAxis: { type: "value", name: "Market MoM%", nameLocation: "center", nameGap: 30,
            axisLabel: { fontSize: 10, formatter: function(v) { return formatCompact(v) + "%"; } },
            splitLine: { lineStyle: { color: "#edf0f3", type: "dashed" } } },
          yAxis: { type: "value", name: "Seller MoM%", nameLocation: "center", nameGap: 40,
            axisLabel: { fontSize: 10, formatter: function(v) { return formatCompact(v) + "%"; } },
            splitLine: { lineStyle: { color: "#edf0f3", type: "dashed" } } },
          series: [{
            type: "scatter", data: scatterData,
            symbolSize: function(val) { return Math.min(18, 6 + Math.abs(val[1]) * 0.3); },
            itemStyle: { color: function(p) { return p.value[1] > 0 ? "#137a4b" : "#ee4d2d"; }, opacity: 0.8 },
            markLine: { silent: true, symbol: "none",
              data: [
                { xAxis: 0, lineStyle: { color: "#68707c", type: "dashed", width: 1 } },
                { yAxis: 0, lineStyle: { color: "#68707c", type: "dashed", width: 1 } }
              ],
              label: { show: false }
            }
          }]
        });
        var ro = new ResizeObserver(function() { chart.resize(); });
        ro.observe(dom); dom._resizeObserver = ro;
      }
      tryInit();
    }, 200);
  }

  // ── 3. Signal detail table (top 15 by |mom|) ──
  signals.sort(function(a, b) { return Math.abs(b.mom || 0) - Math.abs(a.mom || 0); });
  var topSignals = signals.slice(0, 15);
  if (topSignals.length) {
    html += '<div style="margin-top:10px"><div style="font-size:11px;font-weight:700;color:var(--muted);padding:4px 0">Signal Detail (top 15 by |MoM%|)</div>';
    html += '<table class="report-table"><thead><tr><th>Path</th><th>Signal</th><th>MoM%</th><th>Gap</th><th>ADG MTD</th></tr></thead><tbody>';
    topSignals.forEach(function(s) {
      var momTone = (s.mom||0) > 0 ? "up-text" : "dn-text";
      html += '<tr><td style="font-size:10px">' + esc(s.path || "") + '</td>';
      html += '<td>' + esc(signalLabels[s.signal] || s.signal) + '</td>';
      html += '<td class="' + momTone + '">' + (s.mom != null ? formatCompact(s.mom) + "%" : "—") + '</td>';
      html += '<td>' + (s.gap_pp != null ? formatCompact(s.gap_pp) + "pp" : "—") + '</td>';
      html += '<td>' + formatCompact(s.adg_mtd || 0) + '</td></tr>';
    });
    html += '</tbody></table></div>';
  }

  return html;
}
"""


def build_section_js() -> str:
    return volatility_chart_js()


SECTION_ID = "sec_volatility"
FUNC_NAME = "volatilityChart"
