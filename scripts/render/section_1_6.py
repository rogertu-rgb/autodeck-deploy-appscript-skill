#!/usr/bin/env python3
"""
Section 1.6 — Category-Site Anomaly Signal Workbench (类目站点异常信号扫描)

Primary experience: a seller-side anomaly workbench with summary cards,
quadrant scatter, priority queue, selected-signal detail, and linked 1/2/3
highlights. Data comes from sec_volatility_meta.
"""

from __future__ import annotations


def volatility_chart_js() -> str:
    return r"""
function volatilityChart(model) {
  var md = metaDict("sec_volatility");
  var signalCounts = parseLooseJson(md.signal_counts, {});
  var rawSignals = parseLooseJson(md.signals, []);
  var scatterRaw = parseLooseJson(md.scatter_data, []);
  if ((!rawSignals || !rawSignals.length) && (!scatterRaw || !scatterRaw.length)) return emptyStateChart(model);

  var data = volatilityEnrichedSignals(rawSignals, scatterRaw);
  if (!data.length) return emptyStateChart(model);

  var totalSignals = Object.keys(signalCounts || {}).reduce(function(s, k) { return s + (Number(signalCounts[k]) || 0); }, 0);
  var defaultRows = volatilityDefaultRows(data);
  var calloutRows = defaultRows.slice(0, 3);
  calloutRows.forEach(function(d, idx) { d.calloutRank = idx + 1; });

  var uid = Math.random().toString(36).slice(2, 8);
  var rootId = "vol-workbench-" + uid;
  var summaryId = "vol-summary-" + uid;
  var filterId = "vol-filters-" + uid;
  var scatterId = "vol-scatter-" + uid;
  var queueId = "vol-queue-" + uid;
  var detailId = "vol-detail-" + uid;
  var insightId = "vol-insights-" + uid;
  var confidenceId = "vol-confidence-" + uid;
  var lowVolumeId = "vol-low-volume-" + uid;

  var html = "";
  html += '<div class="vol-workbench" id="' + rootId + '">';
  html += '<style>';
  html += '.vol-workbench{--vol-orange:var(--accent,#ee4d2d);--vol-line:var(--line,#d8dce2);--vol-soft:#f7f8fa;--vol-muted:var(--muted,#667085);margin:8px 0 12px}';
  html += '.vol-summary{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin:8px 0 10px}.vol-card{border:1px solid var(--vol-line);background:#fff;padding:8px 10px;min-height:62px}.vol-card .label{font-size:10px;color:var(--vol-muted);font-weight:800;text-transform:uppercase}.vol-card .value{font-size:22px;line-height:1.05;font-weight:850;margin-top:2px}.vol-card .context{font-size:10px;color:var(--vol-muted);margin-top:2px;line-height:1.25}';
  html += '.vol-grid{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(320px,.75fr);gap:10px}.vol-panel{border:1px solid var(--vol-line);background:#fff;padding:10px;min-width:0}.vol-panel-title{display:flex;justify-content:space-between;gap:10px;align-items:start;margin-bottom:6px}.vol-panel-title b{font-size:13px;line-height:1.15}.vol-panel-title small{font-size:10px;color:var(--vol-muted);text-align:right;line-height:1.25}.vol-filters{display:flex;flex-wrap:wrap;gap:5px;margin:6px 0 8px}.vol-filter-btn,.vol-toggle-btn{border:1px solid var(--vol-line);background:#fff;color:#111;padding:4px 8px;font-size:10px;font-weight:800;cursor:pointer;border-radius:0}.vol-filter-btn.active,.vol-toggle-btn.active{border-color:var(--vol-orange);background:#fff1ed;color:var(--vol-orange)}';
  html += '.vol-scatter-wrap{position:relative;height:420px;border:1px solid #eceff3;background:#fff;overflow:hidden}.vol-scatter-wrap svg{position:absolute;inset:0;width:100%;height:100%}.vol-quad{position:absolute;padding:4px 6px;background:rgba(255,255,255,.88);border:1px solid #e3e6ea;font-size:10px;font-weight:800;color:#555}.vol-q1{right:8px;top:8px}.vol-q2{left:8px;top:8px}.vol-q3{left:8px;bottom:8px}.vol-q4{right:8px;bottom:8px;color:#c83025;border-color:#f0bbb5;background:#fff2ef}.vol-axis{position:absolute;color:#555;font-size:10px;font-weight:800}.vol-x{left:50%;bottom:8px;transform:translateX(-50%)}.vol-y{left:8px;top:50%;transform:translateY(-50%) rotate(-90deg);transform-origin:left center}.vol-point{cursor:pointer;stroke:#fff;stroke-width:1.8;opacity:.88}.vol-point.selected{stroke:var(--vol-orange);stroke-width:4;opacity:1}.vol-point.low-confidence{opacity:.22;stroke-dasharray:3 2}.vol-point-label circle{fill:var(--vol-orange);stroke:#fff;stroke-width:1.5}.vol-point-label text{fill:#fff;font-size:13px;font-weight:850;text-anchor:middle;dominant-baseline:central;pointer-events:none}';
  html += '.vol-queue-panel{display:grid;grid-template-rows:auto auto minmax(0,1fr);min-height:0}.vol-queue-list{overflow:auto;max-height:420px;border-top:1px solid var(--vol-line);padding-top:7px}.vol-queue-row{display:grid;grid-template-columns:26px minmax(0,1fr) auto;gap:7px;align-items:start;border:1px solid #e7e9ee;background:#fafafa;padding:7px;margin-bottom:7px;cursor:pointer}.vol-queue-row:hover,.vol-queue-row.selected{outline:2px solid var(--vol-orange);outline-offset:-2px;background:#fff8f5}.vol-callout,.vol-insight-marker{display:inline-grid;place-items:center;width:23px;height:23px;border-radius:50%;background:var(--vol-orange);color:#fff;font-size:13px;font-weight:850;line-height:1}.vol-rank-muted{display:inline-grid;place-items:center;width:23px;height:23px;color:var(--vol-muted);font-size:11px;font-weight:800}.vol-queue-main b{display:block;font-size:11px;line-height:1.22}.vol-queue-main small{display:block;margin-top:3px;color:var(--vol-muted);font-size:10px;line-height:1.28}.vol-tag{display:inline-block;min-width:74px;padding:3px 6px;border:1px solid #ddd;background:#eee;text-align:center;font-size:9px;font-weight:850;white-space:nowrap}.vol-tag-red{background:#fff0ed;border-color:#e9b9b0;color:#c83025}.vol-tag-green{background:#edf8f1;border-color:#b8dcc5;color:#16884f}.vol-tag-blue{background:#eef2ff;border-color:#c5cff7;color:#3157c9}.vol-tag-warn{background:#fff7e8;border-color:#e6c891;color:#a06000}';
  html += '.vol-detail-grid{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,1fr);gap:10px;margin-top:10px}.vol-detail-card,.vol-key{background:#f1f2f4;border:1px solid #dfe3e8;padding:10px 12px;min-width:0}.vol-detail-card h4,.vol-key h4{margin:0 0 6px;font-size:13px;line-height:1.1}.vol-mini-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px;margin-bottom:7px}.vol-mini{background:#fff;border:1px solid #dfe3e8;padding:5px 6px;min-height:42px}.vol-mini span{display:block;color:var(--vol-muted);font-size:9px;font-weight:800;text-transform:uppercase}.vol-mini b{display:block;margin-top:2px;font-size:13px;line-height:1.05}.vol-table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:10px;line-height:1.2}.vol-table th,.vol-table td{padding:5px 6px;border:1px solid #fff;text-align:center;vertical-align:middle}.vol-table th{background:#404040;color:#fff;font-weight:850}.vol-insights{margin:0;padding:0;list-style:none;font-size:11px;line-height:1.42}.vol-insights li{display:flex;align-items:flex-start;gap:8px;margin-bottom:7px}.vol-route-chip{display:inline-block;margin-left:4px;padding:2px 5px;background:#fff;border:1px solid var(--vol-orange);color:var(--vol-orange);font-size:10px;font-weight:850}.vol-empty{padding:18px;color:var(--vol-muted);font-size:12px}.vol-up{color:#16884f;font-weight:850}.vol-down{color:#c83025;font-weight:850}@media(max-width:980px){.vol-summary,.vol-grid,.vol-detail-grid{grid-template-columns:1fr}.vol-panel-title small{text-align:left}.vol-mini-grid{grid-template-columns:1fr 1fr}.vol-queue-list{max-height:360px}}';
  html += '</style>';
  html += '<div class="vol-summary" id="' + summaryId + '"></div>';
  html += '<div class="vol-grid">';
  html += '<section class="vol-panel"><div class="vol-panel-title"><b>四象限异常图</b><small>x=大盘MoM，y=卖家MoM；点大小=ADG，编号=数据诊断Top3</small></div><div class="vol-filters" id="' + filterId + '"></div><div class="vol-scatter-wrap"><div class="vol-quad vol-q1">顺势增长</div><div class="vol-quad vol-q2">逆势增长</div><div class="vol-quad vol-q3">大盘逆风</div><div class="vol-quad vol-q4">红色警报</div><div class="vol-axis vol-x">Market ADG MoM%</div><div class="vol-axis vol-y">Seller ADG MoM%</div><svg id="' + scatterId + '" viewBox="0 0 900 420" role="img" aria-label="seller market volatility scatter"></svg></div></section>';
  html += '<section class="vol-panel vol-queue-panel"><div class="vol-panel-title"><b>优先检查队列</b><small>按 gap × ADG × confidence 排序</small></div><div class="vol-filters"><button class="vol-toggle-btn active" id="' + confidenceId + '">隐藏低可信</button><button class="vol-toggle-btn" id="' + lowVolumeId + '">显示低体量</button></div><div class="vol-queue-list" id="' + queueId + '"></div></section>';
  html += '</div><div class="vol-detail-grid"><div class="vol-detail-card" id="' + detailId + '"></div><aside class="vol-key"><h4>Key Highlights</h4><ol class="vol-insights" id="' + insightId + '"></ol></aside></div>';
  html += '</div>';

  setTimeout(function() {
    var root = document.getElementById(rootId);
    if (!root) return;
    var state = {
      filter: "all",
      hideLowConfidence: true,
      showLowVolume: false,
      selectedId: (defaultRows[0] || data[0] || {}).id || ""
    };
    var filters = [
      { id: "all", label: "全部可行动" },
      { id: "red", label: "红色警报" },
      { id: "downside", label: "跌幅优先" },
      { id: "anti", label: "逆势增长" },
      { id: "low", label: "低可信池" }
    ];

    function byId(id) { return document.getElementById(id); }
    function fmt(n, suffix) {
      if (!validNumber(n)) return "—";
      return formatCompact(n) + (suffix || "");
    }
    function signed(n, suffix) {
      if (!validNumber(n)) return "—";
      return (n > 0 ? "+" : "") + formatCompact(n) + (suffix || "%");
    }
    function color(d) {
      if (d.redAlert) return "#c83025";
      if (d.antiGrowth || d.signal === "VOLATILE_UP") return "#16884f";
      if (d.signal === "SHARE_SHIFT") return "#a06000";
      return "#3157c9";
    }
    function tagClass(d) {
      if (d.redAlert || d.signal === "VOLATILE_DOWN") return "vol-tag-red";
      if (d.antiGrowth || d.signal === "VOLATILE_UP") return "vol-tag-green";
      if (d.signal === "SHARE_SHIFT") return "vol-tag-warn";
      return "vol-tag-blue";
    }
    function tagLabel(d) {
      if (d.redAlert) return "红色警报";
      if (d.antiGrowth) return "逆势增长";
      if (d.signal === "VOLATILE_DOWN") return "暴跌";
      if (d.signal === "VOLATILE_UP") return "暴涨";
      if (d.signal === "MARKET_DIVERGENT") return "市场背离";
      if (d.signal === "SHARE_SHIFT") return "份额迁移";
      if (d.signal === "NEW_ENTRY") return "新进入";
      if (d.signal === "EXIT") return "消失";
      return d.signal || "Signal";
    }
    function filtered() {
      return data.filter(function(d) {
        if (state.filter !== "low" && state.hideLowConfidence && d.lowConfidence) return false;
        if (state.filter !== "low" && !state.showLowVolume && d.lowVolume) return false;
        if (state.filter === "red") return d.redAlert;
        if (state.filter === "downside") return d.signal === "VOLATILE_DOWN" || d.mom < 0;
        if (state.filter === "anti") return d.antiGrowth || d.signal === "VOLATILE_UP";
        if (state.filter === "low") return d.lowConfidence;
        return true;
      }).sort(function(a, b) { return b.score - a.score; });
    }
    function renderSummary(rows) {
      var red = data.filter(function(d) { return d.redAlert && !d.lowConfidence; }).length;
      var hidden = data.filter(function(d) { return d.lowConfidence; }).length;
      var rowsEl = byId(summaryId);
      if (!rowsEl) return;
      rowsEl.innerHTML = [
        ["Total raw signals", totalSignals || data.length, "来自 metadata signal count"],
        ["可行动异常", rows.length, "当前筛选后队列"],
        ["红色警报", red, "卖家跌、大盘涨、且有量"],
        ["低可信隐藏", state.hideLowConfidence ? hidden : 0, "低量 / 极端gap / Other路径"]
      ].map(function(card) {
        return '<div class="vol-card"><div class="label">' + esc(card[0]) + '</div><div class="value">' + esc(card[1]) + '</div><div class="context">' + esc(card[2]) + '</div></div>';
      }).join("");
    }
    function renderFilters() {
      var holder = byId(filterId);
      if (!holder) return;
      holder.innerHTML = filters.map(function(f) {
        return '<button class="vol-filter-btn ' + (state.filter === f.id ? "active" : "") + '" data-filter="' + f.id + '">' + esc(f.label) + '</button>';
      }).join("");
      holder.querySelectorAll(".vol-filter-btn").forEach(function(btn) {
        btn.addEventListener("click", function() {
          state.filter = btn.getAttribute("data-filter");
          render();
        });
      });
      var conf = byId(confidenceId), low = byId(lowVolumeId);
      if (conf) conf.classList.toggle("active", state.hideLowConfidence);
      if (low) low.classList.toggle("active", state.showLowVolume);
    }
    function renderScatter(rows) {
      var svg = byId(scatterId);
      if (!svg) return;
      var w = 900, h = 420, pad = 44;
      var rangeRows = state.filter === "low" ? data.filter(function(d) { return d.lowConfidence; }) : rows.concat(calloutRows);
      if (!rangeRows.length) rangeRows = data;
      var maxAbsX = Math.max.apply(null, [50].concat(rangeRows.map(function(d) { return Math.abs(d.market || 0); })));
      var maxAbsY = Math.max.apply(null, [50].concat(rangeRows.map(function(d) { return Math.abs(d.mom || 0); })));
      var xMax = Math.min(220, Math.ceil(maxAbsX / 25) * 25);
      var yMax = Math.min(240, Math.ceil(maxAbsY / 25) * 25);
      function sx(x) { x = Math.max(-xMax, Math.min(xMax, x || 0)); return pad + ((x + xMax) / (2 * xMax)) * (w - pad * 2); }
      function sy(y) { y = Math.max(-yMax, Math.min(yMax, y || 0)); return h - pad - ((y + yMax) / (2 * yMax)) * (h - pad * 2); }
      var grid = [-1, -.5, 0, .5, 1].map(function(t) {
        var x = pad + (t + 1) / 2 * (w - pad * 2);
        var y = pad + (t + 1) / 2 * (h - pad * 2);
        return '<line x1="' + x + '" y1="' + pad + '" x2="' + x + '" y2="' + (h-pad) + '" stroke="#edf0f3"/><line x1="' + pad + '" y1="' + y + '" x2="' + (w-pad) + '" y2="' + y + '" stroke="#edf0f3"/>';
      }).join("");
      var points = rows.map(function(d) {
        var r = Math.max(5, Math.min(18, 5 + Math.sqrt(Math.max(d.adg_mtd || 0, 0)) * .75));
        return '<circle class="vol-point ' + (d.id === state.selectedId ? "selected " : "") + (d.lowConfidence ? "low-confidence" : "") + '" data-id="' + esc(d.id) + '" cx="' + sx(d.market) + '" cy="' + sy(d.mom) + '" r="' + r + '" fill="' + color(d) + '"><title>' + esc((d.site || "") + " " + (d.l3 || "") + ": seller " + signed(d.mom) + ", market " + signed(d.market)) + '</title></circle>';
      }).join("");
      var labels = rows.filter(function(d) { return d.calloutRank; }).map(function(d) {
        var x = Math.min(w - 18, Math.max(18, sx(d.market) + 16));
        var y = Math.min(h - 18, Math.max(18, sy(d.mom) - 16));
        return '<g class="vol-point-label" data-id="' + esc(d.id) + '"><circle cx="' + x + '" cy="' + y + '" r="11"></circle><text x="' + x + '" y="' + y + '">' + d.calloutRank + '</text></g>';
      }).join("");
      svg.innerHTML = grid + '<line x1="' + sx(0) + '" y1="' + pad + '" x2="' + sx(0) + '" y2="' + (h-pad) + '" stroke="#667085" stroke-width="1.4" stroke-dasharray="4 4"/><line x1="' + pad + '" y1="' + sy(0) + '" x2="' + (w-pad) + '" y2="' + sy(0) + '" stroke="#667085" stroke-width="1.4" stroke-dasharray="4 4"/>' + points + labels;
      svg.querySelectorAll(".vol-point,.vol-point-label").forEach(function(p) {
        p.addEventListener("click", function() {
          state.selectedId = p.getAttribute("data-id");
          render();
        });
      });
    }
    function renderQueue(rows) {
      var queue = byId(queueId);
      if (!queue) return;
      var top = rows.slice(0, 10);
      queue.innerHTML = top.map(function(d, idx) {
        var rank = d.calloutRank ? '<span class="vol-callout">' + d.calloutRank + '</span>' : '<span class="vol-rank-muted">#' + (idx + 1) + '</span>';
        return '<div class="vol-queue-row ' + (d.id === state.selectedId ? "selected" : "") + '" data-id="' + esc(d.id) + '">' + rank + '<div class="vol-queue-main"><b>' + esc((d.site || "—") + " / " + (d.l2 || "—") + " / " + (d.l3 || "—")) + '</b><small>Seller ' + signed(d.mom) + ' · Market ' + signed(d.market) + ' · Gap ' + signed(d.gap_pp, "pp") + ' · ADG ' + fmt(d.adg_mtd) + '</small></div><span class="vol-tag ' + tagClass(d) + '">' + esc(tagLabel(d)) + '</span></div>';
      }).join("") || '<div class="vol-empty">当前筛选没有可展示异常。</div>';
      queue.querySelectorAll(".vol-queue-row").forEach(function(row) {
        row.addEventListener("click", function() {
          state.selectedId = row.getAttribute("data-id");
          render();
        });
      });
    }
    function renderDetail(rows) {
      var selected = data.find(function(d) { return d.id === state.selectedId; }) || rows[0] || data[0];
      var detail = byId(detailId);
      if (detail && selected) {
        var rank = rows.findIndex(function(d) { return d.id === selected.id; }) + 1;
        detail.innerHTML = '<h4>' + esc((selected.site || "—") + " / " + (selected.l1 || "—") + " / " + (selected.l2 || "—") + " / " + (selected.l3 || "—")) + '</h4><div class="vol-mini-grid">' +
          '<div class="vol-mini"><span>Seller MoM</span><b class="' + (selected.mom >= 0 ? "vol-up" : "vol-down") + '">' + signed(selected.mom) + '</b></div>' +
          '<div class="vol-mini"><span>Market MoM</span><b class="' + (selected.market >= 0 ? "vol-up" : "vol-down") + '">' + signed(selected.market) + '</b></div>' +
          '<div class="vol-mini"><span>Gap</span><b class="' + (selected.gap_pp >= 0 ? "vol-up" : "vol-down") + '">' + signed(selected.gap_pp, "pp") + '</b></div>' +
          '<div class="vol-mini"><span>ADG MTD</span><b>' + fmt(selected.adg_mtd) + '</b></div></div>' +
          '<table class="vol-table"><thead><tr><th>Signal</th><th>Confidence</th><th>Route</th><th>Priority</th></tr></thead><tbody><tr><td>' + esc(selected.signal || "—") + '</td><td>' + Math.round((selected.confidence || 0) * 100) + '%</td><td>' + esc(selected.route || "—") + '</td><td>' + (rank > 0 ? "#" + rank : "Hidden") + '</td></tr></tbody></table>';
      }
      var insight = byId(insightId);
      if (insight) {
        insight.innerHTML = calloutRows.map(function(d) {
          return '<li><span class="vol-insight-marker">' + d.calloutRank + '</span><span><strong>' + esc((d.site || "—") + " " + (d.l3 || d.l2 || "—")) + '</strong> ' + esc(tagLabel(d)) + '：seller ' + signed(d.mom) + ' vs market ' + signed(d.market) + '，gap ' + signed(d.gap_pp, "pp") + '，ADG ' + fmt(d.adg_mtd) + '。<span class="vol-route-chip">' + esc(d.route || "继续观察") + '</span></span></li>';
        }).join("") || '<li class="vol-empty">暂无足够高置信异常。</li>';
      }
    }
    function render() {
      var rows = filtered();
      if (!rows.find(function(d) { return d.id === state.selectedId; })) state.selectedId = (rows[0] || data[0] || {}).id || "";
      renderSummary(rows);
      renderFilters();
      renderScatter(rows);
      renderQueue(rows);
      renderDetail(rows);
    }
    var confBtn = byId(confidenceId);
    var lowBtn = byId(lowVolumeId);
    if (confBtn) confBtn.addEventListener("click", function() { state.hideLowConfidence = !state.hideLowConfidence; render(); });
    if (lowBtn) lowBtn.addEventListener("click", function() { state.showLowVolume = !state.showLowVolume; render(); });
    render();
  }, 0);

  return html;
}
"""


def build_section_js() -> str:
    return volatility_chart_js()


SECTION_ID = "sec_volatility"
FUNC_NAME = "volatilityChart"
