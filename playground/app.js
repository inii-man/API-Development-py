// TaskHub API Studio - Interactive Client Logic

const API_BASE = window.location.origin;

// State
let currentPersona = 'alice';
const personaTokens = {
  alice: '',
  bob: '',
  manager: '',
  admin: ''
};

let latestCreatedTaskId = 'tsk_alice_1';
let latestTaskVersion = 1;
let quizAnswers = {};

// Presets data matching slides
const presets = {
  login_alice: {
    method: 'POST',
    path: '/api/v1/auth/token',
    headers: { 'Content-Type': 'application/json' },
    body: { username: 'alice', password: 'Lab-Only-123!' }
  },
  create_task: {
    method: 'POST',
    path: '/api/v1/tasks',
    headers: { 'Content-Type': 'application/json' },
    body: { title: 'Implementasi Kontrak REST TaskHub' },
    authPersona: 'alice'
  },
  list_tasks: {
    method: 'GET',
    path: '/api/v1/tasks?page=1&pageSize=20',
    headers: {},
    body: null,
    authPersona: 'alice'
  },
  detail_task: {
    method: 'GET',
    path: () => `/api/v1/tasks/${latestCreatedTaskId}`,
    headers: {},
    body: null,
    authPersona: 'alice'
  },
  patch_v1: {
    method: 'PATCH',
    path: () => `/api/v1/tasks/${latestCreatedTaskId}`,
    headers: { 'Content-Type': 'application/json' },
    body: () => ({ status: 'done', version: latestTaskVersion }),
    authPersona: 'alice'
  },
  patch_conflict: {
    method: 'PATCH',
    path: () => `/api/v1/tasks/${latestCreatedTaskId}`,
    headers: { 'Content-Type': 'application/json' },
    body: () => ({ status: 'open', version: 1 }), // Send old version 1 on purpose
    authPersona: 'alice'
  },
  login_bob: {
    method: 'POST',
    path: '/api/v1/auth/token',
    headers: { 'Content-Type': 'application/json' },
    body: { username: 'bob', password: 'Lab-Only-123!' }
  },
  bob_bola_attack: {
    method: 'GET',
    path: () => `/api/v1/tasks/${latestCreatedTaskId}`,
    headers: {},
    body: null,
    authPersona: 'bob'
  },
  mass_assignment: {
    method: 'POST',
    path: '/api/v1/tasks',
    headers: { 'Content-Type': 'application/json' },
    body: { title: 'Uji Coba Injeksi Owner', owner_id: 'u2', role: 'admin' },
    authPersona: 'alice'
  },
  boundary_page0: {
    method: 'GET',
    path: '/api/v1/tasks?page=0',
    headers: {},
    body: null,
    authPersona: 'alice'
  },
  malformed_json: {
    method: 'POST',
    path: '/api/v1/tasks',
    headers: { 'Content-Type': 'application/json' },
    rawBody: '{ title: broken_json_without_quotes }',
    authPersona: 'alice'
  },
  delete_task: {
    method: 'DELETE',
    path: () => `/api/v1/tasks/${latestCreatedTaskId}`,
    headers: {},
    body: null,
    authPersona: 'alice'
  },
  get_deleted: {
    method: 'GET',
    path: () => `/api/v1/tasks/${latestCreatedTaskId}`,
    headers: {},
    body: null,
    authPersona: 'alice'
  }
};

// Initialize app
window.addEventListener('DOMContentLoaded', async () => {
  setupShortcuts();
  await ensurePersonaToken('alice');
  updateHeadersEditor();
  refreshDbView();
  loadOpenApiYaml();
  loadModuleDoc('01');
});

// Tab navigation
function showTab(tabName) {
  document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-tab-btn').forEach(el => el.classList.remove('active'));
  
  const targetPane = document.getElementById(`pane-${tabName}`);
  if (targetPane) targetPane.classList.add('active');

  const clickedBtn = Array.from(document.querySelectorAll('.nav-tab-btn')).find(b => b.getAttribute('onclick')?.includes(tabName));
  if (clickedBtn) clickedBtn.classList.add('active');

  if (tabName === 'db-inspector') {
    refreshDbView();
  }
}

// Persona management
async function switchPersona(name) {
  currentPersona = name;
  document.querySelectorAll('.persona-btn').forEach(btn => btn.classList.remove('active'));
  const targetBtn = document.getElementById(`btnPersona${capitalize(name)}`);
  if (targetBtn) targetBtn.classList.add('active');

  await ensurePersonaToken(name);
  updateHeadersEditor();
  
  const roleMap = {
    alice: 'Alice (u1 - Member A)',
    bob: 'Bob (u2 - Member B)',
    manager: 'Manager (u3 - Manager A)',
    admin: 'Admin (u4 - Admin ALL)'
  };
  const ind = document.getElementById('authStatusIndicator');
  if (ind) ind.textContent = `Token: ${roleMap[name] || name}`;
}

async function ensurePersonaToken(name) {
  if (personaTokens[name]) return personaTokens[name];
  try {
    const res = await fetch(`${API_BASE}/api/v1/auth/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: name, password: 'Lab-Only-123!' })
    });
    const data = await res.json();
    if (res.ok && data.token) {
      personaTokens[name] = data.token;
      return data.token;
    }
  } catch (err) {
    console.error('Gagal mengambil token untuk', name, err);
  }
  return '';
}

function updateHeadersEditor() {
  const token = personaTokens[currentPersona];
  const headers = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const method = document.getElementById('reqMethod').value;
  if (['POST', 'PATCH', 'PUT'].includes(method)) {
    headers['Content-Type'] = 'application/json';
  }
  document.getElementById('reqHeaders').value = Object.entries(headers)
    .map(([k, v]) => `${k}: ${v}`)
    .join('\n');
}

function updateMethodColor(selectEl) {
  selectEl.className = `form-select method-select ${selectEl.value}`;
  updateHeadersEditor();
}

function applyPreset(key) {
  if (!key || !presets[key]) return;
  const p = presets[key];

  if (p.authPersona) {
    switchPersona(p.authPersona);
  }

  const methodSelect = document.getElementById('reqMethod');
  methodSelect.value = p.method;
  updateMethodColor(methodSelect);

  const path = typeof p.path === 'function' ? p.path() : p.path;
  document.getElementById('reqPath').value = path;

  // Set headers
  const headers = { ...p.headers };
  const currentToken = personaTokens[currentPersona];
  if (currentToken && !path.includes('/auth/token')) {
    headers['Authorization'] = `Bearer ${currentToken}`;
  }
  document.getElementById('reqHeaders').value = Object.entries(headers)
    .map(([k, v]) => `${k}: ${v}`)
    .join('\n');

  // Set body
  if (p.rawBody) {
    document.getElementById('reqBody').value = p.rawBody;
  } else if (p.body) {
    const bodyObj = typeof p.body === 'function' ? p.body() : p.body;
    document.getElementById('reqBody').value = JSON.stringify(bodyObj, null, 2);
  } else {
    document.getElementById('reqBody').value = '';
  }
}

// Request execution
async function executeApiRequest() {
  const btn = document.getElementById('btnSendRequest');
  btn.disabled = true;
  btn.style.opacity = '0.7';

  const method = document.getElementById('reqMethod').value;
  const rawPath = document.getElementById('reqPath').value.trim();
  const path = rawPath.startsWith('http') ? rawPath : `${API_BASE}${rawPath.startsWith('/') ? '' : '/'}${rawPath}`;
  
  // Parse headers
  const headerLines = document.getElementById('reqHeaders').value.split('\n');
  const headers = {};
  headerLines.forEach(line => {
    const idx = line.indexOf(':');
    if (idx > -1) {
      const k = line.substring(0, idx).trim();
      const v = line.substring(idx + 1).trim();
      if (k) headers[k] = v;
    }
  });

  // Body
  let body = undefined;
  if (['POST', 'PATCH', 'PUT'].includes(method)) {
    body = document.getElementById('reqBody').value;
  }

  const startTime = performance.now();
  try {
    const response = await fetch(path, {
      method,
      headers,
      body: body ? body : undefined
    });
    const endTime = performance.now();
    const duration = Math.round(endTime - startTime);

    document.getElementById('respLatency').textContent = `${duration} ms`;

    // Status badge
    const status = response.status;
    const statusBadge = document.getElementById('respStatusBadge');
    statusBadge.textContent = `${status} ${response.statusText || getStatusText(status)}`;
    statusBadge.className = 'status-badge';
    if (status >= 200 && status < 300) statusBadge.classList.add('s-2xx');
    else if (status === 409) statusBadge.classList.add('s-409');
    else if (status >= 400 && status < 500) statusBadge.classList.add('s-4xx');
    else statusBadge.classList.add('s-5xx');

    // Headers preview
    const respHeadersObj = {};
    response.headers.forEach((v, k) => { respHeadersObj[k] = v; });
    document.getElementById('respHeaders').textContent = Object.entries(respHeadersObj)
      .map(([k, v]) => `${k}: ${v}`).join('\n') || '(Tidak ada header tambahan)';

    // Body
    if (status === 204) {
      document.getElementById('respBodyViewer').textContent = '// [204 No Content] Operasi berhasil tanpa response body.';
    } else {
      const text = await response.text();
      try {
        const json = JSON.parse(text);
        document.getElementById('respBodyViewer').innerHTML = syntaxHighlightJson(json);
        
        // Auto capture latest taskId or token
        if (json.data && json.data.id && json.data.id.startsWith('tsk_')) {
          latestCreatedTaskId = json.data.id;
          latestTaskVersion = json.data.version || 1;
        }
        if (path.includes('/auth/token') && json.token) {
          personaTokens[currentPersona] = json.token;
          updateHeadersEditor();
        }
      } catch {
        document.getElementById('respBodyViewer').textContent = text;
      }
    }

    refreshDbView();
  } catch (err) {
    document.getElementById('respStatusBadge').textContent = 'ERR NETWORK';
    document.getElementById('respStatusBadge').className = 'status-badge s-5xx';
    document.getElementById('respBodyViewer').textContent = `Koneksi gagal atau server offline: ${err.message}`;
  } finally {
    btn.disabled = false;
    btn.style.opacity = '1';
  }
}

// BOLA Simulation Tab
function runBolaSimulation() {
  const caller = document.getElementById('simCaller').value;
  const target = document.getElementById('simTargetTask').value;
  const logSteps = document.getElementById('simLogSteps');

  const callerMeta = {
    alice: { id: 'u1', name: 'Alice', role: 'member', team: 'A' },
    bob: { id: 'u2', name: 'Bob', role: 'member', team: 'B' },
    manager: { id: 'u3', name: 'Manager Tim A', role: 'manager', team: 'A' },
    admin: { id: 'u4', name: 'Admin', role: 'admin', team: 'ALL' }
  }[caller];

  const targetMeta = {
    task_alice: { id: 'tsk_alice_1', owner_id: 'u1', owner_name: 'Alice', owner_team: 'A' },
    task_bob: { id: 'tsk_bob_1', owner_id: 'u2', owner_name: 'Bob', owner_team: 'B' }
  }[target];

  let steps = [];
  steps.push(`[1] Verifikasi Otentikasi: Token pemanggil valid -> User: ${callerMeta.name} (Role: ${callerMeta.role}, Tim: ${callerMeta.team})`);
  steps.push(`[2] Query Resource Target: Task ID '${targetMeta.id}' ditemukan -> Owner ID: ${targetMeta.owner_id} (${targetMeta.owner_name}, Tim: ${targetMeta.owner_team})`);
  steps.push(`[3] Masuk ke fungsi can_access(con, user, task)...`);

  let allowed = false;
  let reason = '';

  if (callerMeta.role === 'admin') {
    steps.push(`    -> Aturan 1: user['role'] == 'admin' -> TRUE`);
    allowed = true;
    reason = 'Admin memiliki otorisasi universal untuk membaca dan memanipulasi semua task.';
  } else if (targetMeta.owner_id === callerMeta.id) {
    steps.push(`    -> Aturan 1: user['role'] == 'admin' -> FALSE`);
    steps.push(`    -> Aturan 2: task['owner_id'] == user['id'] ('${targetMeta.owner_id}' == '${callerMeta.id}') -> TRUE`);
    allowed = true;
    reason = 'Pemanggil adalah pemilik sah (Owner) dari task tersebut.';
  } else if (callerMeta.role === 'manager' && targetMeta.owner_team === callerMeta.team) {
    steps.push(`    -> Aturan 1: user['role'] == 'admin' -> FALSE`);
    steps.push(`    -> Aturan 2: task['owner_id'] == user['id'] -> FALSE`);
    steps.push(`    -> Aturan 3: user['role'] == 'manager' AND owner['team'] == user['team'] ('${targetMeta.owner_team}' == '${callerMeta.team}') -> TRUE`);
    allowed = true;
    reason = 'Manager berhak mengakses task karena pemilik task berada di dalam tim yang sama (Tim A).';
  } else {
    steps.push(`    -> Aturan 1: user['role'] == 'admin' -> FALSE`);
    steps.push(`    -> Aturan 2: task['owner_id'] == user['id'] -> FALSE`);
    steps.push(`    -> Aturan 3: user['role'] == 'manager' AND owner['team'] == user['team'] -> FALSE`);
    steps.push(`    -> Default: return FALSE (Pertahanan BOLA aktif)`);
    allowed = false;
    reason = callerMeta.role === 'manager' 
      ? `Manager Tim ${callerMeta.team} dilarang membaca task milik Tim ${targetMeta.owner_team} (Beda Tim).`
      : `${callerMeta.name} bukan pemilik task ini dan tidak memiliki hak eskalasi objek.`;
  }

  const resultColor = allowed ? '#34d399' : '#fb7185';
  const resultIcon = allowed ? '✅ HAK AKSES DITERIMA (ALLOW - 200 OK)' : '🚫 AKSES DITOLAK (DENY - 403 FORBIDDEN)';

  logSteps.innerHTML = `
    ${steps.map(s => `<div>${s}</div>`).join('')}
    <div style="margin-top:0.75rem; padding:0.5rem 0.75rem; border-radius:4px; font-weight:700; color:${resultColor}; background:rgba(0,0,0,0.3); border-left:4px solid ${resultColor};">
      ${resultIcon}<br>
      <span style="font-size:0.78rem; font-weight:400; color:#cbd5e1;">Alasan: ${reason}</span>
    </div>
  `;
}

// Concurrency Simulator Tab
async function simUpdateClientA() {
  const box = document.getElementById('simResultA');
  box.textContent = 'Mengirim request PATCH (version: 1)...';
  box.style.color = '#60a5fa';

  const token = await ensurePersonaToken('alice');
  const res = await fetch(`${API_BASE}/api/v1/tasks/tsk_alice_1`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ status: 'done', version: 1 })
  });
  const data = await res.json();
  if (res.status === 200) {
    box.textContent = `✅ 200 OK: Berhasil update! Task sekarang status='done', version=${data.data.version}.`;
    box.style.color = '#34d399';
  } else {
    box.textContent = `⚠️ Status ${res.status}: ${data.error?.code || 'Gagal'}`;
    box.style.color = '#fbbf24';
  }
  refreshDbView();
}

async function simUpdateClientB() {
  const box = document.getElementById('simResultB');
  box.textContent = 'Mengirim request PATCH (version: 1)...';
  box.style.color = '#f43f5e';

  const token = await ensurePersonaToken('alice');
  const res = await fetch(`${API_BASE}/api/v1/tasks/tsk_alice_1`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ status: 'open', version: 1 })
  });
  const data = await res.json();
  if (res.status === 409) {
    box.innerHTML = `💥 <strong>409 Conflict</strong> (${data.error?.code}):<br>${data.error?.message}`;
    box.style.color = '#fbbf24';
  } else if (res.status === 200) {
    box.textContent = `✅ 200 OK: Berhasil update! Task version=${data.data.version}.`;
    box.style.color = '#34d399';
  } else {
    box.textContent = `⚠️ Status ${res.status}: ${data.error?.code || 'Gagal'}`;
    box.style.color = '#fb7185';
  }
  refreshDbView();
}

// Database Inspector Tab
async function refreshDbView() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/debug/db`);
    if (!res.ok) return;
    const db = await res.json();

    // Render Tasks
    const tasksTbody = document.querySelector('#dbTasksTable tbody');
    if (tasksTbody) {
      if (db.tasks && db.tasks.length > 0) {
        tasksTbody.innerHTML = db.tasks.map(t => `
          <tr>
            <td style="color:#60a5fa;">${t.id}</td>
            <td>${escapeHtml(t.title)}</td>
            <td><span class="status-badge ${t.status === 'done' ? 's-2xx' : 's-409'}">${t.status}</span></td>
            <td>${t.owner_id}</td>
            <td style="font-weight:700; color:#38bdf8;">${t.version}</td>
          </tr>
        `).join('');
      } else {
        tasksTbody.innerHTML = '<tr><td colspan="5" style="color:var(--text-dim);">Belum ada data task.</td></tr>';
      }
    }

    // Render Tokens
    const tokensTbody = document.querySelector('#dbTokensTable tbody');
    if (tokensTbody) {
      if (db.tokens && db.tokens.length > 0) {
        tokensTbody.innerHTML = db.tokens.map(tk => `
          <tr>
            <td style="color:#a78bfa;">${tk.hash_preview}</td>
            <td>${tk.user_id}</td>
            <td>${tk.expires}</td>
            <td style="color:${tk.ttl_sec > 60 ? '#34d399' : '#fb7185'}; font-weight:700;">${tk.ttl_sec}s</td>
          </tr>
        `).join('');
      } else {
        tokensTbody.innerHTML = '<tr><td colspan="4" style="color:var(--text-dim);">Belum ada token aktif di database.</td></tr>';
      }
    }

    // Render Users
    const usersTbody = document.querySelector('#dbUsersTable tbody');
    if (usersTbody) {
      usersTbody.innerHTML = db.users.map(u => `
        <tr>
          <td style="color:#38bdf8;">${u.id}</td>
          <td style="font-weight:700;">${u.username}</td>
          <td><span class="status-badge s-2xx">${u.role}</span></td>
          <td>${u.team}</td>
          <td style="color:var(--text-dim);">${u.salt}</td>
          <td style="color:#94a3b8;">${u.hash_preview}</td>
        </tr>
      `).join('');
    }
  } catch (err) {
    console.error('Gagal refresh database view', err);
  }
}

async function resetDatabase() {
  if (!confirm('Apakah Anda yakin ingin mereset database ke keadaan awal seed?')) return;
  try {
    const res = await fetch(`${API_BASE}/api/v1/debug/reset`, { method: 'POST' });
    if (res.ok) {
      alert('Database berhasil di-reset ke kondisi awal!');
      personaTokens.alice = '';
      personaTokens.bob = '';
      personaTokens.manager = '';
      personaTokens.admin = '';
      await ensurePersonaToken('alice');
      updateHeadersEditor();
      refreshDbView();
    }
  } catch (err) {
    alert('Gagal mereset database: ' + err.message);
  }
}

// OpenAPI Viewer Tab
async function loadOpenApiYaml() {
  try {
    const res = await fetch(`${API_BASE}/openapi.yaml`);
    if (res.ok) {
      const text = await res.text();
      document.getElementById('openapiYamlViewer').textContent = text;
    }
  } catch (err) {
    document.getElementById('openapiYamlViewer').textContent = 'Gagal memuat openapi.yaml';
  }
}

// Bahan Ajar Reader
const moduleDocs = {
  '01': {
    title: 'Modul 1: Fondasi REST & Semantik HTTP',
    content: `
      <h1>Modul 1: Fondasi REST & Semantik HTTP</h1>
      <p><em>API Development Training - Hari 1: Bagian 2</em></p>
      <hr style="border-color:var(--border-subtle); margin:1.5rem 0;">
      <h2>1. API Sebagai Kontrak Antarperangkat Lunak</h2>
      <p>API adalah spesifikasi kontrak formal yang mengikat klien dan server tanpa perlu mengetahui kode internal masing-masing.</p>
      <blockquote>
        <strong>Prinsip Inti:</strong> Satu operasi harus dapat dipahami dan dijalankan tanpa mengetahui nama tabel atau framework yang digunakan server.
      </blockquote>
      <h2>2. Enam Batasan (Constraints) REST</h2>
      <ul>
        <li><strong>Client-Server:</strong> Pemisahan tanggung jawab antarmuka pengguna dari data storage.</li>
        <li><strong>Stateless:</strong> Setiap request membawa seluruh kredensial dan konteks lengkap. Server tidak menyimpan percakapan di memori.</li>
        <li><strong>Cacheable:</strong> Respons mendeklarasikan apakah data boleh disimpan ulang oleh perantara.</li>
        <li><strong>Uniform Interface:</strong> Resource diidentifikasi lewat URI seragam dan representasi standar.</li>
        <li><strong>Layered System:</strong> Klien tidak perlu tahu apakah tersambung langsung atau via gateway/proxy.</li>
        <li><strong>Code-on-Demand (Opsional):</strong> Server dapat mengirimkan script untuk dieksekusi klien.</li>
      </ul>
      <h2>3. Semantik HTTP Method</h2>
      <table>
        <thead>
          <tr><th>Method</th><th>Semantik</th><th>Safe?</th><th>Idempotent?</th></tr>
        </thead>
        <tbody>
          <tr><td><strong>GET</strong></td><td>Baca representasi</td><td>Ya</td><td>Ya</td></tr>
          <tr><td><strong>POST</strong></td><td>Buat resource / domain action</td><td>Tidak</td><td>Tidak otomatis</td></tr>
          <tr><td><strong>PUT</strong></td><td>Ganti representasi penuh</td><td>Tidak</td><td>Ya</td></tr>
          <tr><td><strong>PATCH</strong></td><td>Perubahan parsial</td><td>Tidak</td><td>Tergantung implementasi</td></tr>
          <tr><td><strong>DELETE</strong></td><td>Hapus resource</td><td>Tidak</td><td>Ya (semantik akhir sama)</td></tr>
        </tbody>
      </table>
    `
  },
  '02': {
    title: 'Modul 2: Desain Kontrak & Validasi',
    content: `
      <h1>Modul 2: Desain Kontrak API, Validasi, & Penanganan Error</h1>
      <p><em>API Development Training - Hari 1: Bagian 3</em></p>
      <hr style="border-color:var(--border-subtle); margin:1.5rem 0;">
      <h2>1. Pertahanan dari Serangan Mass Assignment</h2>
      <p>Klien dilarang mengirimkan field internal seperti <code>owner_id</code>, <code>role</code>, atau <code>is_admin</code> saat membuat task. Server harus menggunakan skema allowlist dan menolak field tak dikenal dengan status <strong>422 Unprocessable Entity</strong>.</p>
      <blockquote>
        <strong>Aturan Emas:</strong> <code>owner_id</code> selalu ditentukan secara mutlak oleh server dari Bearer Token, bukan dari request body klien!
      </blockquote>
      <h2>2. Kontrol Konkurensi: Optimistic Locking</h2>
      <pre><code>UPDATE tasks SET status=?, version=version+1 WHERE id=? AND version=?;</code></pre>
      <p>Jika <code>cur.rowcount == 0</code>, server mengembalikan <strong>409 Conflict (VERSION_CONFLICT)</strong>.</p>
      <h2>3. Taksonomi Status Code</h2>
      <ul>
        <li><strong>201 Created:</strong> Wajib menyertakan header <code>Location: /api/v1/tasks/{id}</code>.</li>
        <li><strong>204 No Content:</strong> Sukses tanpa response body.</li>
        <li><strong>400 Bad Request:</strong> JSON rusak / parse error.</li>
        <li><strong>401 Unauthenticated:</strong> Token tidak ada atau kedaluwarsa.</li>
        <li><strong>403 Forbidden:</strong> Hak akses kurang (BOLA defense).</li>
        <li><strong>422 Unprocessable Entity:</strong> Format JSON valid tapi gagal validasi bisnis.</li>
      </ul>
    `
  },
  '03': {
    title: 'Modul 3: OpenAPI 3.1.1 Sebagai Kontrak',
    content: `
      <h1>Modul 3: OpenAPI 3.1.1 Sebagai Kontrak Teruji</h1>
      <p><em>API Development Training - Hari 1: Bagian 4</em></p>
      <hr style="border-color:var(--border-subtle); margin:1.5rem 0;">
      <h2>1. Contract-First Workflow</h2>
      <p>OpenAPI mendeskripsikan server, path, method, parameter, body, response, schema, dan security. Swagger UI hanyalah alat penampil visual.</p>
      <h2>2. Komponen openapi.yaml TaskHub</h2>
      <ul>
        <li><strong>Security Global:</strong> <code>bearerAuth: []</code> secara default mengunci seluruh endpoint.</li>
        <li><strong>Public Override:</strong> <code>/api/v1/auth/token</code> diatur dengan <code>security: []</code>.</li>
        <li><strong>Strict Schema:</strong> Komponen <code>CreateTask</code> menyertakan <code>additionalProperties: false</code> untuk mencegah mass assignment.</li>
      </ul>
    `
  },
  '04': {
    title: 'Modul 4: Autentikasi, RBAC & BOLA',
    content: `
      <h1>Modul 4: Autentikasi, RBAC, dan Pencegahan BOLA</h1>
      <p><em>API Development Training - Hari 1: Bagian 5</em></p>
      <hr style="border-color:var(--border-subtle); margin:1.5rem 0;">
      <h2>1. Autentikasi vs Otorisasi</h2>
      <p>Autentikasi (401) memastikan <em>siapa Anda</em>. Otorisasi (403) menentukan <em>apakah Anda boleh menyentuh objek ini</em>.</p>
      <h2>2. Bahaya BOLA (Broken Object Level Authorization)</h2>
      <p>BOLA terjadi saat Bob mengganti ID di URL ke milik Alice, dan server lalai memeriksa apakah Bob pemiliknya. UUID acak bukan pengganti otorisasi objek!</p>
      <h2>3. Logika can_access TaskHub Lab</h2>
      <pre><code>def can_access(con, user, task):
    if user["role"] == "admin" or task["owner_id"] == user["id"]:
        return True
    owner = con.execute("SELECT team FROM users WHERE id=?", (task["owner_id"],)).fetchone()
    return user["role"] == "manager" and owner["team"] == user["team"]</code></pre>
    `
  },
  '05': {
    title: 'Modul 5: Panduan Praktik Lab Hands-on',
    content: `
      <h1>Modul 5: Panduan Praktik Lab & Langkah Hands-on</h1>
      <p><em>API Development Training - Hari 1: Bagian 6 & 7</em></p>
      <hr style="border-color:var(--border-subtle); margin:1.5rem 0;">
      <h2>1. Menjalankan Server & Testing</h2>
      <pre><code>python3 -m unittest -v test_lab test_http
python3 app.py</code></pre>
      <h2>2. Akun Demo Lab-Only</h2>
      <ul>
        <li><code>alice</code> (Member Tim A) - Pass: <code>Lab-Only-123!</code></li>
        <li><code>bob</code> (Member Tim B) - Pass: <code>Lab-Only-123!</code></li>
        <li><code>manager</code> (Manager Tim A) - Pass: <code>Lab-Only-123!</code></li>
        <li><code>admin</code> (Administrator ALL) - Pass: <code>Lab-Only-123!</code></li>
      </ul>
    `
  },
  '06': {
    title: 'Modul 6: Evaluasi 7 Kunci & Latihan',
    content: `
      <h1>Modul 6: Evaluasi, Matriks Keamanan, & Latihan Perluasan</h1>
      <p><em>API Development Training - Hari 1: Bagian 8</em></p>
      <hr style="border-color:var(--border-subtle); margin:1.5rem 0;">
      <h2>Tujuh Poin Kunci yang Harus Dikuasai</h2>
      <ol>
        <li>Stateless tidak melarang database.</li>
        <li>401 dan 403 menguji masalah berbeda.</li>
        <li>JWT valid belum membuktikan user boleh membaca task pihak lain.</li>
        <li>UUID bukan pengganti otorisasi objek.</li>
        <li>Basic Auth/base64 bukan enkripsi.</li>
        <li>OAuth bisa memakai opaque token atau JWT.</li>
        <li>Dokumentasi lengkap mendefinisikan semua schema dan error relevan.</li>
      </ol>
    `
  }
};

function loadModuleDoc(modId) {
  document.querySelectorAll('.reader-nav-item').forEach(el => el.classList.remove('active'));
  const activeNavItem = Array.from(document.querySelectorAll('.reader-nav-item')).find(el => el.getAttribute('onclick')?.includes(modId));
  if (activeNavItem) activeNavItem.classList.add('active');

  const doc = moduleDocs[modId];
  if (doc) {
    document.getElementById('readerContentArea').innerHTML = doc.content;
  }
}

// Quiz evaluation
function checkAnswer(qNum, selected, correct) {
  const fb = document.getElementById(`feedback-${qNum}`);
  if (selected === correct) {
    quizAnswers[qNum] = true;
    fb.className = 'quiz-feedback correct';
    fb.innerHTML = '<strong>Jawaban Benar!</strong> Prinsip ini sesuai dengan standar evaluasi Slide 67.';
  } else {
    quizAnswers[qNum] = false;
    fb.className = 'quiz-feedback wrong';
    fb.innerHTML = '<strong>Kurang Tepat.</strong> Silakan pelajari kembali modul materi terkait di tab Bahan Ajar.';
  }

  const score = Object.values(quizAnswers).filter(Boolean).length;
  document.getElementById('quizScoreBadge').textContent = `Skor: ${score} / 7`;
}

// Utility functions
function formatJsonEditor() {
  const el = document.getElementById('reqBody');
  try {
    const obj = JSON.parse(el.value);
    el.value = JSON.stringify(obj, null, 2);
  } catch (err) {
    alert('JSON tidak valid, tidak dapat diformat: ' + err.message);
  }
}

function copyResponseBody() {
  const text = document.getElementById('respBodyViewer').textContent;
  navigator.clipboard.writeText(text);
  alert('Response body berhasil disalin ke clipboard!');
}

function syntaxHighlightJson(json) {
  if (typeof json !== 'string') {
    json = JSON.stringify(json, undefined, 2);
  }
  json = escapeHtml(json);
  return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
    let cls = 'json-number';
    if (/^"/.test(match)) {
      if (/:$/.test(match)) {
        cls = 'json-key';
      } else {
        cls = 'json-string';
      }
    } else if (/true|false/.test(match)) {
      cls = 'json-boolean';
    } else if (/null/.test(match)) {
      cls = 'json-null';
    }
    return `<span class="${cls}">${match}</span>`;
  });
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function getStatusText(code) {
  const map = {
    200: 'OK', 201: 'Created', 202: 'Accepted', 204: 'No Content',
    400: 'Bad Request', 401: 'Unauthenticated', 403: 'Forbidden',
    404: 'Not Found', 409: 'Conflict', 413: 'Payload Too Large',
    415: 'Unsupported Media Type', 422: 'Unprocessable Entity',
    429: 'Too Many Requests', 500: 'Internal Server Error'
  };
  return map[code] || '';
}

function setupShortcuts() {
  window.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      executeApiRequest();
    }
  });
}
