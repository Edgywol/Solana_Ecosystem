/**
 * Solana Ecosystem Intelligence — Clean Dashboard Engine (v2.0)
 * Professional, zero-dependency vanilla JS rendering.
 */
(function () {
  'use strict';

  /* ===================================================================
     STATE
     =================================================================== */
  let report = null;
  let filteredValidators = [];
  let currentPage = 1;
  const PAGE_SIZE = 20;
  let sortKey = 'rank';
  let sortAsc = true;
  let charts = {};

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

    heroTitle: $('hero-title'),
    heroSub: $('hero-sub'),
    heroEyebrow: $('hero-eyebrow'),
    metaEpoch: $('meta-epoch'),
    metaSlot: $('meta-slot'),
    metaHealth: $('meta-health'),
    statusOrb: $('status-orb'),
    statusValue: $('status-value'),
    statusDetail: $('status-detail'),

    kpiGrid: $('kpi-grid'),

    epochPill: $('epoch-pill'),
    progressFill: $('progress-fill'),
    epochSlot: $('epoch-slot'),
    epochIndex: $('epoch-index'),
    epochTotal: $('epoch-total'),
    epochRemaining: $('epoch-remaining'),

    tpsBig: $('tps-big'),
    tpsDeltaChip: $('tps-delta-chip'),
    tpsAvg: $('tps-avg'),
    tpsNonvote: $('tps-nonvote'),
    tpsSlot: $('tps-slot'),
    tpsTx: $('tps-tx'),

    chartTps: $('chart-tps'),
    chartPrice: $('chart-price'),
    chartTvl: $('chart-tvl'),
    chartValidators: $('chart-validators'),
    tpsChartNote: $('tps-chart-note'),
    priceChartNote: $('price-chart-note'),
    tvlChartNote: $('tvl-chart-note'),
    valChartNote: $('val-chart-note'),

    econActive: $('econ-active'),
    econDelinq: $('econ-delinq'),
    econStake: $('econ-stake'),
    econNakamoto: $('econ-nakamoto'),
    econTop10: $('econ-top10'),
    econDelinqStake: $('econ-delinq-stake'),
    stakeFill: $('stake-fill'),
    stakePct: $('stake-pct'),

    supplyTotal: $('supply-total'),
    supplyCirc: $('supply-circ'),
    supplyStaked: $('supply-staked'),
    supplyStakedPct: $('supply-staked-pct'),
    circFill: $('circ-fill'),
    circPct: $('circ-pct'),

    econRev: $('econ-rev'),
    econMedfee: $('econ-medfee'),
    econBasefee: $('econ-basefee'),
    econVelocity: $('econ-velocity'),
    econRevNote: $('econ-rev-note'),

    econTvl: $('econ-tvl'),
    econDex: $('econ-dex'),
    econStables: $('econ-stables'),
    econMcap: $('econ-mcap'),
    econLiquid: $('econ-liquid'),

    valSearch: $('validator-search'),
    valFilter: $('validator-filter'),
    valTbody: $('validator-tbody'),
    valCount: $('validator-count'),
    pageInfo: $('page-info'),
    pagePrev: $('page-prev'),
    pageNext: $('page-next'),
    valTable: $('validator-table'),

    roadmapGrid: $('roadmap-grid'),
    newsGrid: $('news-grid'),
    newsNote: $('news-note'),

    anomalyChip: $('anomaly-chip'),
    anomalyBody: $('anomaly-body'),

    footerVersion: $('footer-version'),
    sourcesList: $('sources-list'),
    footerDisclaimer: $('footer-disclaimer'),

    topnavLinks: document.querySelectorAll('.topnav-link'),
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
    return key.slice(0, start) + '…' + key.slice(-end);
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
     FETCH
     =================================================================== */
  async function fetchReport() {
    for (const path of REPORT_PATHS) {
      try {
        const r = await fetch(path + '?_t=' + Date.now());
        if (r.ok) {
          const d = await r.json();
          if (d && d.status) return d;
        }
      } catch (e) { /* try next */ }
    }
    throw new Error('Could not load report data from any path');
  }

  /* ===================================================================
     TOAST
     =================================================================== */
  function toast(msg, icon) {
    icon = icon || '✓';
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
     RENDER HELPERS
     =================================================================== */
  function setText(el, val) {
    if (el) el.textContent = val || '—';
  }

  function setHTML(el, val) {
    if (el) el.innerHTML = val || '—';
  }

  /* ===================================================================
     RENDER KPI CARDS
     =================================================================== */
  function renderKPI(r) {
    const p = r.price || {};
    const n = r.network || {};
    const v = r.validators || {};
    const e = r.economics || {};

    const cards = [
      {
        label: 'SOL Price',
        value: fmtUSD(p.price_usd),
        delta: fmtDelta(p.change_24h_pct),
        sub: '24h change',
        spark: (r.live_cards && r.live_cards.sol_price && r.live_cards.sol_price.sparkline) || null,
        sparkColor: '#2FE6A2',
      },
      {
        label: 'Network TPS',
        value: fmtNum(Math.round(n.current_tps)),
        delta: fmtDelta((r.live_cards && r.live_cards.network_tps && r.live_cards.network_tps.delta_pct) || 0),
        sub: '15m avg: ' + fmtNum(Math.round(n.avg_tps_15m)),
        spark: (r.live_cards && r.live_cards.network_tps && r.live_cards.network_tps.sparkline) || null,
        sparkColor: '#9945FF',
      },
      {
        label: 'Slot Time',
        value: Math.round(n.avg_slot_time_ms) + 'ms',
        delta: { text: 'target 400ms', cls: n.avg_slot_time_ms > 450 ? 'delta-down' : 'delta-up' },
        sub: 'current slot: ' + fmtNum(n.current_slot),
      },
      {
        label: 'Active Validators',
        value: fmtNum(v.active_validators),
        delta: { text: v.delinquent_validators + ' delinquent', cls: v.delinquent_validators > 10 ? 'delta-down' : 'delta-up' },
        sub: 'Nakamoto: ' + v.nakamoto_coefficient + ' nodes',
        spark: (r.live_cards && r.live_cards.active_validators && r.live_cards.active_validators.sparkline) || null,
        sparkColor: '#14F195',
      },
      {
        label: 'DeFi TVL',
        value: fmtUSD(e.tvl_usd, true),
        delta: fmtDelta(e.tvl_change_24h_pct),
        sub: '24h change',
      },
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
    ];

    el.kpiGrid.innerHTML = cards.map(function (c, i) {
      var d = c.delta || { text: '', cls: '' };
      var sparkHtml = '';
      if (c.spark && c.spark.length > 1) {
        var min = Math.min.apply(null, c.spark);
        var max = Math.max.apply(null, c.spark);
        var range = max - min || 1;
        var pts = c.spark.map(function (s, j) {
          var x = (j / (c.spark.length - 1)) * 100;
          var y = 100 - ((s - min) / range) * 100;
          return x + ',' + y;
        }).join(' ');
        sparkHtml = '<svg class="kpi-spark" viewBox="0 0 100 34" preserveAspectRatio="none" width="100%" height="34">'
          + '<polyline fill="none" stroke="' + c.sparkColor + '" stroke-width="1.5" stroke-linecap="round" stroke-opacity=".85" points="' + pts + '"/>'
          + '<polyline fill="' + c.sparkColor + '" fill-opacity="0.12" stroke="none" points="' + pts + ' 100,34 0,34"/>'
          + '</svg>';
      }
      return '<div class="kpi-card">'
        + '<div class="kpi-label">' + c.label + '</div>'
        + '<div class="kpi-value">' + c.value + '</div>'
        + '<div class="kpi-delta ' + (d.cls || '') + '">' + d.text + '<span class="kpi-sub">' + (c.sub || '') + '</span></div>'
        + (sparkHtml || '') + '</div>';
    }).join('');
  }

  /* ===================================================================
     RENDER EPOCH & NETWORK
     =================================================================== */
  function renderEpoch(r) {
    const n = r.network || {};
    setText(el.epochPill, 'Epoch ' + n.epoch);
    if (el.progressFill) el.progressFill.style.width = (n.epoch_progress_pct || 0) + '%';
    setText(el.epochSlot, fmtNum(n.current_slot));
    setText(el.epochIndex, fmtNum(n.epoch_slot_index));
    setText(el.epochTotal, fmtNum(n.epoch_slots_total));
    setText(el.epochRemaining, (n.epoch_time_remaining_hours || 0).toFixed(1) + 'h');

    setText(el.tpsBig, fmtNum(Math.round(n.current_tps)));
    const d = fmtDelta((r.live_cards && r.live_cards.network_tps && r.live_cards.network_tps.delta_pct) || 0);
    setText(el.tpsDeltaChip, d.text);
    el.tpsDeltaChip.className = 'chip ' + (d.cls === 'delta-up' ? 'chip-up' : 'chip-warn');
    setText(el.tpsAvg, fmtNum(Math.round(n.avg_tps_15m)));
    setText(el.tpsNonvote, fmtNum(Math.round(n.non_vote_tps)));
    setText(el.tpsSlot, Math.round(n.avg_slot_time_ms) + 'ms');
    setText(el.tpsTx, fmtNum(n.total_transactions));
  }

  /* ===================================================================
     RENDER HERO
     =================================================================== */
  function renderHero(r) {
    const h = r.health || {};
    const n = r.network || {};
    setText(el.heroEyebrow, r.status === 'success' ? 'AUTO-UPDATING REPORT' : 'DEGRADED');
    setText(el.heroTitle, 'Live ecosystem health, at a glance.');
    setText(el.heroSub, 'Automated on-chain telemetry, validator analytics, and economic indicators — refreshed directly from the Solana mainnet, no API keys required.');
    setText(el.metaEpoch, 'Epoch ' + n.epoch + ' — ' + (n.epoch_progress_pct || 0).toFixed(1) + '%');
    setText(el.metaSlot, 'Block ' + fmtNum(n.block_height));
    setText(el.metaHealth, h.cluster_status || 'Operational');

    const healthy = h.is_healthy !== false;
    setText(el.statusValue, healthy ? 'All Systems Operational' : 'Degraded');
    setText(el.statusDetail, h.summary || '');
    el.statusOrb.className = 'status-orb' + (healthy ? '' : ' warn');
    el.statusOrb.innerHTML = '<span class="dot dot-' + (healthy ? 'ok' : 'warn') + '"></span>';

    // Health pill
    el.healthPill.className = 'health-pill' + (healthy ? '' : ' warn');
    setText(el.healthPillText, healthy ? 'Operational' : 'Degraded');
    el.healthPill.innerHTML = '<span class="dot dot-' + (healthy ? 'ok' : 'warn') + '"></span><span id="health-pill-text">' + (healthy ? 'Operational' : 'Degraded') + '</span>';
  }

  /* ===================================================================
     RENDER ECONOMY
     =================================================================== */
  function renderEconomy(r) {
    const v = r.validators || {};
    const s = r.supply || {};
    const e = r.economics || {};
    const p = r.price || {};

    setText(el.econActive, fmtNum(v.active_validators));
    setText(el.econDelinq, fmtNum(v.delinquent_validators));
    setText(el.econStake, fmtSOL(v.total_active_stake_sol) + ' SOL');
    setText(el.econNakamoto, v.nakamoto_coefficient);
    setText(el.econTop10, v.top_10_stake_pct != null ? v.top_10_stake_pct.toFixed(2) + '%' : '—');
    setText(el.econDelinqStake, (v.delinquent_stake_pct != null ? v.delinquent_stake_pct.toFixed(2) + '%' : '—'));
    if (el.stakeFill) el.stakeFill.style.width = Math.min((s.staked_pct || 0), 100) + '%';
    setText(el.stakePct, (s.staked_pct || 0).toFixed(1) + '% staked');

    setText(el.supplyTotal, fmtSOL(s.total_sol) + ' SOL');
    setText(el.supplyCirc, fmtSOL(s.circulating_sol) + ' SOL');
    setText(el.supplyStaked, fmtSOL(s.staked_sol) + ' SOL');
    setText(el.supplyStakedPct, (s.staked_pct || 0).toFixed(1) + '%');
    if (s.total_sol && s.total_sol > 0) {
      var circPct = (s.circulating_sol / s.total_sol) * 100;
      if (el.circFill) el.circFill.style.width = Math.min(circPct, 100) + '%';
      setText(el.circPct, circPct.toFixed(1) + '% circulating');
    }

    setText(el.econRev, fmtUSD(e.rev_24h_usd, true) + '/day');
    setText(el.econMedfee, fmtUSD(e.median_fee_usd));
    setText(el.econBasefee, e.base_fee_sol != null ? e.base_fee_sol + ' SOL' : '—');
    setText(el.econVelocity, (e.capital_efficiency_ratio || 0).toFixed(2) + 'x');
    setText(el.econRevNote, e.rev_methodology || '');

    setText(el.econTvl, fmtUSD(e.tvl_usd, true));
    setText(el.econDex, fmtUSD(e.dex_volume_24h_usd, true));
    setText(el.econStables, fmtUSD(e.stablecoin_mcap_usd, true));
    setText(el.econMcap, fmtUSD(p.market_cap_usd, true));
    setText(el.econLiquid, 'DEX volume / TVL: ' + (e.dex_volume_24h_usd && e.tvl_usd ? (e.dex_volume_24h_usd / e.tvl_usd).toFixed(2) + 'x' : '—'));
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
     CHARTS (Chart.js)
     =================================================================== */
  const CHART_COLORS = {
    purple: '#9945FF',
    teal: '#14F195',
    text: '#9AA4B6',
    grid: 'rgba(255,255,255,0.05)',
    fillTps: 'rgba(153,69,255,0.18)',
    fillPrice: 'rgba(47,230,162,0.16)',
    fillTvl: 'rgba(20,241,149,0.14)',
  };

  function baseChartOpts() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
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
      return d.getHours().toString().padStart(2, '0') + ':' + d.getMinutes().toString().padStart(2, '0') + ':' + d.getSeconds().toString().padStart(2, '0');
    });
  }

  function renderLineChart(canvas, labels, data, color, fill, noteEl, noteText, yPrefix) {
    if (!canvas || typeof Chart === 'undefined') return;
    setText(noteEl, noteText);
    const exists = charts[canvas.id];
    if (exists) exists.destroy();
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
          tension: 0.3,
          fill: true,
        }],
      },
      options: Object.assign(baseChartOpts(), {
        scales: Object.assign({}, baseChartOpts().scales, {
          y: Object.assign({}, baseChartOpts().scales.y, {
            ticks: Object.assign({}, baseChartOpts().scales.y.ticks, {
              callback: function (val) { return yPrefix ? yPrefix + ' ' + val.toLocaleString() : val; },
            }),
          }),
        }),
      }),
    });
  }

  function renderBarChart(canvas, labels, values, color, note, noteText) {
    if (!canvas || typeof Chart === 'undefined') return;
    setText(note, noteText);
    const exists = charts[canvas.id];
    if (exists) exists.destroy();
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
          tension: 0.3,
          fill: true,
        }],
      },
      options: baseChartOpts(),
    });
  }

  function renderCharts(r) {
    const ht = r.historical_trends || {};
    const lc = r.live_cards || {};

    // TPS
    const tpsSrc = (ht.tps && ht.tps.length) ? ht.tps : [];
    if (tpsSrc.length) {
      renderLineChart(el.chartTps, timeLabels(tpsSrc), tpsSrc.map(s => s.value), CHART_COLORS.accent, CHART_COLORS.fillTps, el.tpsChartNote, 'trailing snapshots', '');
    } else if (lc.network_tps && lc.network_tps.sparkline) {
      renderLineChart(el.chartTps, lc.network_tps.sparkline.map((_, i) => i), lc.network_tps.sparkline, CHART_COLORS.accent, CHART_COLORS.fillTps, el.tpsChartNote, 'intra-session sparkline', '');
    }

    // SOL Price
    const priceSrc = (ht.sol_price && ht.sol_price.length) ? ht.sol_price : (lc.sol_price && lc.sol_price.sparkline ? lc.sol_price.sparkline.map(function (v) { return { timestamp: new Date().toISOString(), value: v }; }) : []);
    if (priceSrc.length) {
      const labels = ht.sol_price && ht.sol_price.length ? timeLabels(priceSrc) : priceSrc.map((_, i) => i);
      renderLineChart(el.chartPrice, labels, priceSrc.map(s => s.value), CHART_COLORS['teal'], CHART_COLORS.fillPrice, el.priceChartNote, 'USD spot', '$');
    }

    // TVL 30d
    const tvl = ht.historical_tvl_30d || r.economics.historical_tvl_30d || [];
    if (tvl.length) {
      renderBarChart(el.chartTvl, tvl.map(d => d.date.slice(5)), tvl.map(d => +(d.tvl / 1e9).toFixed(2)), CHART_COLORS.teal, el.tvlChartNote, 'USD billion');
    }

    // Validators
    const valSrc = (ht.validators && ht.validators.length) ? ht.validators : (lc.active_validators && lc.active_validators.sparkline ? lc.active_validators.sparkline.map(function (v) { return { timestamp: new Date().toISOString(), value: v }; }) : []);
    if (valSrc.length) {
      const labels = ht.validators && ht.validators.length ? timeLabels(ht.validators) : valSrc.map((_, i) => i);
      renderLineChart(el.chartValidators, labels, valSrc.map(s => s.value), CHART_COLORS.accent, CHART_COLORS.fillTps, el.valChartNote, 'active nodes', '');
    }
  }

  /* ===================================================================
     VALIDATORS TABLE
     =================================================================== */
  function getValidatorSource(r) {
    const v = r.validators || {};
    return Array.isArray(v.top_validators) ? v.top_validators.slice() : [];
  }

  function applyValidatorFilters(r) {
    const v = r.validators || {};
    const nakamoto = v.nakamoto_coefficient || 18;
    let list = getValidatorSource(r);
    const filter = el.valFilter ? el.valFilter.value : 'all';
    const q = el.valSearch ? el.valSearch.value.trim().toLowerCase() : '';

    if (filter === 'top10') list = list.slice(0, 10);
    else if (filter === 'nakamoto') list = list.slice(0, nakamoto);
    else if (filter === 'zero') list = list.filter(x => Number(x.commission) === 0);
    else if (filter === 'high') list = list.filter(x => Number(x.commission) >= 10);

    if (q) list = list.filter(function (x) {
      return (x.name && x.name.toLowerCase().indexOf(q) !== -1) ||
        (x.vote_pubkey && x.vote_pubkey.toLowerCase().indexOf(q) !== -1) ||
        (x.node_pubkey && x.node_pubkey.toLowerCase().indexOf(q) !== -1);
    });

    // Sort
    list.sort(function (a, b) {
      let va, vb;
      if (sortKey === 'rank') { va = a.rank; vb = b.rank; }
      else if (sortKey === 'name') { va = (a.name || '').toLowerCase(); vb = (b.name || '').toLowerCase(); return sortAsc ? (va < vb ? -1 : va > vb ? 1 : 0) : (va > vb ? -1 : va < vb ? 1 : 0); }
      else if (sortKey === 'stake') { va = a.activated_stake_sol; vb = b.activated_stake_sol; }
      else if (sortKey === 'share') { va = a.stake_percentage; vb = b.stake_percentage; }
      else if (sortKey === 'commission') { va = a.commission; vb = b.commission; }
      else return 0;
      return sortAsc ? va - vb : vb - va;
    });

    filteredValidators = list;
    return list;
  }

  function renderValidatorTable(r) {
    const list = applyValidatorFilters(r);
    const totalPages = Math.max(1, Math.ceil(list.length / PAGE_SIZE));
    if (currentPage > totalPages) currentPage = totalPages;
    const start = (currentPage - 1) * PAGE_SIZE;
    const pageRows = list.slice(start, start + PAGE_SIZE);

    setText(el.valCount, list.length + ' validator' + (list.length === 1 ? '' : 's') + ' shown');
    setText(el.pageInfo, currentPage + ' / ' + totalPages);
    el.pagePrev.disabled = currentPage <= 1;
    el.pageNext.disabled = currentPage >= totalPages;

    if (!pageRows.length) {
      setHTML(el.valTbody, '<tr><td colspan="7" style="text-align:center;color:var(--text-3);padding:28px;">No validators match your filters.</td></tr>');
      return;
    }

    el.valTbody.innerHTML = pageRows.map(function (x) {
      const statusCls = x.status === 'delinquent' ? 'delinquent' : 'active';
      return '<tr>'
        + '<td class="num mono">' + (x.rank != null ? x.rank : '—') + '</td>'
        + '<td><div class="val-name">' + (x.name || 'Validator') + '</div>'
        + '<div class="val-pubkey" title="' + (x.vote_pubkey || '') + '">' + truncatePubkey(x.vote_pubkey) + '</div></td>'
        + '<td class="num mono">' + fmtSOL(x.activated_stake_sol) + '</td>'
        + '<td class="num mono">' + (x.stake_percentage != null ? x.stake_percentage.toFixed(2) + '%' : '—') + '</td>'
        + '<td class="num mono">' + (x.commission != null ? x.commission + '%' : '—') + '</td>'
        + '<td class="num mono">' + (x.last_vote != null ? fmtNum(x.last_vote) : '—') + '</td>'
        + '<td class="num"><span class="val-status ' + statusCls + '">' + (x.status === 'delinquent' ? 'Delinquent' : 'Active') + '</span></td>'
        + '</tr>';
    }).join('');
    updateSortIndicators();
  }

  function updateSortIndicators() {
    document.querySelectorAll('.table th.sortable').forEach(function (th) {
      th.classList.remove('asc', 'desc');
      if (th.getAttribute('data-sort') === sortKey) {
        th.classList.add(sortAsc ? 'asc' : 'desc');
      }
    });
  }

  function exportValidatorsCSV(r) {
    const list = getValidatorSource(r);
    const headers = ['rank', 'name', 'vote_pubkey', 'activated_stake_sol', 'stake_percentage', 'commission', 'last_vote', 'status'];
    const rows = list.map(function (x) {
      return headers.map(function (h) { return '"' + String(x[h] == null ? '' : x[h]).replace(/"/g, '""') + '"'; }).join(',');
    });
    const csv = headers.join(',') + '\n' + rows.join('\n');
    download('solana-validators.csv', csv, 'text/csv');
    toast('Validator CSV exported (' + list.length + ' rows)');
  }

  function download(name, content, mime) {
    const blob = new Blob([content], { type: mime + ';charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(a.href);
  }

  /* ===================================================================
     ROADMAP
     =================================================================== */
  function renderRoadmap(r) {
    const news = r.ecosystem_news || {};
    const upgrades = Array.isArray(news.upgrades) ? news.upgrades : [];
    if (!upgrades.length) {
      setHTML(el.roadmapGrid, '<p class="section-note">No upgrade data available.</p>');
      return;
    }
    el.roadmapGrid.innerHTML = upgrades.map(function (u) {
      const impactCls = (u.impact || '').toLowerCase().indexOf('critical') !== -1 ? 'impact-critical' : 'impact-high';
      return '<div class="roadmap-card">'
        + '<div class="roadmap-top"><span class="roadmap-cat">' + (u.category || 'Protocol') + '</span>'
        + '<span class="roadmap-impact ' + impactCls + '">' + (u.impact || 'High') + '</span></div>'
        + '<div class="roadmap-title">' + (u.title || '') + '</div>'
        + '<div class="roadmap-desc">' + (u.description || '') + '</div>'
        + '<div class="roadmap-bottom">'
        + '<span class="roadmap-status">● ' + (u.status || '—') + ' · ' + (u.target_timeline || '') + '</span>'
        + (u.documentation_url ? '<a class="roadmap-docs" href="' + u.documentation_url + '" target="_blank" rel="noopener">Docs →</a>' : '')
        + '</div></div>';
    }).join('');
  }

  /* ===================================================================
     NEWS
     =================================================================== */
  function renderNews(r) {
    const news = r.ecosystem_news || {};
    setText(el.newsNote, news.source_type || '');
    const ann = Array.isArray(news.recent_announcements) ? news.recent_announcements : [];
    if (!ann.length) {
      setHTML(el.newsGrid, '<p class="section-note">No announcements available.</p>');
      return;
    }
    el.newsGrid.innerHTML = ann.map(function (a) {
      return '<div class="news-card">'
        + '<span class="news-tag">' + (a.tag || 'Ecosystem') + '</span>'
        + '<div class="news-title">' + (a.title || '') + '</div>'
        + '<div class="news-summary">' + (a.summary || '') + '</div>'
        + '<div class="news-date">' + (a.date || '') + '</div>'
        + '</div>';
    }).join('');
  }

  /* ===================================================================
     ANOMALIES
     =================================================================== */
  function renderAnomalies(r) {
    const alerts = Array.isArray(r.alerts) ? r.alerts : [];
    const count = r.alerts_count != null ? r.alerts_count : alerts.length;
    if (!count) {
      el.anomalyChip.className = 'chip chip-ok';
      setText(el.anomalyChip, '0 ACTIVE');
      setHTML(el.anomalyBody, '<p class="all-clear">No statistical anomalies detected across throughput, slot latency, validator delinquency, or market moves.</p>');
      return;
    }
    el.anomalyChip.className = 'chip ' + (count > 2 ? 'chip-bad' : 'chip-warn');
    setText(el.anomalyChip, count + ' ACTIVE');
    setHTML(el.anomalyBody, '<div class="anomaly-list">' + alerts.map(function (a) {
      const sev = (a.severity || '').toLowerCase();
      const icon = sev === 'critical' ? '⛔' : sev === 'warning' ? '⚠️' : 'ℹ️';
      return '<div class="anomaly-item"><span class="anomaly-icon">' + icon + '</span>'
        + '<div class="anomaly-text"><strong>' + (a.title || a.rule || 'Alert') + '</strong>'
        + '<p>' + (a.message || a.description || '') + '</p></div></div>';
    }).join('') + '</div>');
  }

  /* ===================================================================
     RENDER ALL
     =================================================================== */
  function renderAll(r) {
    report = r;
    currentPage = 1;
    renderHero(r);
    renderKPI(r);
    renderEpoch(r);
    renderEconomy(r);
    renderCharts(r);
    renderValidatorTable(r);
    renderRoadmap(r);
    renderNews(r);
    renderAnomalies(r);
    renderFooter(r);

    setText(el.updatedAt, 'Updated ' + timeAgo(r.generated_at));
    document.title = 'Solana Ecosystem — Epoch ' + (r.network && r.network.epoch ? r.network.epoch : '') + ' · ' + (r.price ? fmtUSD(r.price.price_usd) : '') + ' · Dashboard';
  }

  /* ===================================================================
     EVENTS
     =================================================================== */
  function setupEvents() {
    // Refresh
    if (el.refreshBtn) el.refreshBtn.addEventListener('click', async function () {
      try {
        const r = await fetchReport();
        renderAll(r);
        toast('Telemetry refreshed from mainnet');
      } catch (e) {
        toast('Failed to refresh: ' + e.message, '⚠');
      }
    });

    // Exports
    if (el.exportJson) el.exportJson.addEventListener('click', function () {
      if (report) { download('solana-report.json', JSON.stringify(report, null, 2), 'application/json'); toast('report.json exported'); }
    });
    if (el.exportCsv) el.exportCsv.addEventListener('click', function () {
      if (report) exportValidatorsCSV(report);
    });

    // Search & filter
    if (el.valSearch) el.valSearch.addEventListener('input', function () { currentPage = 1; if (report) renderValidatorTable(report); });
    if (el.valFilter) el.valFilter.addEventListener('change', function () { currentPage = 1; if (report) renderValidatorTable(report); });

    // Pagination
    if (el.pagePrev) el.pagePrev.addEventListener('click', function () { if (currentPage > 1) { currentPage--; renderValidatorTable(report); } });
    if (el.pageNext) el.pageNext.addEventListener('click', function () { currentPage++; renderValidatorTable(report); });

    // Sort
    if (el.valTable) el.valTable.querySelectorAll('th.sortable').forEach(function (th) {
      th.addEventListener('click', function () {
        const key = th.getAttribute('data-sort');
        if (sortKey === key) { sortAsc = !sortAsc; } else { sortKey = key; sortAsc = true; }
        if (report) renderValidatorTable(report);
      });
    });

    // Top nav active state
    el.topnavLinks.forEach(function (link) {
      link.addEventListener('click', function () {
        el.topnavLinks.forEach(function (l) { l.classList.remove('active'); });
        link.classList.add('active');
      });
    });

    // Mobile hamburger toggle
    var hamburger = document.querySelector('.hamburger');
    var topnav = document.querySelector('.topnav');
    if (hamburger && topnav) {
      hamburger.addEventListener('click', function () {
        var isOpen = topnav.classList.toggle('open');
        hamburger.setAttribute('aria-expanded', isOpen);
        if (isOpen) {
          var firstLink = topnav.querySelector('.topnav-link');
          if (firstLink) firstLink.focus();
        }
      });
      topnav.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && topnav.classList.contains('open')) {
          topnav.classList.remove('open');
          hamburger.setAttribute('aria-expanded', 'false');
          hamburger.focus();
        }
      });
      topnav.querySelectorAll('.topnav-link').forEach(function (link) {
        link.addEventListener('click', function () {
          topnav.classList.remove('open');
          hamburger.setAttribute('aria-expanded', 'false');
        });
      });
    }

    // Scroll-based topbar enhancement
    var topbar = document.querySelector('.topbar');
    if (topbar) {
      var scrollThreshold = 80;
      window.addEventListener('scroll', function () {
        if (window.scrollY > scrollThreshold) {
          topbar.classList.add('scrolled');
        } else {
          topbar.classList.remove('scrolled');
        }
      }, { passive: true });
    }
  }

  /* ===================================================================
     INIT
     =================================================================== */
  function init() {
    setupEvents();
    fetchReport()
      .then(renderAll)
      .catch(function (err) {
        console.error('Load failed:', err);
        setText(el.updatedAt, 'Offline');
        toast('Could not load report data. Check that data/report.json exists.', '⚠');
      })
      .then(function () {
        setTimeout(function () {
          if (el.loading) el.loading.classList.add('hidden');
          // Stagger section animations (respect reduced motion)
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
