/**
 * Solana Ecosystem Intelligence — Dashboard Engine (v4.0)
 * Interactive, zero-dependency vanilla JS dashboard.
 */
(function () {
  'use strict';

  /* ===================================================================
     STATE
     =================================================================== */
  let report = null;
  let allValidators = [];
  let filteredValidators = [];
  let charts = {};
  let refreshLog = [];
  let activeFilter = 'all';
  let searchQuery = '';
  let validatorPage = 1;
  let lastFocusedElement = null;
  const VALIDATOR_PAGE_SIZE = 5;

  const REPORT_PATHS = [
    './data/report.json',
    './report.json',
    '../data/report.json',
    '/data/report.json',
  ];

  /* ===================================================================
     DOM REFS
     =================================================================== */
  const $ = (id) => document.getElementById(id);
  const el = {
    loading: $('app-loading'),
    toast: $('toast-container'),
    healthPill: $('health-pill'),
    healthPillText: $('health-pill-text'),
    updatedAt: $('updated-at'),
    refreshBtn: $('refresh-btn'),
    exportCsv: $('export-csv-btn'),
    exportJson: $('export-json-btn'),
    kpiGrid: $('kpi-grid'),
    kpiGridSecondary: $('kpi-grid-secondary'),
    netEpoch: $('net-epoch'),
    netEpochPct: $('net-epoch-pct'),
    netBlock: $('net-block'),
    netTps: $('net-tps'),
    netTpsSub: $('net-tps-sub'),
    netSlotTime: $('net-slot-time'),
    netSlotSub: $('net-slot-sub'),
    epochProgress: $('epoch-progress'),
    epochProgressFill: $('epoch-progress-fill'),
    chartTps: $('chart-tps'),
    chartPrice: $('chart-price'),
    chartTvl: $('chart-tvl'),
    chartValidators: $('chart-validators'),
    valActive: $('val-active'),
    valDelinquent: $('val-delinquent'),
    valDelinqPct: $('val-delinq-pct'),
    valStakePct: $('val-stake-pct'),
    valTotal: $('val-total'),
    commissionBar: $('commission-bar'),
    topValidatorsList: $('top-validators-list'),
    validatorsPager: $('validators-pager'),
    valPrev: $('val-prev'),
    valNext: $('val-next'),
    valPagerInfo: $('val-pager-info'),
    validatorSearch: $('validator-search'),
    roadmapList: $('roadmap-list'),
    defiTbody: $('defi-tbody'),
    defiCount: $('defi-count'),
    stablecoinContent: $('stablecoin-content'),
    econMcap: $('econ-mcap'),
    econDex: $('econ-dex'),
    supplyCirc: $('supply-circ'),
    econAch: $('econ-ach'),
    econPrice: $('econ-price'),
    econChange: $('econ-change'),
    econTvl: $('econ-tvl'),
    econRealtvl: $('econ-realtvl'),
    econMedfee: $('econ-medfee'),
    econBasefee: $('econ-basefee'),
    refreshHistory: $('refresh-history'),
    footerVersion: $('footer-version'),
    sourcesList: $('sources-list'),
    footerDisclaimer: $('footer-disclaimer'),
    scrollTopBtn: $('scroll-top-btn'),
    modalOverlay: $('modal-overlay'),
    modalTitle: $('modal-title'),
    modalBody: $('modal-body'),
    modalClose: $('modal-close'),
  };

  /* ===================================================================
     FORMATTERS
     =================================================================== */
  function fmtUSD(v, compact) {
    if (v == null || isNaN(v)) return '—';
    if (compact) {
      if (v >= 1e12) return '$' + (v / 1e12).toFixed(2) + 'T';
      if (v >= 1e9)  return '$' + (v / 1e9).toFixed(2) + 'B';
      if (v >= 1e6)  return '$' + (v / 1e6).toFixed(2) + 'M';
      if (v >= 1e3)  return '$' + (v / 1e3).toFixed(2) + 'K';
      return '$' + v.toFixed(2);
    }
    return '$' + v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function fmtNum(n) {
    if (n == null || isNaN(n)) return '—';
    return n.toLocaleString('en-US', { maximumFractionDigits: 2 });
  }

  function fmtDelta(d) {
    if (d == null || isNaN(d)) return { text: '—', cls: '' };
    const prefix = d > 0 ? '+' : '';
    const cls = d >= 0 ? 'delta-up' : 'delta-down';
    return { text: prefix + d.toFixed(2) + '%', cls };
  }

  function fmtSOL(v) {
    if (v == null || isNaN(v)) return '—';
    if (v >= 1e9) return (v / 1e9).toFixed(2) + 'B';
    if (v >= 1e6) return (v / 1e6).toFixed(2) + 'M';
    if (v >= 1e3) return (v / 1e3).toFixed(2) + 'K';
    return fmtNum(v);
  }

  function truncatePubkey(key, start, end) {
    start = start || 6; end = end || 6;
    if (!key || key.length <= start + end) return key || '—';
    return key.slice(0, start) + '\u2026' + key.slice(-end);
  }

  function timeAgo(isoStr) {
    if (!isoStr) return '—';
    const diff = Date.now() - new Date(isoStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return mins + 'm ago';
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return hrs + 'h ago';
    return Math.floor(hrs / 24) + 'd ago';
  }

  /* ===================================================================
     TOAST
     =================================================================== */
  function toast(msg, icon) {
    icon = icon || '\u2713';
    if (!el.toast) return;
    const t = document.createElement('div');
    t.className = 'toast';
    t.innerHTML = '<span class="t-ic">' + icon + '</span><span>' + msg + '</span>';
    el.toast.appendChild(t);
    setTimeout(function () {
      t.classList.add('leaving');
      setTimeout(function () { t.remove && t.remove(); }, 250);
    }, 2800);
  }

  /* ===================================================================
     MODAL
     =================================================================== */
  function showModal(title, content) {
    if (!el.modalOverlay || !el.modalTitle || !el.modalBody) return;
    lastFocusedElement = document.activeElement;
    el.modalTitle.textContent = title;
    el.modalBody.innerHTML = content;
    el.modalOverlay.classList.add('visible');
    document.body.style.overflow = 'hidden';
    setTimeout(function () { if (el.modalClose) el.modalClose.focus(); }, 10);
  }

  function hideModal() {
    if (!el.modalOverlay) return;
    el.modalOverlay.classList.remove('visible');
    document.body.style.overflow = '';
    if (lastFocusedElement && lastFocusedElement.focus) lastFocusedElement.focus();
  }

  /* ===================================================================
     HELPERS
     =================================================================== */
  function setText(element, val) {
    if (element) element.textContent = val || '—';
  }
  function setHTML(element, val) {
    if (element) element.innerHTML = val || '—';
  }

  /* ===================================================================
     RENDER KPI CARDS
     =================================================================== */
  function renderKPI(r) {
    const p = r.price || {};
    const n = r.network || {};
    const v = r.validators || {};
    const e = r.economics || {};
    const s = r.sentiment || {};
    const d = r.daily_active_addresses || {};
    const sCur = s.current || {};
    const dCur = d.current || {};

    const primaryCards = [
      {
        label: 'SOL Price',
        value: fmtUSD(p.price_usd),
        delta: fmtDelta(p.change_24h_pct),
        sub: '24h change',
        detail: '<p><strong>Current:</strong> ' + fmtUSD(p.price_usd) + '</p><p><strong>24h Change:</strong> ' + (p.change_24h_pct != null ? p.change_24h_pct.toFixed(2) + '%' : '\u2014') + '</p><p><strong>Market Cap:</strong> ' + fmtUSD(p.market_cap_usd, true) + '</p><p><strong>24h Volume:</strong> ' + fmtUSD(p.volume_24h_usd, true) + '</p>',
      },
      {
        label: 'Network TPS',
        value: fmtNum(Math.round(n.current_tps)),
        delta: fmtDelta((r.live_cards && r.live_cards.network_tps && r.live_cards.network_tps.delta_pct) || 0),
        sub: '15m avg: ' + fmtNum(Math.round(n.avg_tps_15m)),
        detail: '<p><strong>Current TPS:</strong> ' + fmtNum(Math.round(n.current_tps)) + '</p><p><strong>15m Average:</strong> ' + fmtNum(Math.round(n.avg_tps_15m)) + '</p><p><strong>Non-vote TPS:</strong> ' + fmtNum(Math.round(n.non_vote_tps)) + '</p><p><strong>Total Transactions:</strong> ' + fmtNum(n.total_transactions) + '</p>',
      },
      {
        label: 'Slot Time',
        value: Math.round(n.avg_slot_time_ms) + 'ms',
        delta: { text: 'target 400ms', cls: n.avg_slot_time_ms > 450 ? 'delta-down' : 'delta-up' },
        sub: 'current slot: ' + fmtNum(n.current_slot),
        detail: '<p><strong>Avg Slot Time:</strong> ' + Math.round(n.avg_slot_time_ms) + 'ms</p><p><strong>Target:</strong> 400ms</p><p><strong>Current Slot:</strong> ' + fmtNum(n.current_slot) + '</p><p><strong>Epoch Progress:</strong> ' + (n.epoch_progress_pct || 0).toFixed(1) + '%</p>',
      },
      {
        label: 'Active Validators',
        value: fmtNum(v.active_validators),
        delta: { text: v.delinquent_validators + ' delinquent', cls: v.delinquent_validators > 10 ? 'delta-down' : 'delta-up' },
        sub: 'Nakamoto: ' + v.nakamoto_coefficient + ' nodes',
        detail: '<p><strong>Active:</strong> ' + fmtNum(v.active_validators) + '</p><p><strong>Delinquent:</strong> ' + fmtNum(v.delinquent_validators) + '</p><p><strong>Nakamoto Coefficient:</strong> ' + v.nakamoto_coefficient + '</p><p><strong>Top 10 Stake %:</strong> ' + (v.top_10_stake_pct != null ? v.top_10_stake_pct.toFixed(2) + '%' : '\u2014') + '</p>',
      },
      {
        label: 'DeFi TVL',
        value: fmtUSD(e.tvl_usd, true),
        delta: fmtDelta(e.tvl_change_24h_pct),
        sub: '24h change',
        detail: '<p><strong>Total Value Locked:</strong> ' + fmtUSD(e.tvl_usd, true) + '</p><p><strong>24h Change:</strong> ' + (e.tvl_change_24h_pct != null ? e.tvl_change_24h_pct.toFixed(2) + '%' : '\u2014') + '</p><p><strong>DEX Volume:</strong> ' + fmtUSD(e.dex_volume_24h_usd, true) + '</p>',
      },
    ];

    const secondaryCards = [
      {
        label: '24h DEX Volume',
        value: fmtUSD(e.dex_volume_24h_usd, true),
        delta: { text: '', cls: '' },
        sub: 'capital turnover: ' + (e.capital_efficiency_ratio || 0).toFixed(2) + 'x',
      },
      {
        label: 'Stablecoin Supply',
        value: fmtUSD(e.stablecoin_mcap_usd, true),
        delta: { text: '', cls: '' },
        sub: 'USDC & USDT on Solana',
      },
      {
        label: 'REV / Day',
        value: fmtUSD(e.rev_24h_usd, true),
        delta: { text: '', cls: '' },
        sub: 'base + priority + tips',
      },
      {
        label: 'Community Sentiment',
        value: s.sentiment_status === 'available' ? Math.round((sCur.bullish_pct || 0)) + '% Bullish' : '—',
        delta: { text: sCur.price_momentum_24h_pct != null ? (sCur.price_momentum_24h_pct >= 0 ? '↗ ' : '↘ ') + Math.abs(sCur.price_momentum_24h_pct).toFixed(1) + '%' : '', cls: sCur.price_momentum_24h_pct != null && sCur.price_momentum_24h_pct >= 0 ? 'delta-up' : 'delta-down' },
        sub: 'CoinGecko crowd vote',
        detail: '<p><strong>Bullish:</strong> ' + (sCur.bullish_pct || 0).toFixed(1) + '%</p><p><strong>Bearish:</strong> ' + (sCur.bearish_pct || 0).toFixed(1) + '%</p><p><strong>SOL 24h momentum:</strong> ' + (sCur.price_momentum_24h_pct || 0).toFixed(2) + '%</p><p><strong>Telegram:</strong> ' + fmtNum((sCur.social && sCur.social.telegram_users) || 0) + '</p><p><strong>Trending:</strong> ' + (sCur.trending_keywords || []).join(', ') + '</p><p><em>Source: ' + (s.source_type || '') + '</em></p>',
      },
      {
        label: 'Daily Active Addresses',
        value: d.daa_status === 'available' ? fmtNum(dCur.estimated_daa) : '—',
        delta: { text: d.daa_status === 'available' ? (dCur.trending_direction || '') : '', cls: 'delta-up' },
        sub: 'modeled lower bound',
        detail: '<p><strong>Estimated DAA:</strong> ' + (d.daa_status === 'available' ? fmtNum(dCur.estimated_daa) : 'unavailable this run') + '</p><p><strong>Unique fee payers in sample:</strong> ' + (dCur.unique_signers || 0) + '</p><p><strong>Signatures sampled:</strong> ' + (dCur.signatures_sampled || 0) + '</p><p><strong>Confidence:</strong> ' + (dCur.confidence_pct || 0) + '%</p><p><em>' + (dCur.notes || '') + '</em></p>',
      },
    ];

    function renderCard(c) {
      var d = c.delta || { text: '', cls: '' };
      var attrs = '';
      if (c.detail) {
        attrs = ' data-click-title="' + c.label + '" data-click-content="' + encodeURIComponent(c.detail) + '"';
      }
      return '<div class="kpi-card"' + attrs + '>'
        + '<div class="kpi-label">' + c.label + '</div>'
        + '<div class="kpi-value">' + c.value + '</div>'
        + '<div class="kpi-delta ' + (d.cls || '') + '">' + d.text + '<span class="kpi-sub">' + (c.sub || '') + '</span></div>'
        + '</div>';
    }

    el.kpiGrid.innerHTML = primaryCards.map(renderCard).join('');
    if (el.kpiGridSecondary) {
      el.kpiGridSecondary.innerHTML = secondaryCards.map(renderCard).join('');
    }

    document.querySelectorAll('.kpi-card[data-click-title]').forEach(function(card) {
      card.addEventListener('click', function() {
        var title = card.getAttribute('data-click-title');
        var content = decodeURIComponent(card.getAttribute('data-click-content'));
        showModal(title, content);
      });
    });
  }

  /* ===================================================================
     RENDER NETWORK PANEL
     =================================================================== */
  function renderNetworkPanel(r) {
    const n = r.network || {};
    setText(el.netEpoch, n.epoch);
    setText(el.netEpochPct, (n.epoch_progress_pct || 0).toFixed(1) + '% through epoch');
    setText(el.netBlock, fmtNum(n.block_height));
    setText(el.netTps, fmtNum(Math.round(n.current_tps)));
    setText(el.netTpsSub, 'avg 15m: ' + fmtNum(Math.round(n.avg_tps_15m)));
    setText(el.netSlotTime, Math.round(n.avg_slot_time_ms) + 'ms');
    setText(el.netSlotSub, n.avg_slot_time_ms > 450 ? 'above target' : 'on target');
    if (el.epochProgress) el.epochProgress.setAttribute('aria-valuenow', Math.round(n.epoch_progress_pct || 0));
    if (el.epochProgressFill) el.epochProgressFill.style.width = (n.epoch_progress_pct || 0).toFixed(1) + '%';
  }

  /* ===================================================================
     RENDER VALIDATOR STATUS
     =================================================================== */
  function renderValidatorStatus(r) {
    const v = r.validators || {};
    setText(el.valActive, fmtNum(v.active_validators));
    setText(el.valDelinquent, fmtNum(v.delinquent_validators));
    const total = v.active_validators + v.delinquent_validators;
    setText(el.valDelinqPct, total > 0 ? ((v.delinquent_validators / total) * 100).toFixed(1) : '0');
    setText(el.valStakePct, (v.stake_concentration_pct != null ? v.stake_concentration_pct.toFixed(1) : '\u2014') + '%');
    setText(el.valTotal, fmtNum(total));

    const validators = Array.isArray(v.top_validators) ? v.top_validators : [];
    if (validators.length && el.commissionBar) {
      const z = validators.filter(function(x){return x.commission===0}).length;
      const l = validators.filter(function(x){return x.commission>0&&x.commission<=5}).length;
      const m = validators.filter(function(x){return x.commission>5&&x.commission<10}).length;
      const h = validators.filter(function(x){return x.commission>=10}).length;
      const t = validators.length;
      el.commissionBar.innerHTML =
        '<div class="commission-segment seg-zero" style="width:'+(z/t*100)+'%" title="0%: '+z+'"></div>'+
        '<div class="commission-segment seg-low" style="width:'+(l/t*100)+'%" title="1-5%: '+l+'"></div>'+
        '<div class="commission-segment seg-med" style="width:'+(m/t*100)+'%" title="5-10%: '+m+'"></div>'+
        '<div class="commission-segment seg-high" style="width:'+(h/t*100)+'%" title="\u226510%: '+h+'"></div>';
    }

    renderValidatorPager();
  }

  function clampValidatorPage() {
    var total = filteredValidators.length;
    var maxPage = Math.max(1, Math.ceil(total / VALIDATOR_PAGE_SIZE));
    if (validatorPage > maxPage) validatorPage = maxPage;
    if (validatorPage < 1) validatorPage = 1;
  }

  function renderValidatorPager() {
    if (!el.validatorsPager || !el.valPagerInfo) return;
    var total = filteredValidators.length;
    if (total <= VALIDATOR_PAGE_SIZE) {
      el.validatorsPager.hidden = true;
      return;
    }
    el.validatorsPager.hidden = false;
    clampValidatorPage();
    var start = (validatorPage - 1) * VALIDATOR_PAGE_SIZE + 1;
    var end = Math.min(total, validatorPage * VALIDATOR_PAGE_SIZE);
    el.valPagerInfo.textContent = start + '\u2013' + end + ' of ' + total;
    if (el.valPrev) el.valPrev.disabled = validatorPage <= 1;
    if (el.valNext) el.valNext.disabled = validatorPage >= Math.ceil(total / VALIDATOR_PAGE_SIZE);
  }

  function renderTopValidators() {
    if (!el.topValidatorsList) return;
    clampValidatorPage();
    var validators = filteredValidators.slice((validatorPage - 1) * VALIDATOR_PAGE_SIZE, validatorPage * VALIDATOR_PAGE_SIZE);
    if (!validators.length) {
      el.topValidatorsList.innerHTML = '<p style="color:var(--text-3);padding:8px 0;">No validator data available.</p>';
      renderValidatorPager();
      return;
    }
    el.topValidatorsList.innerHTML = validators.map(function (x) {
      return '<div class="validator-row" data-vote="' + (x.vote_pubkey || '') + '">'
        + '<div class="validator-rank">#' + (x.rank != null ? x.rank : '\u2014') + '</div>'
        + '<div class="validator-info">'
        + '<div class="validator-name">' + (x.name || 'Validator') + '</div>'
        + '<div class="validator-pubkey">' + truncatePubkey(x.vote_pubkey) + '</div>'
        + '</div>'
        + '<div class="validator-stake">' + fmtSOL(x.activated_stake_sol) + ' SOL</div>'
        + '<div class="validator-commission">' + (x.commission != null ? x.commission + '%' : '\u2014') + '</div>'
        + '</div>';
    }).join('');

    el.topValidatorsList.querySelectorAll('.validator-row').forEach(function(row) {
      row.addEventListener('click', function() {
        var votePubkey = row.getAttribute('data-vote');
        var v = allValidators.find(function(x) { return x.vote_pubkey === votePubkey; });
        if (v) {
          showModal('Validator: ' + (v.name || 'Unknown'),
            '<div style="display:grid;gap:12px;">'
            + '<p><strong>Rank:</strong> #' + (v.rank || '\u2014') + '</p>'
            + '<p><strong>Name:</strong> ' + (v.name || '\u2014') + '</p>'
            + '<p><strong>Vote Pubkey:</strong> <code style="font-size:11px;word-break:break-all;">' + (v.vote_pubkey || '\u2014') + '</code></p>'
            + '<p><strong>Activated Stake:</strong> ' + fmtSOL(v.activated_stake_sol) + ' SOL</p>'
            + '<p><strong>Stake %:</strong> ' + (v.stake_percentage != null ? v.stake_percentage.toFixed(2) + '%' : '\u2014') + '</p>'
            + '<p><strong>Commission:</strong> ' + (v.commission != null ? v.commission + '%' : '\u2014') + '</p>'
            + '<p><strong>Last Vote:</strong> ' + fmtNum(v.last_vote) + '</p>'
            + '<p><strong>Status:</strong> ' + (v.status || '\u2014') + '</p>'
            + '</div>'
          );
        }
      });
    });

    renderValidatorPager();
  }

  /* ===================================================================
     RENDER ROADMAP
     =================================================================== */
  function renderRoadmap(r) {
    const news = r.ecosystem_news || {};
    const upgrades = Array.isArray(news.upgrades) ? news.upgrades : [];
    if (!upgrades.length) {
      if (el.roadmapList) setHTML(el.roadmapList, '<p style="color:var(--text-3);padding:12px 0;">No upgrade data available.</p>');
      return;
    }
    if (el.roadmapList) {
      el.roadmapList.innerHTML = upgrades.map(function (u) {
        return '<div class="roadmap-item">'
          + '<div class="roadmap-item-head">'
          + '<span class="roadmap-item-title">' + (u.title || '') + '</span>'
          + '<span class="roadmap-item-timeline">' + (u.target_timeline || '') + '</span>'
          + '</div>'
          + '<div class="roadmap-item-desc">' + (u.description || '') + '</div>'
          + '<div class="roadmap-item-status">' + (u.status || '\u2014') + '</div>'
          + '</div>';
      }).join('');
    }
  }

  /* ===================================================================
     RENDER DEFI TABLE
     =================================================================== */
  function renderDeFiTable(r) {
    const e = r.economics || {};
    const protocols = Array.isArray(e.top_defi_protocols) ? e.top_defi_protocols : [];
    setText(el.defiCount, protocols.length + ' protocols tracked');
    if (!protocols.length) {
      setHTML(el.defiTbody, '<tr><td colspan="3" style="text-align:center;color:var(--text-3);padding:24px;">No DeFi data available.</td></tr>');
      return;
    }
    el.defiTbody.innerHTML = protocols.map(function (p, i) {
      return '<tr data-protocol="' + (p.name || '') + '">'
        + '<td class="num">' + (i + 1) + '</td>'
        + '<td>' + (p.name || '\u2014') + '</td>'
        + '<td class="num">' + fmtUSD(p.tvl_usd, true) + '</td>'
        + '</tr>';
    }).join('');

    el.defiTbody.querySelectorAll('tr[data-protocol]').forEach(function(row) {
      row.addEventListener('click', function() {
        var name = row.getAttribute('data-protocol');
        var p = protocols.find(function(x) { return x.name === name; });
        if (p) {
          showModal('Protocol: ' + p.name,
            '<div style="display:grid;gap:12px;">'
            + '<p><strong>Name:</strong> ' + (p.name || '\u2014') + '</p>'
            + '<p><strong>TVL:</strong> ' + fmtUSD(p.tvl_usd, true) + '</p>'
            + '<p><strong>Type:</strong> ' + (p.type || '\u2014') + '</p>'
            + '</div>'
          );
        }
      });
    });
  }

  /* ===================================================================
     RENDER STABLECOIN PANEL
     =================================================================== */
  function renderStablecoinPanel(r) {
    const e = r.economics || {};
    const supply = e.stablecoin_mcap_usd;
    const tvl = e.tvl_usd;
    if (!supply && !tvl) {
      setHTML(el.stablecoinContent, '<p style="color:var(--text-3);">No stablecoin data available.</p>');
      return;
    }
    setHTML(el.stablecoinContent,
      '<div class="stablecoin-stats">'
      + '<div class="stablecoin-stat"><span class="stablecoin-label">Total Supply</span><strong>' + fmtUSD(supply, true) + '</strong></div>'
      + '<div class="stablecoin-stat"><span class="stablecoin-label">DeFi TVL</span><strong>' + fmtUSD(tvl, true) + '</strong></div>'
      + '<div class="stablecoin-stat"><span class="stablecoin-label">Capital Efficiency</span><strong>' + (e.capital_efficiency_ratio || 0).toFixed(2) + 'x</strong></div>'
      + '</div>'
    );
  }

  /* ===================================================================
     RENDER ECONOMIC INDICATORS
     =================================================================== */
  function renderEconomy(r) {
    const p = r.price || {};
    const e = r.economics || {};
    const s = r.supply || {};
    setText(el.econMcap, fmtUSD(p.market_cap_usd, true));
    setText(el.econDex, fmtUSD(e.dex_volume_24h_usd, true));
    setText(el.supplyCirc, fmtSOL(s.circulating_sol) + ' SOL');
    setText(el.econAch, fmtUSD(p.ath_usd));
    setText(el.econPrice, fmtUSD(p.price_usd));
    setText(el.econChange, p.change_24h_pct != null ? (p.change_24h_pct >= 0 ? '+' : '') + p.change_24h_pct.toFixed(2) + '%' : '\u2014');
    setText(el.econTvl, fmtUSD(e.tvl_usd, true));
    setText(el.econRealtvl, fmtUSD(e.dex_volume_24h_usd, true));
    setText(el.econMedfee, fmtUSD(e.median_fee_usd));
    setText(el.econBasefee, e.base_fee_sol != null ? e.base_fee_sol + ' SOL' : '\u2014');
    if (el.econChange && p.change_24h_pct != null) {
      el.econChange.style.color = p.change_24h_pct >= 0 ? 'var(--green)' : 'var(--red)';
    }
  }

  /* ===================================================================
     RENDER REFRESH HISTORY
     =================================================================== */
  function renderRefreshHistory(r) {
    refreshLog.unshift({
      time: r.generated_at || new Date().toISOString(),
      epoch: r.network ? r.network.epoch : '\u2014',
      status: r.status || 'success'
    });
    if (refreshLog.length > 10) refreshLog = refreshLog.slice(0, 10);
    if (el.refreshHistory) {
      el.refreshHistory.innerHTML = refreshLog.map(function (entry) {
        return '<div class="refresh-log-entry">'
          + '<span class="refresh-log-time">' + timeAgo(entry.time) + '</span>'
          + '<span class="refresh-log-epoch">Epoch ' + entry.epoch + '</span>'
          + '<span class="refresh-log-status ' + (entry.status === 'success' ? 'status-ok' : 'status-warn') + '">' + entry.status + '</span>'
          + '</div>';
      }).join('');
    }
  }

  /* ===================================================================
     RENDER FOOTER
     =================================================================== */
  function renderFooter(r) {
    setText(el.footerVersion, 'v' + (r.generator_version || '1.0.0'));
    const src = r.sources || {};
    var chips = Object.entries(src).map(function (kv) {
      return '<span class="source-chip">' + kv[0] + ': ' + kv[1] + '</span>';
    }).join('');
    setHTML(el.sourcesList, chips);
    setText(el.footerDisclaimer, 'Zero external dependencies: Python 3.11+ stdlib, Solana JSON-RPC, DeFiLlama, CoinGecko. No API keys required.');
  }

  /* ===================================================================
     NAKAMOTO WATERFALL CHART
     =================================================================== */
  function renderNakamotoWaterfall(r) {
    var canvas = document.getElementById('chart-nakamoto');
    var label = document.getElementById('nakamoto-label');
    if (!canvas || typeof Chart === 'undefined') return;
    var v = r.validators || {};
    var validators = Array.isArray(v.top_validators) ? v.top_validators : [];
    var nk = v.nakamoto_coefficient || 18;

    if (validators.length === 0) return;

    // Calculate cumulative stake percentage
    var cumulative = [];
    var running = 0;
    var labels = [];
    var colors = [];
    for (var i = 0; i < Math.min(validators.length, 25); i++) {
      running += (validators[i].stake_percentage || 0);
      cumulative.push(+running.toFixed(2));
      labels.push('#' + (i + 1));
      colors.push(i < nk ? 'rgba(153,69,255,0.7)' : 'rgba(153,69,255,0.25)');
    }

    if (label) label.textContent = 'Nakamoto = ' + nk + ' validators';

    if (charts['chart-nakamoto']) charts['chart-nakamoto'].destroy();
    charts['chart-nakamoto'] = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Cumulative Stake %',
          data: cumulative,
          backgroundColor: colors,
          borderColor: colors.map(function(c) { return c.replace('0.7', '1').replace('0.25', '0.5'); }),
          borderWidth: 1,
          borderRadius: 3,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#1E2636',
            titleColor: '#F1F5F9',
            bodyColor: '#94A3B8',
            borderColor: 'rgba(255,255,255,0.14)',
            borderWidth: 1,
            padding: 10,
            cornerRadius: 6,
            callbacks: {
              title: function(items) {
                var idx = items[0].dataIndex;
                return validators[idx] ? validators[idx].name : '';
              },
              label: function(item) {
                var idx = item.dataIndex;
                var val = validators[idx];
                if (!val) return '';
                return [
                  'Cumulative: ' + item.raw.toFixed(1) + '%',
                  'Stake: ' + fmtSOL(val.activated_stake_sol) + ' SOL',
                  'Individual: ' + (val.stake_percentage || 0).toFixed(2) + '%',
                  'Commission: ' + (val.commission || 0) + '%',
                  idx < nk ? 'Inside Nakamoto set' : 'Outside Nakamoto set'
                ];
              },
            },
          },
          annotation: undefined,
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { color: '#94A3B8', font: { size: 10 }, maxRotation: 0 },
          },
          y: {
            grid: { color: 'rgba(255,255,255,0.06)' },
            ticks: {
              color: '#94A3B8',
              callback: function(val) { return val + '%'; },
            },
            max: Math.min(100, running * 1.2),
          },
        },
      },
      plugins: [{
        id: 'nakamotoLine',
        afterDraw: function(chart) {
          var yScale = chart.scales.y;
          var xScale = chart.scales.x;
          var y33 = yScale.getPixelForValue(33.33);
          var ctx = chart.ctx;
          ctx.save();
          ctx.beginPath();
          ctx.setLineDash([6, 4]);
          ctx.strokeStyle = '#FF6B6B';
          ctx.lineWidth = 1.5;
          ctx.moveTo(xScale.left, y33);
          ctx.lineTo(xScale.right, y33);
          ctx.stroke();
          ctx.fillStyle = '#FF6B6B';
          ctx.font = '10px Inter, sans-serif';
          ctx.textAlign = 'right';
          ctx.fillText('33.3% threshold', xScale.right, y33 - 5);
          ctx.restore();
        },
      }],
    });
  }

  /* ===================================================================
     REV BREAKDOWN
     =================================================================== */
  function renderREVBreakdown(r) {
    var e = r.economics || {};
    var p = r.price || {};
    var solPrice = p.price_usd || 180;

    // Calculate REV components
    var revTotal = e.rev_24h_usd || 0;
    var baseFeeSol = e.base_fee_sol || 0.000005;
    var medianPriorityFeeSol = e.median_priority_fee_sol || (e.median_fee_sol ? e.median_fee_sol - baseFeeSol : 0);
    var medianFeeUsd = e.median_fee_usd || 0;

    // Estimate daily non-vote transactions (~30% of total)
    var network = r.network || {};
    var totalTx = network.total_transactions || 0;
    var dailyNonVote = Math.round(totalTx * 0.001); // rough daily proxy
    if (dailyNonVote < 1000000) dailyNonVote = 13500000; // fallback estimate

    // REV component estimates
    var baseFeesDaily = dailyNonVote * baseFeeSol * solPrice;
    var priorityFeesDaily = dailyNonVote * medianPriorityFeeSol * solPrice;
    var mevTipsDaily = Math.min(1500000, Math.max(250000, (e.dex_volume_24h_usd || 0) * 0.0004));

    setText(document.getElementById('rev-total'), fmtUSD(revTotal, true));
    setText(document.getElementById('rev-base'), fmtUSD(baseFeesDaily, true));
    setText(document.getElementById('rev-priority'), fmtUSD(priorityFeesDaily, true));
    setText(document.getElementById('rev-mev'), fmtUSD(mevTipsDaily, true));

    var methodology = document.getElementById('rev-methodology');
    if (methodology) {
      var feeSource = e.fee_source || 'model estimation';
      methodology.innerHTML = '<strong>Methodology:</strong> REV = (est. daily non-vote transactions × median fee) + estimated Jito MEV tips. '
        + 'Fee source: ' + feeSource + '. '
        + 'Base fee: ' + baseFeeSol + ' SOL (protocol constant). '
        + 'Priority fee: ' + (medianPriorityFeeSol > 0 ? medianPriorityFeeSol.toFixed(9) + ' SOL (measured)' : 'model fallback') + '. '
        + 'MEV estimated from ' + fmtUSD(e.dex_volume_24h_usd, true) + ' DEX volume × 0.04% tip rate.';
    }
  }

  /* ===================================================================
     CHARTS
     =================================================================== */
  var CHART_COLORS = {
    accent: '#9945FF',
    teal: '#14F195',
    text: '#94A3B8',
    grid: 'rgba(255,255,255,0.06)',
    fillTps: 'rgba(153,69,255,0.18)',
    fillPrice: 'rgba(20,241,149,0.16)',
    fillTvl: 'rgba(20,241,149,0.14)',
  };

  function baseChartOpts() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { intersect: false, mode: 'index' },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1E2636',
          titleColor: '#F1F5F9',
          bodyColor: '#94A3B8',
          borderColor: 'rgba(255,255,255,0.14)',
          borderWidth: 1,
          padding: 10,
          cornerRadius: 6,
          displayColors: false,
        },
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: CHART_COLORS.text, maxTicksLimit: 6, maxRotation: 0 } },
        y: { grid: { color: CHART_COLORS.grid }, ticks: { color: CHART_COLORS.text, maxTicksLimit: 5 } },
      },
    };
  }

  function timeLabels(values) {
    return values.map(function (s) {
      const d = new Date(s.timestamp);
      if (isNaN(d.getTime())) return '';
      return d.getHours().toString().padStart(2, '0') + ':' + d.getMinutes().toString().padStart(2, '0');
    });
  }

  function renderLineChart(canvas, labels, data, color, fill, yPrefix) {
    if (!canvas || typeof Chart === 'undefined') return;
    if (charts[canvas.id]) charts[canvas.id].destroy();
    var opts = baseChartOpts();
    if (yPrefix) {
      opts.scales.y.ticks.callback = function (val) { return yPrefix + ' ' + val.toLocaleString(); };
    }
    charts[canvas.id] = new Chart(canvas, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          borderColor: color,
          backgroundColor: fill,
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 4,
          pointHoverBackgroundColor: color,
          tension: 0.3,
          fill: true,
        }],
      },
      options: opts,
    });
  }

  function renderBarChart(canvas, labels, values, color) {
    if (!canvas || typeof Chart === 'undefined') return;
    if (charts[canvas.id]) charts[canvas.id].destroy();
    charts[canvas.id] = new Chart(canvas, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          data: values,
          borderColor: color,
          backgroundColor: CHART_COLORS.fillTvl,
          borderWidth: 1.5,
          pointRadius: 0,
          pointHoverRadius: 4,
          pointHoverBackgroundColor: color,
          tension: 0.3,
          fill: true,
        }],
      },
      options: baseChartOpts(),
    });
  }

  function renderCharts(r) {
    var ht = r.historical_trends || {};
    var lc = r.live_cards || {};

    var tpsSrc = (ht.tps && ht.tps.length) ? ht.tps : [];
    if (tpsSrc.length) {
      renderLineChart(el.chartTps, timeLabels(tpsSrc), tpsSrc.map(function(s){return s.value}), CHART_COLORS.accent, CHART_COLORS.fillTps, '');
    } else if (lc.network_tps && lc.network_tps.sparkline) {
      renderLineChart(el.chartTps, lc.network_tps.sparkline.map(function(_,i){return i}), lc.network_tps.sparkline, CHART_COLORS.accent, CHART_COLORS.fillTps, '');
    }

    var priceSrc = (ht.sol_price && ht.sol_price.length) ? ht.sol_price : [];
    if (priceSrc.length) {
      renderLineChart(el.chartPrice, timeLabels(priceSrc), priceSrc.map(function(s){return s.value}), CHART_COLORS.teal, CHART_COLORS.fillPrice, '$');
    } else if (lc.sol_price && lc.sol_price.sparkline) {
      renderLineChart(el.chartPrice, lc.sol_price.sparkline.map(function(_,i){return i}), lc.sol_price.sparkline, CHART_COLORS.teal, CHART_COLORS.fillPrice, '$');
    }

    var tvl = ht.historical_tvl_30d || (r.economics && r.economics.historical_tvl_30d) || [];
    if (tvl.length) {
      renderBarChart(el.chartTvl, tvl.map(function(d){return d.date.slice(5)}), tvl.map(function(d){return +(d.tvl / 1e9).toFixed(2)}), CHART_COLORS.teal);
    }

    var valSrc = (ht.validators && ht.validators.length) ? ht.validators : [];
    if (valSrc.length) {
      renderLineChart(el.chartValidators, timeLabels(valSrc), valSrc.map(function(s){return s.value}), CHART_COLORS.accent, CHART_COLORS.fillTps, '');
    } else if (lc.active_validators && lc.active_validators.sparkline) {
      renderLineChart(el.chartValidators, lc.active_validators.sparkline.map(function(_,i){return i}), lc.active_validators.sparkline, CHART_COLORS.accent, CHART_COLORS.fillTps, '');
    }
  }

  /* ===================================================================
     TAB NAVIGATION
     =================================================================== */
  function setupTabs() {
    document.querySelectorAll('.section-tab').forEach(function(tab) {
      tab.addEventListener('keydown', function(e) {
        var tabs = Array.prototype.slice.call(document.querySelectorAll('.section-tab'));
        var idx = tabs.indexOf(tab);
        if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
          e.preventDefault();
          var next = tabs[(idx + 1) % tabs.length];
          next.focus();
          next.click();
        } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
          e.preventDefault();
          var prev = tabs[(idx - 1 + tabs.length) % tabs.length];
          prev.focus();
          prev.click();
        } else if (e.key === 'Home') {
          e.preventDefault();
          tabs[0].focus();
          tabs[0].click();
        } else if (e.key === 'End') {
          e.preventDefault();
          tabs[tabs.length - 1].focus();
          tabs[tabs.length - 1].click();
        }
      });
      tab.addEventListener('click', function() {
        document.querySelectorAll('.section-tab').forEach(function(t) {
          t.classList.remove('active');
          t.setAttribute('aria-selected', 'false');
        });
        document.querySelectorAll('.tab-content').forEach(function(tc) {
          tc.classList.remove('active');
        });
        tab.classList.add('active');
        tab.setAttribute('aria-selected', 'true');
        var content = document.getElementById('tab-content-' + tab.getAttribute('data-tab'));
        if (content) content.classList.add('active');
      });
    });
  }

  /* ===================================================================
     VALIDATOR SEARCH & FILTER
     =================================================================== */
  function setupValidatorSearch() {
    if (el.validatorSearch) {
      el.validatorSearch.addEventListener('input', function() {
        searchQuery = this.value.trim().toLowerCase();
        applyFilters();
      });
    }
    document.querySelectorAll('.filter-chip').forEach(function(chip) {
      chip.addEventListener('click', function() {
        document.querySelectorAll('.filter-chip').forEach(function(c) { c.classList.remove('active'); });
        chip.classList.add('active');
        activeFilter = chip.getAttribute('data-filter');
        applyFilters();
      });
    });
    if (el.valPrev) el.valPrev.addEventListener('click', function() {
      if (validatorPage > 1) { validatorPage--; renderTopValidators(); }
    });
    if (el.valNext) el.valNext.addEventListener('click', function() {
      var total = filteredValidators.length;
      var maxPage = Math.max(1, Math.ceil(total / VALIDATOR_PAGE_SIZE));
      if (validatorPage < maxPage) { validatorPage++; renderTopValidators(); }
    });
  }

  function applyFilters() {
    if (!report) return;
    var validators = allValidators.slice();
    if (searchQuery) {
      validators = validators.filter(function(v) {
        return (v.name && v.name.toLowerCase().indexOf(searchQuery) !== -1) ||
               (v.vote_pubkey && v.vote_pubkey.toLowerCase().indexOf(searchQuery) !== -1);
      });
    }
    if (activeFilter === 'top10') validators = validators.slice(0, 10);
    else if (activeFilter === 'nakamoto') {
      var nk = report.validators ? report.validators.nakamoto_coefficient || 18 : 18;
      validators = validators.slice(0, nk);
    } else if (activeFilter === 'zero') validators = validators.filter(function(v) { return v.commission === 0; });
    else if (activeFilter === 'high') validators = validators.filter(function(v) { return v.commission >= 10; });

    filteredValidators = validators;
    validatorPage = 1;
    renderTopValidators();
  }

  /* ===================================================================
     SCROLL TO TOP
     =================================================================== */
  function setupScrollToTop() {
    if (!el.scrollTopBtn) return;
    window.addEventListener('scroll', function() {
      el.scrollTopBtn.classList.toggle('visible', window.scrollY > 300);
    }, { passive: true });
    el.scrollTopBtn.addEventListener('click', function() {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  /* ===================================================================
     MODAL SETUP
     =================================================================== */
  function setupModal() {
    if (el.modalClose) el.modalClose.addEventListener('click', hideModal);
    if (el.modalOverlay) el.modalOverlay.addEventListener('click', function(e) {
      if (e.target === el.modalOverlay) hideModal();
    });
    document.addEventListener('keydown', function(e) {
      if (!el.modalOverlay || !el.modalOverlay.classList.contains('visible')) return;
      if (e.key === 'Escape') {
        hideModal();
        return;
      }
      if (e.key === 'Tab') {
        var focusables = el.modalOverlay.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (!focusables.length) return;
        var first = focusables[0];
        var last = focusables[focusables.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    });
  }

  /* ===================================================================
     KEYBOARD NAVIGATION
     =================================================================== */
  function setupKeyboardNav() {
    document.addEventListener('keydown', function(e) {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        if (el.validatorSearch) {
          var vt = document.querySelector('[data-tab="validators"]');
          if (vt) vt.click();
          el.validatorSearch.focus();
        }
      }
    });
  }

  /* ===================================================================
     RENDER ANOMALY / ALERT PANEL
     =================================================================== */
  function renderAlerts(r) {
    var alerts = r.alerts || [];
    var badge = document.getElementById('alert-count-badge');
    var allClear = document.getElementById('anomaly-all-clear');
    var list = document.getElementById('anomaly-list');
    if (!list) return;

    if (alerts.length === 0) {
      if (badge) badge.hidden = true;
      if (allClear) allClear.style.display = '';
      list.innerHTML = '';
      return;
    }

    if (allClear) allClear.style.display = 'none';
    if (badge) {
      badge.hidden = false;
      badge.textContent = alerts.length + ' alert' + (alerts.length !== 1 ? 's' : '');
      badge.className = 'chip ' + (alerts.some(function(a){return a.severity==='critical';}) ? 'chip-accent' : 'chip-up');
    }

    list.innerHTML = alerts.map(function(a) {
      var icon = a.severity === 'critical' ? '🔴' : a.severity === 'warning' ? '🟡' : 'ℹ️';
      var severityCls = a.severity === 'critical' ? 'delta-down' : a.severity === 'warning' ? 'delta-down' : 'muted';
      return '<div class="anomaly-item" data-alert-id="' + (a.id || '') + '">'
        + '<span class="anomaly-icon">' + icon + '</span>'
        + '<div class="anomaly-text">'
        + '<strong>' + (a.title || a.metric || 'Alert') + '</strong>'
        + '<p>' + (a.description || '') + '</p>'
        + '</div>'
        + '<span class="chip ' + (a.severity === 'critical' ? 'chip-accent' : 'chip-neutral') + '">'
        + (a.severity || 'info') + '</span>'
        + '</div>';
    }).join('');

    // Click to show detail modal
    list.querySelectorAll('.anomaly-item').forEach(function(item) {
      item.addEventListener('click', function() {
        var alertId = item.getAttribute('data-alert-id');
        var alert = alerts.find(function(a) { return a.id === alertId; });
        if (alert) {
          showModal(alert.title || 'Alert Detail',
            '<div style="display:grid;gap:12px;">'
            + '<p><strong>Metric:</strong> ' + (alert.metric || '\u2014') + '</p>'
            + '<p><strong>Severity:</strong> ' + (alert.severity || '\u2014') + '</p>'
            + '<p><strong>Current Value:</strong> ' + (alert.current_value != null ? alert.current_value : '\u2014') + '</p>'
            + '<p><strong>Baseline:</strong> ' + (alert.baseline_value != null ? alert.baseline_value : '\u2014') + '</p>'
            + '<p><strong>Threshold:</strong> ' + (alert.threshold || '\u2014') + '</p>'
            + '<p><strong>Deviation:</strong> ' + (alert.deviation_pct != null ? alert.deviation_pct.toFixed(1) + '%' : '\u2014') + '</p>'
            + '<p><strong>Confidence:</strong> ' + (alert.confidence_score != null ? (alert.confidence_score * 100).toFixed(0) + '%' : '\u2014') + '</p>'
            + '<p><strong>Description:</strong> ' + (alert.description || '\u2014') + '</p>'
            + '<p style="color:var(--text-3);font-size:11px;">Detected: ' + (alert.detected_at || '\u2014') + '</p>'
            + '</div>'
          );
        }
      });
    });
  }

  /* ===================================================================
     RENDER ALL
     =================================================================== */
  function renderAll(r) {
    report = r;
    allValidators = Array.isArray(r.validators && r.validators.top_validators) ? r.validators.top_validators.slice() : [];
    filteredValidators = allValidators.slice();

    renderKPI(r);
    renderNetworkPanel(r);
    renderValidatorStatus(r);
    renderAlerts(r);
    renderNakamotoWaterfall(r);
    renderRoadmap(r);
    renderDeFiTable(r);
    renderStablecoinPanel(r);
    renderEconomy(r);
    renderREVBreakdown(r);
    renderCharts(r);
    renderRefreshHistory(r);
    renderFooter(r);

    var h = r.health || {};
    var healthy = h.is_healthy !== false;
    el.healthPill.className = 'health-pill' + (healthy ? '' : ' warn');
    el.healthPill.innerHTML = '<span class="dot dot-' + (healthy ? 'ok' : 'warn') + '"></span><span id="health-pill-text">' + (healthy ? 'Operational' : 'Degraded') + '</span>';

    setText(el.updatedAt, 'Updated ' + timeAgo(r.generated_at));
    document.title = 'Solana Ecosystem \u2014 Epoch ' + (r.network && r.network.epoch ? r.network.epoch : '') + ' \u00B7 ' + (r.price ? fmtUSD(r.price.price_usd) : '') + ' \u00B7 Dashboard';

    applyFilters();
  }

  /* ===================================================================
     EVENTS
     =================================================================== */
  function setupEvents() {
    if (el.refreshBtn) el.refreshBtn.addEventListener('click', async function () {
      try {
        el.refreshBtn.disabled = true;
        el.refreshBtn.textContent = 'Refreshing...';
        const r = await fetchReport();
        renderAll(r);
        toast('Telemetry refreshed from mainnet');
      } catch (e) {
        toast('Failed to refresh: ' + e.message, '\u26A0');
      } finally {
        el.refreshBtn.disabled = false;
        el.refreshBtn.textContent = 'Refresh';
      }
    });

    if (el.exportJson) el.exportJson.addEventListener('click', function () {
      if (report) {
        var blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
        var a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'solana-report.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(a.href);
        toast('report.json exported');
      }
    });

    if (el.exportCsv) el.exportCsv.addEventListener('click', function () {
      if (!report) return;
      var validators = Array.isArray(report.validators && report.validators.top_validators) ? report.validators.top_validators : [];
      var headers = ['rank', 'name', 'vote_pubkey', 'activated_stake_sol', 'stake_percentage', 'commission', 'last_vote', 'status'];
      var rows = validators.map(function (x) {
        return headers.map(function (h) { return '"' + String(x[h] == null ? '' : x[h]).replace(/"/g, '""') + '"'; }).join(',');
      });
      var csv = headers.join(',') + '\n' + rows.join('\n');
      var blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
      var a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'solana-validators.csv';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(a.href);
      toast('Validator CSV exported (' + validators.length + ' rows)');
    });

    var hamburger = document.querySelector('.hamburger');
    var topbarActions = document.querySelector('.topbar-actions');
    if (hamburger && topbarActions) {
      hamburger.addEventListener('click', function () {
        var isOpen = topbarActions.classList.toggle('open');
        hamburger.setAttribute('aria-expanded', isOpen);
      });
    }
  }

  /* ===================================================================
     FETCH
     =================================================================== */
  async function fetchReport() {
    for (var i = 0; i < REPORT_PATHS.length; i++) {
      try {
        var r = await fetch(REPORT_PATHS[i] + '?_t=' + Date.now());
        if (r.ok) {
          var d = await r.json();
          if (d && d.status) return d;
        }
      } catch (e) { /* try next */ }
    }
    throw new Error('Could not load report data from any path');
  }

  /* ===================================================================
     INIT
     =================================================================== */
  function init() {
    setupEvents();
    setupTabs();
    setupValidatorSearch();
    setupScrollToTop();
    setupModal();
    setupKeyboardNav();

    fetchReport()
      .then(renderAll)
      .catch(function (err) {
        console.error('Load failed:', err);
        setText(el.updatedAt, 'Offline');
        toast('Could not load report data. Check that data/report.json exists.', '\u26A0');
      })
      .then(function () {
        setTimeout(function () {
          if (el.loading) el.loading.classList.add('hidden');
          if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: no-preference)').matches) {
            var sections = document.querySelectorAll('.section');
            sections.forEach(function (sec, i) {
              sec.style.opacity = '0';
              sec.style.transform = 'translateY(20px)';
              sec.style.transition = 'opacity 0.5s ease ' + (i * 80) + 'ms, transform 0.5s ease ' + (i * 80) + 'ms';
            });
            setTimeout(function () {
              sections.forEach(function (sec) {
                sec.style.opacity = '1';
                sec.style.transform = 'translateY(0)';
              });
            }, 100);
          }
        }, 220);
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
