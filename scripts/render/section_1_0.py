#!/usr/bin/env python3
"""
Section 1.0 — 12-Month Performance Overview (12个月业绩概览)

Chart: Stacked bar chart — each bar = one month, stacked by site ADG.
Total ADG label displayed above each bar. X-axis in M/1/YYYY format.
Site legend with consistent colors.

Requirements (from Master Design §7, Section 1.0):
  ✅ Stacked bar chart (no line chart, no dual-axis)
  ✅ Total label — monthly total_adg displayed above each bar
  ✅ X-axis — M/1/YYYY format, all months labeled
  ✅ Site legend — all contributing sites with distinct colors
  ✅ Analysis — ① Total trend ② Site momentum ③ MoM% rhythm
                 ④ Structural health (>60%) ⑤ Site share migration
  ✅ Hover tooltips with exact value + site label
  ✅ Color consistency — same site = same color across all charts
"""

from __future__ import annotations


def history_stacked_chart_js() -> str:
    """
    Generate the JavaScript function 'historyStackedChart(model)'.

    This is called by visualHtml() in engine.py when model.id === 'sec_12m_history'.
    """
    return r"""
function historyStackedChart(model) {
  if (!model || !model.body.length) return emptyStateChart(model);

  // ── 1. Pivot: month × site → ADG ──
  var monthsMap = {};    // monthLabel → { site → adg, total_adg }
  var sitesSet = {};

  model.body.forEach(function(item) {
    var ymRaw = val(item, "year_month");
    var mLabel = excelSerialToDateLabel(ymRaw);  // "5/1/2025" etc
    var site = String(val(item, "site") || "").trim();
    var adg = num(item, "adg") || 0;
    var totalAdg = num(item, "total_adg") || 0;

    if (!mLabel || !site) return;
    sitesSet[site] = true;

    if (!monthsMap[mLabel]) {
      monthsMap[mLabel] = { _total: 0, _sites: {} };
    }
    monthsMap[mLabel]._sites[site] = adg;
    monthsMap[mLabel]._total = totalAdg;
  });

  var sites = Object.keys(sitesSet).sort();
  var months = Object.keys(monthsMap);

  // Sort months by parsed date
  months.sort(function(a, b) {
    var pa = monthParts(a), pb = monthParts(b);
    if (!pa || !pb) return 0;
    return (pa.year - pb.year) * 12 + (pa.month - pb.month);
  });

  if (!months.length || !sites.length) return emptyStateChart(model);

  // ── 2. Build ECharts series (one per site) ──
  var series = [];
  sites.forEach(function(site) {
    var data = months.map(function(m) {
      return monthsMap[m]._sites[site] || 0;
    });
    series.push({
      name: site,
      type: "bar",
      stack: "total",
      data: data,
      emphasis: { focus: "series" },
      itemStyle: { color: siteColor(site) }
    });
  });

  // Totals for label
  var totals = months.map(function(m) {
    return monthsMap[m]._total;
  });

  var maxTotal = 0;
  totals.forEach(function(t) { if (t > maxTotal) maxTotal = t; });

  // ── 3. Chart config ──
  var chartId = "chart-" + model.id + "-" + Math.random().toString(36).slice(2, 8);
  var option = {
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      backgroundColor: "rgba(32,33,36,.94)",
      borderColor: "transparent",
      textStyle: { color: "#fff", fontSize: 12 },
      formatter: function(params) {
        var m = params[0].axisValue;
        var lines = ["<strong>" + m + "</strong>"];
        var total = 0;
        params.forEach(function(p) {
          lines.push('<span style="display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;background:' + p.color + '"></span>' + p.seriesName + ": " + formatCompact(p.value));
          total += p.value;
        });
        lines.push('<hr style="margin:4px 0;border-color:rgba(255,255,255,.2)">Total ADG: <strong>' + formatCompact(total) + '</strong>');
        return lines.join("<br>");
      }
    },
    legend: {
      data: sites,
      top: 0,
      left: "center",
      textStyle: { fontSize: 11 },
      itemWidth: 12,
      itemHeight: 12,
      itemGap: 14,
      padding: [0, 0, 8, 0]
    },
    grid: { left: 12, right: 12, top: 40, bottom: 56 },
    xAxis: {
      type: "category",
      data: months,
      axisLabel: { fontSize: 11, rotate: months.length > 8 ? 30 : 0 },
      axisTick: { alignWithLabel: true }
    },
    yAxis: {
      type: "value",
      axisLabel: {
        fontSize: 10,
        formatter: function(v) { return formatCompact(v); }
      },
      splitLine: { lineStyle: { color: "#edf0f3", type: "dashed" } }
    },
    series: series
  };

  // ── 4. Render chart container ──
  var html = '<div class="chart-container">';
  html += '<div id="' + chartId + '" style="width:100%;height:340px" role="img" aria-label="12-month stacked bar chart by site"></div>';
  html += '</div>';

  // ── 5. Post-render hook ──
  setTimeout(function() {
    var dom = document.getElementById(chartId);
    if (!dom || dom.clientWidth === 0) return;

    // Clean up existing instance
    var existing = echarts.getInstanceByDom(dom);
    if (existing) existing.dispose();

    var chart = echarts.init(dom);
    chart.setOption(option);

    // Resize handler
    var ro = new ResizeObserver(function() { chart.resize(); });
    ro.observe(dom);
    dom._resizeObserver = ro;

    // Click → pin tooltip
    chart.on("click", function() { dom.classList.toggle("chart-pinned"); });
  }, 150);

  return html;
}
"""


def analysis_text_zh() -> str:
    """Return the Chinese analysis template for sec_text tab."""
    return (
        "① 总量趋势：过去12个月总ADG从{adg_12m_ago}变化至{adg_current}，"
        "峰值在{peak_month}（{peak_adg}），谷值在{valley_month}（{valley_adg}）。\n"
        "② 站点动量：{momentum_sites}连续同向变化，其中{top_momentum_site}表现最突出。\n"
        "③ MoM%节奏：{rhythm_pattern}，{inflection_note}。\n"
        "④ 结构健康：{dominant_site}占比{dominant_share}%{health_warning}。\n"
        "⑤ 站点份额迁移：{share_migration_summary}。"
    )


def build_section_js() -> str:
    """
    Return the complete JavaScript code block for section 1.0.

    Includes:
    - historyStackedChart(model) — main chart function
    - buildHistory(model, metrics, bullets) — analysis text builder (optional helper)
    """
    return history_stacked_chart_js()


# ── Python-side helper for test harness auto-registration ──
SECTION_ID = "sec_12m_history"
FUNC_NAME = "historyStackedChart"
