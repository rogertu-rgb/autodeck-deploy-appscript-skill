#!/usr/bin/env python3
"""
AutoDeck Render Engine — shared JavaScript generation.

Each method returns a string of JavaScript code. All strings are concatenated
to build the final <script> block. Per-section visual functions live in
individual section_*.py files, not here.

Design rule: no function duplicates, no raw HTML in JS strings that haven't
been properly escaped, and safeDisplay() guards all meta-tab values.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional


class Engine:
    """Generates shared JavaScript for AutoDeck HTML reports."""

    # ── Site color palette (consistent across all charts) ──
    SITE_COLORS: Dict[str, str] = {
        "ID": "#7aa6f9",
        "MY": "#fb8f67",
        "PH": "#6fbd8a",
        "SG": "#f7cf5b",
        "TH": "#c792b1",
        "VN": "#e0523f",
        "TW": "#ef7772",
        "BR": "#5fa8d4",
        "MX": "#9b7ec4",
        "CO": "#f2a553",
        "CL": "#5cbbab",
        "AR": "#b7d0f8",
    }
    FALLBACK_COLORS: List[str] = [
        "#7aa6f9", "#fb8f67", "#6fbd8a", "#f7cf5b",
        "#c792b1", "#2f9e63", "#e0523f", "#5fa8d4",
        "#9b7ec4", "#f2a553", "#5cbbab", "#b7d0f8",
    ]

    # ── Chinese column labels ──
    COL_LABELS_ZH: Dict[str, str] = {
        "year_month": "月份", "site": "站点", "l1": "一级品类", "l2": "二级品类", "l3": "三级品类",
        "shop_id": "店铺ID", "shop_name": "店铺名", "item_name": "商品名",
        "price_range": "价格带", "price_band": "价格带",
        "adg": "ADG", "adg_mtd": "当月ADG", "adg_m1": "上月ADG",
        "mtd_adg": "当月ADG", "m1_adg": "上月ADG",
        "seller_adg": "卖家ADG", "ads_adg": "广告ADG", "total_adg": "总ADG",
        "ado": "ADO", "ado_mtd": "当月ADO", "ado_m1": "上月ADO",
        "ads_ado": "广告ADO", "total_ado": "总ADO",
        "adg_mom": "ADG环比", "seller_adg_mom": "卖家ADG环比",
        "mkt_adg_mom": "大盘ADG环比", "ado_mom": "ADO环比",
        "seller_ado_mom": "卖家ADO环比", "mkt_ado_mom": "大盘ADO环比",
        "adg_gap_pp": "ADG差距", "ado_gap_pp": "ADO差距", "gap_pp": "差距(pp)",
        "adg_share": "ADG占比", "ado_share": "ADO占比",
        "share_in_site": "站内占比", "share_in_l3": "L3占比",
        "contribution_pct": "贡献度", "total": "合计",
        "fbs_share": "FBS占比", "tpf_share": "TPF占比", "sls_share": "SLS占比",
        "fbs_shift_pp": "FBS变化", "tpf_shift_pp": "TPF变化", "sls_shift_pp": "SLS变化",
        "organic_share": "自然流量占比", "ads_share": "广告占比",
        "live_share": "直播占比", "campaign_share": "活动占比",
        "roas": "ROAS", "acp": "单均成本", "spend": "广告支出",
        "subsidy_share": "补贴占比", "seller_funded_share": "卖家出资占比",
        "platform_funded_share": "平台出资占比", "seller_share": "卖家占比",
        "mkt_price_share": "大盘价格带占比",
        "seller_share_m1": "卖家上月占比", "share_shift_pp": "占比变化",
        "bias_pp": "价格偏差(pp)", "mkt_share": "大盘占比",
        "seller_cnt": "卖家数", "p10_growth": "P10增速", "p25_growth": "P25增速",
        "p50_growth": "P50增速", "days_active": "活跃天数",
        "is_new_item": "是否新品", "is_official_shop": "是否Mall店",
    }

    def __init__(self, lang: str = "zh"):
        self.lang = lang

    # ═══════════════════════════════════════════════════════════════
    # 1. Core Utilities
    # ═══════════════════════════════════════════════════════════════

    def js_core_utilities(self) -> str:
        """HTML escaping, string normalization, blank checking, number parsing."""
        return r"""
function esc(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function norm(value) {
  return String(value == null ? "" : value).trim().toLowerCase();
}

function isBlank(value) {
  return value == null || value === "" || String(value).trim() === "";
}

function parseNum(value) {
  if (value == null || value === "") return null;
  if (typeof value === "number") return isFinite(value) ? value : null;
  var s = String(value).replace(/,/g, "").replace(/%/g, "").replace(/−/g, "-").trim();
  if (!s) return null;
  var n = Number(s);
  return isFinite(n) ? n : null;
}

function prettyCol(col) {
  var key = norm(col);
  if (COL_LABELS[key]) return COL_LABELS[key];
  return String(col == null ? "" : col)
    .replace(/_/g, " ")
    .replace(/\b\w/g, function(ch) { return ch.toUpperCase(); });
}
"""

    # ═══════════════════════════════════════════════════════════════
    # 2. Month / Date handling
    # ═══════════════════════════════════════════════════════════════

    def js_month_utils(self) -> str:
        """Excel serial date conversion and month arithmetic."""
        return r"""
function excelSerialToMonth(value) {
  var n = parseNum(value);
  if (n == null || n < 30000 || n > 60000) return String(value == null ? "" : value);
  var date = new Date(Date.UTC(1899, 11, 30) + Math.round(n) * 86400000);
  return date.getUTCFullYear() + "-" + String(date.getUTCMonth() + 1).padStart(2, "0");
}

function monthSortKey(value) {
  var n = parseNum(value);
  if (n != null && n >= 30000 && n <= 60000) return n;
  var s = String(value == null ? "" : value).trim();
  var iso = s.match(/^(\d{4})-(\d{1,2})/);
  if (iso) return Number(iso[1]) * 100 + Number(iso[2]);
  var slash = s.match(/^(\d{1,2})\/\d{1,2}\/(\d{4})/);
  if (slash) return Number(slash[2]) * 100 + Number(slash[1]);
  return s;
}

function excelSerialToDateLabel(value) {
  var n = parseNum(value);
  if (n != null && n >= 30000 && n <= 60000) {
    var date = new Date(Date.UTC(1899, 11, 30) + Math.round(n) * 86400000);
    return (date.getUTCMonth() + 1) + "/1/" + date.getUTCFullYear();
  }
  var s = String(value == null ? "" : value).trim();
  var iso = s.match(/^(\d{4})-(\d{1,2})/);
  if (iso) return Number(iso[2]) + "/1/" + iso[1];
  var slash = s.match(/^(\d{1,2})\/\d{1,2}\/(\d{4})/);
  if (slash) return Number(slash[1]) + "/1/" + slash[2];
  return s;
}

function monthParts(value) {
  var n = parseNum(value);
  if (n != null && n >= 30000 && n <= 60000) {
    var date = new Date(Date.UTC(1899, 11, 30) + Math.round(n) * 86400000);
    return { year: date.getUTCFullYear(), month: date.getUTCMonth() + 1 };
  }
  var s = String(value == null ? "" : value).trim();
  var iso = s.match(/^(\d{4})-(\d{1,2})/);
  if (iso) return { year: Number(iso[1]), month: Number(iso[2]) };
  var slash = s.match(/^(\d{1,2})\/\d{1,2}\/(\d{4})/);
  if (slash) return { year: Number(slash[2]), month: Number(slash[1]) };
  return null;
}

function monthKey(parts) { return parts ? parts.year + "-" + String(parts.month).padStart(2, "0") : ""; }
function monthLabel(parts) { return parts ? parts.month + "/1/" + parts.year : ""; }

function addMonths(parts, delta) {
  if (!parts) return null;
  var monthIndex = parts.year * 12 + (parts.month - 1) + delta;
  return { year: Math.floor(monthIndex / 12), month: monthIndex % 12 + 1 };
}

function monthDistance(start, end) {
  if (!start || !end) return 0;
  return (end.year - start.year) * 12 + (end.month - start.month);
}
"""

    # ═══════════════════════════════════════════════════════════════
    # 3. Number / Value formatting
    # ═══════════════════════════════════════════════════════════════

    def js_formatting(self) -> str:
        """formatCompact, formatThousands, niceAxisMax, formatValue, sanitizeCell, valueTone."""
        return r"""
function formatCompact(n) {
  if (n == null || !isFinite(n)) return "";
  var abs = Math.abs(n);
  if (abs >= 1000000000) return (n / 1000000000).toFixed(1).replace(/\.0$/, "") + "B";
  if (abs >= 1000000) return (n / 1000000).toFixed(1).replace(/\.0$/, "") + "M";
  if (abs >= 1000) return (n / 1000).toFixed(1).replace(/\.0$/, "") + "K";
  if (abs >= 100) return n.toFixed(0);
  if (abs >= 10) return n.toFixed(1).replace(/\.0$/, "");
  return n.toFixed(2).replace(/\.?0+$/, "");
}

function formatThousands(n) {
  if (n == null || !isFinite(n)) return "";
  return Math.round(n).toLocaleString("en-US");
}

function niceAxisMax(maxVal) {
  if (!maxVal || maxVal <= 0) return 1;
  var roughStep = maxVal / 5;
  var pow = Math.pow(10, Math.floor(Math.log10(roughStep)));
  var unit = roughStep / pow;
  var step = unit <= 1 ? pow : (unit <= 2 ? 2 * pow : (unit <= 5 ? 5 * pow : 10 * pow));
  return Math.ceil(maxVal / step) * step;
}

function formatValue(value, col) {
  if (isBlank(value)) return "";
  var key = norm(col);
  if (key === "year_month" || key === "month") return excelSerialToMonth(value);
  if (key === "shop_id" || key === "item_id" || key === "item_link" || key === "shop_link") return String(value);
  var n = parseNum(value);
  if (n == null) return String(value);
  if (key.indexOf("gap") >= 0 || key.indexOf("shift") >= 0 || key.indexOf("bias") >= 0) return formatCompact(n) + "pp";
  if (key.indexOf("mom") >= 0 || key.indexOf("share") >= 0 || key.indexOf("pct") >= 0) return formatCompact(n) + "%";
  if (key === "roas") return n.toFixed(1).replace(/\.0$/, "");
  return formatCompact(n);
}

function sanitizeCell(value, col) {
  var formatted = formatValue(value, col);
  var s = String(formatted || "").trim();
  if ((s.charAt(0) === "[" || s.charAt(0) === "{") && s.length > 10) return "[data]";
  if (s.indexOf('":') > 0 && s.length > 30) return "[data]";
  return formatted;
}

function valueTone(value, col) {
  var key = norm(col);
  var n = parseNum(value);
  if (n == null) return "";
  if (key.indexOf("mom") >= 0 || key.indexOf("gap") >= 0 || key.indexOf("shift") >= 0 || key.indexOf("bias") >= 0) {
    if (n < 0) return "dn-text";
    if (n > 0) return "up-text";
  }
  return "";
}

function safeDisplay(raw, fallback) {
  if (raw == null || raw === "") return fallback || "";
  var s = String(raw).trim();
  if (s.charAt(0) === "[" || s.charAt(0) === "{") {
    try {
      var obj = JSON.parse(s.replace(/\bnan\b/g, "null").replace(/\bNone\b/g, "null").replace(/\bTrue\b/g, "true").replace(/\bFalse\b/g, "false"));
      if (Array.isArray(obj)) return obj.length + " records";
      if (typeof obj === "object") {
        var keys = Object.keys(obj);
        if (keys.length === 0) return "(empty)";
        if (keys.length <= 3) return keys.map(function(k) { return k + ": " + String(obj[k]).slice(0, 60); }).join("; ");
        return keys.length + " data fields";
      }
    } catch(e) {}
  }
  if (s.length > 80) return s.slice(0, 77) + "...";
  return s;
}
"""

    # ═══════════════════════════════════════════════════════════════
    # 4. Data model
    # ═══════════════════════════════════════════════════════════════

    def js_data_model(self) -> str:
        """rowsModel, rowLabel, colIndex, hasCol, firstCol, val, num, ev, evidenceText."""
        return r"""
function rowsModel(rows) {
  rows = rows || [];
  if (!rows.length) return { header: [], body: [] };
  var header = (rows[0] || []).map(function(x) { return String(x == null ? "" : x); });
  var body = rows.slice(1).map(function(row, idx) {
    var obj = {};
    header.forEach(function(col, ci) { obj[norm(col)] = row[ci]; });
    return { index: idx, row: row || [], obj: obj, label: rowLabel(header, row || []) };
  });
  return { header: header, body: body };
}

function rowLabel(header, row) {
  var preferred = ["site", "l1", "l2", "l3", "price_range", "shop_id", "year_month", "item_name"];
  var parts = [];
  preferred.forEach(function(col) {
    var idx = header.map(norm).indexOf(col);
    if (idx >= 0 && !isBlank(row[idx])) parts.push(formatValue(row[idx], col));
  });
  return parts.slice(0, 3).join(" / ") || "Row";
}

function colIndex(model, col) { return model.header.map(norm).indexOf(norm(col)); }
function hasCol(model, col) { return colIndex(model, col) >= 0; }

function firstCol(model, names) {
  for (var i = 0; i < names.length; i++) {
    if (hasCol(model, names[i])) return names[i];
  }
  return null;
}

function val(item, col) { return item && item.obj ? item.obj[norm(col)] : null; }
function num(item, col) { return parseNum(val(item, col)); }

function ev(model, item, col) {
  var idx = colIndex(model, col);
  return {
    rowIndex: item ? item.index : null,
    colIndex: idx,
    col: col,
    rowLabel: item ? item.label : "",
    value: item ? val(item, col) : ""
  };
}

function evidenceText(evidence) {
  if (!evidence || evidence.rowIndex == null) return "";
  return prettyCol(evidence.col) + " = " + formatValue(evidence.value, evidence.col);
}
"""

    # ═══════════════════════════════════════════════════════════════
    # 5. Aggregation helpers
    # ═══════════════════════════════════════════════════════════════

    def js_aggregation(self) -> str:
        """maxBy, minBy, maxAbsBy."""
        return r"""
function maxBy(items, col, predicate) {
  var best = null;
  items.forEach(function(item) {
    var n = num(item, col);
    if (n == null) return;
    if (predicate && !predicate(n, item)) return;
    if (!best || n > best.value) best = { item: item, value: n, col: col };
  });
  return best;
}

function minBy(items, col, predicate) {
  var best = null;
  items.forEach(function(item) {
    var n = num(item, col);
    if (n == null) return;
    if (predicate && !predicate(n, item)) return;
    if (!best || n < best.value) best = { item: item, value: n, col: col };
  });
  return best;
}

function maxAbsBy(items, col, predicate) {
  var best = null;
  items.forEach(function(item) {
    var n = num(item, col);
    if (n == null) return;
    if (predicate && !predicate(n, item)) return;
    if (!best || Math.abs(n) > Math.abs(best.value)) best = { item: item, value: n, col: col };
  });
  return best;
}
"""

    # ═══════════════════════════════════════════════════════════════
    # 6. Section config
    # ═══════════════════════════════════════════════════════════════

    def js_section_config(self) -> str:
        """getSectionConfigs, rowsForSection, getTextTemplates."""
        return r"""
function getSectionConfigs(tabs) {
  var configs = {};
  var rows = tabs.sec_config || [];
  if (!rows.length) return configs;
  var header = rows[0].map(norm);
  var idIdx = header.indexOf("section_id");
  if (idIdx < 0) return configs;
  rows.slice(1).forEach(function(row) {
    var id = row[idIdx];
    if (!id) return;
    var item = {};
    header.forEach(function(col, idx) { item[col] = row[idx]; });
    configs[id] = item;
  });
  return configs;
}

function rowsForSection(tabs, id) {
  // Only return the main tab — never fall back to _meta tabs.
  // Meta tabs contain JSON strings that would leak raw data into source tables.
  // Section functions read meta tabs directly via window.AUTODECK_LOCAL_DATA.tabs.
  return (tabs[id] && tabs[id].length) ? tabs[id] : [];
}

var TEXT_TEMPLATES = {};

function getTextTemplates(tabs) {
  var rows = tabs.sec_text || [];
  if (!rows.length) return;
  var header = rows[0].map(norm);
  var idIdx = header.indexOf("section_id");
  var tplIdx = header.indexOf("text_template");
  if (idIdx < 0 || tplIdx < 0) return;
  rows.slice(1).forEach(function(row) {
    TEXT_TEMPLATES[row[idIdx]] = row[tplIdx] || "";
  });
}
"""

    # ═══════════════════════════════════════════════════════════════
    # 7. Important rows filter
    # ═══════════════════════════════════════════════════════════════

    def js_important_rows(self) -> str:
        """importantScore, importantRows, numericColumns, categoricalColumns."""
        return r"""
function numericColumns(model) {
  return model.header.map(function(col, idx) {
    var count = 0;
    model.body.forEach(function(item) {
      if (parseNum(item.row[idx]) != null) count += 1;
    });
    return { col: col, idx: idx, count: count };
  }).filter(function(item) { return item.count > 0; });
}

function categoricalColumns(model) {
  var preferred = ["site", "l1", "l2", "l3", "price_range", "signal", "status"];
  var cols = [];
  preferred.forEach(function(name) {
    var idx = colIndex(model, name);
    if (idx >= 0) cols.push({ col: model.header[idx], idx: idx });
  });
  if (!cols.length && model.header.length) cols.push({ col: model.header[0], idx: 0 });
  return cols;
}

function importantScore(model, item) {
  var score = 0;
  ["adg_mtd", "total_adg", "seller_adg", "ads_adg", "total_subsidy", "total", "adg", "mtd_adg"].forEach(function(col) {
    var n = num(item, col);
    if (n != null && n > 0) score += Math.log10(Math.abs(n) + 1) * 8;
  });
  ["adg_share", "ado_share", "share_in_site", "seller_share", "ads_share", "subsidy_share", "contribution_pct"].forEach(function(col) {
    var n = num(item, col);
    if (n != null && n > 0) score += n * 0.15;
  });
  ["adg_mom", "seller_adg_mom"].forEach(function(col) {
    var n = num(item, col);
    if (n != null) score += Math.abs(n) * 0.3;
  });
  return score;
}

function importantRows(model, limit) {
  if (!model.body.length) return model;
  var scored = model.body.map(function(item) {
    return { item: item, score: importantScore(model, item) };
  });
  scored.sort(function(a, b) { return b.score - a.score; });
  var selected = scored.slice(0, limit || 25).map(function(s) { return s.item; });
  if (selected.length > 0 && selected.length < model.body.length * 0.15) {
    selected = scored.slice(0, Math.max(limit || 25, Math.ceil(model.body.length * 0.25))).map(function(s) { return s.item; });
  }
  return { header: model.header, body: selected };
}

function primaryScaleCol(model) {
  return firstCol(model, ["adg_mtd", "total_adg", "seller_adg", "adg", "mtd_adg"]);
}

function primaryMoveCol(model) {
  return firstCol(model, ["adg_mom", "seller_adg_mom", "ado_mom"]);
}

function primaryShareCol(model) {
  return firstCol(model, ["adg_share", "ado_share", "share_in_site", "seller_share"]);
}
"""

    # ═══════════════════════════════════════════════════════════════
    # 8. Table builders
    # ═══════════════════════════════════════════════════════════════

    def js_table_builders(self) -> str:
        """filterableTableHtml, tableHtml."""
        return r"""
function filterableTableHtml(model, maxRows, isOpen) {
  if (!model || !model.header.length) return "";
  var display = importantRows(model, maxRows || 18);
  var headers = display.header;
  var body = display.body;
  if (!body.length) return '<div class="muted" style="padding:8px">No rows to display.</div>';
  var scaleCol = primaryScaleCol(model);
  var moveCol = primaryMoveCol(model);

  // Build filter dropdown — exclude JSON cells
  var catCols = categoricalColumns(model);
  var filterHtml = "";
  catCols.forEach(function(cat) {
    var values = {};
    body.forEach(function(item) {
      var v = sanitizeCell(item.row[cat.idx], cat.col);
      if (v && String(v).charAt(0) !== "{" && String(v).charAt(0) !== "[") values[v] = (values[v] || 0) + 1;
    });
    var keys = Object.keys(values).sort();
    if (keys.length > 1 && keys.length <= 30) {
      filterHtml += '<select data-row-filter="' + esc(model.id || "") + '" style="margin:4px 4px 4px 0;font-size:11px;padding:4px 6px;border:1px solid var(--line);border-radius:4px">';
      filterHtml += '<option value="">All ' + esc(prettyCol(cat.col)) + '</option>';
      keys.forEach(function(k) { filterHtml += '<option value="' + esc(k) + '">' + esc(k) + ' (' + values[k] + ')</option>'; });
      filterHtml += '</select>';
    }
  });

  var detailsOpen = isOpen ? " open" : "";
  var html = filterHtml;
  html += '<details class="source-data"' + detailsOpen + '><summary>Source data (' + body.length + ' of ' + model.body.length + ' rows)</summary>';
  html += '<div style="overflow-x:auto;max-height:360px"><table class="report-table">';
  // Header
  html += '<thead><tr>';
  headers.forEach(function(col) {
    html += '<th>' + esc(prettyCol(col)) + '</th>';
  });
  html += '</tr></thead><tbody>';
  // Body — filter out JSON rows
  body.forEach(function(item, ri) {
    var rowText = item.row.map(function(cell, ci) { return sanitizeCell(cell, headers[ci]); });
    var hasJson = rowText.some(function(v) { return (String(v).charAt(0) === "{" || String(v).charAt(0) === "[") && String(v).length > 40; });
    if (hasJson) return;
    html += '<tr data-row-index="' + ri + '" data-important-section="' + esc(model.id || "") + '"';
    var catVal = catCols.length > 0 ? sanitizeCell(item.row[catCols[0].idx], catCols[0].col) : "";
    if (catVal) html += ' data-filter-value="' + esc(catVal) + '"';
    html += '>';
    headers.forEach(function(col, ci) {
      var tone = valueTone(item.row[ci], col);
      html += '<td data-col-index="' + ci + '" class="' + tone + '">' + sanitizeCell(item.row[ci], col) + '</td>';
    });
    html += '</tr>';
  });
  html += '</tbody></table></div></details>';
  return html;
}

function tableHtml(id, table) {
  if (!table || !table.header || !table.header.length) return "";
  var html = '<details class="source-data"><summary>Source table (' + (table.body||[]).length + ' rows)</summary>';
  html += '<div style="overflow-x:auto;max-height:360px"><table class="report-table"><thead><tr>';
  table.header.forEach(function(col) { html += '<th>' + esc(prettyCol(col)) + '</th>'; });
  html += '</tr></thead><tbody>';
  (table.body || []).forEach(function(row, ri) {
    html += '<tr data-row-index="' + ri + '">';
    (table.header || []).forEach(function(col, ci) {
      html += '<td data-col-index="' + ci + '">' + sanitizeCell(row[ci], col) + '</td>';
    });
    html += '</tr>';
  });
  html += '</tbody></table></div></details>';
  return html;
}
"""

    # ═══════════════════════════════════════════════════════════════
    # 9. Chart helpers
    # ═══════════════════════════════════════════════════════════════

    def js_chart_helpers(self) -> str:
        """ECharts init, site color palette, SVG helpers, chart interactions."""
        return r"""
var SITE_COLORS = """ + json.dumps(self.SITE_COLORS, indent=2) + r""";
var FALLBACK_COLORS = """ + json.dumps(self.FALLBACK_COLORS, indent=2) + r""";

function siteColor(site) {
  if (SITE_COLORS[site]) return SITE_COLORS[site];
  var hash = 0;
  for (var i = 0; i < site.length; i++) { hash = ((hash << 5) - hash) + site.charCodeAt(i); }
  return FALLBACK_COLORS[Math.abs(hash) % FALLBACK_COLORS.length];
}

function chartContainerHtml(chartId, height) {
  return '<div id="' + esc(chartId) + '" style="width:100%;height:' + (height || 300) + 'px" role="img"></div>';
}

function noDataHtml(message) {
  return '<div class="muted" style="padding:16px;text-align:center">' + esc(message || "No chartable rows available") + '</div>';
}

function metaChartHtml(metaRows) {
  if (!metaRows || !metaRows.length) return "";
  var model = rowsModel(metaRows);
  var html = '<div style="display:flex;flex-wrap:wrap;gap:8px;padding:8px 0">';
  model.body.forEach(function(item) {
    var key = String(item.row[0] == null ? "" : item.row[0]);
    var rawVal = String(item.row[1] == null ? "" : item.row[1]);
    html += '<div class="metric-card" style="flex:1 1 180px;min-width:160px">';
    html += '<div class="label">' + esc(prettyCol(key)) + '</div>';
    html += '<div class="value" style="font-size:14px">' + safeDisplay(rawVal, "—") + '</div>';
    html += '</div>';
  });
  html += '</div>';
  return html;
}

function initECharts(domId) {
  var dom = document.getElementById(domId);
  if (!dom) return null;
  if (dom.clientWidth === 0 || dom.clientHeight === 0) return null;
  var chart = echarts.init(dom);
  return chart;
}

function emptyStateChart(model) {
  var metaRows = rowsForSection(window.AUTODECK_LOCAL_DATA ? window.AUTODECK_LOCAL_DATA.tabs : {}, model.id + "_meta");
  if (metaRows.length > 1) return metaChartHtml(metaRows);
  return noDataHtml("Reference — no anomalies this month");
}

// Shared tooltip for ECharts
function makeTooltip() {
  return {
    trigger: "item",
    backgroundColor: "rgba(32,33,36,.94)",
    borderColor: "transparent",
    textStyle: { color: "#fff", fontSize: 12, fontFamily: "Inter, Noto Sans SC, sans-serif" },
    extraCssText: "border-radius:6px;padding:8px 12px;box-shadow:0 4px 16px rgba(0,0,0,.18)"
  };
}

// Click interaction: pause tooltip
function attachChartInteractions() {
  document.querySelectorAll(".chart-container").forEach(function(container) {
    if (container.dataset.bound) return;
    container.dataset.bound = "1";
    container.addEventListener("click", function(e) {
      var target = e.target.closest("[data-chart-id]");
      if (!target) return;
      var chartDom = document.getElementById(target.getAttribute("data-chart-id"));
      if (!chartDom) return;
      // Toggle pinned state
      if (chartDom.classList.contains("chart-pinned")) {
        chartDom.classList.remove("chart-pinned");
      } else {
        document.querySelectorAll(".chart-pinned").forEach(function(el) { el.classList.remove("chart-pinned"); });
        chartDom.classList.add("chart-pinned");
      }
    });
  });
}
"""

    # ═══════════════════════════════════════════════════════════════
    # 10. Section insight builder
    # ═══════════════════════════════════════════════════════════════

    def js_section_insight(self) -> str:
        """buildSectionInsight — builds model object for each section."""
        return r"""
function buildSectionInsight(id, title, rows, config) {
  var model = rowsModel(rows);
  model.id = id;
  model.title = title;
  model.rowCount = model.body.length;
  model.chartType = (config && config.chart_type) || null;

  // Detect key metric columns
  model.scaleCol = primaryScaleCol(model);
  model.moveCol = primaryMoveCol(model);
  model.shareCol = primaryShareCol(model);

  // Build table for source data reference
  model.table = { header: model.header, body: model.body.map(function(item) { return item.row; }) };

  // Build evidence mapping
  model.metrics = [];
  var cols = numericColumns(model);
  cols.sort(function(a, b) { return b.count - a.count; });
  cols.slice(0, 8).forEach(function(c) {
    var best = maxAbsBy(model.body, c.col);
    if (best) {
      model.metrics.push({
        col: c.col,
        best: best.value,
        bestLabel: best.item.label,
        evidence: ev(model, best.item, c.col)
      });
    }
  });

  // Detect anomalies
  model.anomalies = [];
  var moveCol = model.moveCol;
  var scaleCol = model.scaleCol;
  if (moveCol && scaleCol) {
    model.body.forEach(function(item) {
      var mom = num(item, moveCol);
      var scale = num(item, scaleCol);
      if (mom != null && scale != null && Math.abs(mom) > 10 && scale > 0) {
        model.anomalies.push({ item: item, mom: mom, scale: scale });
      }
    });
    model.anomalies.sort(function(a, b) { return Math.abs(b.mom) - Math.abs(a.mom); });
  }

  return model;
}
"""

    # ═══════════════════════════════════════════════════════════════
    # 11. Gate decisions
    # ═══════════════════════════════════════════════════════════════

    def js_gate_decisions(self) -> str:
        """deriveGateDecisions, gateGridHtml."""
        return r"""
function deriveGateDecisions(models) {
  var gates = {
    site_anomaly: { triggered: false, reason: "", sites: [] },
    category_dynamics: { triggered: false, reason: "", l1s: [] },
    subsidy_health: { triggered: false, reason: "", pct: 0 },
    market_position: { triggered: false, reason: "", gap: 0 }
  };

  models.forEach(function(model) {
    if (model.id === "sec_site_benchmark") {
      model.body.forEach(function(item) {
        var gap = num(item, "gap_pp");
        var share = num(item, "adg_share");
        if (gap != null && share != null && Math.abs(gap) > 5 && share > 10) {
          gates.site_anomaly.sites.push(item.label);
        }
      });
      if (gates.site_anomaly.sites.length) {
        gates.site_anomaly.triggered = true;
        gates.site_anomaly.reason = gates.site_anomaly.sites.length + " site(s) with |gap|>5pp & share>10%";
      }
    }
    if (model.id === "sec_l1_overview") {
      model.body.forEach(function(item) {
        var mom = num(item, "adg_mom");
        if (mom != null && Math.abs(mom) > 10) gates.category_dynamics.l1s.push(item.label);
      });
      if (gates.category_dynamics.l1s.length) {
        gates.category_dynamics.triggered = true;
        gates.category_dynamics.reason = gates.category_dynamics.l1s.length + " L1(s) with |MoM|>10%";
      }
    }
    if (model.id === "sec_subsidy") {
      model.body.forEach(function(item) {
        var sub = num(item, "subsidy_share");
        if (sub != null && sub > 40) {
          gates.subsidy_health.triggered = true;
          gates.subsidy_health.pct = sub;
          gates.subsidy_health.reason = "Subsidy/ADG = " + formatCompact(sub) + "% (>40%)";
        }
      });
    }
  });

  return gates;
}

function gateGridHtml(gates) {
  var items = [
    { key: "site_anomaly", label: "Site Anomaly" },
    { key: "category_dynamics", label: "Category Dynamics" },
    { key: "subsidy_health", label: "Subsidy Health" },
    { key: "market_position", label: "Market Position" }
  ];
  var html = "";
  items.forEach(function(g) {
    var gate = gates[g.key];
    var triggered = gate && gate.triggered;
    html += '<div class="gate-chip' + (triggered ? " triggered" : "") + '" style="display:inline-flex;align-items:center;gap:6px;border:1px solid var(--line);border-radius:20px;padding:4px 12px;margin:4px;font-size:11px;' + (triggered ? 'background:var(--warn-bg);border-color:var(--warn)' : '') + '">';
    html += '<span style="font-weight:700">' + esc(g.label) + '</span>';
    html += '<span>' + (triggered ? "⚠️ " + esc(gate.reason || "Triggered") : "✓ Reference") + '</span>';
    html += '</div>';
  });
  return html;
}
"""

    # ═══════════════════════════════════════════════════════════════
    # 12. Navigation & Summary
    # ═══════════════════════════════════════════════════════════════

    def js_nav_summary(self) -> str:
        """renderNav, renderSummary."""
        return r"""
function renderNav(models) {
  var side = document.getElementById("section-nav-list");
  if (!side) return;
  var html = "";
  models.forEach(function(model, idx) {
    html += '<button class="nav-item" data-target-section="' + esc(model.id) + '">';
    html += '<span>' + (idx + 1) + '</span><span>' + esc(model.title) + '</span>';
    html += '</button>';
  });
  side.innerHTML = html;

  // Scroll spy
  var observer = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (!entry.isIntersecting) return;
      var id = entry.target.id.replace("section-", "");
      document.querySelectorAll(".nav-item").forEach(function(btn) {
        btn.classList.toggle("active", btn.getAttribute("data-target-section") === id);
      });
    });
  }, { rootMargin: "-60px 0px -60% 0px" });
  document.querySelectorAll(".sec").forEach(function(sec) { observer.observe(sec); });
}

function renderSummary(models, tabs) {
  var siteModel = models.find(function(m) { return m.id === "sec_site_benchmark"; });
  var l1Model = models.find(function(m) { return m.id === "sec_l1_overview"; });
  var subModel = models.find(function(m) { return m.id === "sec_subsidy"; });

  var totalAdg = 0;
  if (siteModel) siteModel.body.forEach(function(r) { totalAdg += (num(r, "adg_mtd") || 0); });

  var topSite = maxBy(siteModel ? siteModel.body : [], "adg_mtd", function(n) { return n > 0; });
  var topL1 = maxBy(l1Model ? l1Model.body : [], "adg_mtd", function(n) { return n > 0; });
  var topSub = maxBy(subModel ? subModel.body : [], "subsidy_share", function(n) { return n > 0; });

  var card = function(label, value, context, tone) {
    return '<div class="summary-card' + (tone ? ' ' + tone : '') + '"><div class="label">' + esc(label) + '</div><div class="value">' + esc(value) + '</div><div class="context">' + esc(context || "") + '</div></div>';
  };

  var html = card("Total ADG", formatCompact(totalAdg), "Monthly total across all sites");
  html += card("Top Site", topSite ? (topSite.item.label + " " + formatCompact(topSite.value)) : "—",
    topSite ? formatCompact(num(topSite.item, "adg_share") || 0) + "% of total" : "");
  html += card("Top L1", topL1 ? topL1.item.label : "—",
    topL1 ? formatCompact(num(topL1.item, "adg_mom") || 0) + "% MoM" : "");
  html += card("Subsidy Load", topSub ? formatCompact(topSub.value) + "%" : "—",
    topSub && topSub.value > 40 ? "Above health threshold" : "Within healthy range");

  document.getElementById("summary-grid").innerHTML = html;

  // Hero counts
  var rowCount = 0;
  models.forEach(function(m) { rowCount += m.rowCount; });
  document.getElementById("hero-rows").textContent = rowCount;
  document.getElementById("hero-sections").textContent = models.length;
}
"""

    # ═══════════════════════════════════════════════════════════════
    # 13. Analysis helpers
    # ═══════════════════════════════════════════════════════════════

    def js_analysis_helpers(self) -> str:
        """analysisHtml, metricHtml, visualHtml dispatcher."""
        return r"""
function metricHtml(model) {
  if (!model.metrics || !model.metrics.length) return "";
  var html = "";
  model.metrics.slice(0, 6).forEach(function(m) {
    html += '<span class="evidence-btn" data-evidence-section="' + esc(model.id) + '" data-evidence-row="' + (m.evidence.rowIndex||0) + '" data-evidence-col="' + (m.evidence.colIndex||0) + '" title="Scroll to source data">';
    html += esc(prettyCol(m.col)) + ': <strong>' + formatCompact(m.best) + '</strong>';
    html += '</span>';
  });
  return html;
}

function validNumber(n) {
  return n != null && isFinite(n);
}

function signedPct(n) {
  if (!validNumber(n)) return "—";
  return (n > 0 ? "+" : "") + formatCompact(n) + "%";
}

function signedPp(n) {
  if (!validNumber(n)) return "—";
  return (n > 0 ? "+" : "") + formatCompact(n) + "pp";
}

function toneWord(n, upWord, downWord, flatWord) {
  if (!validNumber(n) || Math.abs(n) < 0.5) return flatWord || "持平";
  return n > 0 ? (upWord || "上升") : (downWord || "下降");
}

function rowName(item) {
  return item && item.label ? item.label : "该行";
}

function evidenceChip(model, item, col, label) {
  if (!model || !item || !col || colIndex(model, col) < 0) return "";
  var e = ev(model, item, col);
  return '<span class="evidence-btn" data-evidence-section="' + esc(model.id) +
    '" data-evidence-row="' + (e.rowIndex == null ? 0 : e.rowIndex) +
    '" data-evidence-col="' + (e.colIndex == null ? 0 : e.colIndex) +
    '" title="Scroll to source data">' + esc(label || evidenceText(e)) + '</span>';
}

function analysisLine(text, evidenceHtml) {
  return '<li>' + esc(text) + (evidenceHtml ? ' <span class="evidence-strip" style="display:inline-flex;padding:0;margin-left:6px">' + evidenceHtml + '</span>' : '') + '</li>';
}

function analysisBlock(model, lines) {
  lines = (lines || []).filter(Boolean);
  if (!lines.length) lines = [analysisLine("本节暂无足够数据形成明确诊断，建议先确认该Section的数据抽取是否完整。", "")];
  return '<div class="analysis" data-analysis-mode="computed"><div class="analysis-label">Computed Analysis</div><ul class="analysis-list" style="margin:4px 0 0 18px;padding:0;line-height:1.75">' + lines.join("") + '</ul></div>';
}

function topBy(model, col, opts) {
  opts = opts || {};
  var rows = (model && model.body ? model.body : []).filter(function(item) {
    var n = num(item, col);
    if (!validNumber(n)) return false;
    if (opts.positive && n <= 0) return false;
    if (opts.negative && n >= 0) return false;
    if (opts.nonzero && n === 0) return false;
    return true;
  });
  rows.sort(function(a, b) {
    var av = num(a, col), bv = num(b, col);
    if (opts.abs) return Math.abs(bv) - Math.abs(av);
    if (opts.asc) return av - bv;
    return bv - av;
  });
  return rows[0] || null;
}

function topNBy(model, col, n, opts) {
  opts = opts || {};
  var rows = (model && model.body ? model.body : []).filter(function(item) {
    var v = num(item, col);
    if (!validNumber(v)) return false;
    if (opts.positive && v <= 0) return false;
    if (opts.negative && v >= 0) return false;
    if (opts.nonzero && v === 0) return false;
    return true;
  });
  rows.sort(function(a, b) {
    var av = num(a, col), bv = num(b, col);
    if (opts.abs) return Math.abs(bv) - Math.abs(av);
    if (opts.asc) return av - bv;
    return bv - av;
  });
  return rows.slice(0, n || 3);
}

function sumCol(model, col) {
  var total = 0;
  (model && model.body ? model.body : []).forEach(function(item) {
    var n = num(item, col);
    if (validNumber(n)) total += n;
  });
  return total;
}

function weightedAvg(model, valueCol, weightCol) {
  var nume = 0, deno = 0;
  (model && model.body ? model.body : []).forEach(function(item) {
    var v = num(item, valueCol);
    var w = weightCol ? num(item, weightCol) : 1;
    if (!validNumber(v) || !validNumber(w) || w <= 0) return;
    nume += v * w;
    deno += w;
  });
  return deno ? nume / deno : null;
}

function metaDict(sectionId) {
  var tabs = (window.AUTODECK_LOCAL_DATA && window.AUTODECK_LOCAL_DATA.tabs) || {};
  var rows = tabs[sectionId + "_meta"] || [];
  var out = {};
  rows.forEach(function(row) {
    if (row && row.length >= 2) out[String(row[0])] = row[1];
  });
  return out;
}

function parseLooseJson(raw, fallback) {
  if (raw == null || raw === "") return fallback;
  try {
    return JSON.parse(String(raw)
      .replace(/\bnan\b/g, "null")
      .replace(/\bNaN\b/g, "null")
      .replace(/\bNone\b/g, "null")
      .replace(/\bTrue\b/g, "true")
      .replace(/\bFalse\b/g, "false"));
  } catch(e) {
    return fallback;
  }
}

function getModelById(id) {
  var tabs = (window.AUTODECK_LOCAL_DATA && window.AUTODECK_LOCAL_DATA.tabs) || {};
  var order = (window.AUTODECK_LANG === "zh" && window.AUTODECK_SECTION_ORDER_ZH)
    ? window.AUTODECK_SECTION_ORDER_ZH
    : window.AUTODECK_SECTION_ORDER;
  var title = id;
  order.forEach(function(pair) { if (pair[0] === id) title = pair[1]; });
  return buildSectionInsight(id, title, rowsForSection(tabs, id), {});
}

function cleanPhrase(text) {
  return String(text == null ? "" : text)
    .replace(/\bnanpp\b/gi, "数据缺失")
    .replace(/待填充|待分析|Pending further analysis|Pending/g, "")
    .trim();
}

function siteFromPath(path) {
  return String(path || "").split("/")[0] || "";
}

function sectionHistoryAnalysis(model) {
  var byMonth = {};
  model.body.forEach(function(item) {
    var key = monthSortKey(val(item, "year_month"));
    if (!byMonth[key]) byMonth[key] = { key: key, label: excelSerialToDateLabel(val(item, "year_month")), total: null, rows: [] };
    byMonth[key].rows.push(item);
    var total = num(item, "total_adg");
    if (validNumber(total)) byMonth[key].total = total;
  });
  var months = Object.keys(byMonth).sort(function(a, b) { return Number(a) - Number(b); }).map(function(k) {
    var m = byMonth[k];
    if (!validNumber(m.total)) {
      m.total = 0;
      m.rows.forEach(function(item) { m.total += num(item, "adg") || 0; });
    }
    return m;
  }).filter(function(m) { return validNumber(m.total); });
  if (!months.length) return [];
  var first = months[0], last = months[months.length - 1];
  var prev = months.length > 1 ? months[months.length - 2] : null;
  var peak = months.slice().sort(function(a, b) { return b.total - a.total; })[0];
  var low = months.slice().filter(function(m) { return m.total > 0; }).sort(function(a, b) { return a.total - b.total; })[0] || months[0];
  var latestTop = last.rows.slice().sort(function(a, b) { return (num(b, "adg") || 0) - (num(a, "adg") || 0); })[0];
  var mom = prev && prev.total ? (last.total - prev.total) / prev.total * 100 : null;
  var lines = [];
  lines.push(analysisLine(
    "最新月总ADG为 " + formatCompact(last.total) + (validNumber(mom) ? "，较上一可比月" + signedPct(mom) : "") + "；12个月峰值出现在 " + peak.label + "（" + formatCompact(peak.total) + "），低点为 " + low.label + "（" + formatCompact(low.total) + "）。",
    latestTop ? evidenceChip(model, latestTop, "total_adg", "最新月总ADG " + formatCompact(last.total)) : ""
  ));
  if (latestTop) {
    var latestTopName = val(latestTop, "site") || rowName(latestTop);
    var topShare = num(latestTop, "adg_share");
    lines.push(analysisLine(
      "最新月Top站点为 " + latestTopName + "，贡献ADG " + formatCompact(num(latestTop, "adg") || 0) + (validNumber(topShare) ? "，占比 " + formatCompact(topShare) + "%" : "") + (validNumber(topShare) && topShare > 60 ? "，存在单站点集中风险。" : "，结构仍需结合站点波动继续判断。"),
      evidenceChip(model, latestTop, "adg_share", "Top站点占比 " + formatValue(val(latestTop, "adg_share"), "adg_share"))
    ));
  }
  return lines;
}

function sectionBenchmarkAnalysis(model) {
  var rows = model.body.filter(function(item) { return (num(item, "adg_mtd") || 0) > 0 || validNumber(num(item, "seller_adg_mom")); });
  var scale = rows.slice().sort(function(a, b) { return (num(b, "adg_mtd") || 0) - (num(a, "adg_mtd") || 0); })[0];
  var gap = topBy(model, "adg_gap_pp", { abs: true });
  var lag = topBy(model, "adg_gap_pp", { asc: true });
  var same = 0, comparable = 0;
  rows.forEach(function(item) {
    var seller = num(item, "seller_adg_mom");
    var mkt = num(item, "mkt_adg_mom");
    if (!validNumber(seller) || !validNumber(mkt)) return;
    comparable += 1;
    if ((seller >= 0 && mkt >= 0) || (seller < 0 && mkt < 0)) same += 1;
  });
  var lines = [];
  if (scale) {
    lines.push(analysisLine(
      rowName(scale) + "是当前最大站点，ADG " + formatCompact(num(scale, "adg_mtd") || 0) + "，占GGP " + formatValue(val(scale, "adg_share"), "adg_share") + "；其卖家MoM为 " + signedPct(num(scale, "seller_adg_mom")) + "，大盘MoM为 " + signedPct(num(scale, "mkt_adg_mom")) + "。",
      evidenceChip(model, scale, "adg_mtd", "站点ADG " + formatValue(val(scale, "adg_mtd"), "adg_mtd"))
    ));
  }
  if (gap) {
    lines.push(analysisLine(
      "最大相对偏离来自 " + rowName(gap) + "，卖家与大盘ADG MoM差距为 " + signedPp(num(gap, "adg_gap_pp")) + "；" + (Math.abs(num(gap, "adg_gap_pp")) > 5 ? "已超过5pp阈值，需要进入品类和运营维度拆解。" : "暂未超过5pp阈值。"),
      evidenceChip(model, gap, "adg_gap_pp", "ADG gap " + signedPp(num(gap, "adg_gap_pp")))
    ));
  }
  if (lag && num(lag, "adg_gap_pp") < -5) {
    lines.push(analysisLine(
      rowName(lag) + "显著跑输大盘（" + signedPp(num(lag, "adg_gap_pp")) + "），优先检查该站点的listing、流量和履约是否出现卖家自身问题。",
      evidenceChip(model, lag, "adg_gap_pp", "跑输 " + signedPp(num(lag, "adg_gap_pp")))
    ));
  }
  if (comparable) {
    lines.push(analysisLine(
      "可对标站点中，卖家与大盘同向率为 " + formatCompact(same / comparable * 100) + "%；同向率越低，越说明本月不是单纯大盘行情，而是卖家自身结构或运营动作在驱动。",
      ""
    ));
  }
  return lines;
}

function sectionL1Analysis(model) {
  var top = topBy(model, "adg_mtd", { positive: true });
  var movers = topNBy(model, "adg_mom", 5, { abs: true });
  var gap = topBy(model, "adg_gap_pp", { abs: true });
  var top3Share = topNBy(model, "adg_share", 3, { positive: true }).reduce(function(s, item) { return s + (num(item, "adg_share") || 0); }, 0);
  var volatileCount = movers.filter(function(item) { return Math.abs(num(item, "adg_mom") || 0) > 10; }).length;
  var lines = [];
  if (top) {
    lines.push(analysisLine(
      "Top L1为 " + rowName(top) + "，贡献ADG " + formatCompact(num(top, "adg_mtd") || 0) + "，占比 " + formatValue(val(top, "adg_share"), "adg_share") + "；Top3 L1合计占比约 " + formatCompact(top3Share) + "%，这是品类集中度的主判断口径。",
      evidenceChip(model, top, "adg_share", "Top L1占比 " + formatValue(val(top, "adg_share"), "adg_share"))
    ));
  }
  if (movers.length) {
    var m = movers[0];
    lines.push(analysisLine(
      "按|MoM|排序，最强异动品类是 " + rowName(m) + "（" + signedPct(num(m, "adg_mom")) + "）；本节共有 " + volatileCount + " 个L1超过10%异动阈值，需要向站点×L1矩阵继续拆解。",
      evidenceChip(model, m, "adg_mom", "L1 MoM " + signedPct(num(m, "adg_mom")))
    ));
  }
  if (gap) {
    var g = num(gap, "adg_gap_pp");
    lines.push(analysisLine(
      rowName(gap) + "相对大盘差距最大（" + signedPp(g) + "）；" + (g > 0 ? "卖家正在该品类中抢份额，需确认是否由补贴/广告拉动。" : "卖家在该品类竞争力弱于大盘，需下钻到L2/L3和listing。"),
      evidenceChip(model, gap, "adg_gap_pp", "大盘差距 " + signedPp(g))
    ));
  }
  return lines;
}

function sectionMatrixAnalysis(model) {
  var gap = topBy(model, "gap_pp", { abs: true });
  var share = topBy(model, "share_in_site", { positive: true });
  var flagged = model.body.filter(function(item) {
    return Math.abs(num(item, "gap_pp") || 0) > 5 && (num(item, "share_in_site") || 0) > 5;
  });
  var bySite = {}, byL1 = {};
  flagged.forEach(function(item) {
    var site = String(val(item, "site") || "");
    var l1 = String(val(item, "l1") || "");
    bySite[site] = (bySite[site] || 0) + 1;
    byL1[l1] = (byL1[l1] || 0) + 1;
  });
  function topKey(obj) {
    return Object.keys(obj).sort(function(a, b) { return obj[b] - obj[a]; })[0] || "";
  }
  var lines = [];
  if (gap) {
    lines.push(analysisLine(
      "站点×L1最大偏离为 " + rowName(gap) + "，gap " + signedPp(num(gap, "gap_pp")) + "；这是优先下钻到L2的候选单元。",
      evidenceChip(model, gap, "gap_pp", "最大gap " + signedPp(num(gap, "gap_pp")))
    ));
  }
  if (flagged.length) {
    var site = topKey(bySite), l1 = topKey(byL1);
    lines.push(analysisLine(
      "共有 " + flagged.length + " 个site×L1同时满足|gap|>5pp且站内占比>5%；其中最集中的站点是 " + site + "，最集中的L1是 " + l1 + "，用于判断是站点级问题还是品类级问题。",
      ""
    ));
  }
  if (share) {
    lines.push(analysisLine(
      rowName(share) + "是站内权重最高的格子（share " + formatValue(val(share, "share_in_site"), "share_in_site") + "），其变化会显著影响站点整体表现。",
      evidenceChip(model, share, "share_in_site", "站内占比 " + formatValue(val(share, "share_in_site"), "share_in_site"))
    ));
  }
  return lines;
}

function sectionL2Analysis(model) {
  var delta = topBy(model, "adg_delta", { abs: true });
  var gap = topBy(model, "gap_pp", { abs: true });
  var share = topBy(model, "share_in_l1", { positive: true });
  var lines = [];
  if (delta) {
    lines.push(analysisLine(
      rowName(delta) + "是L2层级最大的ADG变化来源，贡献变化 " + (num(delta, "adg_delta") > 0 ? "+" : "") + formatCompact(num(delta, "adg_delta") || 0) + "；它解释了上层L1变化的主要方向。",
      evidenceChip(model, delta, "adg_delta", "ADG变化 " + formatValue(val(delta, "adg_delta"), "adg_delta"))
    ));
  }
  if (share) {
    lines.push(analysisLine(
      rowName(share) + "在所属L1内占比最高（" + formatValue(val(share, "share_in_l1"), "share_in_l1") + "），若该L2同时异动，应优先进入L3定位具体子类目。",
      evidenceChip(model, share, "share_in_l1", "L1内占比 " + formatValue(val(share, "share_in_l1"), "share_in_l1"))
    ));
  }
  if (gap) {
    lines.push(analysisLine(
      rowName(gap) + "相对大盘gap为 " + signedPp(num(gap, "gap_pp")) + "；超过5pp且有足够share时，按设计应触发L3粒度诊断。",
      evidenceChip(model, gap, "gap_pp", "L2 gap " + signedPp(num(gap, "gap_pp")))
    ));
  }
  return lines;
}

function sectionL3Analysis(model) {
  var scale = topBy(model, "adg_mtd", { positive: true });
  var mom = topBy(model, "adg_mom", { abs: true });
  var p50Rows = model.body.filter(function(item) { return validNumber(num(item, "adg_mom")) && validNumber(num(item, "p50_growth")); });
  var percentile = p50Rows.slice().sort(function(a, b) {
    return Math.abs((num(b, "adg_mom") || 0) - (num(b, "p50_growth") || 0)) - Math.abs((num(a, "adg_mom") || 0) - (num(a, "p50_growth") || 0));
  })[0];
  var lines = [];
  if (scale) {
    lines.push(analysisLine(
      "当前有量的L3为 " + rowName(scale) + "，ADG " + formatCompact(num(scale, "adg_mtd") || 0) + "；L3层用于把上层异常落到可行动的子类目。",
      evidenceChip(model, scale, "adg_mtd", "L3 ADG " + formatValue(val(scale, "adg_mtd"), "adg_mtd"))
    ));
  }
  if (mom) {
    lines.push(analysisLine(
      rowName(mom) + "的L3 MoM为 " + signedPct(num(mom, "adg_mom")) + "；若该变化集中在少数item，应继续用Listing榜验证单品风险。",
      evidenceChip(model, mom, "adg_mom", "L3 MoM " + signedPct(num(mom, "adg_mom")))
    ));
  }
  if (percentile) {
    var seller = num(percentile, "adg_mom"), p50 = num(percentile, "p50_growth");
    lines.push(analysisLine(
      rowName(percentile) + "卖家增速" + signedPct(seller) + "，大盘P50为" + signedPct(p50) + "；" + (seller >= p50 ? "说明相对同类卖家不弱。" : "说明正在低于中位数，需要干预。"),
      evidenceChip(model, percentile, "p50_growth", "P50 " + signedPct(p50))
    ));
  }
  return lines;
}

function sectionVolatilityAnalysis(model) {
  var md = metaDict("sec_volatility");
  var counts = parseLooseJson(md.signal_counts, {});
  var signals = parseLooseJson(md.signals, []);
  var total = Object.keys(counts).reduce(function(s, k) { return s + (counts[k] || 0); }, 0);
  signals.sort(function(a, b) { return Math.abs(b.mom || 0) - Math.abs(a.mom || 0); });
  var bySite = {};
  signals.forEach(function(s) {
    var site = siteFromPath(s.path);
    if (site) bySite[site] = (bySite[site] || 0) + 1;
  });
  var topSite = Object.keys(bySite).sort(function(a, b) { return bySite[b] - bySite[a]; })[0];
  var lines = [];
  lines.push(analysisLine("本月共检出 " + total + " 个波动信号，其中暴跌 " + (counts.VOLATILE_DOWN || 0) + " 个、市场背离 " + (counts.MARKET_DIVERGENT || 0) + " 个、份额迁移 " + (counts.SHARE_SHIFT || 0) + " 个；优先级按暴跌且有量 > 市场背离 > 份额迁移处理。", ""));
  if (signals.length) {
    var s0 = signals[0];
    lines.push(analysisLine("最强波动路径为 " + (s0.path || "—") + "，信号类型 " + (s0.signal || "—") + "，MoM " + signedPct(s0.mom) + "，gap " + signedPp(s0.gap_pp) + "。", ""));
  }
  if (topSite) {
    lines.push(analysisLine("信号最集中站点为 " + topSite + "（" + bySite[topSite] + "个信号）；如果信号集中在单站点，应优先排查站点级流量、履约或平台政策。", ""));
  }
  return lines;
}

function sectionShopAnalysis(model) {
  var up = topBy(model, "adg_delta", { positive: true });
  var down = topBy(model, "adg_delta", { negative: true });
  var share = topBy(model, "share_in_l3", { positive: true });
  var lines = [];
  if (up) {
    lines.push(analysisLine(
      "增长贡献最大的店铺是 " + rowName(up) + "，ADG变化 +" + formatCompact(num(up, "adg_delta") || 0) + "，贡献度 " + formatValue(val(up, "contribution_pct"), "contribution_pct") + "。",
      evidenceChip(model, up, "adg_delta", "店铺增量 " + formatValue(val(up, "adg_delta"), "adg_delta"))
    ));
  }
  if (down) {
    lines.push(analysisLine(
      "下滑贡献最大的店铺是 " + rowName(down) + "，ADG变化 " + formatCompact(num(down, "adg_delta") || 0) + "；若该店铺为主力店，需要检查断货、账号限制或改价。",
      evidenceChip(model, down, "adg_delta", "店铺下滑 " + formatValue(val(down, "adg_delta"), "adg_delta"))
    ));
  }
  if (share) {
    var s = num(share, "share_in_l3");
    lines.push(analysisLine(
      "Top店铺在L3内share为 " + formatCompact(s) + "%；" + (s > 40 ? "超过40%单店依赖阈值，店铺表现会直接决定该L3表现。" : "暂未超过单店依赖阈值。"),
      evidenceChip(model, share, "share_in_l3", "店铺share " + formatValue(val(share, "share_in_l3"), "share_in_l3"))
    ));
  }
  return lines;
}

function sectionListingAnalysis(model) {
  var md = metaDict("sec_listing_change");
  var perSite = parseLooseJson(md.per_site, {});
  var items = [];
  Object.keys(perSite || {}).forEach(function(site) {
    ((perSite[site] || {}).items || []).forEach(function(item) {
      item._site = site;
      items.push(item);
    });
  });
  items.sort(function(a, b) { return (b.mtd_adg || 0) - (a.mtd_adg || 0); });
  var top = items[0];
  var newCount = items.filter(function(i) { return Number(i.is_new || 0) === 1; }).length;
  var byBand = {};
  items.forEach(function(i) { var b = i.price_range || "Unknown"; byBand[b] = (byBand[b] || 0) + (i.mtd_adg || 0); });
  var band = Object.keys(byBand).sort(function(a, b) { return byBand[b] - byBand[a]; })[0];
  var cross = parseLooseJson(md.cross_site_items, {});
  var crossCount = Object.keys(cross || {}).length;
  var lines = [];
  if (top) {
    lines.push(analysisLine("Top listing为 " + (top.item_name || top.item_id || "—").slice(0, 48) + "（" + top._site + "），MTD ADG " + formatCompact(top.mtd_adg || 0) + "，价格带 " + (top.price_range || "—") + "；这是当前单品贡献的第一优先维护对象。", ""));
  }
  lines.push(analysisLine("Top listing池中新品数为 " + newCount + "，跨站点重复item数为 " + crossCount + "；新品高说明上新在贡献增长，跨站重合高说明存在GGP级核心爆品。", ""));
  if (band) {
    lines.push(analysisLine("Top listing ADG最集中价格带为 " + band + "（约 " + formatCompact(byBand[band]) + " ADG），应与价格带竞争定位章节交叉验证是否贴合大盘需求。", ""));
  }
  return lines;
}

function sectionFulfillmentAnalysis(model) {
  var fbs = sumCol(model, "fbs"), tpf = sumCol(model, "tpf"), sls = sumCol(model, "sls"), total = sumCol(model, "total");
  var shares = total > 0 ? { fbs: fbs / total * 100, tpf: tpf / total * 100, sls: sls / total * 100 } : { fbs: 0, tpf: 0, sls: 0 };
  var dom = Object.keys(shares).sort(function(a, b) { return shares[b] - shares[a]; })[0];
  var shiftRows = [];
  ["fbs_shift_pp","tpf_shift_pp","sls_shift_pp"].forEach(function(c) {
    model.body.forEach(function(item) {
      var v = num(item, c);
      if (validNumber(v)) shiftRows.push({ item: item, col: c, value: v });
    });
  });
  shiftRows.sort(function(a, b) { return Math.abs(b.value) - Math.abs(a.value); });
  var shift = shiftRows[0];
  var domLabel = dom === "fbs" ? "FBS" : (dom === "tpf" ? "TPF" : "SLS");
  var lines = [];
  lines.push(analysisLine("整体履约以 " + domLabel + " 为主，占ADO约 " + formatCompact(shares[dom]) + "%；" + (dom === "fbs" && shares[dom] > 60 ? "FBS依赖高，需重点确认CB仓库存。" : dom === "tpf" && shares[dom] > 40 ? "TPF依赖较高，需关注配送速度和服务质量。" : "履约结构需要结合站点迁移判断。"), ""));
  if (shift) {
    lines.push(analysisLine(rowName(shift.item) + "发生最大履约迁移，" + prettyCol(shift.col) + " " + signedPp(shift.value) + "；若对应站点/品类ADG下滑，履约迁移可能是根因候选。", evidenceChip(model, shift.item, shift.col, "履约迁移 " + signedPp(shift.value))));
  }
  return lines;
}

function sectionTrafficAnalysis(model) {
  var total = sumCol(model, "total");
  var ch = [
    { key: "organic", label: "Organic" },
    { key: "ads", label: "Ads" },
    { key: "live", label: "Live" },
    { key: "campaign", label: "Campaign" }
  ];
  ch.forEach(function(c) { c.value = sumCol(model, c.key); c.share = total > 0 ? c.value / total * 100 : 0; });
  ch.sort(function(a, b) { return b.share - a.share; });
  var worstRows = [];
  ["organic_mom","ads_mom","live_mom","campaign_mom"].forEach(function(c) {
    model.body.forEach(function(item) {
      var v = num(item, c);
      if (validNumber(v)) worstRows.push({ item: item, col: c, value: v });
    });
  });
  worstRows.sort(function(a, b) { return a.value - b.value; });
  var worst = worstRows[0];
  var roas = weightedAvg(model, "roas", "ads");
  var lines = [];
  lines.push(analysisLine("渠道结构以 " + ch[0].label + " 为主，占ADG约 " + formatCompact(ch[0].share) + "%；Ads占比约 " + formatCompact((ch.find(function(x){return x.key==='ads';}) || {}).share || 0) + "%，用于判断是否付费流量依赖。", ""));
  if (worst) {
    lines.push(analysisLine(rowName(worst.item) + "的" + prettyCol(worst.col) + "下降最明显（" + signedPct(worst.value) + "）；若总ADG同步下滑，则优先检查该渠道动作是否减少。", evidenceChip(model, worst.item, worst.col, prettyCol(worst.col) + " " + signedPct(worst.value))));
  }
  if (validNumber(roas)) {
    lines.push(analysisLine("按广告ADG加权的ROAS约为 " + formatCompact(roas) + "；若广告占比高且ROAS走弱，应先优化投放效率再扩量。", ""));
  }
  return lines;
}

function sectionSubsidyAnalysis(model) {
  var totalSub = sumCol(model, "total_subsidy");
  var totalAdg = sumCol(model, "total_adg");
  var load = totalAdg > 0 ? totalSub / totalAdg * 100 : null;
  var sellerFund = sumCol(model, "seller_item") + sumCol(model, "seller_shipping");
  var platformFund = sumCol(model, "platform_item") + sumCol(model, "platform_shipping");
  var high = topBy(model, "subsidy_share", { positive: true });
  var sellerShare = sellerFund + platformFund > 0 ? sellerFund / (sellerFund + platformFund) * 100 : null;
  var lines = [];
  if (validNumber(load)) {
    lines.push(analysisLine("整体补贴负荷为 " + formatCompact(load) + "%（total subsidy / ADG）；" + (load > 40 ? "超过40%高度依赖阈值，增长质量需要谨慎看待。" : load >= 20 ? "处于20-40%中等依赖区间，需监控趋势。" : "低于20%，补贴依赖相对健康。"), ""));
  }
  if (high) {
    lines.push(analysisLine(rowName(high) + "补贴占比最高，达到 " + formatValue(val(high, "subsidy_share"), "subsidy_share") + "；若该站点增长较快，需要判断是否由补贴购买增长。", evidenceChip(model, high, "subsidy_share", "补贴占比 " + formatValue(val(high, "subsidy_share"), "subsidy_share"))));
  }
  if (validNumber(sellerShare)) {
    lines.push(analysisLine("卖家出资占卖家+平台补贴约 " + formatCompact(sellerShare) + "%；卖家出资占比越高，利润率压力越需要纳入拜访讨论。", ""));
  }
  return lines;
}

function sectionPriceAnalysis(model) {
  var bias = topBy(model, "bias_pp", { abs: true });
  var shift = topBy(model, "share_shift_pp", { abs: true });
  var share = topBy(model, "seller_share", { positive: true });
  var lines = [];
  if (bias) {
    lines.push(analysisLine(rowName(bias) + "价格带偏差最大，" + (val(bias, "price_range") || "该价格带") + " bias " + signedPp(num(bias, "bias_pp")) + "；正偏差代表卖家过度集中，负偏差代表覆盖不足。", evidenceChip(model, bias, "bias_pp", "价格偏差 " + signedPp(num(bias, "bias_pp")))));
  }
  if (shift) {
    lines.push(analysisLine(rowName(shift) + "发生最大价格带迁移，share shift " + signedPp(num(shift, "share_shift_pp")) + "；迁移方向可判断消费者降级/升级或卖家商品组合变化。", evidenceChip(model, shift, "share_shift_pp", "份额迁移 " + signedPp(num(shift, "share_shift_pp")))));
  }
  if (share) {
    lines.push(analysisLine("卖家份额最高的价格带是 " + rowName(share) + "，seller share " + formatValue(val(share, "seller_share"), "seller_share") + "；若该带大盘份额较低，就是结构性错位候选。", evidenceChip(model, share, "seller_share", "卖家价格带share " + formatValue(val(share, "seller_share"), "seller_share"))));
  }
  return lines;
}

function sectionAmsAnalysis(model) {
  var roasHigh = topBy(model, "roas", { positive: true });
  var roasLow = topBy(model, "roas", { positive: true, asc: true });
  var adsShare = topBy(model, "ads_share", { positive: true });
  var spendDown = topBy(model, "spend_mom", { negative: true });
  var avgRoas = weightedAvg(model, "roas", "ads_adg");
  var lines = [];
  if (validNumber(avgRoas)) {
    lines.push(analysisLine("按广告ADG加权ROAS约为 " + formatCompact(avgRoas) + "；ROAS>5可考虑扩量，2-5需监控边际收益，<2优先优化素材/定向。", ""));
  }
  if (roasHigh) {
    lines.push(analysisLine(rowName(roasHigh) + "广告效率最高，ROAS " + formatValue(val(roasHigh, "roas"), "roas") + "，是加投候选。", evidenceChip(model, roasHigh, "roas", "ROAS " + formatValue(val(roasHigh, "roas"), "roas"))));
  }
  if (adsShare) {
    lines.push(analysisLine(rowName(adsShare) + "广告GMV占比最高（" + formatValue(val(adsShare, "ads_share"), "ads_share") + "）；若>50%，预算波动会直接影响GMV。", evidenceChip(model, adsShare, "ads_share", "Ads share " + formatValue(val(adsShare, "ads_share"), "ads_share"))));
  }
  if (spendDown) {
    lines.push(analysisLine(rowName(spendDown) + "广告支出MoM下降 " + signedPct(num(spendDown, "spend_mom")) + "；若同站点ADG下降，可能是广告削减导致。", evidenceChip(model, spendDown, "spend_mom", "Spend MoM " + signedPct(num(spendDown, "spend_mom")))));
  }
  return lines;
}

function sectionRootCauseAnalysis(model) {
  var bm = getModelById("sec_site_benchmark");
  var sub = getModelById("sec_subsidy");
  var fulfill = getModelById("sec_fulfillment");
  var md = metaDict("sec_volatility");
  var signals = parseLooseJson(md.signals, []);
  var bySite = {};
  signals.forEach(function(s) {
    var site = siteFromPath(s.path);
    if (site) bySite[site] = (bySite[site] || 0) + 1;
  });
  var siteRows = bm.body.slice().sort(function(a, b) {
    return Math.abs(num(b, "adg_gap_pp") || 0) - Math.abs(num(a, "adg_gap_pp") || 0);
  });
  var lead = siteRows[0];
  var negative = siteRows.filter(function(item) { return (num(item, "adg_gap_pp") || 0) < -5; })[0];
  var highSub = topBy(sub, "subsidy_share", { positive: true });
  var shiftRows = [];
  ["fbs_shift_pp","tpf_shift_pp","sls_shift_pp"].forEach(function(c) {
    fulfill.body.forEach(function(item) {
      var v = num(item, c);
      if (validNumber(v)) shiftRows.push({ item: item, col: c, value: v });
    });
  });
  shiftRows.sort(function(a, b) { return Math.abs(b.value) - Math.abs(a.value); });
  var shift = shiftRows[0];
  var lines = [];
  if (lead) {
    lines.push(analysisLine("站点根因诊断先按benchmark gap排序：首要站点为 " + rowName(lead) + "，ADG gap " + signedPp(num(lead, "adg_gap_pp")) + "，ADG share " + formatValue(val(lead, "adg_share"), "adg_share") + "；它决定本月整体诊断主线。", evidenceChip(bm, lead, "adg_gap_pp", "站点gap " + signedPp(num(lead, "adg_gap_pp")))));
  }
  if (negative) {
    lines.push(analysisLine(rowName(negative) + "跑输大盘超过5pp，按决策树应优先排查卖家自身问题：Top item断崖、渠道下滑、履约迁移、价格错位、补贴变化。", evidenceChip(bm, negative, "adg_gap_pp", "跑输 " + signedPp(num(negative, "adg_gap_pp")))));
  }
  var signalSite = Object.keys(bySite).sort(function(a, b) { return bySite[b] - bySite[a]; })[0];
  if (signalSite) {
    lines.push(analysisLine("波动信号最集中在 " + signalSite + "（" + bySite[signalSite] + "个信号），根因假设优先落到该站点的listing/品类组合，而不是泛泛归因为大盘。", ""));
  }
  if (highSub) {
    lines.push(analysisLine(rowName(highSub) + "补贴负荷最高（" + formatValue(val(highSub, "subsidy_share"), "subsidy_share") + "），若同时增长强劲，需要判断增长是否由补贴驱动。", evidenceChip(sub, highSub, "subsidy_share", "补贴负荷 " + formatValue(val(highSub, "subsidy_share"), "subsidy_share"))));
  }
  if (shift) {
    lines.push(analysisLine(rowName(shift.item) + "履约迁移最大（" + prettyCol(shift.col) + " " + signedPp(shift.value) + "），若该站点下滑则优先确认仓配/物流状态。", evidenceChip(fulfill, shift.item, shift.col, "履约迁移 " + signedPp(shift.value))));
  }
  return lines;
}

function genericSectionAnalysis(model) {
  var lines = [];
  if (model.anomalies && model.anomalies.length) {
    var a = model.anomalies[0];
    lines.push(analysisLine("本节检出 " + model.anomalies.length + " 个|MoM|>10%的异常行，最大异动为 " + rowName(a.item) + "（" + signedPct(a.mom) + "）。", evidenceChip(model, a.item, model.moveCol, "最大MoM " + signedPct(a.mom))));
  }
  if (model.scaleCol) {
    var scale = topBy(model, model.scaleCol, { positive: true });
    if (scale) lines.push(analysisLine("当前最大规模行是 " + rowName(scale) + "，" + prettyCol(model.scaleCol) + "为 " + formatValue(val(scale, model.scaleCol), model.scaleCol) + "。", evidenceChip(model, scale, model.scaleCol, prettyCol(model.scaleCol) + " " + formatValue(val(scale, model.scaleCol), model.scaleCol))));
  }
  return lines;
}

function computedAnalysisFindings(model) {
  if (!model) return [];
  if (model.id === "sec_12m_history") return sectionHistoryAnalysis(model);
  if (model.id === "sec_site_benchmark") return sectionBenchmarkAnalysis(model);
  if (model.id === "sec_l1_overview") return sectionL1Analysis(model);
  if (model.id === "sec_l1_matrix") return sectionMatrixAnalysis(model);
  if (model.id === "sec_l2_drill") return sectionL2Analysis(model);
  if (model.id === "sec_l3_granular") return sectionL3Analysis(model);
  if (model.id === "sec_volatility") return sectionVolatilityAnalysis(model);
  if (model.id === "sec_shop_impact") return sectionShopAnalysis(model);
  if (model.id === "sec_listing_change") return sectionListingAnalysis(model);
  if (model.id === "sec_fulfillment") return sectionFulfillmentAnalysis(model);
  if (model.id === "sec_traffic_channel") return sectionTrafficAnalysis(model);
  if (model.id === "sec_subsidy") return sectionSubsidyAnalysis(model);
  if (model.id === "sec_price_band") return sectionPriceAnalysis(model);
  if (model.id === "sec_ams") return sectionAmsAnalysis(model);
  if (model.id === "sec_root_cause") return sectionRootCauseAnalysis(model);
  return genericSectionAnalysis(model);
}

function analysisHtml(model) {
  return analysisBlock(model, computedAnalysisFindings(model));
}

// visualHtml dispatcher — calls per-section chart functions
function visualHtml(model) {
  // Sections with _meta tabs may have data despite empty main tab
  var hasMetaTab = (window.AUTODECK_LOCAL_DATA && window.AUTODECK_LOCAL_DATA.tabs && window.AUTODECK_LOCAL_DATA.tabs[model.id + "_meta"]);
  if (!model.rowCount && model.chartType !== "meta" && !hasMetaTab) return emptyStateChart(model);

  var id = model.id;
  // These functions are provided by individual section modules
  if (id === "sec_12m_history" && typeof historyStackedChart === "function") return historyStackedChart(model);
  if (id === "sec_site_benchmark" && typeof siteBenchmarkChart === "function") return siteBenchmarkChart(model);
  if (id === "sec_l1_overview" && typeof l1OverviewChart === "function") return l1OverviewChart(model);
  if (id === "sec_l1_matrix" && typeof l1MatrixChart === "function") return l1MatrixChart(model);
  if (id === "sec_l2_drill" && typeof l2DrillChart === "function") return l2DrillChart(model);
  if (id === "sec_l3_granular" && typeof l3GranularChart === "function") return l3GranularChart(model);
  if (id === "sec_volatility" && typeof volatilityChart === "function") return volatilityChart(model);
  if (id === "sec_shop_impact" && typeof shopImpactChart === "function") return shopImpactChart(model);
  if (id === "sec_listing_change" && typeof listingChangeChart === "function") return listingChangeChart(model);
  if (id === "sec_fulfillment" && typeof fulfillmentChart === "function") return fulfillmentChart(model);
  if (id === "sec_traffic_channel" && typeof trafficChannelChart === "function") return trafficChannelChart(model);
  if (id === "sec_subsidy" && typeof subsidyChart === "function") return subsidyChart(model);
  if (id === "sec_price_band" && typeof priceBandChart === "function") return priceBandChart(model);
  if (id === "sec_ams" && typeof amsChart === "function") return amsChart(model);
  if (id === "sec_root_cause" && typeof rootCauseChart === "function") return rootCauseChart(model);

  // Fallback for sections without custom chart
  if (model.metrics && model.metrics.length) return metaChartHtml([[null].concat(model.metrics.map(function(m) { return m.col + ": " + formatCompact(m.best); }))]);
  return noDataHtml("Chart module not loaded — " + id);
}
"""

    # ═══════════════════════════════════════════════════════════════
    # 14. Main render function
    # ═══════════════════════════════════════════════════════════════

    def js_render_report(self) -> str:
        """The main renderReport function that orchestrates all sections."""
        return r"""
function renderReport(payload) {
  var root = document.getElementById("report-root");
  payload = payload || window.AUTODECK_LOCAL_DATA || {};
  var tabs = payload.tabs || {};
  var configs = getSectionConfigs(tabs);
  getTextTemplates(tabs);
  var order = (window.AUTODECK_LANG === "zh" && window.AUTODECK_SECTION_ORDER_ZH)
    ? window.AUTODECK_SECTION_ORDER_ZH
    : window.AUTODECK_SECTION_ORDER;
  var models = order.map(function(pair) {
    return buildSectionInsight(pair[0], pair[1], rowsForSection(tabs, pair[0]), configs[pair[0]] || {});
  });
  var gates = deriveGateDecisions(models);
  renderNav(models);
  renderSummary(models, tabs);
  var gateEl = document.getElementById("gate-grid");
  if (gateEl) gateEl.innerHTML = gateGridHtml(gates);
  var html = "";
  models.forEach(function(model, idx) {
    html += '<section id="section-' + esc(model.id) + '" class="sec ' + (idx < 2 ? "open" : "") + '" data-section-title="' + esc(model.title.toLowerCase()) + '">';
    html += '<button class="sec-head" data-toggle-section="' + esc(model.id) + '" aria-expanded="' + (idx < 2 ? "true" : "false") + '">';
    html += '<span class="sec-title"><strong>' + (idx + 1) + '. ' + esc(model.title) + '</strong><span>' + esc(model.rowCount) + ' source rows</span></span>';
    html += '<span class="status-chip">' + esc(model.chartType || (model.rowCount ? 'Ready' : 'No data')) + '</span>';
    html += '<span class="chev" aria-hidden="true">›</span></button>';
    html += '<div class="sec-body">';
    html += visualHtml(model);
    html += filterableTableHtml(model, 18, false);
    html += '<div class="evidence-strip">' + metricHtml(model) + '</div>';
    html += analysisHtml(model);
    html += tableHtml(model.id, model.table);
    html += '</div></section>';
  });
  root.innerHTML = html || '<div class="empty">No AutoDeck section tabs found.</div>';
  var link = document.getElementById("sheet-link");
  if (payload.sheetUrl) link.innerHTML = '<a class="link-button" href="' + esc(payload.sheetUrl) + '" target="_blank">Open Sheet</a>';
  bindInteractions();
}

function bindInteractions() {
  // Section toggle
  document.querySelectorAll("[data-toggle-section]").forEach(function(button) {
    if (button.dataset.bound) return;
    button.dataset.bound = "1";
    button.addEventListener("click", function() {
      var sec = document.getElementById("section-" + button.getAttribute("data-toggle-section"));
      if (sec) {
        sec.classList.toggle("open");
        button.setAttribute("aria-expanded", sec.classList.contains("open") ? "true" : "false");
      }
    });
  });
  // Nav click → scroll to section
  document.querySelectorAll("[data-target-section]").forEach(function(button) {
    if (button.dataset.bound) return;
    button.dataset.bound = "1";
    button.addEventListener("click", function() {
      var id = button.getAttribute("data-target-section");
      var sec = document.getElementById("section-" + id);
      if (!sec) return;
      sec.classList.add("open");
      sec.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
  // Evidence chip click → scroll to source table row
  document.querySelectorAll(".evidence-btn").forEach(function(button) {
    if (button.dataset.bound) return;
    button.dataset.bound = "1";
    button.addEventListener("click", function(event) {
      event.stopPropagation();
      focusEvidence(
        button.getAttribute("data-evidence-section"),
        button.getAttribute("data-evidence-row"),
        button.getAttribute("data-evidence-col")
      );
    });
  });
  // Section search
  var search = document.getElementById("section-search");
  if (search && !search.dataset.bound) {
    search.dataset.bound = "1";
    search.addEventListener("input", function() {
      var q = norm(search.value);
      document.querySelectorAll(".sec").forEach(function(sec) {
        var text = norm(sec.textContent || "");
        sec.classList.toggle("filtered", q && text.indexOf(q) < 0);
      });
    });
  }
  // Chart interactions (deferred for ECharts)
  setTimeout(function() {
    if (typeof attachChartInteractions === "function") attachChartInteractions();
  }, 300);
}

function focusEvidence(sectionId, rowIndex, colIndex) {
  var sec = document.getElementById("section-" + sectionId);
  if (!sec) return;
  sec.classList.add("open");
  var details = sec.querySelector("details.source-data");
  if (details) details.open = true;
  sec.scrollIntoView({ behavior: "smooth", block: "start" });
  setTimeout(function() {
    document.querySelectorAll(".row-hit").forEach(function(el) { el.classList.remove("row-hit"); });
    document.querySelectorAll(".cell-hit").forEach(function(el) { el.classList.remove("cell-hit"); });
    var row = sec.querySelector('tr[data-row-index="' + rowIndex + '"]');
    var cell = row ? row.querySelector('td[data-col-index="' + colIndex + '"]') : null;
    if (row) row.classList.add("row-hit");
    if (cell) { cell.classList.add("cell-hit"); cell.scrollIntoView({ behavior: "smooth", block: "center" }); }
  }, 180);
}
"""

    # ═══════════════════════════════════════════════════════════════
    # 15. Column labels definition
    # ═══════════════════════════════════════════════════════════════

    def js_col_labels(self) -> str:
        """Column label definitions in both zh and en."""
        zh_json = json.dumps(self.COL_LABELS_ZH, indent=2, ensure_ascii=False)
        return f"var COL_LABELS = {zh_json};"

    # ═══════════════════════════════════════════════════════════════
    # Assembly
    # ═══════════════════════════════════════════════════════════════

    def all_shared_js(self) -> str:
        """Return ALL shared JavaScript as a single string."""
        blocks = [
            self.js_col_labels(),
            self.js_core_utilities(),
            self.js_month_utils(),
            self.js_formatting(),
            self.js_data_model(),
            self.js_aggregation(),
            self.js_section_config(),
            self.js_important_rows(),
            self.js_table_builders(),
            self.js_chart_helpers(),
            self.js_section_insight(),
            self.js_gate_decisions(),
            self.js_nav_summary(),
            self.js_analysis_helpers(),
            self.js_render_report(),
        ]
        return "\n".join(blocks)
