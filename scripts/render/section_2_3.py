#!/usr/bin/env python3
"""
Section 2.3 — Root Cause Diagnosis (站点根因诊断)

Per-site diagnostic cards from sec_root_cause_meta JSON.
6-level decision tree walkthrough per site.
"""

from __future__ import annotations


def root_cause_chart_js() -> str:
    return r"""
function rootCauseChart(model) {
  var benchmark = getModelById("sec_site_benchmark");
  var subsidy = getModelById("sec_subsidy");
  var fulfillment = getModelById("sec_fulfillment");
  var price = getModelById("sec_price_band");
  var md = metaDict("sec_volatility");
  var signals = parseLooseJson(md.signals, []);

  if (!benchmark.body.length) return emptyStateChart(model);

  function rowBySite(sectionModel, site) {
    return (sectionModel.body || []).filter(function(item) {
      return String(val(item, "site") || "") === site;
    })[0] || null;
  }

  function signalCount(site) {
    var count = 0;
    signals.forEach(function(sig) {
      if (siteFromPath(sig.path) === site) count += 1;
    });
    return count;
  }

  function maxPriceBias(site) {
    var rows = (price.body || []).filter(function(item) { return String(val(item, "site") || "") === site; });
    rows.sort(function(a, b) { return Math.abs(num(b, "bias_pp") || 0) - Math.abs(num(a, "bias_pp") || 0); });
    return rows[0] || null;
  }

  function maxFulfillmentShift(item) {
    if (!item) return null;
    var best = null;
    ["fbs_shift_pp", "tpf_shift_pp", "sls_shift_pp"].forEach(function(col) {
      var v = num(item, col);
      if (!validNumber(v)) return;
      if (!best || Math.abs(v) > Math.abs(best.value)) best = { col: col, value: v };
    });
    return best;
  }

  var cards = benchmark.body.slice().filter(function(item) {
    return String(val(item, "site") || "");
  }).sort(function(a, b) {
    return (num(b, "adg_mtd") || 0) - (num(a, "adg_mtd") || 0);
  }).map(function(item) {
    var site = String(val(item, "site") || "");
    var gap = num(item, "adg_gap_pp");
    var sellerMom = num(item, "seller_adg_mom");
    var share = num(item, "adg_share");
    var subRow = rowBySite(subsidy, site);
    var fulRow = rowBySite(fulfillment, site);
    var priceRow = maxPriceBias(site);
    var shift = maxFulfillmentShift(fulRow);
    var sigCount = signalCount(site);
    var subShare = subRow ? num(subRow, "subsidy_share") : null;
    var priceBias = priceRow ? num(priceRow, "bias_pp") : null;

    var status = "✅";
    if ((validNumber(gap) && gap < -5) || (validNumber(sellerMom) && sellerMom < -20 && sigCount > 0)) status = "🔴";
    else if ((validNumber(gap) && Math.abs(gap) > 5) || sigCount > 0 || (validNumber(subShare) && subShare > 40)) status = "⚠️";

    var evidence = [];
    evidence.push({ level: "L1 需求端", finding: "ADG MoM " + signedPct(sellerMom) + "，大盘差 " + signedPp(gap), verdict: validNumber(gap) && Math.abs(gap) > 5 ? "卖家相对大盘出现显著偏离" : "与大盘差距暂不显著" });
    if (sigCount) evidence.push({ level: "L2 供给端", finding: sigCount + "个波动信号集中在该站点", verdict: "优先检查Top listing、断货、下架或竞品替代" });
    if (shift) evidence.push({ level: "L4 运营端", finding: prettyCol(shift.col) + " " + signedPp(shift.value), verdict: Math.abs(shift.value) > 20 ? "履约迁移可能影响转化/订单" : "履约变化可作为辅助证据" });
    if (priceRow && validNumber(priceBias)) evidence.push({ level: "L5 定价端", finding: (val(priceRow, "price_range") || "价格带") + " bias " + signedPp(priceBias), verdict: Math.abs(priceBias) > 10 ? "价格带覆盖与大盘存在错位" : "价格带基本可控" });
    if (subRow && validNumber(subShare)) evidence.push({ level: "L6 激励端", finding: "补贴负荷 " + formatCompact(subShare) + "%", verdict: subShare > 40 ? "增长质量需扣除补贴依赖" : "补贴依赖处于可控区间" });

    var hypothesis = "";
    if (validNumber(gap) && gap < -5) hypothesis = "卖家自身问题优先：相对大盘跑输，按listing/渠道/履约/定价/补贴顺序排查。";
    else if (validNumber(gap) && gap > 5 && validNumber(subShare) && subShare > 40) hypothesis = "跑赢大盘但补贴负荷高，增长可能部分由激励购买。";
    else if (validNumber(gap) && gap > 5) hypothesis = "相对大盘抢份额，优先维护供给和库存，并验证是否可扩量。";
    else if (sigCount) hypothesis = "大盘差距不强但波动信号存在，优先定位具体L3/listing。";
    else hypothesis = "暂无强异常，作为参考站点持续监控。";

    var recommendation = "";
    if (status === "🔴") recommendation = "拜访时先拿Top listing和渠道动作逐项核对，确认是否存在断货、下架、广告削减或履约迁移。";
    else if (status === "⚠️") recommendation = "保留为二级排查对象，结合品类矩阵和价格带确认偏离是否可复制或需纠偏。";
    else recommendation = "保持当前节奏，关注后续月份是否出现新的gap或波动信号。";

    return {
      site: site,
      status: status,
      adg: num(item, "adg_mtd"),
      share: share,
      gap: gap,
      evidence: evidence.slice(0, 5),
      confidence: evidence.length >= 4 ? "HIGH" : (evidence.length >= 2 ? "MEDIUM" : "LOW"),
      root_cause_hypothesis: hypothesis,
      recommendation: recommendation
    };
  });

  var sitesAnalyzed = cards.length;

  var html = '<div style="display:flex;flex-wrap:wrap;gap:8px;margin:8px 0">';
  html += '<div class="metric-card" style="flex:1 1 120px"><div class="label">Sites Analyzed</div><div class="value" style="font-size:16px">' + sitesAnalyzed + '</div></div>';
  html += '</div>';

  // Per-site diagnostic cards
  cards.forEach(function(card) {
    var statusColor = card.status === "🔴" ? "var(--down)" : (card.status === "⚠️" ? "var(--warn)" : "var(--up)");
    html += '<div style="border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin-bottom:10px;background:var(--surface);border-left:4px solid ' + statusColor + '">';
    html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">';
    html += '<strong style="font-size:14px">' + esc(card.site) + '</strong>';
    html += '<span style="font-size:18px">' + esc(card.status || "") + '</span>';
    html += '</div>';
    html += '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px">';
    html += '<span class="pill">ADG ' + formatCompact(card.adg || 0) + '</span>';
    html += '<span class="pill">Share ' + (validNumber(card.share) ? formatCompact(card.share) + '%' : '—') + '</span>';
    html += '<span class="pill">Gap ' + signedPp(card.gap) + '</span>';
    html += '<span class="pill">Confidence ' + esc(card.confidence || '—') + '</span>';
    html += '</div>';

    // Evidence chain
    if (card.evidence && card.evidence.length) {
      html += '<div style="font-size:11px;color:var(--muted);margin-bottom:6px">Diagnostic Chain:</div>';
      card.evidence.forEach(function(ev) {
        html += '<div style="display:flex;gap:8px;padding:3px 0;font-size:11px">';
        html += '<span style="color:var(--muted);min-width:70px">' + esc(ev.level || "") + '</span>';
        html += '<span>' + esc(ev.finding || "") + '</span>';
        html += '<span style="color:var(--muted)">→ ' + esc(ev.verdict || "") + '</span>';
        html += '</div>';
      });
    }

    // Hypothesis + recommendation
    html += '<div style="margin-top:8px;padding:8px 10px;background:var(--surface-soft);border-radius:6px;font-size:12px">';
    html += '<strong>Hypothesis:</strong> ' + esc(card.root_cause_hypothesis || "暂无强异常，作为参考站点持续监控。") + '<br>';
    html += '<strong>Confidence:</strong> ' + esc(card.confidence || "—") + '<br>';
    html += '<strong>Recommendation:</strong> ' + esc(card.recommendation || "保持当前节奏，关注后续月份是否出现新的gap或波动信号。");
    html += '</div>';
    html += '</div>';
  });

  return html;
}
"""


def build_section_js() -> str:
    return root_cause_chart_js()


SECTION_ID = "sec_root_cause"
FUNC_NAME = "rootCauseChart"
