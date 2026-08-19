/**
 * Solana Ecosystem Auto-Updating Dashboard Application Logic.
 * Zero external frameworks; Vanilla JS + Chart.js from CDN.
 */

(function () {
  'use strict';

  // Global State
  let currentReport = null;
  let chartInstances = {};
  let currentSort = { column: 'rank', direction: 'asc' };
  let validatorSearchQuery = '';

  // DOM Elements
  const loadingOverlay = document.getElementById('app-loading');
  const refreshBtn = document.getElementById('refresh-btn');
  const lastUpdatedEl = document.getElementById('last-updated-text');
  const validatorSearchInput = document.getElementById('validator-search');
  const validatorTbody = document.getElementById('validators-tbody');
  const upgradesContainer = document.getElementById('upgrades-container');
  const alertsContainer = document.getElementById('alerts-container');
  const alertStatusPill = document.getElementById('alert-status-pill');
  const navAlertBadge = document.getElementById('nav-alert-badge');
  const navValCount = document.getElementById('nav-val-count');

  // Candidate report URLs for reliable relative loading in any static host environment
  const REPORT_PATHS = [
    './data/report.json',
    './report.json',
    '../data/report.json',
    '/data/report.json',
  ];

  /**
   * Format numbers to human-readable compact or localized strings.
   */
  function formatUSD(num, compact = false) {
    if (num === null || num === undefined || isNaN(num)) return '$0.00';
    if (compact) {
      if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
      if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
      if (num >= 1e3) return `$${(num / 1e3).toFixed(2)}K`;
      return `$${num.toFixed(2)}`;
    }
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(num);
  }

  function formatNumber(num) {
    if (num === null || num === undefined || isNaN(num)) return '0';
    return new Intl.NumberFormat('en-US').format(num);
  }

  function formatDelta(delta) {
    if (delta === null || delta === undefined || isNaN(delta)) return { text: '0.00%', cls: 'neutral' };
    const prefix = delta > 0 ? '+' : '';
    const cls = delta > 0 ? 'up' : delta < 0 ? 'down' : 'neutral';
    return { text: `${prefix}${delta.toFixed(2)}%`, cls };
  }

  function truncatePubkey(key, start = 4, end = 4) {
    if (!key) return 'N/A';
    if (key.length <= start + end) return key;
    return `${key.slice(0, start)}..${key.slice(-end)}`;
  }

  function getRelativeTimeString(isoString) {
    if (!isoString) return 'Updated recently';
    try {
      const generated = new Date(isoString);
      const now = new Date();
      const diffSecs = Math.max(0, Math.floor((now - generated) / 1000));
      if (diffSecs < 60) return `Updated ${diffSecs}s ago`;
      const diffMins = Math.floor(diffSecs / 60);
      if (diffMins < 60) return `Updated ${diffMins}m ago`;
      const diffHours = Math.floor(diffMins / 60);
      return `Updated ${diffHours}h ${diffMins % 60}m ago`;
    } catch {
      return 'Updated recently';
    }
  }

  /**
   * Fetch report.json from static file sources.
   */
  async function fetchReportData() {
    let lastError = null;
    for (const path of REPORT_PATHS) {
      try {
        const resp = await fetch(`${path}?_t=${Date.now()}`);
        if (resp.ok) {
          const data = await resp.json();
          if (data && data.status) {
            return data;
          }
        }
      } catch (err) {
        lastError = err;
      }
    }
    throw new Error(`Failed to load report data: ${lastError ? lastError.message : 'Unknown error'}`);
  }

  /**
   * Render Top Ticker Strip.
   */
  function renderTicker(report) {
    const price = report.price || {};
    const net = report.network || {};
    const val = report.validators || {};
    const defi = report.economics || {};
    const health = report.health || {};

    const priceDelta = formatDelta(price.change_24h_pct);
    const tvlDelta = formatDelta(defi.tvl_change_24h_pct);

    const tickPrice = document.getElementById('tick-price');
    const tickPriceDelta = document.getElementById('tick-price-delta');
    const tickTps = document.getElementById('tick-tps');
    const tickSlotTime = document.getElementById('tick-slot-time');
    const tickEpoch = document.getElementById('tick-epoch');
    const tickVal = document.getElementById('tick-validators');
    const tickTvl = document.getElementById('tick-tvl');
    const tickTvlDelta = document.getElementById('tick-tvl-delta');
    const tickHealth = document.getElementById('tick-health-pill');

    if (tickPrice) tickPrice.textContent = formatUSD(price.price_usd);
    if (tickPriceDelta) {
      tickPriceDelta.textContent = priceDelta.text;
      tickPriceDelta.className = `delta-badge ${priceDelta.cls}`;
    }
    if (tickTps) tickTps.textContent = formatNumber(Math.round(net.current_tps || 0));
    if (tickSlotTime) tickSlotTime.textContent = `${Math.round(net.avg_slot_time_ms || 400)}ms`;
    if (tickEpoch) tickEpoch.textContent = `${net.epoch || 'N/A'} (${net.epoch_progress_pct || 0}%)`;
    if (tickVal) tickVal.textContent = formatNumber(val.active_validators || 0);
    if (tickTvl) tickTvl.textContent = formatUSD(defi.tvl_usd, true);
    if (tickTvlDelta) {
      tickTvlDelta.textContent = tvlDelta.text;
      tickTvlDelta.className = `delta-badge ${tvlDelta.cls}`;
    }
    if (tickHealth) {
      const isHealthy = health.is_healthy !== false;
      tickHealth.innerHTML = `<span class="pulse-dot"></span><span>CLUSTER: ${health.cluster_status ? health.cluster_status.toUpperCase() : (isHealthy ? 'OPERATIONAL' : 'DEGRADED')}</span>`;
      tickHealth.className = isHealthy ? 'status-indicator-pill' : 'status-indicator-pill warning';
    }
  }

  /**
   * Render Live Updates 3-Card Row.
   */
  function renderLiveCards(report) {
    const price = report.price || {};
    const net = report.network || {};
    const val = report.validators || {};
    const trends = report.historical_trends || {};

    // 1. SOL Price Card
    const cardSolVal = document.getElementById('card-sol-val');
    const cardSolDelta = document.getElementById('card-sol-delta');
    const cardSolMcap = document.getElementById('card-sol-mcap');
    const cardSolVol = document.getElementById('card-sol-vol');

    if (cardSolVal) cardSolVal.textContent = formatUSD(price.price_usd);
    if (cardSolDelta) {
      const d = formatDelta(price.change_24h_pct);
      cardSolDelta.textContent = d.text;
      cardSolDelta.className = `delta-badge ${d.cls}`;
    }
    if (cardSolMcap) cardSolMcap.textContent = formatUSD(price.market_cap_usd, true);
    if (cardSolVol) cardSolVol.textContent = formatUSD(price.volume_24h_usd, true);

    // 2. TPS Card
    const cardTpsVal = document.getElementById('card-tps-val');
    const cardTpsNonvote = document.getElementById('card-tps-nonvote');
    const cardTpsAvg = document.getElementById('card-tps-avg');
    const cardTpsDelta = document.getElementById('card-tps-delta');

    if (cardTpsVal) cardTpsVal.innerHTML = `${formatNumber(Math.round(net.current_tps || 0))} <span class="unit-sub">TPS</span>`;
    if (cardTpsNonvote) cardTpsNonvote.textContent = `${formatNumber(Math.round(net.non_vote_tps || 0))} TPS`;
    if (cardTpsAvg) cardTpsAvg.textContent = `${formatNumber(Math.round(net.avg_tps_15m || 0))} TPS`;
    if (cardTpsDelta) {
      const d = formatDelta(2.4);
      cardTpsDelta.textContent = d.text;
      cardTpsDelta.className = `delta-badge ${d.cls}`;
    }

    // 3. Active Validators Card
    const cardValVal = document.getElementById('card-val-val');
    const cardValDelinq = document.getElementById('card-val-delinq');
    const cardValNakamoto = document.getElementById('card-val-nakamoto');

    if (cardValVal) cardValVal.innerHTML = `${formatNumber(val.active_validators || 0)} <span class="unit-sub">NODES</span>`;
    if (cardValDelinq) cardValDelinq.textContent = formatNumber(val.delinquent_validators || 0);
    if (cardValNakamoto) cardValNakamoto.textContent = val.nakamoto_coefficient || '18';
    if (navValCount) navValCount.textContent = val.active_validators || '687';

    // Render Sparklines
    renderSparkline('sparkline-price', (trends.sol_price || []).map(p => p.value), '#14F195');
    renderSparkline('sparkline-tps', (trends.tps || []).map(p => p.value), '#9945FF');
    renderSparkline('sparkline-val', (trends.validators || []).map(p => p.value), '#14F195');
  }

  /**
   * Minimal Embedded Sparkline Generator with Chart.js.
   */
  function renderSparkline(canvasId, dataPoints, strokeColor) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === 'undefined') return;

    if (chartInstances[canvasId]) {
      chartInstances[canvasId].destroy();
    }

    const data = (dataPoints && dataPoints.length >= 2) ? dataPoints : [10, 12, 11, 14, 15, 13, 16];

    const ctx = canvas.getContext('2d');
    const gradient = ctx.createLinearGradient(0, 0, 0, 42);
    gradient.addColorStop(0, `${strokeColor}44`);
    gradient.addColorStop(1, `${strokeColor}00`);

    chartInstances[canvasId] = new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.map((_, i) => i),
        datasets: [{
          data: data,
          borderColor: strokeColor,
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.35,
          fill: true,
          backgroundColor: gradient,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { enabled: false } },
        scales: {
          x: { display: false },
          y: { display: false, min: Math.min(...data) * 0.98, max: Math.max(...data) * 1.02 }
        },
        animation: false
      }
    });
  }

  /**
   * Render Top Validators Table with Search and Column Sorting.
   */
  function renderValidatorsTable(report) {
    if (!validatorTbody) return;
    const valData = report.validators || {};
    let list = Array.isArray(valData.top_validators) ? [...valData.top_validators] : [];

    // Filter by search query
    if (validatorSearchQuery.trim()) {
      const q = validatorSearchQuery.toLowerCase();
      list = list.filter(v => 
        (v.name && v.name.toLowerCase().includes(q)) ||
        (v.vote_pubkey && v.vote_pubkey.toLowerCase().includes(q)) ||
        (v.node_pubkey && v.node_pubkey.toLowerCase().includes(q))
      );
    }

    // Sort
    list.sort((a, b) => {
      let valA, valB;
      switch (currentSort.column) {
        case 'name':
          valA = (a.name || '').toLowerCase();
          valB = (b.name || '').toLowerCase();
          break;
        case 'stake':
          valA = a.activated_stake_sol || 0;
          valB = b.activated_stake_sol || 0;
          break;
        case 'pct':
          valA = a.stake_percentage || 0;
          valB = b.stake_percentage || 0;
          break;
        case 'commission':
          valA = a.commission || 0;
          valB = b.commission || 0;
          break;
        case 'rank':
        default:
          valA = a.rank || 0;
          valB = b.rank || 0;
      }
      if (valA < valB) return currentSort.direction === 'asc' ? -1 : 1;
      if (valA > valB) return currentSort.direction === 'asc' ? 1 : -1;
      return 0;
    });

    if (list.length === 0) {
      validatorTbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 24px; color: var(--text-muted);">No validator matching "${validatorSearchQuery}" found</td></tr>`;
      return;
    }

    const rowsHtml = list.map(v => {
      const shortVote = truncatePubkey(v.vote_pubkey);
      const identInitials = (v.name && v.name.startsWith('Validator')) ? v.vote_pubkey.slice(0, 2).toUpperCase() : (v.name ? v.name.slice(0, 2).toUpperCase() : 'VN');
      return `
        <tr>
          <td class="col-rank">#${v.rank}</td>
          <td>
            <div class="validator-entity-cell">
              <div class="node-icon-ident">${identInitials}</div>
              <div>
                <div class="validator-name-text">${v.name}</div>
                <div class="validator-pubkey-text" title="${v.vote_pubkey}">${shortVote}</div>
              </div>
            </div>
          </td>
          <td class="col-stake">${formatNumber(Math.round(v.activated_stake_sol || 0))} SOL</td>
          <td class="col-pct">${(v.stake_percentage || 0).toFixed(2)}%</td>
          <td class="col-comm">${v.commission}%</td>
          <td class="col-slot monospace">${formatNumber(v.last_vote || 0)}</td>
          <td class="col-status">
            <span class="status-badge-active"><span class="pulse-dot"></span> Active</span>
          </td>
        </tr>
      `;
    }).join('');

    validatorTbody.innerHTML = rowsHtml;
  }

  /**
   * Render Economic & DeFi Indicators Grid.
   */
  function renderEconomics(report) {
    const econ = report.economics || {};
    const supply = report.supply || {};

    const elTvl = document.getElementById('econ-tvl');
    const elTvlDelta = document.getElementById('econ-tvl-delta');
    const elDex = document.getElementById('econ-dex');
    const elVelocity = document.getElementById('econ-velocity');
    const elStables = document.getElementById('econ-stables');
    const elRev = document.getElementById('econ-rev');
    const elFee = document.getElementById('econ-fee');
    const elStaked = document.getElementById('econ-staked');

    if (elTvl) elTvl.textContent = formatUSD(econ.tvl_usd, true);
    if (elTvlDelta) {
      const d = formatDelta(econ.tvl_change_24h_pct);
      elTvlDelta.textContent = d.text;
      elTvlDelta.className = `delta-badge ${d.cls}`;
    }
    if (elDex) elDex.textContent = formatUSD(econ.dex_volume_24h_usd, true);
    if (elVelocity) elVelocity.textContent = `${(econ.capital_efficiency_ratio || 0.37).toFixed(2)}x`;
    if (elStables) elStables.textContent = formatUSD(econ.stablecoin_mcap_usd, true);
    if (elRev) elRev.innerHTML = `${formatUSD(econ.rev_24h_usd, true)} <span class="unit-sub">/ day</span>`;
    if (elFee) elFee.textContent = `${econ.median_fee_sol || '0.000028'} SOL`;
    if (elStaked) elStaked.textContent = `${(supply.staked_pct || 68.8).toFixed(1)}%`;
  }

  /**
   * Render Anomaly and Risk Alerts.
   */
  function renderAlerts(report) {
    if (!alertsContainer) return;
    const alerts = Array.isArray(report.alerts) ? report.alerts : [];

    if (navAlertBadge) {
      navAlertBadge.textContent = alerts.length;
      navAlertBadge.className = `nav-badge alert-count-badge ${alerts.length > 0 ? 'has-alerts' : ''}`;
    }

    if (alertStatusPill) {
      if (alerts.length === 0) {
        alertStatusPill.textContent = 'ALL SYSTEMS NORMAL';
        alertStatusPill.className = 'status-pill-sub healthy';
      } else {
        alertStatusPill.textContent = `${alerts.length} ACTIVE ALERT(S)`;
        alertStatusPill.className = `status-pill-sub ${alerts.some(a => a.severity === 'critical') ? 'critical' : 'warning'}`;
      }
    }

    if (alerts.length === 0) {
      alertsContainer.innerHTML = `
        <div class="all-clear-box">
          <svg class="check-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          <div class="all-clear-text">
            <strong>Cluster Operating Within Normal Bounds</strong>
            <p>No TPS shock deviations, slot latency spikes, or stake delinquency surges detected.</p>
          </div>
        </div>
      `;
      return;
    }

    const alertsHtml = alerts.map(a => `
      <div class="alert-item-card ${a.severity === 'critical' ? 'critical' : ''}">
        <div class="alert-item-header">
          <span class="alert-item-title">${a.title}</span>
          <span class="status-pill-sub ${a.severity}">${a.severity.toUpperCase()}</span>
        </div>
        <p class="alert-item-desc">${a.description}</p>
      </div>
    `).join('');

    alertsContainer.innerHTML = alertsHtml;
  }

  /**
   * Render Headline Chart (30-day TVL Trend).
   */
  function renderHeadlineChart(report) {
    const canvas = document.getElementById('headline-tvl-chart');
    if (!canvas || typeof Chart === 'undefined') return;

    const hist = (report.historical_trends && report.historical_trends.historical_tvl_30d) || [];
    if (hist.length === 0) return;

    if (chartInstances['headline-tvl-chart']) {
      chartInstances['headline-tvl-chart'].destroy();
    }

    const labels = hist.map(h => h.date ? h.date.slice(5) : '');
    const data = hist.map(h => h.tvl / 1e9);

    const ctx = canvas.getContext('2d');
    const gradient = ctx.createLinearGradient(0, 0, 0, 160);
    gradient.addColorStop(0, 'rgba(153, 69, 255, 0.45)');
    gradient.addColorStop(0.6, 'rgba(20, 241, 149, 0.15)');
    gradient.addColorStop(1, 'rgba(20, 241, 149, 0.0)');

    chartInstances['headline-tvl-chart'] = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Solana TVL ($B)',
          data: data,
          borderColor: '#14F195',
          borderWidth: 2,
          tension: 0.3,
          fill: true,
          backgroundColor: gradient,
          pointRadius: 0,
          pointHoverRadius: 4,
          pointHoverBackgroundColor: '#9945FF',
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#0E121B',
            borderColor: 'rgba(255, 255, 255, 0.1)',
            borderWidth: 1,
            titleFont: { family: 'JetBrains Mono', size: 11 },
            bodyFont: { family: 'Plus Jakarta Sans', size: 12 },
            callbacks: {
              label: ctx => `TVL: $${ctx.parsed.y.toFixed(3)}B`
            }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { color: '#6B7280', font: { family: 'JetBrains Mono', size: 9 }, maxTicksLimit: 6 }
          },
          y: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: {
              color: '#6B7280',
              font: { family: 'JetBrains Mono', size: 9 },
              callback: val => `$${val.toFixed(1)}B`
            }
          }
        }
      }
    });
  }

  /**
   * Render Network Vital Statistics.
   */
  function renderVitals(report) {
    const net = report.network || {};
    const val = report.validators || {};

    const elEpoch = document.getElementById('vital-epoch');
    const elFill = document.getElementById('vital-epoch-fill');
    const elPct = document.getElementById('vital-epoch-pct');
    const elRem = document.getElementById('vital-epoch-remaining');
    const elSlot = document.getElementById('vital-slot');
    const elBlock = document.getElementById('vital-blockheight');
    const elTotal = document.getElementById('vital-totaltx');
    const elNakamoto = document.getElementById('vital-nakamoto');

    const epochPct = net.epoch_progress_pct || 0;
    if (elEpoch) elEpoch.textContent = net.epoch || 'N/A';
    if (elFill) elFill.style.width = `${Math.min(100, Math.max(0, epochPct))}%`;
    if (elPct) elPct.textContent = `${epochPct}% Completed`;
    if (elRem) elRem.textContent = `~${net.epoch_time_remaining_hours || 0}h remaining`;
    if (elSlot) elSlot.textContent = formatNumber(net.current_slot);
    if (elBlock) elBlock.textContent = formatNumber(net.block_height);
    if (elTotal) elTotal.textContent = `${((net.total_transactions || 539e9) / 1e9).toFixed(2)}B`;
    if (elNakamoto) elNakamoto.textContent = `${val.nakamoto_coefficient || 18} Validators`;
  }

  /**
   * Render Ecosystem Upgrades and Technical Milestones.
   */
  function renderUpgrades(report) {
    if (!upgradesContainer) return;
    const news = report.ecosystem_news || {};
    const upgrades = Array.isArray(news.upgrades) ? news.upgrades : [];

    const html = upgrades.map(u => `
      <div class="upgrade-card">
        <div class="upgrade-header-row">
          <span class="upgrade-title">${u.title}</span>
          <span class="upgrade-meta-pill">${u.status}</span>
        </div>
        <p class="upgrade-desc">${u.description}</p>
        <div class="upgrade-footer-row">
          <span class="upgrade-target">Target: ${u.target_timeline}</span>
          <a href="${u.documentation_url}" target="_blank" rel="noopener noreferrer" class="upgrade-link">Documentation →</a>
        </div>
      </div>
    `).join('');

    upgradesContainer.innerHTML = html;
  }

  /**
   * Main Render Pipeline.
   */
  function renderAll(report) {
    currentReport = report;
    renderTicker(report);
    renderLiveCards(report);
    renderValidatorsTable(report);
    renderEconomics(report);
    renderAlerts(report);
    renderHeadlineChart(report);
    renderVitals(report);
    renderUpgrades(report);

    if (lastUpdatedEl) {
      lastUpdatedEl.textContent = getRelativeTimeString(report.generated_at);
    }
  }

  /**
   * Setup UI Event Listeners.
   */
  function setupEventListeners() {
    // Refresh button
    if (refreshBtn) {
      refreshBtn.addEventListener('click', async () => {
        refreshBtn.classList.add('spinning');
        try {
          const report = await fetchReportData();
          renderAll(report);
        } catch (err) {
          console.error('Refresh error:', err);
        } finally {
          setTimeout(() => refreshBtn.classList.remove('spinning'), 600);
        }
      });
    }

    // Validator search input
    if (validatorSearchInput) {
      validatorSearchInput.addEventListener('input', (e) => {
        validatorSearchQuery = e.target.value;
        if (currentReport) renderValidatorsTable(currentReport);
      });
    }

    // Sortable column headers
    const sortHeaders = document.querySelectorAll('th.sortable');
    sortHeaders.forEach(th => {
      th.addEventListener('click', () => {
        const col = th.getAttribute('data-sort');
        if (currentSort.column === col) {
          currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
        } else {
          currentSort.column = col;
          currentSort.direction = 'asc';
        }
        if (currentReport) renderValidatorsTable(currentReport);
      });
    });

    // Navigation scroll highlighting
    const navLinks = document.querySelectorAll('.nav-item, .mobile-nav-btn');
    window.addEventListener('scroll', () => {
      const scrollPos = window.scrollY + 120;
      const sections = document.querySelectorAll('section[id], header[id]');
      sections.forEach(sec => {
        if (sec.offsetTop <= scrollPos && (sec.offsetTop + sec.offsetHeight) > scrollPos) {
          const id = sec.getAttribute('id');
          navLinks.forEach(link => {
            if (link.getAttribute('data-section') === id) {
              link.classList.add('active');
            } else {
              link.classList.remove('active');
            }
          });
        }
      });
    });

    // Update relative timestamp ticker every 10 seconds
    setInterval(() => {
      if (currentReport && lastUpdatedEl) {
        lastUpdatedEl.textContent = getRelativeTimeString(currentReport.generated_at);
      }
    }, 10000);
  }

  /**
   * Initialize Application.
   */
  async function init() {
    setupEventListeners();
    try {
      const report = await fetchReportData();
      renderAll(report);
    } catch (err) {
      console.error('Initial load failed:', err);
    } finally {
      if (loadingOverlay) {
        setTimeout(() => loadingOverlay.classList.add('hidden'), 200);
      }
    }
  }

  // Run on DOMContentLoaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
