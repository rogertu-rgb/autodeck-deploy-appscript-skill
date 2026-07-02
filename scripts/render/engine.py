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
        "scope": "范围", "rank_type": "排名类型", "rank": "排名", "top_site": "主要站点",
        "shop_id": "店铺ID", "shop_name": "店铺名", "item_id": "商品ID", "item_name": "商品名",
        "price_range": "价格带", "price_band": "价格带",
        "adg": "ADG", "adg_mtd": "当月ADG", "adg_m1": "上月ADG",
        "mtd_adg": "当月ADG", "m1_adg": "上月ADG",
        "seller_adg": "卖家ADG", "ads_adg": "广告ADG", "total_adg": "总ADG",
        "ado": "ADO", "ado_mtd": "当月ADO", "ado_m1": "上月ADO",
        "adimp_mtd": "当月日均曝光", "adclick_mtd": "当月日均点击",
        "adimp_m1": "上月日均曝光", "adclick_m1": "上月日均点击",
        "adimp_delta": "日均曝光变化", "adclick_delta": "日均点击变化",
        "ctr_mtd": "当月CTR", "cr_mtd": "当月CR",
        "ctr_m1": "上月CTR", "cr_m1": "上月CR",
        "ctr_delta_pp": "CTR变化", "cr_delta_pp": "CR变化",
        "adg_per_order_mtd": "当月单均ADG", "adg_per_order_delta": "单均ADG变化",
        "ads_ado": "广告ADO", "total_ado": "总ADO",
        "adg_mom": "ADG环比", "adimp_mom": "曝光环比", "adclick_mom": "点击环比", "seller_adg_mom": "卖家ADG环比",
        "shopee_adg_mom": "Shopee ADG环比", "shopee_ado_mom": "Shopee ADO环比",
        "mkt_adg_mom": "大盘ADG环比", "ado_mom": "ADO环比",
        "seller_ado_mom": "卖家ADO环比", "mkt_ado_mom": "大盘ADO环比",
        "adg_gap_pp": "ADG差距", "ado_gap_pp": "ADO差距", "gap_pp": "差距(pp)",
        "adg_share": "ADG占比", "ado_share": "ADO占比",
        "source_label": "来源/手段", "source_group": "来源类型",
        "ctr": "CTR", "cr": "CR", "mtd_adpv": "当月ADPV", "mtd_adimp": "当月曝光",
        "fulfillment_ado": "履约ADO", "local_ado": "本地履约ADO", "local_share": "本地履约占比",
        "local_shift_pp": "本地履约变化", "fulfillment_coverage": "履约覆盖率",
        "ads_ado_share": "广告ADO占比", "he1_ads_adg_pct": "HE1 Ads ADG%",
        "ads_spend_gmv": "Ads Spend/GMV", "efficiency_status": "效率判断",
        "share_in_site": "站内占比", "share_in_l3": "L3占比",
        "contribution_pct": "贡献度", "site_delta_contribution_pct": "站点波动贡献", "primary_driver": "主要驱动", "total": "合计",
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
  if (key === "ctr" || key === "cr" || key === "ctr_mtd" || key === "cr_mtd" || key === "ctr_m1" || key === "cr_m1") return formatCompact(n * 100) + "%";
  if (key === "ads_spend_gmv" || key === "fulfillment_coverage") return formatCompact(n) + "%";
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
  var preferred = ["site", "source_label", "l1", "l2", "l3", "price_range", "shop_id", "item_id", "year_month", "item_name"];
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
  if (model.id !== "sec_12m_history") {
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
  }

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

function signedDelta(n) {
  if (!validNumber(n)) return "—";
  return (n > 0 ? "+" : "") + formatCompact(n);
}

function toneWord(n, upWord, downWord, flatWord) {
  if (!validNumber(n) || Math.abs(n) < 0.5) return flatWord || "持平";
  return n > 0 ? (upWord || "上升") : (downWord || "下降");
}

function rowName(item) {
  return item && item.label ? item.label : "该行";
}

function fullCategoryLabel(item, levels, fallback) {
  fallback = fallback || {};
  var site = String(val(item, "site") || fallback.site || "").trim();
  var parts = [];
  (levels || ["l1", "l2", "l3"]).forEach(function(col) {
    var v = String(val(item, col) || fallback[col] || "").trim();
    if (v && v !== "Total") parts.push(v);
  });
  var path = parts.join(" > ");
  if (site && path) return site + " / " + path;
  if (path) return path;
  return rowName(item);
}

function l2CategoryLabel(item, fallback) {
  return fullCategoryLabel(item, ["l1", "l2"], fallback);
}

function l3CategoryLabel(item, fallback) {
  return fullCategoryLabel(item, ["l1", "l2", "l3"], fallback);
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

function analysisCalloutLine(idx, text, evidenceHtml) {
  return '<li class="analysis-callout-line"><span class="analysis-callout-marker">' + esc(idx) + '</span><span class="analysis-callout-text">' + esc(text) + (evidenceHtml ? ' <span class="evidence-strip" style="display:inline-flex;padding:0;margin-left:6px">' + evidenceHtml + '</span>' : '') + '</span></li>';
}

function analysisBlock(model, lines) {
  lines = (lines || []).filter(Boolean);
  if (!lines.length) lines = [analysisLine("本节暂无足够数据形成明确诊断，建议先确认该Section的数据抽取是否完整。", "")];
  return '<div class="analysis" data-analysis-mode="computed"><div class="analysis-label">数据诊断</div><ul class="analysis-list" style="margin:4px 0 0 18px;padding:0;line-height:1.75">' + lines.join("") + '</ul></div>';
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

function activeTabs() {
  return ((window.AUTODECK_ACTIVE_DATA && window.AUTODECK_ACTIVE_DATA.tabs) ||
          (window.AUTODECK_LOCAL_DATA && window.AUTODECK_LOCAL_DATA.tabs) || {});
}

function metaDict(sectionId) {
  var tabs = activeTabs();
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
  var tabs = activeTabs();
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

function sellerDataPresent(item, shareCols) {
  shareCols = shareCols || ["adg_share", "share_in_site", "share_in_l1", "share_in_l2"];
  var adg = num(item, "adg_mtd");
  var prev = num(item, "adg_m1");
  var mom = num(item, "adg_mom");
  var sellerMom = num(item, "seller_adg_mom");
  if (validNumber(adg) && adg > 0) return true;
  if (validNumber(prev) && prev > 0) return true;
  if (validNumber(mom)) return true;
  if (validNumber(sellerMom)) return true;
  for (var i = 0; i < shareCols.length; i++) {
    var s = num(item, shareCols[i]);
    if (validNumber(s) && s > 0) return true;
  }
  return false;
}

function sameRowIdentity(a, b, cols) {
  return cols.every(function(col) { return String(val(a, col) || "") === String(val(b, col) || ""); });
}

function siteFromPath(path) {
  return String(path || "").split("/")[0] || "";
}

function volatilitySignalParts(path) {
  var p = String(path || "").split("/");
  return {
    site: p[0] || "",
    l1: p[1] || "",
    l2: p[2] || "",
    l3: p.slice(3).join("/") || ""
  };
}

function volatilitySignalLabel(signal) {
  if (signal === "VOLATILE_DOWN") return "暴跌";
  if (signal === "VOLATILE_UP") return "暴涨";
  if (signal === "MARKET_DIVERGENT") return "市场背离";
  if (signal === "SHARE_SHIFT") return "份额迁移";
  if (signal === "NEW_ENTRY") return "新进入";
  if (signal === "EXIT") return "消失";
  return signal || "Signal";
}

function volatilityRoute(d) {
  if (!d) return "继续观察";
  if (d.redAlert || d.signal === "VOLATILE_DOWN") return "查 Listing / 履约";
  if (d.signal === "MARKET_DIVERGENT") return "查补贴 / 根因";
  if (d.signal === "VOLATILE_UP" || d.antiGrowth) return "复盘正向动作";
  if (d.signal === "SHARE_SHIFT") return "回到品类下钻";
  if (d.signal === "NEW_ENTRY" || d.signal === "EXIT") return "查店铺/商品变化";
  return "继续观察";
}

function volatilityEnrichedSignals(rawSignals, scatterRaw) {
  rawSignals = Array.isArray(rawSignals) ? rawSignals.slice() : [];
  scatterRaw = Array.isArray(scatterRaw) ? scatterRaw : [];
  if (!rawSignals.length && scatterRaw.length) {
    rawSignals = scatterRaw.map(function(p) {
      var seller = parseNum(p.seller_mom);
      var market = parseNum(p.mkt_mom);
      return {
        path: p.site_l3 || [p.site, p.l1, p.l2, p.l3].filter(Boolean).join("/"),
        signal: "SCATTER",
        mom: seller,
        gap_pp: validNumber(seller) && validNumber(market) ? seller - market : null,
        adg_mtd: parseNum(p.adg_mtd || p.adg || p.mtd_adg)
      };
    });
  }
  var out = rawSignals.map(function(s, idx) {
    var path = String(s.path || s.site_l3 || [s.site, s.l1, s.l2, s.l3].filter(Boolean).join("/"));
    var p = volatilitySignalParts(path);
    var mom = parseNum(s.mom != null ? s.mom : s.seller_mom);
    var gap = parseNum(s.gap_pp);
    var market = parseNum(s.market_mom != null ? s.market_mom : (s.mkt_mom != null ? s.mkt_mom : s.market));
    if (!validNumber(market) && validNumber(mom) && validNumber(gap)) market = mom - gap;
    var adg = parseNum(s.adg_mtd != null ? s.adg_mtd : (s.mtd_adg != null ? s.mtd_adg : s.adg));
    if (!validNumber(adg)) adg = 0;
    var genericPath = /\/Other(s)?$/i.test(path) || /\/Other(s)?\//i.test(path);
    var extremeGap = validNumber(gap) && Math.abs(gap) > 300;
    var lowVolume = adg < 5;
    var lowConfidence = genericPath || extremeGap || lowVolume;
    var redAlert = validNumber(mom) && validNumber(market) && validNumber(gap) && mom < 0 && market > 0 && gap < -15 && adg >= 5;
    var antiGrowth = validNumber(mom) && validNumber(market) && mom > 0 && market < 0;
    var confidence = (genericPath ? .72 : 1) * (extremeGap ? .45 : 1) * (lowVolume ? .55 : 1);
    var scoreBase = validNumber(gap) ? Math.abs(gap) : Math.abs(mom || 0);
    var d = {
      id: "vol-s" + idx,
      path: path,
      signal: s.signal || "SCATTER",
      mom: mom,
      gap_pp: gap,
      market: market,
      adg_mtd: adg,
      genericPath: genericPath,
      extremeGap: extremeGap,
      lowVolume: lowVolume,
      lowConfidence: lowConfidence,
      redAlert: redAlert,
      antiGrowth: antiGrowth,
      confidence: confidence,
      score: scoreBase * Math.log(adg + 2) * confidence,
      site: p.site,
      l1: p.l1,
      l2: p.l2,
      l3: p.l3
    };
    d.route = volatilityRoute(d);
    return d;
  }).filter(function(d) {
    return validNumber(d.mom) || validNumber(d.gap_pp) || d.adg_mtd > 0;
  });
  out.sort(function(a, b) { return b.score - a.score; });
  return out;
}

function volatilityDefaultRows(data) {
  data = Array.isArray(data) ? data : [];
  var rows = data.filter(function(d) { return !d.lowConfidence && !d.lowVolume; });
  if (!rows.length) rows = data.filter(function(d) { return !d.lowConfidence; });
  if (!rows.length) rows = data.slice();
  rows.sort(function(a, b) { return b.score - a.score; });
  return rows;
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
  var shopeeMom = null;
  last.rows.some(function(item) {
    var n = num(item, "shopee_adg_mom");
    if (validNumber(n)) {
      shopeeMom = n;
      return true;
    }
    return false;
  });
  var lines = [];
  var marketGap = validNumber(mom) && validNumber(shopeeMom) ? mom - shopeeMom : null;
  lines.push(analysisLine(
    "最新月总ADG为 " + formatCompact(last.total) + (validNumber(mom) ? "，GGP较上一可比月" + signedPct(mom) : "") + (validNumber(shopeeMom) ? "，同期Shopee大盘MoM为" + signedPct(shopeeMom) : "") + (validNumber(marketGap) ? "，Seller - Shopee gap为" + signedPp(marketGap) + (marketGap >= 0 ? "，本月跑赢大盘" : "，本月跑输大盘") : "") + "；12个月峰值出现在 " + peak.label + "（" + formatCompact(peak.total) + "），低点为 " + low.label + "（" + formatCompact(low.total) + "）。",
    latestTop ? evidenceChip(model, latestTop, validNumber(shopeeMom) ? "shopee_adg_mom" : "total_adg", validNumber(shopeeMom) ? "Shopee MoM " + signedPct(shopeeMom) : "最新月总ADG " + formatCompact(last.total)) : ""
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
  var calloutRows = rows.filter(function(item) {
    return validNumber(num(item, "seller_adg_mom")) && validNumber(num(item, "mkt_adg_mom")) && validNumber(num(item, "adg_gap_pp")) && (num(item, "adg_mtd") || 0) > 0;
  }).sort(function(a, b) {
    var ap = Math.abs(num(a, "adg_gap_pp") || 0) * Math.max(num(a, "adg_share") || 0, 0);
    var bp = Math.abs(num(b, "adg_gap_pp") || 0) * Math.max(num(b, "adg_share") || 0, 0);
    return bp - ap;
  }).slice(0, 3);
  var calloutLabels = calloutRows.map(function(item) { return rowName(item); });
  var same = 0, comparable = 0;
  rows.forEach(function(item) {
    var seller = num(item, "seller_adg_mom");
    var mkt = num(item, "mkt_adg_mom");
    if (!validNumber(seller) || !validNumber(mkt)) return;
    comparable += 1;
    if ((seller >= 0 && mkt >= 0) || (seller < 0 && mkt < 0)) same += 1;
  });
  var lines = [];
  calloutRows.forEach(function(item, idx) {
    var site = rowName(item);
    var seller = num(item, "seller_adg_mom");
    var market = num(item, "mkt_adg_mom");
    var g = num(item, "adg_gap_pp");
    var share = num(item, "adg_share");
    var route = "表现接近大盘，优先作为对照组观察。";
    if (g >= 5) {
      route = "跑赢大盘，建议复盘该站点的商品、流量和履约动作，判断能否复制到同类站点。";
    } else if (g <= -5) {
      route = "跑输大盘，建议优先检查该站点 listing、流量和履约是否存在卖家自身问题。";
    }
    lines.push(analysisCalloutLine(
      idx + 1,
      site + " 是当前第" + (idx + 1) + "优先站点归因信号：卖家ADG MoM " + signedPct(seller) + "，大盘MoM " + signedPct(market) + "，差距 " + signedPp(g) + "，ADG占比 " + formatValue(val(item, "adg_share"), "adg_share") + "；" + route,
      evidenceChip(model, item, "adg_gap_pp", "差距 " + signedPp(g)) + evidenceChip(model, item, "adg_share", "ADG占比 " + formatValue(val(item, "adg_share"), "adg_share"))
    ));
  });
  if (scale && calloutLabels.indexOf(rowName(scale)) < 0) {
    lines.push(analysisLine(
      rowName(scale) + "是当前最大站点，ADG " + formatCompact(num(scale, "adg_mtd") || 0) + "，占GGP " + formatValue(val(scale, "adg_share"), "adg_share") + "；其卖家MoM为 " + signedPct(num(scale, "seller_adg_mom")) + "，大盘MoM为 " + signedPct(num(scale, "mkt_adg_mom")) + "。",
      evidenceChip(model, scale, "adg_mtd", "站点ADG " + formatValue(val(scale, "adg_mtd"), "adg_mtd"))
    ));
  }
  if (!calloutRows.length && gap) {
    lines.push(analysisLine(
      "最大相对偏离来自 " + rowName(gap) + "，卖家与大盘ADG MoM差距为 " + signedPp(num(gap, "adg_gap_pp")) + "；" + (Math.abs(num(gap, "adg_gap_pp")) > 5 ? "已超过5pp阈值，需要进入品类和运营维度拆解。" : "暂未超过5pp阈值。"),
      evidenceChip(model, gap, "adg_gap_pp", "ADG gap " + signedPp(num(gap, "adg_gap_pp")))
    ));
  }
  if (lag && num(lag, "adg_gap_pp") < -5 && calloutLabels.indexOf(rowName(lag)) < 0) {
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
  var matrix = getModelById("sec_l1_matrix");
  var matrixPriorities = (matrix.body || []).filter(function(item) {
    return sellerDataPresent(item, ["share_in_site"]) &&
      validNumber(num(item, "gap_pp")) &&
      ((num(item, "adg_mtd") || 0) > 0 || (num(item, "share_in_site") || 0) > 0);
  }).sort(function(a, b) {
    var ap = Math.abs(num(a, "gap_pp") || 0) * Math.max(num(a, "share_in_site") || 0, 0.5);
    var bp = Math.abs(num(b, "gap_pp") || 0) * Math.max(num(b, "share_in_site") || 0, 0.5);
    return bp - ap;
  }).slice(0, 3);
  matrixPriorities.forEach(function(item, idx) {
    var g = num(item, "gap_pp");
    var route = g <= -5 ? "应优先下钻到L2/L3验证卖家侧问题。" : (g >= 5 ? "可复盘该站点品类打法并判断是否可复制。" : "可作为对照格子观察。");
    lines.push(analysisCalloutLine(
      idx + 1,
      "编号" + (idx + 1) + "对应矩阵中的 " + (val(item, "site") || "—") + " × " + (val(item, "l1") || "—") + "：站内占比 " + formatValue(val(item, "share_in_site"), "share_in_site") + "，ADG " + formatCompact(num(item, "adg_mtd") || 0) + "，卖家MoM " + signedPct(num(item, "adg_mom")) + "，大盘MoM " + signedPct(num(item, "mkt_adg_mom")) + "，gap " + signedPp(g) + "；" + route,
      ""
    ));
  });
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
  var md = metaDict("sec_l2_drill");
  var fallback = { l1: md.l1_filter || md.l1 || "" };
  var rows = model.body.filter(function(item) { return sellerDataPresent(item, ["share_in_l1"]); });
  var calloutRows = rows.filter(function(item) {
    return validNumber(num(item, "gap_pp")) && ((num(item, "adg_mtd") || 0) > 0 || (num(item, "share_in_l1") || 0) > 0);
  }).sort(function(a, b) {
    var ap = Math.abs(num(a, "gap_pp") || 0) * Math.max(num(a, "share_in_l1") || 0, 0.5);
    var bp = Math.abs(num(b, "gap_pp") || 0) * Math.max(num(b, "share_in_l1") || 0, 0.5);
    return bp - ap;
  }).slice(0, 3);
  var delta = rows.slice().sort(function(a, b) { return Math.abs(num(b, "adg_delta") || 0) - Math.abs(num(a, "adg_delta") || 0); })[0];
  var share = rows.slice().sort(function(a, b) { return (num(b, "share_in_l1") || 0) - (num(a, "share_in_l1") || 0); })[0];
  function inCallouts(item) {
    return calloutRows.some(function(c) { return sameRowIdentity(c, item, ["site", "l1", "l2"]); });
  }
  var lines = [];
  calloutRows.forEach(function(item, idx) {
    var g = num(item, "gap_pp");
    var route = g <= -5 ? "这是高优先级跑输归因点，需要继续进L3/listing验证。" : (g >= 5 ? "这是跑赢归因点，可复盘该L2的商品和运营动作。" : "差距接近大盘，可作为对照。");
    lines.push(analysisCalloutLine(
      idx + 1,
      "编号" + (idx + 1) + "对应二级品类图中的 " + l2CategoryLabel(item, fallback) + "：占L1 " + formatValue(val(item, "share_in_l1"), "share_in_l1") + "，ADG " + formatCompact(num(item, "adg_mtd") || 0) + "，卖家MoM " + signedPct(num(item, "adg_mom")) + "，大盘MoM " + signedPct(num(item, "mkt_adg_mom")) + "，gap " + signedPp(g) + "；" + route,
      evidenceChip(model, item, "gap_pp", "gap " + signedPp(g)) + evidenceChip(model, item, "share_in_l1", "占L1 " + formatValue(val(item, "share_in_l1"), "share_in_l1"))
    ));
  });
  if (delta) {
    lines.push(analysisLine(
      l2CategoryLabel(delta, fallback) + "是L2层级最大的ADG变化来源，贡献变化 " + (num(delta, "adg_delta") > 0 ? "+" : "") + formatCompact(num(delta, "adg_delta") || 0) + "；它解释了上层L1变化的主要方向。",
      evidenceChip(model, delta, "adg_delta", "ADG变化 " + formatValue(val(delta, "adg_delta"), "adg_delta"))
    ));
  }
  if (share && !inCallouts(share)) {
    lines.push(analysisLine(
      l2CategoryLabel(share, fallback) + "在所属L1内占比最高（" + formatValue(val(share, "share_in_l1"), "share_in_l1") + "），若该L2同时异动，应优先进入L3定位具体子类目。",
      evidenceChip(model, share, "share_in_l1", "L1内占比 " + formatValue(val(share, "share_in_l1"), "share_in_l1"))
    ));
  }
  return lines;
}

function sectionL3Analysis(model) {
  var md = metaDict("sec_l3_granular");
  var fallback = { l1: md.l1 || "", l2: md.l2 || "" };
  var rows = model.body.filter(function(item) { return sellerDataPresent(item, ["share_in_l2"]); });
  rows.forEach(function(item) {
    var seller = num(item, "adg_mom");
    var p50 = num(item, "p50_growth");
    var gapSignal = validNumber(seller) && validNumber(p50) ? Math.abs(seller - p50) : Math.abs(seller || 0);
    item._calloutScore = gapSignal * Math.max(num(item, "share_in_l2") || 0, 0.5) + Math.log((num(item, "adg_mtd") || 0) + 1) * 2;
  });
  var calloutRows = rows.slice().sort(function(a, b) { return (b._calloutScore || 0) - (a._calloutScore || 0); }).slice(0, 3);
  var scale = rows.slice().sort(function(a, b) { return (num(b, "adg_mtd") || 0) - (num(a, "adg_mtd") || 0); })[0];
  var mom = rows.slice().sort(function(a, b) { return Math.abs(num(b, "adg_mom") || 0) - Math.abs(num(a, "adg_mom") || 0); })[0];
  var p50Rows = rows.filter(function(item) { return validNumber(num(item, "adg_mom")) && validNumber(num(item, "p50_growth")); });
  var percentile = p50Rows.slice().sort(function(a, b) {
    return Math.abs((num(b, "adg_mom") || 0) - (num(b, "p50_growth") || 0)) - Math.abs((num(a, "adg_mom") || 0) - (num(a, "p50_growth") || 0));
  })[0];
  function l3Action(item) {
    var share = num(item, "share_in_l2") || 0;
    var seller = num(item, "adg_mom");
    var p50 = num(item, "p50_growth");
    if (share >= 20 && validNumber(seller) && seller < -10) return "进入listing验证";
    if (validNumber(seller) && validNumber(p50) && seller - p50 < -10 && share >= 10) return "复盘对标差距";
    if (validNumber(seller) && seller > 10) return "正向复制";
    return "继续观察";
  }
  function inCallouts(item) {
    return calloutRows.some(function(c) { return sameRowIdentity(c, item, ["site", "l1", "l2", "l3"]); });
  }
  var lines = [];
  calloutRows.forEach(function(item, idx) {
    var seller = num(item, "adg_mom");
    var p50 = num(item, "p50_growth");
    var gapText = validNumber(seller) && validNumber(p50) ? "，卖家-P50 " + signedPp(seller - p50) : "，当前缺P50，仅作为卖家侧证据";
    lines.push(analysisCalloutLine(
      idx + 1,
      "编号" + (idx + 1) + "对应L3证据表中的 " + l3CategoryLabel(item, fallback) + "：占L2 " + formatValue(val(item, "share_in_l2"), "share_in_l2") + "，ADG " + formatCompact(num(item, "adg_mtd") || 0) + "，卖家MoM " + signedPct(seller) + "，P50 " + signedPct(p50) + gapText + "；建议动作：" + l3Action(item) + "。",
      evidenceChip(model, item, "adg_mom", "卖家MoM " + signedPct(seller)) + evidenceChip(model, item, "share_in_l2", "占L2 " + formatValue(val(item, "share_in_l2"), "share_in_l2"))
    ));
  });
  if (scale && !inCallouts(scale)) {
    lines.push(analysisLine(
      "当前有量的L3为 " + l3CategoryLabel(scale, fallback) + "，ADG " + formatCompact(num(scale, "adg_mtd") || 0) + "；L3层用于把上层异常落到可行动的子类目。",
      evidenceChip(model, scale, "adg_mtd", "L3 ADG " + formatValue(val(scale, "adg_mtd"), "adg_mtd"))
    ));
  }
  if (mom && !inCallouts(mom)) {
    lines.push(analysisLine(
      l3CategoryLabel(mom, fallback) + "的L3 MoM为 " + signedPct(num(mom, "adg_mom")) + "；若该变化集中在少数item，应继续用Listing榜验证单品风险。",
      evidenceChip(model, mom, "adg_mom", "L3 MoM " + signedPct(num(mom, "adg_mom")))
    ));
  }
  if (percentile) {
    var seller = num(percentile, "adg_mom"), p50 = num(percentile, "p50_growth");
    lines.push(analysisLine(
      l3CategoryLabel(percentile, fallback) + "卖家增速" + signedPct(seller) + "，大盘P50为" + signedPct(p50) + "；" + (seller >= p50 ? "说明相对同类卖家不弱。" : "说明正在低于中位数，需要干预。"),
      evidenceChip(model, percentile, "p50_growth", "P50 " + signedPct(p50))
    ));
  }
  return lines;
}

function sectionVolatilityAnalysis(model) {
  var md = metaDict("sec_volatility");
  var counts = parseLooseJson(md.signal_counts, {});
  var signals = volatilityEnrichedSignals(parseLooseJson(md.signals, []), parseLooseJson(md.scatter_data, []));
  var total = Object.keys(counts).reduce(function(s, k) { return s + (Number(counts[k]) || 0); }, 0);
  if (!total) total = signals.length;
  var actionable = volatilityDefaultRows(signals);
  var lowConfidence = signals.filter(function(s) { return s.lowConfidence; }).length;
  var bySite = {};
  actionable.forEach(function(s) {
    if (s.site) bySite[s.site] = (bySite[s.site] || 0) + 1;
  });
  var topSite = Object.keys(bySite).sort(function(a, b) { return bySite[b] - bySite[a]; })[0];
  var lines = [];
  lines.push(analysisLine("本月共检出 " + total + " 个波动信号，其中暴跌 " + (counts.VOLATILE_DOWN || 0) + " 个、市场背离 " + (counts.MARKET_DIVERGENT || 0) + " 个、份额迁移 " + (counts.SHARE_SHIFT || 0) + " 个；已将低体量、极端gap、Other/Others泛路径标为低可信，当前可行动队列保留 " + actionable.length + " 条。", ""));
  actionable.slice(0, 3).forEach(function(s, idx) {
    lines.push(analysisCalloutLine(
      idx + 1,
      "编号" + (idx + 1) + "对应 " + (s.site || "—") + " / " + (s.l2 || s.l1 || "—") + " / " + (s.l3 || "—") + "：" + volatilitySignalLabel(s.signal) + "，卖家MoM " + signedPct(s.mom) + " vs 大盘 " + signedPct(s.market) + "，gap " + signedPp(s.gap_pp) + "，ADG " + formatCompact(s.adg_mtd || 0) + "；建议路由：" + s.route + "。",
      ""
    ));
  });
  if (!actionable.length && signals.length) {
    var hidden = signals[0];
    lines.push(analysisLine("当前信号主要落在低可信池，最高分路径为 " + (hidden.path || "—") + "，但因低体量、极端gap或Other路径需要先做数据/类目确认，再进入卖家动作判断。", ""));
  }
  if (topSite) {
    lines.push(analysisLine("可行动信号最集中站点为 " + topSite + "（" + bySite[topSite] + "个）；若集中在单站点，应优先排查该站点的Listing、履约、流量或平台政策变化。", ""));
  }
  if (lowConfidence) {
    lines.push(analysisLine("另有 " + lowConfidence + " 条低可信信号已默认隐藏，主要用于二次审计，不应直接作为卖家结论。", ""));
  }
  return lines;
}

function sectionShopAnalysis(model) {
  var enriched = (model.body || []).some(function(item) { return String(val(item, "rank_type") || ""); });
  if (enriched) {
    function byType(type) {
      return model.body.filter(function(item) { return String(val(item, "rank_type") || "") === type; })
        .sort(function(a, b) { return (num(a, "rank") || 0) - (num(b, "rank") || 0); });
    }
    function shopLabel(item) {
      var name = String(val(item, "shop_name") || "").trim();
      var id = String(val(item, "shop_id") || "").trim();
      return name ? name + "（" + id + "）" : "店铺" + id;
    }
    function signedShopDelta(n) {
      if (!validNumber(n)) return "—";
      return (n > 0 ? "+" : "") + formatCompact(n);
    }
    var topAdg = byType("top_adg")[0];
    var topAdo = byType("top_ado")[0];
    var keyShops = byType("site_key_shop");
    var gain = keyShops.slice().sort(function(a, b) { return (num(b, "adg_delta") || 0) - (num(a, "adg_delta") || 0); })[0];
    var loss = keyShops.slice().sort(function(a, b) { return (num(a, "adg_delta") || 0) - (num(b, "adg_delta") || 0); })[0];
    var l3Gain = byType("l3_price_gain").sort(function(a, b) { return (num(b, "adg_delta") || 0) - (num(a, "adg_delta") || 0); })[0];
    var l3Loss = byType("l3_price_loss").sort(function(a, b) { return (num(a, "adg_delta") || 0) - (num(b, "adg_delta") || 0); })[0];
    var siteMap = {};
    model.body.forEach(function(item) {
      var site = String(val(item, "site") || "");
      if (site && site !== "All") siteMap[site] = true;
    });
    var lines = [];
    if (topAdg) {
      lines.push(analysisLine(
        "Top ADG店铺是 " + shopLabel(topAdg) + "，当前ADG " + formatCompact(num(topAdg, "adg_mtd") || 0) + "，主要贡献站点为 " + (val(topAdg, "top_site") || val(topAdg, "site") || "—") + "。",
        evidenceChip(model, topAdg, "adg_mtd", "Top ADG " + formatValue(val(topAdg, "adg_mtd"), "adg_mtd"))
      ));
    }
    if (topAdo) {
      lines.push(analysisLine(
        "Top ADO店铺是 " + shopLabel(topAdo) + "，当前ADO " + formatCompact(num(topAdo, "ado_mtd") || 0) + "；用于判断订单量规模是否与GMV贡献一致。",
        evidenceChip(model, topAdo, "ado_mtd", "Top ADO " + formatValue(val(topAdo, "ado_mtd"), "ado_mtd"))
      ));
    }
    if (gain) {
      lines.push(analysisLine(
        "站点key driver中增长最大的是 " + (val(gain, "top_site") || val(gain, "site") || "—") + " 的 " + shopLabel(gain) + "，ADG增量 " + signedShopDelta(num(gain, "adg_delta")) + "；漏斗提示为 " + (val(gain, "primary_driver") || "结构变化") + "，ADIMP变化 " + signedShopDelta(num(gain, "adimp_delta")) + "，点击变化 " + signedShopDelta(num(gain, "adclick_delta")) + "。",
        evidenceChip(model, gain, "adg_delta", "增长 " + formatValue(val(gain, "adg_delta"), "adg_delta"))
      ));
    }
    if (loss) {
      lines.push(analysisLine(
        "站点key driver中流失最大的是 " + (val(loss, "top_site") || val(loss, "site") || "—") + " 的 " + shopLabel(loss) + "，ADG变化 " + signedShopDelta(num(loss, "adg_delta")) + "；漏斗提示为 " + (val(loss, "primary_driver") || "结构变化") + "，需判断是整体流量流失、点击效率下降还是转化率问题。",
        evidenceChip(model, loss, "adg_delta", "流失 " + formatValue(val(loss, "adg_delta"), "adg_delta"))
      ));
    }
    if (l3Gain) {
      lines.push(analysisLine(
        "key shop下钻中，涨幅最大的L3×价格带是 " + (val(l3Gain, "top_site") || val(l3Gain, "site") || "—") + " / " + (val(l3Gain, "l3") || "—") + " / " + (val(l3Gain, "price_range") || "—") + "，ADG增量 " + signedShopDelta(num(l3Gain, "adg_delta")) + "，主要driver为 " + (val(l3Gain, "primary_driver") || "结构变化") + "。",
        evidenceChip(model, l3Gain, "adg_delta", "L3价格带增长 " + formatValue(val(l3Gain, "adg_delta"), "adg_delta"))
      ));
    }
    if (l3Loss) {
      lines.push(analysisLine(
        "key shop下钻中，跌幅最大的L3×价格带是 " + (val(l3Loss, "top_site") || val(l3Loss, "site") || "—") + " / " + (val(l3Loss, "l3") || "—") + " / " + (val(l3Loss, "price_range") || "—") + "，ADG变化 " + signedShopDelta(num(l3Loss, "adg_delta")) + "，主要driver为 " + (val(l3Loss, "primary_driver") || "结构变化") + "。",
        evidenceChip(model, l3Loss, "adg_delta", "L3价格带流失 " + formatValue(val(l3Loss, "adg_delta"), "adg_delta"))
      ));
    }
    lines.push(analysisLine("本节已按 " + Object.keys(siteMap).length + " 个站点先定位key driver shop，再下钻到这些店铺的L3×价格带与traffic funnel，适合直接转成卖家动作排查清单。", ""));
    return lines;
  }
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
  var topRows = model.body.filter(function(item) { return val(item, "rank_type") === "top_adg"; });
  var growthRows = model.body.filter(function(item) { return val(item, "rank_type") === "top_growth"; });
  var lossRows = model.body.filter(function(item) { return val(item, "rank_type") === "top_loss"; });
  var top = topRows.slice().sort(function(a, b) { return (num(b, "mtd_adg") || 0) - (num(a, "mtd_adg") || 0); })[0];
  var gain = growthRows.slice().sort(function(a, b) { return (num(b, "adg_delta") || 0) - (num(a, "adg_delta") || 0); })[0];
  var loss = lossRows.slice().sort(function(a, b) { return (num(a, "adg_delta") || 0) - (num(b, "adg_delta") || 0); })[0];
  var newCount = model.body.filter(function(item) { return Number(val(item, "is_new") || 0) === 1; }).length;
  var lines = [];
  if (top) {
    lines.push(analysisLine("卖得最好的listing是 " + (val(top, "item_name") || val(top, "item_id") || "—").slice(0, 48) + "（" + (val(top, "site") || "—") + "），当月ADG " + formatCompact(num(top, "mtd_adg") || 0) + "，价格带 " + (val(top, "price_range") || "—") + "；建议让卖家复盘该商品的标题、价格带、履约和流量共性。", evidenceChip(model, top, "mtd_adg", "Top ADG " + formatValue(val(top, "mtd_adg"), "mtd_adg"))));
  }
  if (gain) {
    lines.push(analysisLine("增长最多的listing是 " + (val(gain, "item_name") || val(gain, "item_id") || "—").slice(0, 42) + "（" + (val(gain, "site") || "—") + "），ADG变化 " + signedDelta(num(gain, "adg_delta")) + "，当前诊断driver为 " + (val(gain, "primary_driver") || "—") + "。", evidenceChip(model, gain, "adg_delta", "Listing增长 " + formatValue(val(gain, "adg_delta"), "adg_delta"))));
  }
  if (loss) {
    lines.push(analysisLine("跌幅最多的listing是 " + (val(loss, "item_name") || val(loss, "item_id") || "—").slice(0, 42) + "（" + (val(loss, "site") || "—") + "），ADG变化 " + signedDelta(num(loss, "adg_delta")) + "；优先检查是否为订单下降、CTR承接弱或下单转化弱。", evidenceChip(model, loss, "adg_delta", "Listing下滑 " + formatValue(val(loss, "adg_delta"), "adg_delta"))));
  }
  lines.push(analysisLine("当前Top listing池中新品记录数为 " + newCount + "；本节来自 cncbbi_general.autodeck__dws_item_rpt_mi，item funnel 使用 ADIMP→ADPV→ADO，其中 CTR=ADPV/ADIMP，CR=ADO/ADPV。", ""));
  return lines;
}

function sectionFulfillmentAnalysis(model) {
  var topLocal = topBy(model, "local_share", { positive: true });
  var growLocal = topBy(model, "local_shift_pp", { positive: true });
  var lowLocal = topBy(model, "local_share", { positive: true, asc: true });
  var coverageIssue = model.body.filter(function(item) {
    var c = num(item, "fulfillment_coverage");
    return validNumber(c) && (c < 95 || c > 105) && (num(item, "total_ado") || 0) > 1;
  })[0];
  var lines = [];
  if (topLocal) {
    lines.push(analysisLine(rowName(topLocal) + "本地履约化最高，Local占比 " + formatValue(val(topLocal, "local_share"), "local_share") + "；这类站点适合让卖家复盘FBS/TPF库存和时效收益。", evidenceChip(model, topLocal, "local_share", "Local " + formatValue(val(topLocal, "local_share"), "local_share"))));
  }
  if (growLocal) {
    lines.push(analysisLine(rowName(growLocal) + "本地履约占比提升最快，环比 " + signedPp(num(growLocal, "local_shift_pp")) + "；若该站点增长同步改善，可作为推进本地履约的正样本。", evidenceChip(model, growLocal, "local_shift_pp", "Local MoM " + signedPp(num(growLocal, "local_shift_pp")))));
  }
  if (lowLocal) {
    lines.push(analysisLine(rowName(lowLocal) + "本地履约占比最低（" + formatValue(val(lowLocal, "local_share"), "local_share") + "），是优先push FBS/TPF的站点候选。", evidenceChip(model, lowLocal, "local_share", "Local " + formatValue(val(lowLocal, "local_share"), "local_share"))));
  }
  if (coverageIssue) {
    lines.push(analysisLine(rowName(coverageIssue) + "的FBS+TPF+SLS与总ADO覆盖率为 " + formatValue(val(coverageIssue, "fulfillment_coverage"), "fulfillment_coverage") + "，需要先确认履约字段口径。", evidenceChip(model, coverageIssue, "fulfillment_coverage", "覆盖率 " + formatValue(val(coverageIssue, "fulfillment_coverage"), "fulfillment_coverage"))));
  }
  return lines;
}

function sectionTrafficAnalysis(model) {
  var primary = topBy(model, "ado_mtd", { positive: true });
  var growth = topBy(model, "ado_delta", { positive: true });
  var loss = topBy(model, "ado_delta", { negative: true });
  var lines = [];
  if (primary) {
    lines.push(analysisLine("当前最大出单driver是 " + rowName(primary) + "，ADO " + formatCompact(num(primary, "ado_mtd") || 0) + "，占该站点ADO " + formatValue(val(primary, "ado_share"), "ado_share") + "；这是拜访时要先问卖家是否可复制/维持的手段。", evidenceChip(model, primary, "ado_mtd", "ADO " + formatValue(val(primary, "ado_mtd"), "ado_mtd"))));
  }
  if (growth) {
    lines.push(analysisLine("增长最明显的出单手段是 " + rowName(growth) + "，ADO变化 " + signedDelta(num(growth, "ado_delta")) + "；若同站点总ADO增长，应检查该动作是否为主要贡献。", evidenceChip(model, growth, "ado_delta", "ADO增长 " + formatValue(val(growth, "ado_delta"), "ado_delta"))));
  }
  if (loss) {
    lines.push(analysisLine("下滑最明显的出单手段是 " + rowName(loss) + "，ADO变化 " + signedDelta(num(loss, "ado_delta")) + "；若卖家总盘下滑，优先排查该来源是否减少投放/活动/补贴。", evidenceChip(model, loss, "ado_delta", "ADO下滑 " + formatValue(val(loss, "ado_delta"), "ado_delta"))));
  }
  lines.push(analysisLine("本节来源、广告、补贴、CFS、Campaign不是MECE，同一订单可能重复命中；因此占比只用于定位driver，不能相加为100%。", ""));
  return lines;
}

function sectionSubsidyAnalysis(model) {
  var topLever = topBy(model, "ado_mtd", { positive: true }) || topBy(model, "adg_mtd", { positive: true });
  var growth = topBy(model, "ado_delta", { positive: true }) || topBy(model, "adg_delta", { positive: true });
  var highSeller = topBy(model, "seller_funded_share", { positive: true });
  var highLoad = topBy(model, "subsidy_share", { positive: true });
  var lines = [];
  if (topLever) {
    lines.push(analysisLine("当前最有效促销/补贴手段是 " + rowName(topLever) + "，ADO " + formatCompact(num(topLever, "ado_mtd") || 0) + "，ADG " + formatCompact(num(topLever, "adg_mtd") || 0) + "；这个手段应与订单来源章节合并判断是否真实促成出单。", evidenceChip(model, topLever, "ado_mtd", "促销ADO " + formatValue(val(topLever, "ado_mtd"), "ado_mtd"))));
  }
  if (growth) {
    lines.push(analysisLine("促销增长最明显的是 " + rowName(growth) + "，ADO变化 " + signedDelta(num(growth, "ado_delta")) + "；若增长来自平台手段，可推动卖家承接库存和价格。", evidenceChip(model, growth, "ado_delta", "促销增长 " + formatValue(val(growth, "ado_delta"), "ado_delta"))));
  }
  if (highSeller) {
    lines.push(analysisLine(rowName(highSeller) + "卖家出资占比最高（" + formatValue(val(highSeller, "seller_funded_share"), "seller_funded_share") + "），需要和卖家确认利润率是否能支撑继续加码。", evidenceChip(model, highSeller, "seller_funded_share", "卖家出资 " + formatValue(val(highSeller, "seller_funded_share"), "seller_funded_share"))));
  }
  if (highLoad) {
    lines.push(analysisLine(rowName(highLoad) + "整体补贴负荷最高，total subsidy / ADG 为 " + formatValue(val(highLoad, "subsidy_share"), "subsidy_share") + "；若增长也集中在该站点，要判断是否为补贴买量。", evidenceChip(model, highLoad, "subsidy_share", "补贴负荷 " + formatValue(val(highLoad, "subsidy_share"), "subsidy_share"))));
  }
  lines.push(analysisLine("本节促销、补贴、CFS、Campaign、LPP不是MECE，适合判断哪类动作更能促成出单，不适合把占比相加。", ""));
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
  var adsShare = topBy(model, "ads_adg_share", { positive: true });
  var spendLoad = topBy(model, "ads_spend_gmv", { positive: true });
  var spendDown = topBy(model, "ads_spend_mom", { negative: true });
  var avgRoas = weightedAvg(model, "roas", "ads_spend");
  var lines = [];
  if (validNumber(avgRoas)) {
    lines.push(analysisLine("按广告花费加权的站点ROAS约为 " + formatCompact(avgRoas) + "；ROAS>5可考虑扩量，2-5需监控边际收益，<2优先优化素材/定向。", ""));
  }
  if (roasHigh) {
    lines.push(analysisLine(rowName(roasHigh) + "ADS效率最高，ROAS " + formatValue(val(roasHigh, "roas"), "roas") + "，是加投候选。", evidenceChip(model, roasHigh, "roas", "ROAS " + formatValue(val(roasHigh, "roas"), "roas"))));
  }
  if (adsShare) {
    lines.push(analysisLine(rowName(adsShare) + "ADS ADG占比最高（" + formatValue(val(adsShare, "ads_adg_share"), "ads_adg_share") + "），说明该站点对广告出单依赖最高；若预算波动，总GMV也会更敏感。", evidenceChip(model, adsShare, "ads_adg_share", "Ads ADG% " + formatValue(val(adsShare, "ads_adg_share"), "ads_adg_share"))));
  }
  if (spendLoad) {
    lines.push(analysisLine(rowName(spendLoad) + "Spend/GMV最高（" + formatValue(val(spendLoad, "ads_spend_gmv"), "ads_spend_gmv") + "），需要和ROAS一起判断是否高投入低回报。", evidenceChip(model, spendLoad, "ads_spend_gmv", "Spend/GMV " + formatValue(val(spendLoad, "ads_spend_gmv"), "ads_spend_gmv"))));
  }
  if (roasLow && (num(roasLow, "ads_spend") || 0) > 0) {
    lines.push(analysisLine(rowName(roasLow) + "ROAS最低（" + formatValue(val(roasLow, "roas"), "roas") + "），若同时Spend/GMV较高，应先优化投放效率再扩量。", evidenceChip(model, roasLow, "roas", "低ROAS " + formatValue(val(roasLow, "roas"), "roas"))));
  }
  if (spendDown) {
    lines.push(analysisLine(rowName(spendDown) + "广告支出MoM下降 " + signedPct(num(spendDown, "ads_spend_mom")) + "；若同站点ADG下降，可能是广告削减导致。", evidenceChip(model, spendDown, "ads_spend_mom", "Spend MoM " + signedPct(num(spendDown, "ads_spend_mom")))));
  }
  lines.push(analysisLine("HE1 Ads ADG% 当前按 ads_adg / total_adg 计算，因为raw_dws_shop没有独立HE1字段；后续若BI补字段，可直接替换该列。", ""));
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
  var tabs = activeTabs();
  var hasMetaTab = tabs && tabs[model.id + "_meta"];
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
  window.AUTODECK_ACTIVE_DATA = payload;
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
