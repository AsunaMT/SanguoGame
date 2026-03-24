/* ═══════════════════════════════════════════
   app.js — 主控制器（全局状态 + 工具函数）
   ═══════════════════════════════════════════ */

const API = {
  base: '',   // 同域

  async post(path, body = {}) {
    const r = await fetch(this.base + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${r.status}`);
    }
    return r.json();
  },

  async get(path) {
    const r = await fetch(this.base + path);
    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${r.status}`);
    }
    return r.json();
  },
};

// ── 全局游戏状态缓存 ───────────────────────────────────────
let G = {
  phase: 'idle',
  resources: {},
  ministers: {},
  date: '公元208年秋',
  turn: 1,
};

// ── 加载遮罩 ───────────────────────────────────────────────
function showLoading(text = '稍候……') {
  document.getElementById('loading-text').textContent = text;
  document.getElementById('loading-mask').classList.remove('hidden');
}
function hideLoading() {
  document.getElementById('loading-mask').classList.add('hidden');
}

// ── 界面切换 ───────────────────────────────────────────────
function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.add('hidden'));
  document.getElementById(id).classList.remove('hidden');
}

// ── 消息追加 ───────────────────────────────────────────────
function appendMessage(who, content, type = 'minister') {
  const wrap = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = `msg-bubble msg-${type}`;
  if (who) {
    const name = document.createElement('div');
    name.className = 'msg-name';
    name.textContent = who;
    div.appendChild(name);
  }
  const text = document.createElement('div');
  text.textContent = content;
  div.appendChild(text);
  wrap.appendChild(div);
  wrap.scrollTop = wrap.scrollHeight;
}

function appendSystem(text) {
  appendMessage(null, text, 'system');
}

// ── 资源面板更新 ──────────────────────────────────────────
function updateResourcePanel(res) {
  if (!res) return;
  G.resources = res;
  document.getElementById('res-troops').textContent = res.troops?.toLocaleString() ?? '-';
  document.getElementById('res-gold').textContent   = res.gold?.toLocaleString()   ?? '-';
  document.getElementById('res-food').textContent   = res.food?.toLocaleString()   ?? '-';
  document.getElementById('res-prestige').textContent = res.prestige ?? '-';
}

// ── 阶段显示更新 ──────────────────────────────────────────
const PHASE_ZH = {
  idle: '待机', kai_chao: '鸣鞭入殿', bingzou: '禀奏',
  yishi: '议事', nizhi: '拟旨', tui_chao: '退朝',
  world_update: '世界推进', week_report: '周报',
};
function updatePhaseDisplay(phase) {
  G.phase = phase;
  const el = document.getElementById('phase-display');
  if (el) {
    el.textContent = PHASE_ZH[phase] || phase;
    el.style.animation = 'none';
    void el.offsetWidth;
    el.style.animation = '';
  }
  // 按钮可见性
  const btnKai    = document.getElementById('btn-kai-chao');
  const btnYishi  = document.getElementById('btn-yishi');
  const btnNizhi  = document.getElementById('btn-nizhi');
  const btnTui    = document.getElementById('btn-tui-chao');
  const decreeArea = document.getElementById('decree-area');
  const chatBar   = document.querySelector('.chat-input-bar');

  btnKai.classList.toggle('hidden',   phase !== 'idle');
  btnYishi.classList.toggle('hidden', phase !== 'bingzou');
  btnNizhi.classList.toggle('hidden', phase !== 'yishi');
  btnTui.classList.toggle('hidden',   !['yishi','nizhi'].includes(phase));
  decreeArea.classList.toggle('hidden', phase !== 'nizhi');
  if (chatBar) chatBar.style.display = phase === 'yishi' ? 'flex' : 'none';
}

// ── 大臣面板更新 ──────────────────────────────────────────
function updateMinisterPanel(ministers) {
  if (!ministers) return;
  G.ministers = ministers;
  const list = document.getElementById('minister-list');
  list.innerHTML = '';
  const roleZH = { internal: '内政', military: '军事', diplomacy: '外交' };
  for (const [role, m] of Object.entries(ministers)) {
    const div = document.createElement('div');
    div.className = 'minister-entry';
    div.id = `me-${role}`;
    div.innerHTML = `
      <div class="me-name">${m.name}</div>
      <div class="me-role">${roleZH[role] || role}大臣</div>
      <div class="me-status" id="me-status-${role}">就位</div>
    `;
    list.appendChild(div);
  }

  // 同步对话框选项
  const sel = document.getElementById('minister-select');
  if (sel) {
    sel.innerHTML = '';
    for (const [role, m] of Object.entries(ministers)) {
      const opt = document.createElement('option');
      opt.value = role;
      opt.textContent = `${m.name}（${roleZH[role]}）`;
      sel.appendChild(opt);
    }
  }
}

function setMinisterStatus(role, status) {
  const el = document.getElementById(`me-status-${role}`);
  if (el) el.textContent = status;
  const entry = document.getElementById(`me-${role}`);
  if (entry) {
    entry.classList.toggle('speaking', status === '发言中…');
  }
}

// ── 资源浮动数字 ──────────────────────────────────────────
function floatDelta(elId, delta) {
  if (!delta) return;
  const el = document.getElementById(elId);
  if (!el) return;
  const rect = el.getBoundingClientRect();
  const span = document.createElement('span');
  span.className = `delta-float ${delta > 0 ? 'positive' : 'negative'}`;
  span.textContent = `${delta > 0 ? '+' : ''}${delta}`;
  span.style.left = `${rect.left + rect.width / 2}px`;
  span.style.top  = `${rect.top}px`;
  document.body.appendChild(span);
  setTimeout(() => span.remove(), 1300);
}

// ── 初始化：尝试加载已有存档 ──────────────────────────────
async function tryLoadExistingGame() {
  try {
    const data = await API.get('/api/world/state');
    if (data.turn >= 1) {
      updateResourcePanel(data.resources);
      updateMinisterPanel(data.ministers);
      updatePhaseDisplay(data.court_phase || 'idle');
      G.date = data.date;
      document.getElementById('date-display').textContent = data.date;
      showScreen('screen-court');
      appendSystem(`已恢复存档：第${data.turn}周，${data.date}`);
      return true;
    }
  } catch {
    /* 未创建游戏，显示开局 */
  }
  return false;
}

// ── 全局应用对象 ───────────────────────────────────────────
const app = {
  mainMenu: null,
  setupScreen: null,
  courtScreen: null,

  loadState: function(state) {
    updateResourcePanel(state.resources);
    updateMinisterPanel(state.ministers);
    updatePhaseDisplay(state.court_phase || 'idle');
    G.date = state.date;
    document.getElementById('date-display').textContent = state.date;
  },

  showPhaseTransition: function() {
    appendSystem(`── 进入${PHASE_ZH[G.phase] || G.phase}阶段 ──`);
  }
};

window.addEventListener('DOMContentLoaded', async () => {
  // 初始化主菜单
  if (typeof MainMenu !== 'undefined') {
    app.mainMenu = new MainMenu();
  }

  // 默认显示主菜单
  showScreen('screen-main-menu');
});
