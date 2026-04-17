<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Bought Together · Order Analyser</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Fraunces:ital,wght@0,300;0,600;0,900;1,300&display=swap');

  :root {
    --bg: #0e0e0e;
    --surface: #161616;
    --surface2: #1e1e1e;
    --border: #2a2a2a;
    --accent: #c8f04a;
    --text: #f0f0f0;
    --muted: #666;
    --danger: #ff6b6b;
    --radius: 10px;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: 'DM Mono', monospace; min-height: 100vh; font-size: 13px; line-height: 1.6; }

  header {
    border-bottom: 1px solid var(--border);
    padding: 22px 32px;
    display: flex; align-items: center; justify-content: space-between;
    position: sticky; top: 0; background: var(--bg); z-index: 100;
  }
  .logo { font-family: 'Fraunces', serif; font-size: 22px; font-weight: 900; letter-spacing: -0.5px; }
  .logo span { color: var(--accent); }
  .status-pill {
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 999px; padding: 4px 14px; font-size: 11px; color: var(--muted);
    display: flex; align-items: center; gap: 6px;
  }
  .status-pill .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--muted); transition: background 0.3s; }
  .status-pill.loaded .dot { background: var(--accent); }
  .status-pill.loaded { color: var(--text); }

  main { max-width: 1100px; margin: 0 auto; padding: 40px 32px 80px; }

  .section-label { font-size: 10px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted); margin-bottom: 12px; }

  .help-text {
    background: var(--surface); border-left: 3px solid var(--accent);
    border-radius: 0 var(--radius) var(--radius) 0;
    padding: 14px 18px; font-size: 12px; color: var(--muted); margin-bottom: 24px; line-height: 1.8;
  }
  .help-text strong { color: var(--text); }

  .upload-zone {
    border: 2px dashed var(--border); border-radius: var(--radius);
    padding: 48px 32px; text-align: center; cursor: pointer;
    transition: all 0.2s; background: var(--surface); position: relative;
  }
  .upload-zone:hover, .upload-zone.dragover { border-color: var(--accent); background: #1a1f0f; }
  .upload-zone input[type=file] { position: absolute; inset: 0; opacity: 0; cursor: pointer; }
  .upload-zone h2 { font-family: 'Fraunces', serif; font-size: 20px; font-weight: 600; margin-bottom: 8px; }
  .upload-zone p { color: var(--muted); font-size: 12px; }
  .upload-zone p strong { color: var(--accent); }
  .upload-icon { font-size: 36px; margin-bottom: 12px; display: block; }

  .btn {
    display: inline-flex; align-items: center; gap: 8px;
    background: var(--accent); color: #0e0e0e;
    border: none; border-radius: var(--radius); padding: 10px 20px;
    font-family: 'DM Mono', monospace; font-size: 12px; font-weight: 500;
    cursor: pointer; transition: all 0.15s; margin-top: 20px;
  }
  .btn:hover { background: #d4f85c; transform: translateY(-1px); }
  .btn:disabled { opacity: 0.4; cursor: not-allowed; transform: none; }
  .btn.secondary { background: var(--surface2); color: var(--text); border: 1px solid var(--border); }
  .btn.secondary:hover { border-color: var(--accent); color: var(--accent); background: var(--surface2); }

  #progress-bar-wrap { display: none; margin-top: 20px; }
  #progress-bar-wrap.visible { display: block; }
  .progress-track { background: var(--border); border-radius: 4px; height: 6px; overflow: hidden; }
  .progress-fill { height: 100%; background: var(--accent); border-radius: 4px; transition: width 0.3s; width: 0%; }
  .progress-label { font-size: 11px; color: var(--muted); margin-top: 8px; text-align: center; }

  #stats-bar { display: none; gap: 1px; margin-bottom: 32px; border-radius: var(--radius); overflow: hidden; border: 1px solid var(--border); }
  #stats-bar.visible { display: flex; }
  .stat-box { flex: 1; background: var(--surface); padding: 16px 20px; text-align: center; }
  .stat-box .val { font-family: 'Fraunces', serif; font-size: 28px; font-weight: 900; color: var(--accent); display: block; }
  .stat-box .lbl { font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.1em; }

  #search-section { display: none; margin-bottom: 32px; }
  #search-section.visible { display: block; }

  .search-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px; }
  @media(max-width:600px){ .search-grid { grid-template-columns: 1fr; } }

  .field { display: flex; flex-direction: column; gap: 6px; }
  .field label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); }
  .field input, .field select {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 10px 14px; color: var(--text);
    font-family: 'DM Mono', monospace; font-size: 13px; transition: border-color 0.15s; width: 100%;
  }
  .field input:focus, .field select:focus { outline: none; border-color: var(--accent); }
  .field input::placeholder { color: var(--muted); }

  .search-actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
  .search-actions .btn { margin-top: 0; }

  #results-section { display: none; }
  #results-section.visible { display: block; }
  .results-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; flex-wrap: wrap; gap: 10px; }
  .results-header h3 { font-family: 'Fraunces', serif; font-size: 18px; font-weight: 600; }
  .results-header h3 span { color: var(--accent); }
  .results-meta { font-size: 11px; color: var(--muted); }

  .product-card {
    background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
    padding: 20px 24px; margin-bottom: 10px;
    display: grid; grid-template-columns: 1fr auto; align-items: center; gap: 16px;
    transition: border-color 0.15s;
    animation: fadeUp 0.25s ease both;
  }
  .product-card:hover { border-color: #3a3a3a; }
  @keyframes fadeUp { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
  .product-card:nth-child(2) { animation-delay:.05s }
  .product-card:nth-child(3) { animation-delay:.1s }
  .product-card:nth-child(4) { animation-delay:.15s }
  .product-card:nth-child(5) { animation-delay:.2s }

  .pc-rank { font-family:'Fraunces',serif; font-size:11px; color:var(--muted); margin-bottom:4px; }
  .pc-name { font-family:'Fraunces',serif; font-size:16px; font-weight:600; margin-bottom:4px; }
  .pc-meta { font-size:11px; color:var(--muted); display:flex; gap:12px; flex-wrap:wrap; }
  .pc-right { text-align:right; min-width:90px; }
  .pc-pct { font-family:'Fraunces',serif; font-size:32px; font-weight:900; color:var(--accent); line-height:1; margin-bottom:4px; }
  .pc-count { font-size:11px; color:var(--muted); }
  .bar-wrap { height:4px; background:var(--border); border-radius:2px; margin-top:12px; overflow:hidden; grid-column:1/-1; }
  .bar-fill { height:100%; background:var(--accent); border-radius:2px; transition:width 0.6s cubic-bezier(0.22,1,0.36,1); }

  .empty-state { text-align:center; padding:60px 20px; color:var(--muted); }
  .empty-state span { font-size:40px; display:block; margin-bottom:16px; }

  /* Column mapper */
  #mapper-section { display:none; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:24px; margin-bottom:32px; }
  #mapper-section.visible { display:block; }
  #mapper-section h3 { font-family:'Fraunces',serif; font-size:16px; font-weight:600; margin-bottom:6px; }
  #mapper-section p { color:var(--muted); font-size:12px; margin-bottom:20px; }
  .mapper-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:12px; margin-bottom:20px; }

  #results-list { max-height:70vh; overflow-y:auto; padding-right:4px; }
  #results-list::-webkit-scrollbar { width:4px; }
  #results-list::-webkit-scrollbar-thumb { background:var(--border); border-radius:2px; }

  .toast { position:fixed; bottom:24px; right:24px; background:var(--surface2); border:1px solid var(--border); border-radius:var(--radius); padding:12px 20px; font-size:12px; opacity:0; transform:translateY(12px); transition:all 0.25s; z-index:999; max-width:320px; }
  .toast.show { opacity:1; transform:translateY(0); }
  .toast.error { border-color:var(--danger); color:var(--danger); }
  .toast.success { border-color:var(--accent); color:var(--accent); }

  #spinner { display:none; width:16px; height:16px; border:2px solid var(--border); border-top-color:var(--accent); border-radius:50%; animation:spin 0.7s linear infinite; }
  #spinner.visible { display:inline-block; }
  @keyframes spin { to { transform:rotate(360deg); } }
</style>
</head>
<body>

<header>
  <div class="logo">bought<span>·</span>together</div>
  <div class="status-pill" id="status-pill">
    <div class="dot"></div>
    <span id="status-text">No data loaded</span>
  </div>
</header>

<main>

  <!-- Upload Section -->
  <div id="upload-section">
    <div class="section-label">Step 1 · Upload your Shopify orders export</div>
    <div class="help-text">
      <strong>How to export from Shopify:</strong> Go to <em>Orders → Export → All orders → Export orders (CSV)</em>.<br>
      Your file is processed on the server and stays private. Large files with 70k+ orders work fine.
    </div>
    <div class="upload-zone" id="drop-zone">
      <input type="file" id="file-input" accept=".csv,.xlsx,.xls" />
      <span class="upload-icon">📦</span>
      <h2>Drop your orders CSV here</h2>
      <p>Supports <strong>.csv</strong> files from Shopify · Handles 100k+ orders</p>
      <button class="btn" id="choose-btn" onclick="document.getElementById('file-input').click(); event.stopPropagation();">Choose File</button>
    </div>
    <div id="progress-bar-wrap">
      <div class="progress-track"><div class="progress-fill" id="progress-fill"></div></div>
      <div class="progress-label" id="progress-label">Uploading…</div>
    </div>
  </div>

  <!-- Column Mapper (shown if auto-detect fails) -->
  <div id="mapper-section">
    <h3>Map your columns</h3>
    <p>We couldn't auto-detect all required columns. Please match your spreadsheet columns to the fields below.</p>
    <div class="mapper-grid" id="mapper-grid"></div>
    <button class="btn" onclick="submitWithMapping()">Confirm & Analyse →</button>
  </div>

  <!-- Stats Bar -->
  <div id="stats-bar">
    <div class="stat-box"><span class="val" id="stat-orders">0</span><span class="lbl">Orders</span></div>
    <div class="stat-box"><span class="val" id="stat-products">0</span><span class="lbl">Products</span></div>
    <div class="stat-box"><span class="val" id="stat-skus">0</span><span class="lbl">Unique SKUs</span></div>
    <div class="stat-box"><span class="val" id="stat-types">0</span><span class="lbl">Product Types</span></div>
  </div>

  <!-- Search Section -->
  <div id="search-section">
    <div class="section-label">Step 2 · Search for a product</div>
    <div class="search-grid">
      <div class="field">
        <label>Product Name</label>
        <input type="text" id="s-name" placeholder="e.g. Blue T-Shirt" />
      </div>
      <div class="field">
        <label>Variant SKU</label>
        <input type="text" id="s-sku" placeholder="e.g. SHIRT-BLU-M" />
      </div>
      <div class="field">
        <label>Product ID</label>
        <input type="text" id="s-id" placeholder="e.g. 12345678" />
      </div>
      <div class="field">
        <label>Product Type</label>
        <input type="text" id="s-type" placeholder="e.g. Apparel" list="types-list" />
        <datalist id="types-list"></datalist>
      </div>
    </div>
    <div class="search-actions">
      <button class="btn" onclick="runSearch()" id="search-btn">
        <span id="spinner"></span>
        Analyse →
      </button>
      <button class="btn secondary" onclick="clearSearch()">Clear</button>
      <button class="btn secondary" onclick="clearData()">🗑 Clear Data</button>
    </div>
  </div>

  <!-- Results Section -->
  <div id="results-section">
    <div class="results-header">
      <h3>Products bought with <span id="results-query"></span></h3>
      <div class="results-meta" id="results-meta"></div>
    </div>
    <div id="results-list"></div>
  </div>

</main>

<div class="toast" id="toast"></div>

<script>
// ── Config ────────────────────────────────────────────────────
// When running locally this points to localhost.
// When deployed, change this to your Railway/Render URL e.g.:
//   const API = "https://your-app.up.railway.app";
const API = window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1")
  ? "http://localhost:8000"
  : window.location.origin;  // assumes frontend is served from same origin

// ── State ─────────────────────────────────────────────────────
let pendingFile = null;
let pendingHeaders = [];
let serverLoaded = false;

// ── File handling ─────────────────────────────────────────────
document.getElementById('file-input').addEventListener('change', e => {
  if (e.target.files[0]) uploadFile(e.target.files[0]);
});
const dz = document.getElementById('drop-zone');
dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('dragover'); });
dz.addEventListener('dragleave', () => dz.classList.remove('dragover'));
dz.addEventListener('drop', e => {
  e.preventDefault(); dz.classList.remove('dragover');
  if (e.dataTransfer.files[0]) uploadFile(e.dataTransfer.files[0]);
});

async function uploadFile(file) {
  pendingFile = file;
  showProgress(true, 'Uploading file…', 20);

  const form = new FormData();
  form.append('file', file);

  try {
    const res = await fetch(`${API}/upload`, { method: 'POST', body: form });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();

    if (data.status === 'needs_mapping') {
      showProgress(false);
      pendingHeaders = data.headers;
      showMapper(data.headers, data.col_map);
    } else {
      showProgress(true, 'Processing complete!', 100);
      setTimeout(() => { showProgress(false); applyStats(data); }, 600);
    }
  } catch(err) {
    showProgress(false);
    showToast('Upload failed: ' + err.message, 'error');
  }
}

function showMapper(headers, detected) {
  const section = document.getElementById('mapper-section');
  const grid = document.getElementById('mapper-grid');
  grid.innerHTML = '';

  const fields = [
    { key: 'order_id',     label: 'Order ID *' },
    { key: 'product_name', label: 'Product Name *' },
    { key: 'sku',          label: 'SKU' },
    { key: 'product_id',   label: 'Product ID' },
    { key: 'product_type', label: 'Product Type' },
  ];

  fields.forEach(f => {
    const detectedIdx = detected[f.key] !== undefined ? detected[f.key] : '';
    const div = document.createElement('div');
    div.className = 'field';
    div.innerHTML = `
      <label>${f.label}</label>
      <select id="map-${f.key}">
        <option value="">— not mapped —</option>
        ${headers.map((h, i) => `<option value="${i}" ${detectedIdx===i?'selected':''}>${h}</option>`).join('')}
      </select>`;
    grid.appendChild(div);
  });

  section.classList.add('visible');
}

async function submitWithMapping() {
  const get = id => { const el = document.getElementById(id); return el ? el.value : ''; };
  const orderIdCol = get('map-order_id');
  const nameCol    = get('map-product_name');
  if (!orderIdCol && orderIdCol !== '0') { showToast('Order ID column is required', 'error'); return; }
  if (!nameCol    && nameCol    !== '0') { showToast('Product Name column is required', 'error'); return; }

  showProgress(true, 'Processing with your mapping…', 30);

  const params = new URLSearchParams({
    order_id_col:      orderIdCol,
    product_name_col:  nameCol,
    sku_col:           get('map-sku')          || -1,
    product_id_col:    get('map-product_id')   || -1,
    product_type_col:  get('map-product_type') || -1,
  });

  const form = new FormData();
  form.append('file', pendingFile);

  try {
    const res = await fetch(`${API}/upload-with-mapping?${params}`, { method: 'POST', body: form });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    showProgress(true, 'Done!', 100);
    document.getElementById('mapper-section').classList.remove('visible');
    setTimeout(() => { showProgress(false); applyStats(data); }, 600);
  } catch(err) {
    showProgress(false);
    showToast('Failed: ' + err.message, 'error');
  }
}

function applyStats(data) {
  document.getElementById('stat-orders').textContent   = (data.order_count   || 0).toLocaleString();
  document.getElementById('stat-products').textContent = (data.product_count || 0).toLocaleString();
  document.getElementById('stat-skus').textContent     = (data.sku_count     || 0).toLocaleString();
  document.getElementById('stat-types').textContent    = (data.type_count    || 0).toLocaleString();

  const dl = document.getElementById('types-list');
  if (data.types) dl.innerHTML = data.types.map(t => `<option value="${t}">`).join('');

  document.getElementById('stats-bar').classList.add('visible');
  document.getElementById('search-section').classList.add('visible');
  document.getElementById('upload-section').style.display = 'none';

  const pill = document.getElementById('status-pill');
  pill.classList.add('loaded');
  document.getElementById('status-text').textContent = `${(data.order_count||0).toLocaleString()} orders loaded`;
  serverLoaded = true;
  showToast(`✓ Loaded ${(data.order_count||0).toLocaleString()} orders`, 'success');
}

// ── Search ───────────────────────────────────────────────────
async function runSearch() {
  const name = document.getElementById('s-name').value.trim();
  const sku  = document.getElementById('s-sku').value.trim();
  const pid  = document.getElementById('s-id').value.trim();
  const type = document.getElementById('s-type').value.trim();

  if (!name && !sku && !pid && !type) { showToast('Enter at least one search term', 'error'); return; }

  setSearchLoading(true);

  const params = new URLSearchParams();
  if (name) params.set('name', name);
  if (sku)  params.set('sku',  sku);
  if (pid)  params.set('pid',  pid);
  if (type) params.set('type', type);

  try {
    const res = await fetch(`${API}/search?${params}`);
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || res.statusText);
    }
    const data = await res.json();
    showResults(data.results, name || sku || pid || type, data.match_count);
  } catch(err) {
    showToast('Search failed: ' + err.message, 'error');
  } finally {
    setSearchLoading(false);
  }
}

function setSearchLoading(on) {
  document.getElementById('spinner').classList.toggle('visible', on);
  document.getElementById('search-btn').disabled = on;
}

['s-name','s-sku','s-id','s-type'].forEach(id => {
  document.getElementById(id).addEventListener('keydown', e => { if (e.key === 'Enter') runSearch(); });
});

function showResults(results, query, matchCount) {
  const section = document.getElementById('results-section');
  section.classList.add('visible');
  document.getElementById('results-query').textContent = `"${query}"`;
  document.getElementById('results-meta').textContent =
    `Found in ${matchCount.toLocaleString()} order${matchCount !== 1 ? 's' : ''}`;

  const list = document.getElementById('results-list');
  if (!results.length) {
    list.innerHTML = `<div class="empty-state"><span>🔍</span><p>${matchCount > 0 ? 'This product was always bought alone.' : 'No orders matched your search.'}</p></div>`;
    return;
  }

  const maxPct = results[0].pct;
  list.innerHTML = results.map((r, i) => `
    <div class="product-card">
      <div>
        <div class="pc-rank">#${i+1}</div>
        <div class="pc-name">${esc(r.name)}</div>
        <div class="pc-meta">
          ${r.sku  ? `<span>🏷 ${esc(r.sku)}</span>` : ''}
          ${r.type ? `<span>📂 ${esc(r.type)}</span>` : ''}
          ${r.id   ? `<span>🆔 ${esc(r.id)}</span>` : ''}
        </div>
      </div>
      <div class="pc-right">
        <div class="pc-pct">${r.pct}%</div>
        <div class="pc-count">${r.count.toLocaleString()} order${r.count !== 1 ? 's' : ''}</div>
      </div>
      <div class="bar-wrap">
        <div class="bar-fill" style="width:${Math.round(r.pct/maxPct*100)}%"></div>
      </div>
    </div>
  `).join('');
}

function clearSearch() {
  ['s-name','s-sku','s-id','s-type'].forEach(id => document.getElementById(id).value = '');
  document.getElementById('results-section').classList.remove('visible');
}

async function clearData() {
  serverLoaded = false;
  pendingFile = null;
  document.getElementById('upload-section').style.display = 'block';
  document.getElementById('stats-bar').classList.remove('visible');
  document.getElementById('search-section').classList.remove('visible');
  document.getElementById('results-section').classList.remove('visible');
  document.getElementById('file-input').value = '';
  document.getElementById('status-pill').classList.remove('loaded');
  document.getElementById('status-text').textContent = 'No data loaded';
  clearSearch();
}

// ── Progress bar ─────────────────────────────────────────────
function showProgress(show, label='', pct=0) {
  const wrap = document.getElementById('progress-bar-wrap');
  wrap.classList.toggle('visible', show);
  document.getElementById('progress-fill').style.width = pct + '%';
  document.getElementById('progress-label').textContent = label;
  document.getElementById('choose-btn').disabled = show;
}

// ── Utils ────────────────────────────────────────────────────
function esc(s) {
  return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
let toastTimer;
function showToast(msg, type='') {
  const t = document.getElementById('toast');
  t.textContent = msg; t.className = 'toast show ' + type;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('show'), 3500);
}

// ── Check if server already has data (e.g. page refresh) ─────
(async () => {
  try {
    const res = await fetch(`${API}/stats`);
    if (res.ok) {
      const data = await res.json();
      applyStats(data);
    }
  } catch(e) { /* server not ready yet, that's fine */ }
})();
</script>
</body>
</html>
