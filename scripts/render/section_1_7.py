#!/usr/bin/env python3
"""
Section 1.7 — Shop Contribution Analysis (店铺贡献分析)

Shop traffic attribution workbench:
- Overall Top ADG / Top ADO shops
- Site-filtered shop movers with traffic funnel diagnostics
- Site-filtered L3 x price range gain/loss drivers
"""

from __future__ import annotations


def shop_impact_chart_js() -> str:
    return r"""
function shopImpactChart(model) {
  if (!model || !model.body.length) return emptyStateChart(model);

  function shopRow(item) {
    var shopId = String(val(item, "shop_id") || "").trim();
    return {
      item: item,
      scope: String(val(item, "scope") || ""),
      type: String(val(item, "rank_type") || ""),
      rank: num(item, "rank") || 0,
      site: String(val(item, "site") || ""),
      topSite: String(val(item, "top_site") || ""),
      shopId: shopId,
      shopName: String(val(item, "shop_name") || ""),
      l3: String(val(item, "l3") || ""),
      price: String(val(item, "price_range") || ""),
      adg: num(item, "adg_mtd") || 0,
      ado: num(item, "ado_mtd") || 0,
      adimp: num(item, "adimp_mtd") || 0,
      adclick: num(item, "adclick_mtd") || 0,
      ctr: num(item, "ctr_mtd"),
      cr: num(item, "cr_mtd"),
      adgM1: num(item, "adg_m1") || 0,
      adoM1: num(item, "ado_m1") || 0,
      adimpM1: num(item, "adimp_m1") || 0,
      adclickM1: num(item, "adclick_m1") || 0,
      ctrM1: num(item, "ctr_m1"),
      crM1: num(item, "cr_m1"),
      adgDelta: num(item, "adg_delta") || 0,
      adoDelta: num(item, "ado_delta") || 0,
      adimpDelta: num(item, "adimp_delta") || 0,
      adclickDelta: num(item, "adclick_delta") || 0,
      ctrDelta: num(item, "ctr_delta_pp"),
      crDelta: num(item, "cr_delta_pp"),
      aovDelta: num(item, "adg_per_order_delta"),
      adgMom: num(item, "adg_mom"),
      adoMom: num(item, "ado_mom"),
      adimpMom: num(item, "adimp_mom"),
      adclickMom: num(item, "adclick_mom"),
      share: num(item, "site_adg_share"),
      contribution: num(item, "site_delta_contribution_pct"),
      driver: String(val(item, "primary_driver") || ""),
      isMall: val(item, "is_official_shop"),
      days: num(item, "days_cnt") || 0
    };
  }

  var rows = model.body.map(shopRow).filter(function(r) { return r.shopId; });
  var hasEnrichedRows = rows.some(function(r) { return r.type; });
  if (!rows.length) return emptyStateChart(model);
  if (!hasEnrichedRows) return legacyShopImpactChart(model);

  var topAdg = rows.filter(function(r) { return r.type === "top_adg"; }).sort(function(a,b) { return a.rank - b.rank; });
  var topAdo = rows.filter(function(r) { return r.type === "top_ado"; }).sort(function(a,b) { return a.rank - b.rank; });
  var siteKeyShops = rows.filter(function(r) { return r.type === "site_key_shop"; });
  var shopMovers = rows.filter(function(r) { return r.type === "shop_mover"; });
  if (siteKeyShops.length) shopMovers = siteKeyShops;
  if (!shopMovers.length) shopMovers = rows.filter(function(r) { return r.type === "site_gain" || r.type === "site_loss"; });
  var l3Gain = rows.filter(function(r) { return r.type === "l3_price_gain"; });
  var l3Loss = rows.filter(function(r) { return r.type === "l3_price_loss"; });
  var sites = Array.from(new Set(shopMovers.concat(l3Gain).concat(l3Loss).map(function(r) { return r.topSite || r.site; }).filter(function(s) { return s && s !== "All"; }))).sort();
  var uniqueShops = Array.from(new Set(shopMovers.map(function(r) { return (r.topSite || r.site) + ":" + r.shopId; }))).length || Array.from(new Set(rows.map(function(r) { return r.shopId; }))).length;
  var bestGain = shopMovers.slice().sort(function(a,b) { return b.adgDelta - a.adgDelta; })[0];
  var worstLoss = shopMovers.slice().sort(function(a,b) { return a.adgDelta - b.adgDelta; })[0];

  function label(r) { return r.shopName ? r.shopName : ("Shop " + r.shopId); }
  function siteOf(r) { return (r.topSite && r.topSite !== "All") ? r.topSite : r.site; }
  function signed(n) { if (!validNumber(n)) return "—"; return (n > 0 ? "+" : "") + formatCompact(n); }
  function signedPctValue(n) { if (!validNumber(n)) return "—"; return (n > 0 ? "+" : "") + formatCompact(n) + "%"; }
  function signedPpValue(n) { if (!validNumber(n)) return "—"; return (n > 0 ? "+" : "") + formatCompact(n) + "pp"; }
  function rateText(n) { if (!validNumber(n)) return "—"; return formatCompact(n * 100) + "%"; }
  function toneClass(n) { return n >= 0 ? "shop-up" : "shop-down"; }
  function driverClass(text) {
    if (/下降|减少|流失/.test(text)) return "down";
    if (/提升|增长|增加/.test(text)) return "up";
    return "";
  }
  function driverChip(r) {
    var text = r.driver || "结构变化";
    return '<span class="shop-driver ' + driverClass(text) + '">' + esc(text) + '</span>';
  }
  function metricDelta(labelText, value, suffix, tone) {
    return '<span class="shop-metric-delta ' + (tone || toneClass(value || 0)) + '"><b>' + esc(labelText) + '</b>' + esc(validNumber(value) ? ((value > 0 ? "+" : "") + formatCompact(value) + (suffix || "")) : "—") + '</span>';
  }
  function card(labelText, valueText, context, tone) {
    return '<div class="shop-card ' + (tone || "") + '"><div class="label">' + esc(labelText) + '</div><div class="value">' + esc(valueText) + '</div><div class="context">' + esc(context || "") + '</div></div>';
  }
  function rankTable(title, rows, metric) {
    var html = '<div class="shop-panel"><div class="shop-panel-title"><b>' + esc(title) + '</b><small>整体店铺榜</small></div>';
    html += '<table class="shop-table shop-rank-table"><thead><tr><th>#</th><th>店铺</th><th>站点</th><th>ADG</th><th>ADO</th><th>ADG Δ</th><th>Driver</th></tr></thead><tbody>';
    rows.slice(0, 8).forEach(function(r) {
      html += '<tr><td><span class="shop-rank">' + esc(r.rank || "") + '</span></td><td class="shop-left"><b>' + esc(label(r)) + '</b><small>' + esc(r.shopId) + '</small></td><td>' + esc(siteOf(r) || "—") + '</td><td class="' + (metric === "adg" ? "shop-strong" : "") + '">' + formatCompact(r.adg) + '</td><td class="' + (metric === "ado" ? "shop-strong" : "") + '">' + formatCompact(r.ado) + '</td><td class="' + toneClass(r.adgDelta) + '">' + signed(r.adgDelta) + '</td><td>' + driverChip(r) + '</td></tr>';
    });
    html += '</tbody></table></div>';
    return html;
  }
  function siteFilterRows(list, site) {
    return list.filter(function(r) { return site === "__all" || siteOf(r) === site; });
  }
  function shopMoverRow(r) {
    return '<tr><td class="shop-left"><b>' + esc(label(r)) + '</b><small>' + esc(siteOf(r) + " · " + r.shopId) + '</small></td>' +
      '<td class="' + toneClass(r.adgDelta) + '">' + signed(r.adgDelta) + '</td>' +
      '<td class="' + toneClass(r.adimpDelta) + '">' + signed(r.adimpDelta) + '</td>' +
      '<td class="' + toneClass(r.adclickDelta) + '">' + signed(r.adclickDelta) + '</td>' +
      '<td class="' + toneClass(r.ctrDelta || 0) + '">' + signedPpValue(r.ctrDelta) + '</td>' +
      '<td class="' + toneClass(r.crDelta || 0) + '">' + signedPpValue(r.crDelta) + '</td>' +
      '<td>' + driverChip(r) + '</td></tr>';
  }
  function l3DriverRow(r) {
    return '<div class="shop-driver-row"><div class="shop-driver-main"><b>' + esc(r.l3 || "—") + '</b><small>' + esc((r.price || "—") + " · " + label(r) + " · " + siteOf(r)) + '</small></div>' +
      '<div class="' + toneClass(r.adgDelta) + '">' + signed(r.adgDelta) + '</div>' +
      '<div class="shop-driver-metrics">' + metricDelta("Imp", r.adimpDelta, "", toneClass(r.adimpDelta)) + metricDelta("CTR", r.ctrDelta, "pp", toneClass(r.ctrDelta || 0)) + metricDelta("CR", r.crDelta, "pp", toneClass(r.crDelta || 0)) + '</div>' +
      driverChip(r) + '</div>';
  }

  var siteButtonsId = "shop-site-buttons-" + Math.random().toString(36).slice(2, 8);
  var detailId = "shop-detail-" + Math.random().toString(36).slice(2, 8);
  var html = '<div class="shop-impact-workbench">';
  html += '<style>';
  html += '.shop-impact-workbench{--shop-orange:var(--accent,#ee4d2d);--shop-line:var(--line,#dfe3e8);--shop-muted:var(--muted,#68707c);margin:8px 0 12px}.shop-cards{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px;margin:8px 0 10px}.shop-card{border:1px solid var(--shop-line);background:#fff;padding:8px 10px;min-height:66px}.shop-card.gain{border-color:rgba(19,122,75,.45);background:#f3fbf7}.shop-card.loss{border-color:rgba(180,35,24,.45);background:#fff6f4}.shop-card .label{font-size:10px;color:var(--shop-muted);font-weight:800;text-transform:uppercase}.shop-card .value{margin-top:3px;font-size:16px;line-height:1.08;font-weight:850;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.shop-card .context{font-size:10px;color:var(--shop-muted);margin-top:3px;line-height:1.25;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}';
  html += '.shop-top-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px}.shop-panel{border:1px solid var(--shop-line);background:#fff;padding:10px;min-width:0}.shop-panel-title{display:flex;align-items:flex-start;justify-content:space-between;gap:8px;margin-bottom:7px}.shop-panel-title b{font-size:13px}.shop-panel-title small{font-size:10px;color:var(--shop-muted);text-align:right}.shop-table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:10px}.shop-table th{background:#404040;color:#fff;font-weight:850;padding:5px 6px}.shop-table td{border:1px solid #fff;background:#f4f5f7;padding:5px 6px;text-align:center;vertical-align:middle}.shop-table .shop-left{text-align:left}.shop-table b{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.shop-table small{display:block;color:var(--shop-muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.shop-rank{display:inline-grid;place-items:center;width:20px;height:20px;border-radius:50%;background:var(--shop-orange);color:#fff;font-size:11px;font-weight:850}.shop-strong{font-weight:850;color:#111}.shop-up{color:var(--up,#137a4b);font-weight:850}.shop-down{color:var(--down,#b42318);font-weight:850}.shop-driver{display:inline-block;border:1px solid #d7dce2;background:#fff;padding:2px 5px;font-size:9px;font-weight:850;white-space:nowrap}.shop-driver.up{color:var(--up,#137a4b);background:#eef8f2;border-color:#bfe2cd}.shop-driver.down{color:var(--down,#b42318);background:#fff0ed;border-color:#efc0b7}';
  html += '.shop-site-toolbar{display:flex;flex-wrap:wrap;gap:5px;margin:4px 0 8px}.shop-site-btn,.shop-key-btn{border:1px solid var(--shop-line);background:#fff;padding:4px 8px;font-size:10px;font-weight:800;cursor:pointer;border-radius:0}.shop-site-btn.active,.shop-key-btn.active{border-color:var(--shop-orange);background:#fff1ed;color:var(--shop-orange)}.shop-key-toolbar{display:flex;flex-wrap:wrap;gap:5px;margin:0 0 8px}.shop-key-btn span{color:var(--shop-muted);font-weight:700;margin-left:4px}.shop-detail-grid{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,.95fr);gap:10px}.shop-driver-list{display:grid;grid-template-columns:1fr;gap:6px}.shop-driver-row{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(150px,.55fr) auto;gap:6px;align-items:center;border:1px solid #e7e9ee;background:#fafafa;padding:6px}.shop-driver-main b{display:block;font-size:10px;line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.shop-driver-main small{display:block;color:var(--shop-muted);font-size:9px;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.shop-driver-metrics{display:flex;flex-wrap:wrap;gap:3px}.shop-metric-delta{display:inline-flex;gap:3px;align-items:center;border:1px solid #e0e4ea;background:#fff;padding:2px 4px;font-size:9px}.shop-metric-delta b{color:var(--shop-muted);font-weight:850}.shop-empty{font-size:11px;color:var(--shop-muted);padding:10px;border:1px dashed var(--shop-line);background:#fafafa}@media(max-width:1100px){.shop-cards,.shop-top-grid,.shop-detail-grid{grid-template-columns:1fr}.shop-driver-row{grid-template-columns:1fr}.shop-card .value,.shop-card .context{white-space:normal}}';
  html += '</style>';
  html += '<div class="shop-cards">';
  html += card("Unique Shops", uniqueShops, sites.length + " sites covered", "");
  html += card("Top ADG Shop", topAdg[0] ? label(topAdg[0]) : "—", topAdg[0] ? "ADG " + formatCompact(topAdg[0].adg) + " · " + siteOf(topAdg[0]) + " · " + (topAdg[0].driver || "结构变化") : "", "");
  html += card("Top ADO Shop", topAdo[0] ? label(topAdo[0]) : "—", topAdo[0] ? "ADO " + formatCompact(topAdo[0].ado) + " · " + siteOf(topAdo[0]) + " · " + (topAdo[0].driver || "结构变化") : "", "");
  html += card("Best Growth", bestGain ? label(bestGain) : "—", bestGain ? siteOf(bestGain) + " · ADG Δ " + signed(bestGain.adgDelta) + " · " + bestGain.driver : "", "gain");
  html += card("Largest Loss", worstLoss ? label(worstLoss) : "—", worstLoss ? siteOf(worstLoss) + " · ADG Δ " + signed(worstLoss.adgDelta) + " · " + worstLoss.driver : "", "loss");
  html += '</div>';
  html += '<div class="shop-top-grid">' + rankTable("Top ADG店铺", topAdg, "adg") + rankTable("Top ADO店铺", topAdo, "ado") + '</div>';
  html += '<div class="shop-panel"><div class="shop-panel-title"><b>店铺流量归因与L3×价格带定位</b><small>ADIMP=日均曝光，ADCLICK=日均点击，CTR=点击/曝光，CR=订单/点击</small></div>';
  html += '<div class="shop-site-toolbar" id="' + siteButtonsId + '"><button class="shop-site-btn active" data-site="__all">All</button>' + sites.map(function(site) { return '<button class="shop-site-btn" data-site="' + esc(site) + '">' + esc(site) + '</button>'; }).join("") + '</div>';
  html += '<div id="' + detailId + '"></div></div>';
  html += '</div>';

  setTimeout(function() {
    var buttons = document.getElementById(siteButtonsId);
    var detail = document.getElementById(detailId);
    if (!buttons || !detail) return;
    var state = { site: "__all", shop: "__all" };
    function shopKey(r) { return siteOf(r) + "::" + r.shopId; }
    function keyShopButtons(movers) {
      var html = '<div class="shop-key-toolbar"><button class="shop-key-btn active" data-shop="__all">全部key shops</button>';
      movers.slice(0, 8).forEach(function(r) {
        html += '<button class="shop-key-btn" data-shop="' + esc(shopKey(r)) + '">' + esc(label(r).slice(0, 18)) + '<span>' + esc(siteOf(r)) + " " + signed(r.adgDelta) + '</span></button>';
      });
      html += '</div>';
      return html;
    }
    function render() {
      var site = state.site;
      var movers = siteFilterRows(shopMovers, site).sort(function(a,b) { return Math.abs(b.adgDelta) - Math.abs(a.adgDelta); }).slice(0, site === "__all" ? 14 : 8);
      var keySet = {};
      movers.forEach(function(r) { keySet[shopKey(r)] = true; });
      function l3Matches(r) {
        var withinSite = site === "__all" || siteOf(r) === site;
        if (!withinSite) return false;
        if (state.shop !== "__all") return shopKey(r) === state.shop;
        return keySet[shopKey(r)];
      }
      var gains = l3Gain.filter(l3Matches).sort(function(a,b) { return b.adgDelta - a.adgDelta; }).slice(0, 10);
      var losses = l3Loss.filter(l3Matches).sort(function(a,b) { return a.adgDelta - b.adgDelta; }).slice(0, 10);
      var h = '<div class="shop-detail-grid"><div class="shop-panel"><div class="shop-panel-title"><b>' + (site === "__all" ? "站点key driver shops" : esc(site) + " key driver shops") + '</b><small>先按站点找关键店铺，再下钻这些店铺</small></div>';
      h += keyShopButtons(movers);
      h += '<table class="shop-table"><thead><tr><th>店铺</th><th>ADG Δ</th><th>ADIMP Δ</th><th>ADCLICK Δ</th><th>CTR Δ</th><th>CR Δ</th><th>Driver</th></tr></thead><tbody>' + (movers.length ? movers.map(shopMoverRow).join("") : '<tr><td colspan="7">暂无店铺波动</td></tr>') + '</tbody></table></div>';
      h += '<div class="shop-panel"><div class="shop-panel-title"><b>L3 × Price Range 归因</b><small>' + (state.shop === "__all" ? "当前key shops" : "当前key shop") + ' 的类目价格带下钻</small></div><div class="shop-driver-list">';
      h += '<div class="shop-list-block"><div class="shop-panel-title"><b class="shop-up">涨幅发生位置</b><small>Top L3×价格带</small></div>' + (gains.length ? gains.map(l3DriverRow).join("") : '<div class="shop-empty">当前筛选无明显涨幅类目价格带。</div>') + '</div>';
      h += '<div class="shop-list-block" style="margin-top:8px"><div class="shop-panel-title"><b class="shop-down">跌幅发生位置</b><small>Top L3×价格带</small></div>' + (losses.length ? losses.map(l3DriverRow).join("") : '<div class="shop-empty">当前筛选无明显跌幅类目价格带。</div>') + '</div>';
      h += '</div></div></div>';
      detail.innerHTML = h;
      detail.querySelectorAll(".shop-key-btn").forEach(function(btn) {
        btn.classList.toggle("active", btn.getAttribute("data-shop") === state.shop);
        btn.addEventListener("click", function() {
          state.shop = btn.getAttribute("data-shop");
          render();
        });
      });
    }
    buttons.querySelectorAll(".shop-site-btn").forEach(function(btn) {
      btn.addEventListener("click", function() {
        buttons.querySelectorAll(".shop-site-btn").forEach(function(b) { b.classList.toggle("active", b === btn); });
        state.site = btn.getAttribute("data-site");
        state.shop = "__all";
        render();
      });
    });
    render();
  }, 0);

  return html;
}

function legacyShopImpactChart(model) {
  var shops = [];
  model.body.forEach(function(item) {
    var id = String(val(item, "shop_id") || "").trim();
    if (!id) return;
    shops.push({ id: id, adg: num(item, "adg_mtd") || 0, delta: num(item, "adg_delta") || 0, share: num(item, "share_in_l3") || 0, isMall: val(item, "is_official_shop"), days: num(item, "days_cnt") || 0 });
  });
  if (!shops.length) return emptyStateChart(model);
  shops.sort(function(a, b) { return b.adg - a.adg; });
  var html = '<div style="margin-top:8px"><table class="report-table"><thead><tr><th>Shop ID</th><th>ADG MTD</th><th>ADG Δ</th><th>Share</th><th>Mall</th><th>Days Active</th></tr></thead><tbody>';
  shops.forEach(function(s) {
    html += '<tr><td class="shop-id">' + esc(s.id) + '</td><td>' + formatCompact(s.adg) + '</td><td class="' + (s.delta >= 0 ? "up-text" : "dn-text") + '">' + (s.delta > 0 ? "+" : "") + formatCompact(s.delta) + '</td><td>' + formatCompact(s.share) + '%</td><td>' + (s.isMall == 1 ? "Mall" : "Non-Mall") + '</td><td>' + s.days + '</td></tr>';
  });
  html += '</tbody></table></div>';
  return html;
}
"""


def build_section_js() -> str:
    return shop_impact_chart_js()


SECTION_ID = "sec_shop_impact"
FUNC_NAME = "shopImpactChart"
