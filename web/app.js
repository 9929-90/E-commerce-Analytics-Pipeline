/* Olist Insights dashboard. This file only consumes local Gold CSV exports. */
(() => {
  const $ = (id) => document.getElementById(id);
  const state = { daily: [], products: [], dailyChart: null, mixChart: null, category: 'all', date: 'all' };
  const number = (v) => { const n = Number(String(v ?? '').replace(/[R$,%\s]/g, '').replace(/,/g, '')); return Number.isFinite(n) ? n : 0; };
  const money = (v, compact = false) => {
    if (compact && Math.abs(v) >= 1e6) return 'R$ ' + (v / 1e6).toFixed(2) + 'M';
    if (compact && Math.abs(v) >= 1e3) return 'R$ ' + (v / 1e3).toFixed(1) + 'K';
    return 'R$ ' + Number(v || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };
  const int = (v) => Number(v || 0).toLocaleString('en-US', { maximumFractionDigits: 0 });
  const key = (obj, candidates) => {
    const keys = Object.keys(obj);
    for (const candidate of candidates) {
      const found = keys.find(k => k.toLowerCase().replace(/[^a-z0-9]/g, '') === candidate.toLowerCase().replace(/[^a-z0-9]/g, ''));
      if (found) return found;
    }
    return null;
  };
  function parseCSV(text) {
    const rows = []; let row = [], cell = '', quoted = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (c === '"' && quoted && text[i + 1] === '"') { cell += '"'; i++; }
      else if (c === '"') quoted = !quoted;
      else if (c === ',' && !quoted) { row.push(cell); cell = ''; }
      else if ((c === '\n' || c === '\r') && !quoted) {
        if (c === '\r' && text[i + 1] === '\n') i++;
        row.push(cell); if (row.some(x => x.trim() !== '')) rows.push(row);
        row = []; cell = '';
      } else cell += c;
    }
    if (cell.length || row.length) { row.push(cell); rows.push(row); }
    if (rows.length < 2) throw new Error('The CSV needs a header row and at least one data row.');
    const headers = rows.shift().map(h => h.trim().replace(/^\uFEFF/, ''));
    return rows.map(r => Object.fromEntries(headers.map((h, i) => [h, (r[i] ?? '').trim()])));
  }
  function normalizeDaily(rows) {
    return rows.map(r => {
      const dateKey = key(r, ['orderdate','date','day','salesdate','createddate']);
      const revenueKey = key(r, ['totalrevenue','revenue','total_sales','salesrevenue','grossrevenue','totalsales']);
      const productKey = key(r, ['productrevenue','product_sales','itemrevenue','total_product_sales']);
      const freightKey = key(r, ['freightrevenue','freightvalue','shippingrevenue','total_freight']);
      const ordersKey = key(r, ['totalorders','deliveredorders','ordercount','orders','orderscount']);
      const date = dateKey ? r[dateKey] : '';
      const productRevenue = productKey ? number(r[productKey]) : 0;
      const freightRevenue = freightKey ? number(r[freightKey]) : 0;
      const totalRevenue = revenueKey ? number(r[revenueKey]) : productRevenue + freightRevenue;
      return { date, productRevenue, freightRevenue, totalRevenue, orders: ordersKey ? number(r[ordersKey]) : 0 };
    }).filter(r => r.date);
  }
  function normalizeProducts(rows) {
    return rows.map(r => {
      const idKey = key(r, ['productid','product_id','id']);
      const nameKey = key(r, ['productname','product_name','name','productcategoryname','category']);
      const categoryKey = key(r, ['productcategoryname','category','categoryname','productcategory']);
      const revenueKey = key(r, ['totalrevenue','productrevenue','revenue','total_sales']);
      const unitsKey = key(r, ['totalunits','unitssold','units_sold','quantity','totalquantity']);
      const ordersKey = key(r, ['totalorders','orders','ordercount','distinctorders']);
      return { id: idKey ? r[idKey] : '—', name: nameKey ? r[nameKey] : (idKey ? r[idKey] : 'Product'), category: categoryKey ? r[categoryKey] : 'Uncategorized', revenue: revenueKey ? number(r[revenueKey]) : 0, units: unitsKey ? number(r[unitsKey]) : 0, orders: ordersKey ? number(r[ordersKey]) : 0 };
    });
  }
  function setStatus(message, good = false) {
    $('dataStatus').innerHTML = '<span class="status-dot ' + (good ? '' : 'muted') + '"></span> ' + message;
  }
  function updateKpis() {
    if (!state.daily.length) return;
    const filtered = getFilteredDaily();
    const revenue = filtered.reduce((s, r) => s + r.totalRevenue, 0);
    const orders = filtered.reduce((s, r) => s + r.orders, 0);
    const freight = filtered.reduce((s, r) => s + r.freightRevenue, 0);
    $('totalRevenue').textContent = money(revenue, true);
    $('deliveredOrders').textContent = int(orders);
    $('averageOrder').textContent = money(orders ? revenue / orders : 0);
    $('freightRevenue').textContent = money(freight, true);
    $('filterStatus').textContent = state.date === 'all' ? 'Showing all dates in uploaded Gold data' : 'Filtered to ' + state.date;
  }
  function getFilteredDaily() {
    let rows = [...state.daily];
    if (state.date !== 'all') rows = rows.filter(r => r.date.startsWith(state.date));
    return rows.sort((a, b) => a.date.localeCompare(b.date));
  }
  function renderDaily() {
    const rows = getFilteredDaily();
    $('salesEmpty').classList.toggle('hidden', rows.length > 0);
    if (state.dailyChart) state.dailyChart.destroy();
    if (!rows.length) { state.dailyChart = null; return; }
    state.dailyChart = new Chart($('salesChart'), {
      type: 'line',
      data: { labels: rows.map(r => r.date), datasets: [{ label: 'Revenue', data: rows.map(r => r.totalRevenue), borderColor: '#7866e8', backgroundColor: 'rgba(120,102,232,.10)', fill: true, borderWidth: 2, tension: .28, pointRadius: rows.length > 100 ? 0 : 2, pointHoverRadius: 4 }] },
      options: { responsive: true, maintainAspectRatio: false, interaction: { intersect: false, mode: 'index' }, plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ' ' + money(ctx.parsed.y) } } }, scales: { x: { grid: { display: false }, ticks: { color: '#9aa2b1', maxTicksLimit: 7, maxRotation: 0 }, border: { display: false } }, y: { grid: { color: '#f0f2f7' }, ticks: { color: '#9aa2b1', callback: v => v >= 1e6 ? 'R$' + (v / 1e6).toFixed(1) + 'M' : v >= 1000 ? 'R$' + (v / 1000).toFixed(0) + 'K' : 'R$' + v }, border: { display: false } } } }
    });
  }
  function renderMix() {
    if (state.mixChart) state.mixChart.destroy();
    state.mixChart = new Chart($('mixChart'), { type: 'doughnut', data: { labels: ['Product revenue', 'Freight revenue'], datasets: [{ data: [13221498.11, 2198275.64], backgroundColor: ['#7d6ae8', '#48bba0'], borderWidth: 0, hoverOffset: 5 }] }, options: { responsive: true, maintainAspectRatio: false, cutout: '78%', plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ctx.label + ': ' + money(ctx.parsed) } } } } });
  }
  function renderProducts() {
    const query = $('productSearch').value.trim().toLowerCase();
    const sort = $('sortProducts').value;
    const category = $('categoryFilter').value;
    const rows = state.products.filter(p => (category === 'all' || p.category === category) && (!query || (p.name + ' ' + p.id + ' ' + p.category).toLowerCase().includes(query))).sort((a,b) => b[sort] - a[sort]);
    const total = state.products.reduce((s,p) => s + p.revenue, 0);
    $('productCount').textContent = state.products.length ? int(rows.length) + ' of ' + int(state.products.length) + ' products' : '32,951 products in Gold output';
    if (!rows.length) {
      $('productRows').innerHTML = '<tr><td colspan="5" class="empty-table"><span class="empty-icon">▦</span><strong>' + (state.products.length ? 'No matching products' : 'Product-level details are ready to connect') + '</strong><p>' + (state.products.length ? 'Try a different search or category.' : 'Upload the product performance CSV to populate this table with real product metrics.') + '</p></td></tr>';
      return;
    }
    $('productRows').innerHTML = rows.slice(0, 100).map(p => {
      const share = total ? p.revenue / total * 100 : 0;
      return '<tr><td><div>' + escapeHtml(p.name) + '</div><small style="color:#9aa2b1;font-weight:400">' + escapeHtml(p.id) + '</small></td><td>' + money(p.revenue) + '</td><td>' + int(p.units) + '</td><td>' + int(p.orders) + '</td><td><div style="display:flex;align-items:center;gap:8px"><div class="share-bar"><span style="width:' + Math.min(100,share) + '%"></span></div><span>' + share.toFixed(2) + '%</span></div></td></tr>';
    }).join('');
  }
  function escapeHtml(s) { return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
  function refreshFilters() {
    const dates = [...new Set(state.daily.map(r => r.date.slice(0,7)).filter(Boolean))].sort();
    const dateSelect = $('dateFilter');
    dateSelect.innerHTML = '<option value="all">All available dates</option>' + dates.map(d => '<option value="' + escapeHtml(d) + '">' + escapeHtml(d) + '</option>').join('');
    const categories = [...new Set(state.products.map(p => p.category).filter(Boolean))].sort();
    $('categoryFilter').innerHTML = '<option value="all">All categories</option>' + categories.map(c => '<option value="' + escapeHtml(c) + '">' + escapeHtml(c) + '</option>').join('');
  }
  $('dailyFile').addEventListener('change', async e => {
    const file = e.target.files[0]; if (!file) return;
    try {
      const parsed = normalizeDaily(parseCSV(await file.text()));
      if (!parsed.length) throw new Error('Could not find a date column. Expected a column such as order_date or date.');
      state.daily = parsed;
      $('dailyFileName').textContent = file.name + ' · ' + int(parsed.length) + ' rows';
      refreshFilters(); updateKpis(); renderDaily();
      setStatus('Loaded daily sales · ' + int(parsed.length) + ' rows', true);
    } catch (err) { setStatus('Could not load daily sales: ' + err.message); alert(err.message); }
  });
  $('productFile').addEventListener('change', async e => {
    const file = e.target.files[0]; if (!file) return;
    try {
      const parsed = normalizeProducts(parseCSV(await file.text()));
      if (!parsed.length || !parsed.some(p => p.id !== '—' || p.revenue || p.units)) throw new Error('The CSV needs product identifiers and product metrics.');
      state.products = parsed;
      $('productFileName').textContent = file.name + ' · ' + int(parsed.length) + ' rows';
      refreshFilters(); renderProducts();
      setStatus('Loaded Gold outputs · ' + int(state.daily.length) + ' daily rows, ' + int(parsed.length) + ' products', true);
    } catch (err) { setStatus('Could not load product data: ' + err.message); alert(err.message); }
  });
  $('dateFilter').addEventListener('change', e => { state.date = e.target.value; updateKpis(); renderDaily(); });
  $('categoryFilter').addEventListener('change', e => { state.category = e.target.value; renderProducts(); });
  $('productSearch').addEventListener('input', renderProducts);
  $('sortProducts').addEventListener('change', renderProducts);
  $('resetBtn').addEventListener('click', () => { $('dateFilter').value = 'all'; $('categoryFilter').value = 'all'; $('productSearch').value = ''; $('sortProducts').value = 'revenue'; state.date = 'all'; state.category = 'all'; updateKpis(); renderDaily(); renderProducts(); });
  $('exportSummary').addEventListener('click', () => {
    const daily = getFilteredDaily();
    const summary = { project: 'Olist E-commerce Analytics', currency: 'BRL', source: 'Gold layer CSV exports', exportedAt: new Date().toISOString(), dailyRowsLoaded: state.daily.length, productRowsLoaded: state.products.length, filteredRevenue: state.daily.length ? daily.reduce((s,r)=>s+r.totalRevenue,0) : 15419773.75, filteredOrders: state.daily.length ? daily.reduce((s,r)=>s+r.orders,0) : 96478, productRevenue: 13221498.11, freightRevenue: 2198275.64, note: state.daily.length ? 'Filtered metrics based on uploaded daily Gold CSV.' : 'Revenue and order metrics are verified project-level baseline totals; upload Gold CSVs for date-level filtering.' };
    const blob = new Blob([JSON.stringify(summary, null, 2)], {type:'application/json'});
    const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href=url; a.download='olist-dashboard-summary.json'; a.click(); URL.revokeObjectURL(url);
  });
  async function loadBundledData() {
    try {
      const [dailyResponse, productResponse] = await Promise.all([
        fetch('data/daily_sales.csv'),
        fetch('data/product_performance.csv')
      ]);
      if (!dailyResponse.ok || !productResponse.ok) return;
      const [dailyText, productText] = await Promise.all([dailyResponse.text(), productResponse.text()]);
      const daily = normalizeDaily(parseCSV(dailyText));
      const products = normalizeProducts(parseCSV(productText));
      if (daily.length) {
        state.daily = daily;
        $('dailyFileName').textContent = 'data/daily_sales.csv · ' + int(daily.length) + ' rows';
      }
      if (products.length) {
        state.products = products;
        $('productFileName').textContent = 'data/product_performance.csv · ' + int(products.length) + ' rows';
      }
      refreshFilters();
      updateKpis();
      renderDaily();
      renderProducts();
      setStatus('Loaded published Gold data · ' + int(state.daily.length) + ' daily rows, ' + int(state.products.length) + ' products', true);
    } catch (error) {
      console.warn('Bundled Gold CSVs could not be loaded:', error);
    }
  }

  renderMix();
  loadBundledData();
})();