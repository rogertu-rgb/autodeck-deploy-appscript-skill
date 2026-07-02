#!/usr/bin/env python3
"""
Section 1.0 — 12-Month Performance Overview (12个月业绩概览)

Chart: split diagnostic visual. The left panel shows monthly site mix with
share/absolute toggles; the right panel compares GGP MoM% with Shopee MoM%
and exposes the Seller - Shopee gap in pp.

Requirements (from Master Design §7, Section 1.0):
  - Site mix remains the primary visual, defaulting to 100% stacked share.
  - Absolute ADG stacked view is available via toggle.
  - GGP MoM%, Shopee MoM%, and Seller-Shopee gap pp are separated to avoid overlap.
  - Total label — monthly total_adg displayed above each bar.
  - X-axis — M/1/YYYY format, all months labeled.
  - Site legend — all contributing sites with distinct colors.
  - Analysis — keep the shared computed-analysis block styling from engine.py.
  - Hover tooltips with exact value + site label.
  - Color consistency — same site = same color across all charts.
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

  // ── 1. Pivot: month × site → ADG + month-level benchmark MoM ──
  var monthsMap = {};    // monthLabel → { site → adg, total_adg }
  var sitesSet = {};

  model.body.forEach(function(item) {
    var ymRaw = val(item, "year_month");
    var mLabel = excelSerialToDateLabel(ymRaw);  // "5/1/2025" etc
    var site = String(val(item, "site") || "").trim();
    var adg = num(item, "adg") || 0;
    var totalAdg = num(item, "total_adg") || 0;
    var shopeeAdgMom = num(item, "shopee_adg_mom");

    if (!mLabel || !site) return;
    sitesSet[site] = true;

    if (!monthsMap[mLabel]) {
      monthsMap[mLabel] = { _total: 0, _sites: {} };
    }
    monthsMap[mLabel]._sites[site] = adg;
    monthsMap[mLabel]._total = totalAdg;
    if (validNumber(shopeeAdgMom)) monthsMap[mLabel]._shopeeAdgMom = shopeeAdgMom;
  });

  var months = Object.keys(monthsMap);
  months.sort(function(a, b) {
    var pa = monthParts(a), pb = monthParts(b);
    if (!pa || !pb) return 0;
    return (pa.year - pb.year) * 12 + (pa.month - pb.month);
  });

  if (!months.length) return emptyStateChart(model);

  var latestMonth = months[months.length - 1];
  var sites = Object.keys(sitesSet).sort(function(a, b) {
    var diff = (monthsMap[latestMonth]._sites[b] || 0) - (monthsMap[latestMonth]._sites[a] || 0);
    return diff || a.localeCompare(b);
  });

  if (!sites.length) return emptyStateChart(model);

  var totals = months.map(function(m) {
    var total = monthsMap[m]._total || 0;
    if (!total) {
      sites.forEach(function(site) { total += monthsMap[m]._sites[site] || 0; });
      monthsMap[m]._total = total;
    }
    return total;
  });

  var maxTotal = 0;
  totals.forEach(function(t) { if (t > maxTotal) maxTotal = t; });

  // ── 2. Compute GGP total MoM%, Shopee total MoM%, and outperformance gap ──
  var ggpMom = [];
  var shopeeMom = [];
  for (var mi = 0; mi < months.length; mi++) {
    var m = months[mi];
    var curTotal = monthsMap[m]._total || 0;
    if (mi > 0) {
      var prevTotal = monthsMap[months[mi - 1]]._total || 0;
      ggpMom.push(prevTotal > 0 ? parseFloat(((curTotal / prevTotal - 1) * 100).toFixed(1)) : null);
    } else {
      ggpMom.push(null);
    }
    var marketMom = monthsMap[m]._shopeeAdgMom;
    shopeeMom.push(validNumber(marketMom) ? parseFloat(marketMom.toFixed(1)) : null);
  }

  var gaps = ggpMom.map(function(v, i) {
    return validNumber(v) && validNumber(shopeeMom[i]) ? parseFloat((v - shopeeMom[i]).toFixed(1)) : null;
  });

  function signedPpLocal(v) {
    if (!validNumber(v)) return "-";
    return (v > 0 ? "+" : "") + formatCompact(v) + "pp";
  }

  function monthDisplay(label) {
    var p = monthParts(label);
    if (!p) return label;
    return String(p.month) + "/1/" + String(p.year);
  }

  function siteSeries(mode) {
    return sites.map(function(site) {
      return {
        name: site,
        type: "bar",
        stack: "site-mix",
        barMaxWidth: 36,
        data: months.map(function(m) {
          var raw = monthsMap[m]._sites[site] || 0;
          var total = monthsMap[m]._total || 0;
          var share = total ? raw / total * 100 : 0;
          return {
            value: mode === "share" ? parseFloat(share.toFixed(2)) : raw,
            raw: raw,
            share: share,
            total: total
          };
        }),
        itemStyle: { color: siteColor(site) },
        emphasis: { focus: "series" }
      };
    });
  }

  function siteOption(mode) {
    var isShare = mode === "share";
    var yMax = isShare ? 100 : Math.max(1, Math.ceil(maxTotal * 1.18 / 1000) * 1000);
    var labelLineData = isShare ? months.map(function() { return 100; }) : totals.slice();

    return {
      animationDuration: 450,
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        backgroundColor: "rgba(32,33,36,.94)",
        borderColor: "transparent",
        textStyle: { color: "#fff", fontSize: 12 },
        formatter: function(params) {
          var idx = params && params.length ? params[0].dataIndex : 0;
          var lines = ["<strong>" + esc(months[idx] || "") + "</strong>"];
          var total = totals[idx] || 0;
          params.forEach(function(p) {
            if (p.seriesName === "Total ADG") return;
            var d = p.data || {};
            if (!d.raw) return;
            lines.push(p.marker + p.seriesName + ": " + formatCompact(d.raw) + " ADG / " + formatCompact(d.share || 0) + "%");
          });
          lines.push('<hr style="margin:4px 0;border-color:rgba(255,255,255,.2)">Total ADG: <strong>' + formatCompact(total) + '</strong>');
          return lines.join("<br>");
        }
      },
      legend: {
        type: "scroll",
        data: sites,
        top: 0,
        left: 0,
        right: 0,
        textStyle: { fontSize: 10 },
        itemWidth: 10,
        itemHeight: 10,
        itemGap: 8,
        pageIconSize: 10,
        pageTextStyle: { fontSize: 10 }
      },
      grid: { left: 44, right: 16, top: 54, bottom: 58, containLabel: true },
      xAxis: {
        type: "category",
        data: months.map(monthDisplay),
        axisLabel: { fontSize: 10, rotate: months.length > 8 ? 35 : 0 },
        axisTick: { alignWithLabel: true }
      },
      yAxis: {
        type: "value",
        name: isShare ? "ADG占比" : "ADG",
        min: 0,
        max: yMax,
        axisLabel: {
          fontSize: 10,
          formatter: function(v) { return isShare ? formatCompact(v) + "%" : formatCompact(v); }
        },
        splitLine: { lineStyle: { color: "#edf0f3", type: "dashed" } }
      },
      series: siteSeries(mode).concat([{
        name: "Total ADG",
        type: "line",
        silent: true,
        symbol: "none",
        data: labelLineData,
        lineStyle: { opacity: 0 },
        tooltip: { show: false },
        label: {
          show: true,
          position: "top",
          distance: 4,
          color: "#111827",
          fontSize: 10,
          fontWeight: 700,
          formatter: function(p) { return formatCompact(totals[p.dataIndex] || 0); }
        }
      }])
    };
  }

  function gapOption() {
    var lineVals = [];
    ggpMom.concat(shopeeMom).forEach(function(v) {
      if (validNumber(v)) lineVals.push(v);
    });
    var minLineSource = Math.min.apply(null, lineVals.concat([0]));
    var maxLineSource = Math.max.apply(null, lineVals.concat([0]));
    var lineMin = Math.min(-10, Math.floor(minLineSource / 5) * 5);
    var lineMax = Math.max(20, Math.ceil(maxLineSource / 5) * 5);
    var maxGap = 10;
    gaps.forEach(function(v) {
      if (validNumber(v)) maxGap = Math.max(maxGap, Math.ceil(Math.abs(v) / 5) * 5);
    });

    return {
      animationDuration: 450,
      tooltip: {
        trigger: "axis",
        backgroundColor: "rgba(32,33,36,.94)",
        borderColor: "transparent",
        textStyle: { color: "#fff", fontSize: 12 },
        formatter: function(params) {
          var idx = params && params.length ? params[0].dataIndex : 0;
          var lines = ["<strong>" + esc(months[idx] || "") + "</strong>"];
          lines.push("GGP MoM: <strong>" + (validNumber(ggpMom[idx]) ? signedPct(ggpMom[idx]) : "-") + "</strong>");
          lines.push("Shopee MoM: <strong>" + (validNumber(shopeeMom[idx]) ? signedPct(shopeeMom[idx]) : "-") + "</strong>");
          lines.push("Gap: <strong>" + signedPpLocal(gaps[idx]) + "</strong>");
          return lines.join("<br>");
        }
      },
      legend: {
        data: ["GGP MoM%", "Shopee MoM%", "Gap pp"],
        top: 0,
        left: 0,
        textStyle: { fontSize: 10 },
        itemWidth: 12,
        itemHeight: 10,
        itemGap: 10
      },
      grid: [
        { left: 46, right: 24, top: 44, height: "35%", containLabel: true },
        { left: 46, right: 24, top: "60%", bottom: 48, containLabel: true }
      ],
      xAxis: [
        {
          type: "category",
          data: months.map(monthDisplay),
          gridIndex: 0,
          axisLabel: { show: false },
          axisTick: { show: false }
        },
        {
          type: "category",
          data: months.map(monthDisplay),
          gridIndex: 1,
          axisLabel: { fontSize: 10, rotate: months.length > 8 ? 35 : 0 },
          axisTick: { alignWithLabel: true }
        }
      ],
      yAxis: [
        {
          type: "value",
          name: "MoM%",
          min: lineMin,
          max: lineMax,
          gridIndex: 0,
          axisLabel: { fontSize: 10, formatter: function(v) { return formatCompact(v) + "%"; } },
          splitLine: { lineStyle: { color: "#edf0f3", type: "dashed" } }
        },
        {
          type: "value",
          name: "gap pp",
          min: -maxGap,
          max: maxGap,
          interval: maxGap,
          gridIndex: 1,
          axisLabel: { fontSize: 10, formatter: function(v) { return formatCompact(v) + "pp"; } },
          splitLine: { lineStyle: { color: "#edf0f3", type: "dashed" } }
        }
      ],
      series: [
        {
          name: "GGP MoM%",
          type: "line",
          xAxisIndex: 0,
          yAxisIndex: 0,
          data: ggpMom,
          smooth: true,
          symbol: "circle",
          symbolSize: 6,
          lineStyle: { color: "#111827", width: 2.4 },
          itemStyle: { color: "#111827" }
        },
        {
          name: "Shopee MoM%",
          type: "line",
          xAxisIndex: 0,
          yAxisIndex: 0,
          data: shopeeMom,
          smooth: true,
          symbol: "diamond",
          symbolSize: 7,
          lineStyle: { color: "#ee4d2d", width: 2.8 },
          itemStyle: { color: "#ee4d2d" }
        },
        {
          name: "Gap pp",
          type: "bar",
          xAxisIndex: 1,
          yAxisIndex: 1,
          barMaxWidth: 22,
          data: gaps,
          itemStyle: {
            color: function(p) { return (p.value || 0) >= 0 ? "#1d8f57" : "#d83a2e"; }
          },
          label: { show: false },
          markLine: {
            symbol: "none",
            silent: true,
            lineStyle: { color: "#333", width: 1 },
            data: [{ yAxis: 0 }]
          }
        }
      ]
    };
  }

  // ── 3. Render split visual container ──
  var uid = model.id + "-" + Math.random().toString(36).slice(2, 8);
  var siteChartId = "chart-site-mix-" + uid;
  var gapChartId = "chart-gap-" + uid;
  var html = '<style>';
  html += '.history-visual{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(330px,.9fr);gap:12px;margin:8px 0 10px;}';
  html += '.history-panel{min-width:0;border:1px solid var(--line);border-radius:8px;background:#fff;padding:10px 12px;}';
  html += '.history-panel-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;margin-bottom:4px;}';
  html += '.history-title{font-size:13px;font-weight:760;color:var(--ink);line-height:1.2;}';
  html += '.history-subtitle{font-size:11px;color:var(--muted);line-height:1.35;margin-top:2px;}';
  html += '.history-controls{display:inline-flex;border:1px solid var(--line);border-radius:6px;overflow:hidden;background:var(--surface-soft);flex:0 0 auto;}';
  html += '.history-controls button{border:0;border-right:1px solid var(--line);background:transparent;color:var(--muted);height:26px;min-width:56px;padding:0 10px;font:inherit;font-size:12px;font-weight:700;cursor:pointer;}';
  html += '.history-controls button:last-child{border-right:0;}';
  html += '.history-controls button.active{background:var(--accent);color:#fff;}';
  html += '.history-chart{width:100%;height:380px;}';
  html += '@media(max-width:900px){.history-visual{grid-template-columns:1fr}.history-chart{height:340px}}';
  html += '</style>';
  html += '<div class="chart-container history-visual">';
  html += '<div class="history-panel">';
  html += '<div class="history-panel-head"><div><div class="history-title">站点结构与规模贡献</div><div class="history-subtitle">默认看各站点ADG占比，切到规模后看绝对ADG贡献。</div></div>';
  html += '<div class="history-controls" data-history-controls="' + esc(uid) + '"><button type="button" class="active" data-mode="share">占比</button><button type="button" data-mode="absolute">规模</button></div></div>';
  html += '<div id="' + siteChartId + '" class="history-chart" role="img" aria-label="12-month site contribution mix"></div>';
  html += '</div>';
  html += '<div class="history-panel">';
  html += '<div class="history-panel-head"><div><div class="history-title">GGP是否跑赢Shopee</div><div class="history-subtitle">上半区比较MoM，下半区用Seller - Shopee gap直接判定跑赢/跑输。</div></div></div>';
  html += '<div id="' + gapChartId + '" class="history-chart" role="img" aria-label="GGP versus Shopee MoM and gap"></div>';
  html += '</div>';
  html += '</div>';

  // ── 4. Post-render hook ──
  setTimeout(function() {
    var siteDom = document.getElementById(siteChartId);
    var gapDom = document.getElementById(gapChartId);
    if (!siteDom || !gapDom || siteDom.clientWidth === 0 || gapDom.clientWidth === 0) return;

    var existingSite = echarts.getInstanceByDom(siteDom);
    if (existingSite) existingSite.dispose();
    var existingGap = echarts.getInstanceByDom(gapDom);
    if (existingGap) existingGap.dispose();

    var siteChart = echarts.init(siteDom);
    var gapChart = echarts.init(gapDom);
    siteChart.setOption(siteOption("share"), true);
    gapChart.setOption(gapOption(), true);

    var controls = document.querySelector('[data-history-controls="' + uid + '"]');
    if (controls) {
      controls.querySelectorAll("button[data-mode]").forEach(function(btn) {
        btn.addEventListener("click", function(ev) {
          ev.stopPropagation();
          controls.querySelectorAll("button[data-mode]").forEach(function(b) { b.classList.remove("active"); });
          btn.classList.add("active");
          siteChart.setOption(siteOption(btn.getAttribute("data-mode") || "share"), true);
        });
      });
    }

    var ro = new ResizeObserver(function() {
      siteChart.resize();
      gapChart.resize();
    });
    ro.observe(siteDom);
    ro.observe(gapDom);
    siteDom._resizeObserver = ro;
    gapDom._resizeObserver = ro;

    siteChart.on("click", function() { siteDom.classList.toggle("chart-pinned"); });
    gapChart.on("click", function() { gapDom.classList.toggle("chart-pinned"); });
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
