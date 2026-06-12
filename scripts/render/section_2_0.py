#!/usr/bin/env python3
"""
Section 2.0 — Order Source Split (订单来源拆分)

Traffic funnel per site: Impressions → Clicks → CTR → ADO → CR.
Note: sources (Organic/Ads/Live/Campaign) are not MECE — show as reference, not 100% stack.
"""

from __future__ import annotations


def traffic_channel_chart_js() -> str:
    return r"""
function trafficChannelChart(model) {
  if (!model || !model.body.length) return emptyStateChart(model);

  // Aggregate by site (not site×L1)
  var siteMap = {};
  model.body.forEach(function(item) {
    var site = String(val(item, "site") || "").trim();
    if (!site) return;
    if (!siteMap[site]) {
      siteMap[site] = { site: site, impr: 0, clicks: 0, ado: 0, ado_m1: 0, adg: 0, adg_m1: 0,
        organic: 0, ads: 0, live: 0, campaign: 0,
        org_mom: null, ads_mom: null, live_mom: null, camp_mom: null,
        impr_m1: 0, clicks_m1: 0, roas: null, spend: 0, acp: null };
    }
    var s = siteMap[site];
    s.impr += num(item, "adimp") || num(item, "impression") || 0;
    s.clicks += num(item, "adclicks") || num(item, "clicks") || 0;
    s.ado += num(item, "ado") || num(item, "mtd_ado") || 0;
    s.adg += num(item, "total") || 0;
    s.organic += num(item, "organic") || 0;
    s.ads += num(item, "ads") || 0;
    s.live += num(item, "live") || 0;
    s.campaign += num(item, "campaign") || 0;
    // Capture MoM from first available L1 row
    if (s.org_mom == null) s.org_mom = num(item, "organic_mom");
    if (s.ads_mom == null) s.ads_mom = num(item, "ads_mom");
    if (s.live_mom == null) s.live_mom = num(item, "live_mom");
    if (s.camp_mom == null) s.camp_mom = num(item, "campaign_mom");
    var r = num(item, "roas");
    if (r != null) s.roas = r;
    s.spend += num(item, "spend") || 0;
    var a = num(item, "acp");
    if (a != null) s.acp = a;
  });

  var sites = Object.keys(siteMap).sort();
  if (!sites.length) return emptyStateChart(model);

  // ── 1. Funnel table per site ──
  var html = '<table class="report-table"><thead><tr>';
  html += '<th>Site</th><th>Impression</th><th>Clicks</th><th>CTR</th><th>CTR MoM</th><th>ADO</th><th>ADO MoM</th><th>CR</th><th>CR MoM</th><th>ADG</th><th>ROAS</th><th>ACP</th><th>Spend</th>';
  html += '</tr></thead><tbody>';
  sites.forEach(function(site) {
    var s = siteMap[site];
    var ctr = s.impr > 0 ? (s.clicks / s.impr * 100) : null;
    var cr = s.clicks > 0 && s.ado > 0 ? (s.ado / s.clicks * 100) : null;
    // CTR MoM and CR MoM: computed when M-1 data available
    var ctrM1 = s.impr_m1 > 0 && s.clicks_m1 > 0 ? (s.clicks_m1 / s.impr_m1 * 100) : null;
    var crM1 = s.clicks_m1 > 0 && s.ado_m1 > 0 ? (s.ado_m1 / s.clicks_m1 * 100) : null;
    var ctrMom = ctr != null && ctrM1 != null ? ((ctr - ctrM1) / ctrM1 * 100) : null;
    var crMom = cr != null && crM1 != null ? ((cr - crM1) / crM1 * 100) : null;
    var adoMomVal = s.ado_m1 > 0 ? ((s.ado - s.ado_m1) / s.ado_m1 * 100) : null;
    html += '<tr>';
    html += '<td><strong>' + esc(site) + '</strong></td>';
    html += '<td>' + (s.impr > 0 ? formatCompact(s.impr) : "—") + '</td>';
    html += '<td>' + (s.clicks > 0 ? formatCompact(s.clicks) : "—") + '</td>';
    html += '<td>' + (ctr != null ? ctr.toFixed(2) + '%' : "—") + '</td>';
    html += '<td class="' + ((ctrMom||0) > 0 ? 'up-text' : ((ctrMom||0) < 0 ? 'dn-text' : '')) + '">' + (ctrMom != null ? (ctrMom>0?'+':'') + formatCompact(ctrMom) + '%' : '—') + '</td>';
    html += '<td>' + (s.ado > 0 ? formatCompact(s.ado) : "—") + '</td>';
    html += '<td class="' + ((adoMomVal||0) > 0 ? 'up-text' : ((adoMomVal||0) < 0 ? 'dn-text' : '')) + '">' + (adoMomVal != null ? (adoMomVal>0?'+':'') + formatCompact(adoMomVal) + '%' : '—') + '</td>';
    html += '<td>' + (cr != null ? cr.toFixed(2) + '%' : "—") + '</td>';
    html += '<td class="' + ((crMom||0) > 0 ? 'up-text' : ((crMom||0) < 0 ? 'dn-text' : '')) + '">' + (crMom != null ? (crMom>0?'+':'') + formatCompact(crMom) + '%' : '—') + '</td>';
    html += '<td>' + formatCompact(s.adg) + '</td>';
    html += '<td>' + (s.roas != null ? s.roas.toFixed(1) : "—") + '</td>';
    html += '<td>' + (s.acp != null ? formatCompact(s.acp) : "—") + '</td>';
    html += '<td>' + (s.spend > 0 ? formatCompact(s.spend) : "—") + '</td>';
    html += '</tr>';
  });
  html += '</tbody></table>';

  // ── 2. Source split with MoM (reference — not MECE) ──
  html += '<div style="margin-top:12px"><div style="font-size:11px;font-weight:700;color:var(--muted);padding:4px 0">Source Split — ADG & MoM (reference, not MECE)</div>';
  html += '<table class="report-table"><thead><tr>';
  html += '<th>Site</th><th>Organic</th><th>Org MoM</th><th>Ads</th><th>Ads MoM</th><th>Live</th><th>Live MoM</th><th>Campaign</th><th>Camp MoM</th><th>Total ADG</th>';
  html += '</tr></thead><tbody>';
  sites.forEach(function(site) {
    var s = siteMap[site];
    function momCell(val) { return '<td class="' + ((val||0)>0?'up-text':((val||0)<0?'dn-text':'')) + '">' + (val!=null?(val>0?'+':'')+formatCompact(val)+'%':'—') + '</td>'; }
    html += '<tr><td><strong>' + esc(site) + '</strong></td>';
    html += '<td>' + formatCompact(s.organic) + '</td>' + momCell(s.org_mom);
    html += '<td>' + formatCompact(s.ads) + '</td>' + momCell(s.ads_mom);
    html += '<td>' + formatCompact(s.live) + '</td>' + momCell(s.live_mom);
    html += '<td>' + formatCompact(s.campaign) + '</td>' + momCell(s.camp_mom);
    html += '<td>' + formatCompact(s.adg) + '</td></tr>';
  });
  html += '</tbody></table></div>';

  return html;
}
"""


def build_section_js() -> str:
    return traffic_channel_chart_js()


SECTION_ID = "sec_traffic_channel"
FUNC_NAME = "trafficChannelChart"
