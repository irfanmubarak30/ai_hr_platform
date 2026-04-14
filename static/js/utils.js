// ─── Shared Utilities ──────────────────────────────────────────────────────

const API = {
  async get(path) {
    const r = await fetch(path);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  },
  async post(path, data) {
    const r = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  },
  async postForm(path, formData) {
    const r = await fetch(path, { method: 'POST', body: formData });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  },
  async put(path, data) {
    const r = await fetch(path, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return r.json();
  },
  async delete(path) {
    const r = await fetch(path, { method: 'DELETE' });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  }
};

// ─── Toast Notifications ──────────────────────────────────────────────────

function toast(message, type = 'info', duration = 4000) {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${icons[type] || '•'}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = 'toastOut 0.3s ease forwards';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ─── Score Helpers ────────────────────────────────────────────────────────

function scoreClass(score) {
  if (score >= 7) return 'high';
  if (score >= 5) return 'medium';
  return 'low';
}

function scoreColorClass(score) {
  if (score >= 7) return 'score-high';
  if (score >= 5) return 'score-medium';
  return 'score-low';
}

function renderScore(score) {
  const cls = scoreClass(score);
  const colorCls = scoreColorClass(score);
  const pct = (score / 10) * 100;
  return `
    <div class="score-display">
      <div class="score-bar"><div class="score-fill ${cls}" style="width:${pct}%"></div></div>
      <span class="score-num ${colorCls}">${score}</span>
    </div>
  `;
}

function statusBadge(status) {
  const map = {
    'appoint': '<span class="badge badge-appoint">✓ Appointed</span>',
    'reject': '<span class="badge badge-reject">✗ Rejected</span>',
    'open': '<span class="badge badge-open">● Open</span>',
    'closed': '<span class="badge badge-closed">Closed</span>',
    'pending': '<span class="badge badge-pending">Pending</span>'
  };
  return map[status?.toLowerCase()] || `<span class="badge">${status || '—'}</span>`;
}

// ─── Date Formatting ──────────────────────────────────────────────────────

function formatDate(isoStr) {
  if (!isoStr) return '—';
  const d = new Date(isoStr);
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
}

function timeAgo(isoStr) {
  if (!isoStr) return '';
  const diff = Date.now() - new Date(isoStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

// ─── Name Helpers ─────────────────────────────────────────────────────────

function candidateName(c) {
  const info = c.candidate || c;
  return `${info.first_name || ''} ${info.last_name || ''}`.trim() || 'Unknown';
}

function initials(name) {
  return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
}

// ─── Copy to Clipboard ────────────────────────────────────────────────────

function copyText(text) {
  navigator.clipboard.writeText(text).then(() => toast('Copied to clipboard', 'success'));
}

// ─── Set Active Nav ────────────────────────────────────────────────────────

function setActiveNav() {
  const page = location.pathname.replace('/', '').replace('.html', '') || 'dashboard';
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.page === page);
  });
}

document.addEventListener('DOMContentLoaded', setActiveNav);

// Animate numbers on load
function animateNumber(el, target, duration = 800) {
  const start = 0;
  const step = target / (duration / 16);
  let current = start;
  const timer = setInterval(() => {
    current = Math.min(current + step, target);
    el.textContent = Math.round(current);
    if (current >= target) clearInterval(timer);
  }, 16);
}
